"""
Search models and classes for search operations
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum
import uuid

from .product import Product


class SearchStatus(str, Enum):
    """Search status enumeration."""
    INITIATED = "initiated"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


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
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Search:
    """Search operation class - manages search state and lifecycle."""
    
    def __init__(self, query: str, max_results: int = 10):
        self.id = str(uuid.uuid4())
        self.query = query
        self.max_results = max_results
        self.status = SearchStatus.INITIATED
        self.products: List[Product] = []
        self.events: List[SearchEvent] = []
        self.created_at = datetime.now(timezone.utc)
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
    
    def start(self):
        """Mark search as started."""
        self.status = SearchStatus.RUNNING
        self.add_event("started", {
            "query": self.query,
            "max_results": self.max_results
        })
    
    def add_product(self, product: Product):
        """Add a product to search results."""
        self.products.append(product)
        self.add_event("product_found", {
            "vendor_id": product.vendor_id,
            "product": product.model_dump()
        })
    
    def add_vendor_started(self, vendor_id: str, vendor_name: str):
        """Add vendor started event."""
        self.add_event("vendor_started", {
            "vendor_id": vendor_id,
            "vendor_name": vendor_name
        })
    
    def add_vendor_completed(self, vendor_id: str, products_found: int, duration: float):
        """Add vendor completed event."""
        self.add_event("vendor_completed", {
            "vendor_id": vendor_id,
            "products_found": products_found,
            "duration": duration
        })
    
    def add_vendor_error(self, vendor_id: str, error_message: str):
        """Add vendor error event."""
        self.add_event("vendor_error", {
            "vendor_id": vendor_id,
            "error": error_message
        })
    
    def complete(self):
        """Mark search as completed."""
        self.status = SearchStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.add_event("completed", {
            "total_results": len(self.products),
            "duration": (self.completed_at - self.created_at).total_seconds()
        })
    
    def fail(self, error_message: str):
        """Mark search as failed."""
        self.status = SearchStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(timezone.utc)
        self.add_event("error", {
            "error": error_message
        })
    
    def add_event(self, event_type: str, data: Dict[str, Any]):
        """Add an event to the search."""
        event = SearchEvent(
            event=event_type,
            data=data,
            timestamp=datetime.now(timezone.utc)
        )
        self.events.append(event)
    
    def get_new_events(self, last_event_index: int = 0) -> List[SearchEvent]:
        """Get events since last_event_index."""
        return self.events[last_event_index:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert search to dictionary for serialization."""
        return {
            "id": self.id,
            "query": self.query,
            "max_results": self.max_results,
            "status": self.status.value,
            "products": [product.model_dump() for product in self.products],
            "events": [event.model_dump() for event in self.events],
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message
        }

