"""
Scraper registry for managing vendor scrapers and their information
"""

import importlib
import pkgutil
from typing import Dict, Type, List
from .base import BaseScraper
from ..models import Vendor


class ScraperRegistry:
    """Registry for managing scrapers and vendors with caching."""
    
    def __init__(self):
        self._scraper_classes: Dict[str, Type[BaseScraper]] = {}
        self._vendor_cache: Dict[str, Vendor] = {}
        self._scraper_cache: Dict[str, BaseScraper] = {}
        self._discover_scrapers()
    
    def _discover_scrapers(self):
        """Discover and register all available scrapers."""
        # Import current scrapers manually for now (will be auto-discovery later)
        from .cemaco import CemacoScraper
        from .placeholders import MaxScraper, ElektraScraper, WalmartScraper
        
        scrapers = [CemacoScraper, MaxScraper, ElektraScraper, WalmartScraper]
        
        for scraper_class in scrapers:
            if hasattr(scraper_class, 'VENDOR_INFO') and scraper_class.VENDOR_INFO:
                vendor_id = scraper_class.VENDOR_INFO.id
                self._scraper_classes[vendor_id] = scraper_class
                # Pre-cache vendor info
                self._vendor_cache[vendor_id] = scraper_class.VENDOR_INFO
    
    def get_vendor(self, vendor_id: str) -> Vendor:
        """Get vendor information by ID."""
        if vendor_id not in self._vendor_cache:
            if vendor_id not in self._scraper_classes:
                raise ValueError(f"Unknown vendor: {vendor_id}")
            
            scraper_class = self._scraper_classes[vendor_id]
            self._vendor_cache[vendor_id] = scraper_class.VENDOR_INFO
        
        return self._vendor_cache[vendor_id]
    
    def get_scraper(self, vendor_id: str) -> BaseScraper:
        """Get scraper instance by vendor ID (cached singleton)."""
        if vendor_id not in self._scraper_cache:
            if vendor_id not in self._scraper_classes:
                raise ValueError(f"Unknown vendor: {vendor_id}")
            
            scraper_class = self._scraper_classes[vendor_id]
            self._scraper_cache[vendor_id] = scraper_class()
        
        return self._scraper_cache[vendor_id]
    
    def get_all_vendors(self) -> Dict[str, Vendor]:
        """Get all available vendors."""
        return self._vendor_cache.copy()
    
    def get_active_vendors(self) -> Dict[str, Vendor]:
        """Get only active vendors."""
        return {
            vendor_id: vendor 
            for vendor_id, vendor in self._vendor_cache.items() 
            if vendor.active
        }
    
    def get_vendor_ids(self) -> List[str]:
        """Get list of all vendor IDs."""
        return list(self._scraper_classes.keys())
    
    def get_active_vendor_ids(self) -> List[str]:
        """Get list of active vendor IDs."""
        return [
            vendor_id for vendor_id, vendor in self._vendor_cache.items()
            if vendor.active
        ]
    
    def get_scraper_classes(self) -> Dict[str, Type[BaseScraper]]:
        """Get all scraper classes (for compatibility)."""
        return self._scraper_classes.copy()


# Global registry instance
_registry = ScraperRegistry()

# Compatibility functions for existing code
def get_vendor(vendor_id: str) -> Vendor:
    """Get vendor by ID (compatibility function)."""
    return _registry.get_vendor(vendor_id)

def get_all_vendors() -> Dict[str, Vendor]:
    """Get all vendors (compatibility function)."""
    return _registry.get_all_vendors()

def get_active_vendors() -> Dict[str, Vendor]:
    """Get only active vendors (compatibility function)."""
    return _registry.get_active_vendors()

def get_scraper_registry() -> ScraperRegistry:
    """Get the global scraper registry."""
    return _registry

