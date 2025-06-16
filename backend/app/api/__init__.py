# Import all API routers
from .search import router as search_router
from .products import router as products_router
from .vendors import router as vendors_router
from .categories import router as categories_router
from .websocket import router as websocket_router

__all__ = [
    "search_router",
    "products_router", 
    "vendors_router",
    "categories_router",
    "websocket_router"
]

