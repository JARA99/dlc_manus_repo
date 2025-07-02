"""
DondeLoCompro.gt API - New OOP Architecture
A simplified, scalable API for product price comparison in Guatemala
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .core import SearchManager, SSEManager
from .api import SearchAPI, HealthAPI
from .scrapers import get_scraper_registry

# Load environment variables
load_dotenv()


class DondeLoComproAPI:
    """Main application class with dependency injection."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Initialize core components
        self.scraper_registry = get_scraper_registry()
        self.search_manager = SearchManager(self.scraper_registry)
        self.sse_manager = SSEManager()
        
        # Initialize API components
        self.search_api = SearchAPI(self.search_manager, self.sse_manager)
        self.health_api = HealthAPI()
        
        # Create FastAPI app
        self.app = self._create_app()
        
        self._initialized = True
    
    def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application."""
        app = FastAPI(
            title="DondeLoCompro.gt API",
            description="Product price comparison API for Guatemala",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Include API routers
        app.include_router(self.health_api.router, tags=["health"])
        app.include_router(self.search_api.router, tags=["search"])
        
        return app
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app


# Create application instance
api_instance = DondeLoComproAPI()
app = api_instance.get_app()


# For backwards compatibility and direct execution
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting DondeLoCompro.gt API v2.0.0")
    print(f"📡 Server: http://{host}:{port}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    print(f"🕷️ Scrapers: {', '.join(api_instance.scraper_registry.get_active_vendor_ids())}")
    
    uvicorn.run(
        "dlc_api.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

