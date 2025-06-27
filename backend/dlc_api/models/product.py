"""
Product model for scraped product information
"""

from typing import Optional
from pydantic import BaseModel


class Product(BaseModel):
    """Product information from scraping."""
    name: str
    price: float
    currency: str = "GTQ"
    vendor_id: str
    vendor_name: str
    url: str
    image_url: Optional[str] = None
    availability: str = "unknown"  # "in_stock", "out_of_stock", "unknown"
    brand: Optional[str] = None
    
    # Future fields for enhanced product data
    # description: Optional[str] = None
    # rating: Optional[float] = None
    # review_count: Optional[int] = None
    # category: Optional[str] = None

