"""
Scraping result models
"""

from typing import List, Optional
from pydantic import BaseModel

from .product import Product


class ScrapingResult(BaseModel):
    """Result from a scraper."""
    vendor_id: str
    vendor_name: str
    success: bool
    products: List[Product] = []
    error_message: Optional[str] = None
    duration: float = 0.0

