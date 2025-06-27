"""
Health API endpoints
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from ..scrapers import get_scraper_registry


class HealthAPI:
    """Health check API endpoints."""
    
    def __init__(self):
        self.router = APIRouter()
        self.scraper_registry = get_scraper_registry()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.router.get("/")
        async def root():
            """API root endpoint."""
            return {
                "message": "DondeLoCompro.gt API",
                "version": "2.0.0",
                "status": "running"
            }
        
        @self.router.get("/health")
        async def health():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc),
                "scrapers": self.scraper_registry.get_vendor_ids(),
                "active_scrapers": self.scraper_registry.get_active_vendor_ids()
            }

