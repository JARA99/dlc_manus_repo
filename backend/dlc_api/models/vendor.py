"""
Vendor model for store/vendor information
"""

from pydantic import BaseModel, Field


class Vendor(BaseModel):
    """Vendor/Store information."""
    id: str = Field(..., description="Unique vendor identifier")
    name: str = Field(..., description="Display name of the vendor")
    base_url: str = Field(..., description="Base URL of the vendor website")
    country: str = Field(default="GT", description="Country code")
    currency: str = Field(default="GTQ", description="Default currency")
    active: bool = Field(default=True, description="Whether vendor is active")
    
    # Future fields for shipping costs, rate limiting, etc.
    # shipping_cost: Optional[float] = None
    # free_shipping_threshold: Optional[float] = None
    # rate_limit_per_minute: int = 60
    # timeout_seconds: int = 30

