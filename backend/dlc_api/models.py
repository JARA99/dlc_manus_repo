from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class Product(BaseModel):
    """Product information from scraping."""
    name: str
    price: float
    currency: str = "GTQ"
    vendor_id: str
    vendor_name: str
    url: str
    image_url: Optional[str] = None
    availability: str = "unknown"
    brand: Optional[str] = None


class SearchRequest(BaseModel):
    """Search request from client."""
    query: str
    max_results: int = 10


class SearchResponse(BaseModel):
    """Search response with SSE endpoint."""
    search_id: str
    sse_url: str
    message: str


class SearchEvent(BaseModel):
    """Server-Sent Event for search updates."""
    event: str  # "started", "product_found", "vendor_completed", "completed", "error"
    data: dict
    timestamp: datetime = datetime.utcnow()


class ScrapingResult(BaseModel):
    """Result from a scraper."""
    vendor_id: str
    vendor_name: str
    success: bool
    products: List[Product] = []
    error_message: Optional[str] = None
    duration: float = 0.0

