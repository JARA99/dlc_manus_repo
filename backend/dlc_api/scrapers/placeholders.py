"""
Placeholder scrapers for future implementation
"""

import asyncio
import time
from typing import List
from ..models import Vendor, Product, ScrapingResult
from .base import BaseScraper


class MaxScraper(BaseScraper):
    """Placeholder scraper for Max."""
    
    # Vendor information defined at class level
    VENDOR_INFO = Vendor(
        id="max",
        name="Max",
        base_url="https://www.max.com.gt",
        country="GT", 
        currency="GTQ",
        active=True
    )
    
    async def search(self, query: str, max_results: int = 10) -> ScrapingResult:
        """Placeholder search - returns empty results."""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        return ScrapingResult(
            vendor_id=self.vendor.id,
            vendor_name=self.vendor.name,
            success=True,
            products=[],  # Empty for now
            duration=0.1
        )


class ElektraScraper(BaseScraper):
    """Placeholder scraper for Elektra."""
    
    # Vendor information defined at class level
    VENDOR_INFO = Vendor(
        id="elektra",
        name="Elektra",
        base_url="https://www.elektra.com.gt",
        country="GT",
        currency="GTQ", 
        active=True
    )
    
    async def search(self, query: str, max_results: int = 10) -> ScrapingResult:
        """Placeholder search - returns empty results."""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        return ScrapingResult(
            vendor_id=self.vendor.id,
            vendor_name=self.vendor.name,
            success=True,
            products=[],  # Empty for now
            duration=0.1
        )


class WalmartScraper(BaseScraper):
    """Placeholder scraper for Walmart."""
    
    # Vendor information defined at class level
    VENDOR_INFO = Vendor(
        id="walmart",
        name="Walmart Guatemala",
        base_url="https://www.walmart.com.gt",
        country="GT",
        currency="GTQ",
        active=True
    )
    
    async def search(self, query: str, max_results: int = 10) -> ScrapingResult:
        """Placeholder search - returns empty results."""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        return ScrapingResult(
            vendor_id=self.vendor.id,
            vendor_name=self.vendor.name,
            success=True,
            products=[],  # Empty for now
            duration=0.1
        )

