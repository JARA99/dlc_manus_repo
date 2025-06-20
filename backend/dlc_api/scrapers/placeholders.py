"""
Placeholder scrapers for future implementation
"""

import asyncio
import time
from typing import List
from ..models import Product, ScrapingResult
from ..vendors import get_vendor


class MaxScraper:
    """Placeholder scraper for Max."""
    
    def __init__(self):
        self.vendor = get_vendor("max")
    
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


class ElektraScraper:
    """Placeholder scraper for Elektra."""
    
    def __init__(self):
        self.vendor = get_vendor("elektra")
    
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


class WalmartScraper:
    """Placeholder scraper for Walmart."""
    
    def __init__(self):
        self.vendor = get_vendor("walmart")
    
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

