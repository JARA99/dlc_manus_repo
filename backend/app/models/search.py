from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Search(Base):
    """Model for tracking search requests and their results."""
    
    __tablename__ = "searches"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Search parameters
    query = Column(String, nullable=False, index=True)
    normalized_query = Column(String, index=True)  # Processed/normalized query
    
    # Filters applied
    filters = Column(JSON)  # Store search filters as JSON
    options = Column(JSON)  # Store search options as JSON
    
    # Search execution
    status = Column(String, default="initiated", index=True)  # initiated, running, completed, failed, timeout
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration = Column(Numeric(8, 3))  # Duration in seconds
    
    # Results summary
    total_results = Column(String, default="0")
    vendors_searched = Column(JSON)  # List of vendor IDs searched
    vendors_successful = Column(JSON)  # List of vendor IDs that returned results
    vendors_failed = Column(JSON)  # List of vendor IDs that failed
    
    # Result statistics
    lowest_price = Column(Numeric(10, 2))
    highest_price = Column(Numeric(10, 2))
    average_price = Column(Numeric(10, 2))
    price_range = Column(Numeric(10, 2))
    
    # Client information
    client_ip = Column(String, index=True)
    user_agent = Column(Text)
    
    # Future: User association
    user_id = Column(String, index=True)  # For future user authentication
    
    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSON)
    
    def __repr__(self):
        return f"<Search(id='{self.id}', query='{self.query}', status='{self.status}')>"


class SearchResult(Base):
    """Model for individual search results linking searches to products."""
    
    __tablename__ = "search_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    search_id = Column(UUID(as_uuid=True), ForeignKey("searches.id"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    
    # Result metadata
    rank = Column(String)  # Position in search results
    relevance_score = Column(Numeric(5, 4))  # 0.0 to 1.0 relevance score
    found_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Vendor-specific information at time of search
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=False)
    price_at_search = Column(Numeric(10, 2))
    availability_at_search = Column(String)
    
    # Relationships
    search = relationship("Search", backref="results")
    product = relationship("Product", backref="search_results")
    vendor = relationship("Vendor")
    
    # Indexes
    __table_args__ = (
        Index('idx_search_results_search_rank', 'search_id', 'rank'),
        Index('idx_search_results_product', 'product_id'),
        Index('idx_search_results_vendor', 'vendor_id'),
    )
    
    def __repr__(self):
        return f"<SearchResult(search_id='{self.search_id}', product_id='{self.product_id}', rank={self.rank})>"


class SearchAnalytics(Base):
    """Model for storing search analytics and trends."""
    
    __tablename__ = "search_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time period
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    hour = Column(String)  # Hour of day (0-23)
    
    # Search metrics
    total_searches = Column(String, default="0")
    successful_searches = Column(String, default="0")
    failed_searches = Column(String, default="0")
    average_duration = Column(Numeric(8, 3))
    
    # Popular queries
    top_queries = Column(JSON)  # List of most searched queries
    top_categories = Column(JSON)  # List of most searched categories
    
    # Vendor performance
    vendor_stats = Column(JSON)  # Performance stats per vendor
    
    # Result metrics
    average_results_per_search = Column(Numeric(8, 2))
    total_products_found = Column(String, default="0")
    
    # Indexes
    __table_args__ = (
        Index('idx_analytics_date', 'date'),
        Index('idx_analytics_date_hour', 'date', 'hour'),
    )
    
    def __repr__(self):
        return f"<SearchAnalytics(date='{self.date}', total_searches={self.total_searches})>"

