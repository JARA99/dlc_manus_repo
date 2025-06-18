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
    """Service for handling product searches."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # Cache vendor names to avoid repeated DB queries
        self._vendor_cache = {}
    
    async def initiate_search(self, search_request: SearchRequest, client_ip: str = None) -> str:
        """
        Initiate a new product search.
        
        Args:
            search_request: Search parameters
            client_ip: Client IP address for tracking
            
        Returns:
            Search ID for tracking progress
        """
        # Create search record
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
        
        # Start background search task
        asyncio.create_task(self._execute_search(search_id, search_request))
        
        return search_id
    
    async def _execute_search(self, search_id: str, search_request: SearchRequest):
        """Execute the actual search in background."""
        try:
            # Update search status
            await self._update_search_status(search_id, SearchStatus.RUNNING)
            
            # Get vendor configurations and cache vendor names
            vendor_configs = await self._get_vendor_configs()
            await self._cache_vendor_names(list(vendor_configs.keys()))
            
            # Filter vendors if specified
            enabled_vendors = None
            if search_request.filters and search_request.filters.vendors:
                enabled_vendors = search_request.filters.vendors
            
            # Send search started WebSocket message
            vendors_to_search = list(vendor_configs.keys())
            if enabled_vendors:
                vendors_to_search = [v for v in vendors_to_search if v in enabled_vendors]
            
            await manager.send_search_started(search_id, len(vendors_to_search))
            
            # Execute search across vendors
            max_results = 50
            if search_request.options and search_request.options.max_results:
                max_results = search_request.options.max_results
            
            scraping_results = await scraping_engine.search_all_vendors(
                query=search_request.query,
                vendor_configs=vendor_configs,
                max_results_per_vendor=max_results,
                enabled_vendors=enabled_vendors
            )
            
            # Process and store results with batch operations
            total_products = 0
            successful_vendors = []
            failed_vendors = []
            
            # Prepare batch data
            products_to_store = []
            search_results_to_store = []
            
            for result in scraping_results:
                if result.success:
                    successful_vendors.append(result.vendor_id)
                    
                    # Send vendor started message (cached vendor name)
                    vendor_name = self._get_cached_vendor_name(result.vendor_id)
                    await manager.send_vendor_started(search_id, result.vendor_id, vendor_name)
                    
                    # Prepare products for batch storage
                    for product_data in result.products:
                        products_to_store.append((product_data, result.vendor_id, vendor_name))
                    
                    total_products += len(result.products)
                    
                    # Send vendor completed message
                    await manager.send_vendor_completed(
                        search_id, 
                        result.vendor_id, 
                        len(result.products), 
                        result.duration
                    )
                    
                else:
                    failed_vendors.append(result.vendor_id)
                    await manager.send_error(search_id, result.error_message, result.vendor_id)
            
            # Batch store products and send WebSocket updates
            await self._batch_store_products(search_id, products_to_store)
            
            # Update search record (single commit)
            search = await self.db.get(Search, search_id)
            search.status = SearchStatus.COMPLETED
            search.completed_at = datetime.utcnow()
            search.total_results = str(total_products)
            search.vendors_searched = vendors_to_search
            search.vendors_successful = successful_vendors
            search.vendors_failed = failed_vendors
            
            # Calculate comparison statistics (optimized)
            if total_products > 0:
                comparison = await self._calculate_comparison_fast(search_id)
                if comparison:
                    search.lowest_price = comparison["lowest_price"]
                    search.highest_price = comparison["highest_price"]
                    search.average_price = comparison["average_price"]
                    search.price_range = comparison["price_range"]
            
            await self.db.commit()
            
            # Send search completed message
            total_duration = (search.completed_at - search.started_at).total_seconds()
            await manager.send_search_completed(
                search_id, 
                total_products, 
                total_duration, 
                comparison if total_products > 0 else None
            )
            
            logger.info(f"Search completed: {search_id} - {total_products} products found in {total_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Search execution failed for {search_id}: {str(e)}")
            await self._update_search_status(search_id, SearchStatus.FAILED, str(e))
            await manager.send_error(search_id, str(e))
    
    async def _batch_store_products(self, search_id: str, products_data: List[tuple]):
        """Store products in batch and send WebSocket updates."""
        for product_data, vendor_id, vendor_name in products_data:
            # Store product (optimized with less commits)
            product_id = await self._store_product_fast(product_data)
            
            # Create product dict for WebSocket
            product_dict = {
                "id": str(product_id),
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
            
            # Send product found message immediately
            await manager.send_product_found(search_id, vendor_id, product_dict)
            
            # Store search result (batch this later if needed)
            search_result = SearchResult(
                search_id=search_id,
                product_id=product_id,
                vendor_id=vendor_id,
                rank=str(len(products_data))
            )
            self.db.add(search_result)
        
        # Single commit for all search results
        await self.db.commit()
    
    async def _cache_vendor_names(self, vendor_ids: List[str]):
        """Cache vendor names to avoid repeated queries."""
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
        stmt = select(Product.id, Product.name, Product.price).where(
            and_(
                Product.vendor_id == product_data.vendor_id,
                Product.vendor_url == product_data.vendor_url
            )
        )
        result = await self.db.execute(stmt)
        existing = result.first()
        
        if existing:
            # Update existing product (minimal update)
            stmt = select(Product).where(Product.id == existing.id)
            result = await self.db.execute(stmt)
            existing_product = result.scalar_one()
            
            existing_product.price = product_data.price
            existing_product.availability = product_data.availability
            existing_product.last_seen_at = datetime.utcnow()
            existing_product.last_updated_at = datetime.utcnow()
            
            await self.db.commit()
            return existing.id
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
            await self.db.commit()
            await self.db.refresh(product)
            return product.id
    
    async def _calculate_comparison_fast(self, search_id: str) -> Optional[Dict[str, float]]:
        """Calculate price comparison with optimized query."""
        stmt = (
            select(func.min(Product.price), func.max(Product.price), func.avg(Product.price), func.count(Product.price))
            .join(SearchResult)
            .where(SearchResult.search_id == search_id)
        )
        
        result = await self.db.execute(stmt)
        row = result.first()
        
        if not row or row[3] == 0:  # count is 0
            return None
        
        min_price, max_price, avg_price, count = row
        
        return {
            "lowest_price": float(min_price),
            "highest_price": float(max_price),
            "average_price": float(avg_price),
            "price_range": float(max_price - min_price)
        }
    
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
    
    async def _get_vendor_name(self, vendor_id: str) -> str:
        """Get vendor display name (deprecated - use cached version)."""
        if vendor_id in self._vendor_cache:
            return self._vendor_cache[vendor_id]
        
        vendor = await self.db.get(Vendor, vendor_id)
        name = vendor.name if vendor else vendor_id
        self._vendor_cache[vendor_id] = name
        return name
    
    async def _store_product(self, product_data) -> str:
        """Store product in database (deprecated - use fast version)."""
        return await self._store_product_fast(product_data)
    
    async def _store_search_result(self, search_id: str, product_id: str, vendor_id: str, total_results: int):
        """Store search result linking search to product."""
        search_result = SearchResult(
            search_id=search_id,
            product_id=product_id,
            vendor_id=vendor_id,
            rank=str(total_results)  # Simple ranking by order found
        )
        
        self.db.add(search_result)
        await self.db.commit()
    
    async def _calculate_comparison(self, search_id: str) -> Optional[Dict[str, float]]:
        """Calculate price comparison statistics (deprecated - use fast version)."""
        return await self._calculate_comparison_fast(search_id)

