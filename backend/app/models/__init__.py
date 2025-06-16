# Import all models to ensure they are registered with SQLAlchemy
from .vendor import Vendor
from .category import Category
from .product import Product, ProductPriceHistory
from .search import Search, SearchResult, SearchAnalytics

__all__ = [
    "Vendor",
    "Category", 
    "Product",
    "ProductPriceHistory",
    "Search",
    "SearchResult", 
    "SearchAnalytics"
]

