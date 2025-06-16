from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Vendor(Base):
    """Model for e-commerce vendors/stores."""
    
    __tablename__ = "vendors"
    
    id = Column(String, primary_key=True, index=True)  # e.g., "cemaco", "max"
    name = Column(String, nullable=False)  # e.g., "Cemaco", "Max"
    website = Column(String, nullable=False)
    logo_url = Column(String)
    
    # Configuration
    base_url = Column(String, nullable=False)
    search_url_template = Column(String)  # Template for search URLs
    is_active = Column(Boolean, default=True)
    
    # Scraping configuration
    scraping_config = Column(JSON)  # Store scraper-specific settings
    
    # Delivery information
    delivery_areas = Column(JSON)  # List of delivery areas
    default_delivery_cost = Column(String)  # Default delivery cost info
    
    # Categories supported
    supported_categories = Column(JSON)  # List of category IDs
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_scraped_at = Column(DateTime(timezone=True))
    
    # Status tracking
    status = Column(String, default="active")  # active, inactive, error
    last_error = Column(Text)
    error_count = Column(String, default="0")
    
    def __repr__(self):
        return f"<Vendor(id='{self.id}', name='{self.name}')>"

