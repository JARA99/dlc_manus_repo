"""
Base scraper class for all vendor scrapers
"""

from abc import ABC, abstractmethod
from typing import List
from ..models import Vendor, Product, ScrapingResult


class BaseScraper(ABC):
    """Base class for all vendor scrapers."""
    
    # Must be defined by subclasses
    VENDOR_INFO: Vendor = None
    
    def __init__(self):
        if self.VENDOR_INFO is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define VENDOR_INFO class attribute"
            )
        self.vendor = self.VENDOR_INFO
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> ScrapingResult:
        """
        Search for products on this vendor's platform.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            ScrapingResult with products found and metadata
        """
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}(vendor_id='{self.vendor.id}')"

