from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SearchFilters(BaseModel):
    """Search filters model."""
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    categories: Optional[List[str]] = Field(None, description="Category IDs to filter by")
    vendors: Optional[List[str]] = Field(None, description="Vendor IDs to filter by")
    brands: Optional[List[str]] = Field(None, description="Brand names to filter by")


class SearchOptions(BaseModel):
    """Search options model."""
    include_delivery: bool = Field(True, description="Include delivery information")
    max_results: int = Field(50, ge=1, le=100, description="Maximum results per vendor")
    timeout: int = Field(30, ge=5, le=60, description="Search timeout in seconds")


class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    filters: Optional[SearchFilters] = None
    options: Optional[SearchOptions] = None


class SearchStatus(str, Enum):
    """Search status enumeration."""
    INITIATED = "initiated"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ProductBase(BaseModel):
    """Base product model."""
    name: str
    price: float
    currency: str = "GTQ"
    vendor_id: str
    vendor_name: str
    url: str
    image_url: Optional[str] = None
    availability: str = "unknown"
    brand: Optional[str] = None
    model: Optional[str] = None
    delivery_cost: Optional[float] = None
    delivery_time: Optional[str] = None
    last_updated: datetime


class Product(ProductBase):
    """Product model with ID."""
    id: str
    
    class Config:
        from_attributes = True


class ProductDetail(Product):
    """Detailed product model."""
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    features: Optional[List[str]] = None
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    price_history: Optional[List[Dict[str, Any]]] = None


class SearchComparison(BaseModel):
    """Search result comparison statistics."""
    lowest_price: float
    highest_price: float
    average_price: float
    price_range: float


class SearchResultResponse(BaseModel):
    """Search result response model."""
    search_id: str
    status: SearchStatus
    total_results: int
    search_time: float
    results: List[Product]
    comparison: Optional[SearchComparison] = None


class SearchInitResponse(BaseModel):
    """Search initiation response model."""
    search_id: str
    status: SearchStatus
    estimated_time: int
    websocket_url: str


class VendorBase(BaseModel):
    """Base vendor model."""
    id: str
    name: str
    website: str
    logo_url: Optional[str] = None


class Vendor(VendorBase):
    """Vendor model."""
    categories: List[str]
    delivery_areas: List[str]
    status: str
    last_scraped: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    """Base category model."""
    id: str
    name: str
    name_en: Optional[str] = None


class Category(CategoryBase):
    """Category model."""
    parent_id: Optional[str] = None
    level: int
    path: str
    subcategories: Optional[List['Category']] = None
    
    class Config:
        from_attributes = True


class SearchHistoryItem(BaseModel):
    """Search history item model."""
    search_id: str
    query: str
    timestamp: datetime
    results_count: int
    status: SearchStatus


class SearchHistory(BaseModel):
    """Search history response model."""
    searches: List[SearchHistoryItem]
    total: int
    limit: int
    offset: int


class ErrorResponse(BaseModel):
    """Error response model."""
    error: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    database: str
    redis: str


# WebSocket message models
class WSMessageType(str, Enum):
    """WebSocket message types."""
    SEARCH_STARTED = "search_started"
    VENDOR_STARTED = "vendor_started"
    PRODUCT_FOUND = "product_found"
    VENDOR_COMPLETED = "vendor_completed"
    SEARCH_COMPLETED = "search_completed"
    ERROR = "error"


class WSMessage(BaseModel):
    """Base WebSocket message model."""
    type: WSMessageType
    search_id: str
    timestamp: datetime


class WSSearchStarted(WSMessage):
    """WebSocket search started message."""
    type: WSMessageType = WSMessageType.SEARCH_STARTED
    vendors_count: int


class WSVendorStarted(WSMessage):
    """WebSocket vendor started message."""
    type: WSMessageType = WSMessageType.VENDOR_STARTED
    vendor: str
    vendor_name: str


class WSProductFound(WSMessage):
    """WebSocket product found message."""
    type: WSMessageType = WSMessageType.PRODUCT_FOUND
    vendor: str
    product: ProductBase


class WSVendorCompleted(WSMessage):
    """WebSocket vendor completed message."""
    type: WSMessageType = WSMessageType.VENDOR_COMPLETED
    vendor: str
    results_count: int
    duration: float


class WSSearchCompleted(WSMessage):
    """WebSocket search completed message."""
    type: WSMessageType = WSMessageType.SEARCH_COMPLETED
    total_results: int
    total_duration: float
    comparison: Optional[SearchComparison] = None


class WSError(WSMessage):
    """WebSocket error message."""
    type: WSMessageType = WSMessageType.ERROR
    vendor: Optional[str] = None
    error: str

