"""
Search Manager - Core business logic for search operations
"""

import asyncio
from typing import Dict, Optional
from ..models import Search, SearchRequest, SearchStatus
from ..scrapers import get_scraper_registry, ScraperRegistry


class SearchManager:
    """Manages search operations and lifecycle."""
    
    def __init__(self, scraper_registry: Optional[ScraperRegistry] = None):
        self.scraper_registry = scraper_registry or get_scraper_registry()
        self.active_searches: Dict[str, Search] = {}
    
    async def create_search(self, request: SearchRequest) -> Search:
        """Create a new search operation."""
        search = Search(query=request.query, max_results=request.max_results)
        self.active_searches[search.id] = search
        
        # Start background search execution
        asyncio.create_task(self._execute_search(search))
        
        return search
    
    def get_search(self, search_id: str) -> Optional[Search]:
        """Get search by ID."""
        return self.active_searches.get(search_id)
    
    def get_search_results(self, search_id: str) -> Optional[Dict]:
        """Get search results as dictionary."""
        search = self.get_search(search_id)
        if search:
            return search.to_dict()
        return None
    
    async def _execute_search(self, search: Search):
        """Execute search across all active scrapers."""
        try:
            search.start()
            
            # Get active vendor IDs
            active_vendor_ids = self.scraper_registry.get_active_vendor_ids()
            
            # Execute scrapers for each vendor
            for vendor_id in active_vendor_ids:
                try:
                    # Get scraper instance (singleton)
                    scraper = self.scraper_registry.get_scraper(vendor_id)
                    
                    # Add vendor started event
                    search.add_vendor_started(vendor_id, scraper.vendor.name)
                    
                    # Execute scraper
                    result = await scraper.search(search.query, search.max_results)
                    
                    if result.success:
                        # Add products to search
                        for product in result.products:
                            search.add_product(product)
                        
                        # Add vendor completed event
                        search.add_vendor_completed(
                            vendor_id, 
                            len(result.products), 
                            result.duration
                        )
                    else:
                        # Add vendor error event
                        search.add_vendor_error(vendor_id, result.error_message or "Unknown error")
                
                except Exception as e:
                    # Handle individual vendor errors
                    search.add_vendor_error(vendor_id, str(e))
            
            # Mark search as completed
            search.complete()
            
        except Exception as e:
            # Handle overall search failure
            search.fail(str(e))
        
        # Note: Search cleanup is handled separately to allow result retrieval

