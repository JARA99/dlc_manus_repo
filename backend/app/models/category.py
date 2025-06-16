from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Category(Base):
    """Model for product categories."""
    
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, index=True)  # e.g., "electronics"
    name = Column(String, nullable=False)  # e.g., "Electrónicos"
    name_en = Column(String)  # English name
    parent_id = Column(String, ForeignKey("categories.id"))
    
    # Hierarchy
    level = Column(String, default="0")  # 0 = root, 1 = subcategory, etc.
    path = Column(String)  # Full path like "electronics/phones"
    
    # Display
    description = Column(Text)
    icon = Column(String)  # Icon identifier
    color = Column(String)  # Color for UI
    
    # SEO
    slug = Column(String, unique=True, index=True)
    meta_description = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    sort_order = Column(String, default="0")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent = relationship("Category", remote_side="Category.id", backref="children")
    
    def __repr__(self):
        return f"<Category(id='{self.id}', name='{self.name}')>"

