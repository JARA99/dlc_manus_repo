from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Product(Base):
    """Model for products found across different vendors."""
    
    __tablename__ = "products"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Product information
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    brand = Column(String, index=True)
    model = Column(String)
    sku = Column(String)  # Vendor-specific SKU
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=False, index=True)
    currency = Column(String, default="GTQ")
    original_price = Column(Numeric(10, 2))  # If on sale
    discount_percentage = Column(Numeric(5, 2))
    
    # Vendor information
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=False, index=True)
    vendor_product_id = Column(String)  # Original product ID from vendor
    vendor_url = Column(String, nullable=False)  # Direct link to product
    
    # Category
    category_id = Column(String, ForeignKey("categories.id"), index=True)
    
    # Images and media
    image_url = Column(String)
    image_urls = Column(JSON)  # List of additional images
    
    # Availability and delivery
    availability = Column(String, default="unknown")  # in_stock, out_of_stock, limited, unknown
    stock_quantity = Column(String)  # If available
    delivery_cost = Column(Numeric(8, 2))
    delivery_time = Column(String)  # e.g., "2-3 días"
    delivery_areas = Column(JSON)  # Specific delivery areas if different from vendor default
    
    # Product specifications
    specifications = Column(JSON)  # Key-value pairs of product specs
    features = Column(JSON)  # List of product features
    
    # SEO and search
    search_keywords = Column(Text)  # Processed keywords for search
    normalized_name = Column(String, index=True)  # Normalized product name for matching
    
    # Quality and validation
    data_quality_score = Column(Numeric(3, 2))  # 0.0 to 1.0 score
    is_validated = Column(Boolean, default=False)
    validation_notes = Column(Text)
    
    # Tracking
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_price_change_at = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    vendor = relationship("Vendor", backref="products")
    category = relationship("Category", backref="products")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_product_vendor_price', 'vendor_id', 'price'),
        Index('idx_product_category_price', 'category_id', 'price'),
        Index('idx_product_brand_model', 'brand', 'model'),
        Index('idx_product_search', 'normalized_name', 'brand'),
        Index('idx_product_active_updated', 'is_active', 'last_updated_at'),
    )
    
    def __repr__(self):
        return f"<Product(id='{self.id}', name='{self.name}', vendor='{self.vendor_id}', price={self.price})>"


class ProductPriceHistory(Base):
    """Model for tracking product price changes over time."""
    
    __tablename__ = "product_price_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    
    # Price information
    price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2))
    currency = Column(String, default="GTQ")
    
    # Availability at time of recording
    availability = Column(String)
    
    # Timestamp
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    product = relationship("Product", backref="price_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_price_history_product_date', 'product_id', 'recorded_at'),
    )
    
    def __repr__(self):
        return f"<ProductPriceHistory(product_id='{self.product_id}', price={self.price}, date='{self.recorded_at}')>"

