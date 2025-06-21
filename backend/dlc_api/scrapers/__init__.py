"""
Scrapers package initialization
"""

from .base import BaseScraper
from .cemaco import CemacoScraper
from .placeholders import MaxScraper, ElektraScraper, WalmartScraper
from .registry import ScraperRegistry, get_scraper_registry, get_vendor, get_all_vendors, get_active_vendors

# Get the global registry
_registry = get_scraper_registry()

# Available scrapers (for compatibility with existing code)
SCRAPERS = _registry.get_scraper_classes()

# Available vendors (for compatibility with existing code)  
VENDORS = _registry.get_all_vendors()

__all__ = [
    "BaseScraper",
    "CemacoScraper", 
    "MaxScraper", 
    "ElektraScraper", 
    "WalmartScraper",
    "ScraperRegistry",
    "get_scraper_registry",
    "get_vendor",
    "get_all_vendors", 
    "get_active_vendors",
    "SCRAPERS",
    "VENDORS"
]

