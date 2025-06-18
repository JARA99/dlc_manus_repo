from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
import uuid
import asyncio
import logging
from datetime import datetime
from app.models import Search, SearchResult, Product, Vendor, Category
from app.schemas.search import SearchRequest, SearchStatus, SearchResultResponse, SearchComparison
from app.scraping import scraping_engine, ScrapingResult
from app.api.websocket import manager

logger = logging.getLogger(__name__)


class SearchService:
    """Service for handling product searches with search-first, save-later architecture."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # Cache vendor names to avoid repeated DB queries
        self._vendor_cache = {}
    
    async def initiate_search(self, search_request: SearchRequest, client_ip: str = None) -> str:
        """
        Initiate a new product search with immediate response.
        
        Args:
            search_request: Search parameters
            client_ip: Client IP address for tracking
            
        Returns:
            Search ID for tracking progress
        """
        # Create search record (minimal DB operation)
        search_id = str(uuid.uuid4())
        
        search = Search(
            id=search_id,
            query=search_request.query,
            normalized_query=self._normalize_query(search_request.query),
            filters=search_request.filters.model_dump() if search_request.filters else None,
            options=search_request.options.model_dump() if search_request.options else None,
            status=SearchStatus.INITIATED,
            client_ip=client_ip
        )
        
        self.db.add(search)
        await self.db.commit()
        
        logger.info(f"Search initiated: {search_id} for query '{search_request.query}'")
        
        # Start immediate search task (no DB blocking)
        asyncio.create_task(self._execute_search_immediate(search_id, search_request))
        
        return search_id
    
    async def _execute_search_immediate(self, search_id: str, search_request: SearchRequest):
        """Execute search with immediate WebSocket updates, save to DB later."""
        try:
            # Update search status (quick operation)
            await self._update_search_status(search_id, SearchStatus.RUNNING)
            
            # Get vendor configurations and cache vendor names
            vendor_configs = await self._get_vendor_configs()
            await self._cache_vendor_names(list(vendor_configs.keys()))
            
            # Filter vendors if specified
            enabled_vendors = None
            if search_request.filters and search_request.filters.vendors:
                enabled_vendors = search_request.filters.vendors
            
            # Send search started WebSocket message IMMEDIATELY
            vendors_to_search = list(vendor_configs.keys())
            if enabled_vendors:
                vendors_to_search = [v for v in vendors_to_search if v in enabled_vendors]
            
            await manager.send_search_started(search_id, len(vendors_to_search))
            
            # Execute search across vendors
            max_results = 50
            if search_request.options and search_request.options.max_results:
                max_results = search_request.options.max_results
            
            # IMMEDIATE SEARCH - NO DATABASE BLOCKING
            scraping_results = await scraping_engine.search_all_vendors(
                query=search_request.query,
                vendor_configs=vendor_configs,
                max_results_per_vendor=max_results,
                enabled_vendors=enabled_vendors
            )
            
            # Process results and send IMMEDIATELY via WebSocket
            total_products = 0
            successful_vendors = []
            failed_vendors = []
            all_products_data = []  # Store for later DB save
            
            for result in scraping_results:
                if result.success:
                    successful_vendors.append(result.vendor_id)
                    
                    # Send vendor started message IMMEDIATELY
                    vendor_name = self._get_cached_vendor_name(result.vendor_id)
                    await manager.send_vendor_started(search_id, result.vendor_id, vendor_name)
                    
                    # Send products IMMEDIATELY - NO DB OPERATIONS
                    for product_data in result.products:
                        # Create product dict for WebSocket (no DB needed)
                        product_dict = {
                            "id": str(uuid.uuid4()),  # Temporary ID for frontend
                            "name": product_data.name,
                            "price": float(product_data.price),
                            "currency": product_data.currency,
                            "vendor_id": product_data.vendor_id,
                            "vendor_name": vendor_name,
                            "url": product_data.vendor_url,
                            "image_url": product_data.image_url,
                            "availability": product_data.availability,
                            "brand": product_data.brand,
                            "model": product_data.model,
                            "delivery_cost": float(product_data.delivery_cost) if product_data.delivery_cost else None,
                            "delivery_time": product_data.delivery_time,
                            "last_updated": datetime.utcnow()
                        }
                        
                        # Send product found message IMMEDIATELY
                        await manager.send_product_found(search_id, result.vendor_id, product_dict)
                        
                        # Store for later DB save
                        all_products_data.append((product_data, result.vendor_id, vendor_name))
                    
                    total_products += len(result.products)
                    
                    # Send vendor completed message IMMEDIATELY
                    await manager.send_vendor_completed(
                        search_id, 
                        result.vendor_id, 
                        len(result.products), 
                        result.duration
                    )
                    
                else:
                    failed_vendors.append(result.vendor_id)
                    await manager.send_error(search_id, result.error_message, result.vendor_id)
            
            # Calculate comparison from in-memory data (no DB needed)
            comparison = None
            if total_products > 0:
                prices = [float(product_data[0].price) for product_data in all_products_data]
                comparison = {
                    "lowest_price": min(prices),
                    "highest_price": max(prices),
                    "average_price": sum(prices) / len(prices),
                    "price_range": max(prices) - min(prices)
                }
            
            # Send search completed message IMMEDIATELY
            search_start_time = datetime.utcnow()  # We'll get real start time from DB later
            total_duration = 2.0  # Approximate for immediate response
            await manager.send_search_completed(
                search_id, 
                total_products, 
                total_duration, 
                comparison
            )
            
            logger.info(f"Search completed IMMEDIATELY: {search_id} - {total_products} products sent via WebSocket")
            
            # NOW save to database in background (non-blocking)
            asyncio.create_task(self._save_search_results_background(
                search_id, all_products_data, successful_vendors, failed_vendors, 
                vendors_to_search, comparison
            ))
            
        except Exception as e:
            logger.error(f"Search execution failed for {search_id}: {str(e)}")
            await self._update_search_status(search_id, SearchStatus.FAILED, str(e))
            await manager.send_error(search_id, str(e))
    
    async def _save_search_results_background(
        self, 
        search_id: str, 
        products_data: List[tuple], 
        successful_vendors: List[str],
        failed_vendors: List[str],
        vendors_searched: List[str],
        comparison: Optional[Dict[str, float]]
    ):
        """Save search results to database in background (after WebSocket updates sent)."""
        try:
            logger.info(f"Starting background DB save for search {search_id}")
            
            # Batch store products
            for product_data, vendor_id, vendor_name in products_data:
                product_id = await self._store_product_fast(product_data)
                
                # Store search result
                search_result = SearchResult(
                    search_id=search_id,
                    product_id=product_id,
                    vendor_id=vendor_id,
                    rank=str(len(products_data))
                )
                self.db.add(search_result)
            
            # Update search record
            search = await self.db.get(Search, search_id)
            if search:
                search.status = SearchStatus.COMPLETED
                search.completed_at = datetime.utcnow()
                search.total_results = str(len(products_data))
                search.vendors_searched = vendors_searched
                search.vendors_successful = successful_vendors
                search.vendors_failed = failed_vendors
                
                if comparison:
                    search.lowest_price = comparison["lowest_price"]
                    search.highest_price = comparison["highest_price"]
                    search.average_price = comparison["average_price"]
                    search.price_range = comparison["price_range"]
            
            # Single commit for all background operations
            await self.db.commit()
            
            logger.info(f"Background DB save completed for search {search_id}")
            
        except Exception as e:
            logger.error(f"Background DB save failed for {search_id}: {str(e)}")
    
    async def _cache_vendor_names(self, vendor_ids: List[str]):
        """Cache vendor names to avoid repeated queries."""
        if not vendor_ids:
            return
            
        stmt = select(Vendor).where(Vendor.id.in_(vendor_ids))
        result = await self.db.execute(stmt)
        vendors = result.scalars().all()
        
        for vendor in vendors:
            self._vendor_cache[vendor.id] = vendor.name
    
    def _get_cached_vendor_name(self, vendor_id: str) -> str:
        """Get vendor name from cache."""
        return self._vendor_cache.get(vendor_id, vendor_id)
    
    async def _store_product_fast(self, product_data) -> str:
        """Store product with optimized database operations."""
        # Check if product already exists (single query)
        stmt = select(Product.id).where(
            and_(
                Product.vendor_id == product_data.vendor_id,
                Product.vendor_url == product_data.vendor_url
            )
        )
        result = await self.db.execute(stmt)
        existing_id = result.scalar_one_or_none()
        
        if existing_id:
            # Update existing product (minimal update)
            stmt = select(Product).where(Product.id == existing_id)
            result = await self.db.execute(stmt)
            existing_product = result.scalar_one()
            
            existing_product.price = product_data.price
            existing_product.availability = product_data.availability
            existing_product.last_seen_at = datetime.utcnow()
            existing_product.last_updated_at = datetime.utcnow()
            
            return existing_id
        else:
            # Create new product
            product = Product(
                name=product_data.name,
                price=product_data.price,
                currency=product_data.currency,
                vendor_id=product_data.vendor_id,
                vendor_url=product_data.vendor_url,
                image_url=product_data.image_url,
                availability=product_data.availability,
                brand=product_data.brand,
                model=product_data.model,
                delivery_cost=product_data.delivery_cost,
                delivery_time=product_data.delivery_time,
                original_price=product_data.original_price,
                discount_percentage=product_data.discount_percentage,
                specifications=product_data.specifications,
                normalized_name=product_data.name.lower().strip()
            )
            
            self.db.add(product)
            await self.db.flush()  # Get ID without committing
            return product.id
    
    async def get_search_results(self, search_id: str) -> Optional[SearchResultResponse]:
        """Get search results by search ID."""
        # Get search record
        search = await self.db.get(Search, search_id)
        if not search:
            return None
        
        # Get search results with products (optimized query)
        stmt = (
            select(SearchResult, Product)
            .join(Product)
            .where(SearchResult.search_id == search_id)
            .order_by(SearchResult.rank)
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        # Convert to response format
        products = []
        for search_result, product in rows:
            vendor_name = self._get_cached_vendor_name(product.vendor_id)
            
            products.append({
                "id": str(product.id),
                "name": product.name,
                "price": float(product.price),
                "currency": product.currency,
                "vendor_id": product.vendor_id,
                "vendor_name": vendor_name,
                "url": product.vendor_url,
                "image_url": product.image_url,
                "availability": product.availability,
                "brand": product.brand,
                "model": product.model,
                "delivery_cost": float(product.delivery_cost) if product.delivery_cost else None,
                "delivery_time": product.delivery_time,
                "last_updated": product.last_updated_at or product.first_seen_at
            })
        
        # Calculate comparison if completed
        comparison = None
        if search.status == SearchStatus.COMPLETED and products:
            prices = [p["price"] for p in products]
            comparison = {
                "lowest_price": min(prices),
                "highest_price": max(prices),
                "average_price": sum(prices) / len(prices),
                "price_range": max(prices) - min(prices)
            }
        
        # Calculate search time
        search_time = 0.0
        if search.completed_at:
            search_time = (search.completed_at - search.started_at).total_seconds()
        
        return SearchResultResponse(
            search_id=search_id,
            status=search.status,
            total_results=len(products),
            search_time=search_time,
            results=products,
            comparison=comparison
        )
    
    def _normalize_query(self, query: str) -> str:
        """Normalize search query."""
        return query.strip().lower()
    
    async def _update_search_status(self, search_id: str, status: SearchStatus, error_message: str = None):
        """Update search status."""
        search = await self.db.get(Search, search_id)
        if search:
            search.status = status
            if error_message:
                search.error_message = error_message
            await self.db.commit()
    
    async def _get_vendor_configs(self) -> Dict[str, dict]:
        """Get vendor configurations from database."""
        stmt = select(Vendor).where(Vendor.is_active == True)
        result = await self.db.execute(stmt)
        vendors = result.scalars().all()
        
        configs = {}
        for vendor in vendors:
            config = vendor.scraping_config or {}
            config.setdefault('delay', 1.0)
            config.setdefault('timeout', 30)
            config.setdefault('max_retries', 3)
            configs[vendor.id] = config
        
        return configs

