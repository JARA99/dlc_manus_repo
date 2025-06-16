from typing import Dict, Type, List
from app.scraping.base_scraper import BaseScraper, ScrapingResult
from app.scraping.cemaco_scraper import CemacoScraper
from app.scraping.max_scraper import MaxScraper
from app.scraping.elektra_scraper import ElektraScraper
from app.scraping.walmart_scraper import WalmartScraper
import asyncio
import logging
from app.models.vendor import Vendor
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ScrapingEngine:
    """Main scraping engine that coordinates all vendor scrapers."""
    
    def __init__(self):
        self.scrapers: Dict[str, Type[BaseScraper]] = {
            'cemaco': CemacoScraper,
            'max': MaxScraper,
            'elektra': ElektraScraper,
            'walmart': WalmartScraper,
        }
    
    def register_scraper(self, vendor_id: str, scraper_class: Type[BaseScraper]):
        """Register a new scraper for a vendor."""
        self.scrapers[vendor_id] = scraper_class
        logger.info(f"Registered scraper for vendor: {vendor_id}")
    
    async def search_all_vendors(
        self, 
        query: str, 
        vendor_configs: Dict[str, dict],
        max_results_per_vendor: int = 50,
        enabled_vendors: List[str] = None
    ) -> List[ScrapingResult]:
        """
        Search for products across all enabled vendors.
        
        Args:
            query: Search query string
            vendor_configs: Configuration for each vendor
            max_results_per_vendor: Maximum results per vendor
            enabled_vendors: List of vendor IDs to search (None = all)
            
        Returns:
            List of ScrapingResult objects
        """
        if enabled_vendors is None:
            enabled_vendors = list(self.scrapers.keys())
        
        # Filter to only enabled vendors that have scrapers
        vendors_to_search = [
            vendor_id for vendor_id in enabled_vendors 
            if vendor_id in self.scrapers and vendor_id in vendor_configs
        ]
        
        logger.info(f"Starting search for '{query}' across {len(vendors_to_search)} vendors")
        
        # Create scraping tasks
        tasks = []
        for vendor_id in vendors_to_search:
            config = vendor_configs[vendor_id]
            scraper_class = self.scrapers[vendor_id]
            
            task = self._search_vendor(
                vendor_id, 
                scraper_class, 
                config, 
                query, 
                max_results_per_vendor
            )
            tasks.append(task)
        
        # Execute all searches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        scraping_results = []
        for i, result in enumerate(results):
            vendor_id = vendors_to_search[i]
            
            if isinstance(result, Exception):
                logger.error(f"Search failed for {vendor_id}: {str(result)}")
                scraping_results.append(ScrapingResult(
                    vendor_id=vendor_id,
                    query=query,
                    products=[],
                    success=False,
                    error_message=str(result)
                ))
            else:
                scraping_results.append(result)
        
        # Log summary
        total_products = sum(len(result.products) for result in scraping_results if result.success)
        successful_vendors = sum(1 for result in scraping_results if result.success)
        
        logger.info(f"Search completed: {total_products} products found from {successful_vendors}/{len(vendors_to_search)} vendors")
        
        return scraping_results
    
    async def _search_vendor(
        self,
        vendor_id: str,
        scraper_class: Type[BaseScraper],
        config: dict,
        query: str,
        max_results: int
    ) -> ScrapingResult:
        """Search a single vendor."""
        try:
            async with scraper_class(vendor_id, config) as scraper:
                result = await scraper.search(query, max_results)
                return result
        except Exception as e:
            logger.error(f"Error searching {vendor_id}: {str(e)}")
            return ScrapingResult(
                vendor_id=vendor_id,
                query=query,
                products=[],
                success=False,
                error_message=str(e)
            )
    
    async def search_vendor(
        self,
        vendor_id: str,
        query: str,
        config: dict,
        max_results: int = 50
    ) -> ScrapingResult:
        """
        Search a specific vendor.
        
        Args:
            vendor_id: Vendor identifier
            query: Search query
            config: Vendor configuration
            max_results: Maximum results to return
            
        Returns:
            ScrapingResult object
        """
        if vendor_id not in self.scrapers:
            raise ValueError(f"No scraper registered for vendor: {vendor_id}")
        
        scraper_class = self.scrapers[vendor_id]
        return await self._search_vendor(vendor_id, scraper_class, config, query, max_results)
    
    def get_supported_vendors(self) -> List[str]:
        """Get list of supported vendor IDs."""
        return list(self.scrapers.keys())
    
    def is_vendor_supported(self, vendor_id: str) -> bool:
        """Check if a vendor is supported."""
        return vendor_id in self.scrapers
    
    @staticmethod
    def load_vendor_configs(db: Session) -> Dict[str, dict]:
        """
        Load vendor configurations from database.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary mapping vendor IDs to their configurations
        """
        vendors = db.query(Vendor).filter(Vendor.is_active == True).all()
        
        configs = {}
        for vendor in vendors:
            config = vendor.scraping_config or {}
            
            # Add default configuration values
            config.setdefault('delay', 1.0)
            config.setdefault('timeout', 30)
            config.setdefault('max_retries', 3)
            
            configs[vendor.id] = config
        
        return configs


# Global scraping engine instance
scraping_engine = ScrapingEngine()

