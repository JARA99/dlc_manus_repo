# Database Schema Documentation

## Overview
The dondelocompro.gt database schema is designed to efficiently store and query product information from multiple Guatemalan e-commerce vendors, track search history, and provide analytics.

## Core Tables

### vendors
Stores information about e-commerce vendors/stores that are scraped.

**Key Fields:**
- `id` (String, PK): Unique vendor identifier (e.g., "cemaco", "max")
- `name` (String): Display name (e.g., "Cemaco", "Max")
- `website` (String): Vendor website URL
- `base_url` (String): Base URL for scraping
- `scraping_config` (JSON): Vendor-specific scraping configuration
- `is_active` (Boolean): Whether vendor is currently being scraped
- `status` (String): Current vendor status (active, inactive, error)

### categories
Hierarchical product categories for classification and filtering.

**Key Fields:**
- `id` (String, PK): Category identifier (e.g., "electronics")
- `name` (String): Display name in Spanish
- `name_en` (String): English name
- `parent_id` (String, FK): Parent category for hierarchy
- `path` (String): Full category path
- `is_active` (Boolean): Whether category is active

### products
Core table storing product information from all vendors.

**Key Fields:**
- `id` (UUID, PK): Unique product identifier
- `name` (String): Product name as found on vendor site
- `normalized_name` (String): Processed name for search matching
- `brand` (String): Product brand
- `model` (String): Product model
- `price` (Numeric): Current price in GTQ
- `vendor_id` (String, FK): Reference to vendor
- `category_id` (String, FK): Reference to category
- `vendor_url` (String): Direct link to product on vendor site
- `availability` (String): Stock status
- `specifications` (JSON): Product specifications
- `is_active` (Boolean): Whether product is currently available

**Indexes:**
- `idx_product_vendor_price`: Vendor + price for vendor-specific queries
- `idx_product_category_price`: Category + price for category browsing
- `idx_product_search`: Normalized name + brand for search
- `idx_product_active_updated`: Active status + update time for maintenance

### product_price_history
Tracks price changes over time for trend analysis.

**Key Fields:**
- `id` (UUID, PK): Unique record identifier
- `product_id` (UUID, FK): Reference to product
- `price` (Numeric): Price at time of recording
- `recorded_at` (DateTime): When price was recorded
- `availability` (String): Availability at time of recording

### searches
Tracks search requests and their metadata.

**Key Fields:**
- `id` (UUID, PK): Unique search identifier
- `query` (String): Original search query
- `normalized_query` (String): Processed query for analysis
- `status` (String): Search status (initiated, running, completed, failed)
- `filters` (JSON): Applied search filters
- `total_results` (Integer): Number of results found
- `duration` (Numeric): Search execution time
- `client_ip` (String): Client IP for rate limiting

### search_results
Links searches to found products with relevance scoring.

**Key Fields:**
- `id` (UUID, PK): Unique result identifier
- `search_id` (UUID, FK): Reference to search
- `product_id` (UUID, FK): Reference to product
- `rank` (Integer): Position in search results
- `relevance_score` (Numeric): Search relevance (0.0-1.0)
- `price_at_search` (Numeric): Product price when found

### search_analytics
Aggregated search statistics for business intelligence.

**Key Fields:**
- `id` (UUID, PK): Unique analytics record
- `date` (DateTime): Date of analytics period
- `total_searches` (Integer): Number of searches performed
- `top_queries` (JSON): Most popular search queries
- `vendor_stats` (JSON): Performance statistics per vendor

## Relationships

```
vendors (1) ←→ (N) products
categories (1) ←→ (N) products
categories (1) ←→ (N) categories (self-referential hierarchy)
products (1) ←→ (N) product_price_history
searches (1) ←→ (N) search_results
products (1) ←→ (N) search_results
vendors (1) ←→ (N) search_results
```

## Data Types and Constraints

### Numeric Fields
- **Prices**: `Numeric(10, 2)` - Supports up to 99,999,999.99 GTQ
- **Scores**: `Numeric(5, 4)` - Supports 0.0000 to 9.9999 range
- **Durations**: `Numeric(8, 3)` - Supports up to 99999.999 seconds

### String Fields
- **IDs**: Variable length strings for vendor/category IDs
- **Names**: Standard VARCHAR for product/vendor names
- **URLs**: TEXT for long URLs
- **Descriptions**: TEXT for unlimited length content

### JSON Fields
Used for flexible, schema-less data:
- **Configurations**: Vendor scraping settings
- **Specifications**: Product technical details
- **Filters**: Search filter parameters
- **Analytics**: Aggregated statistics

### DateTime Fields
All timestamps use `DateTime(timezone=True)` with UTC storage.

## Indexing Strategy

### Primary Indexes
- All primary keys are automatically indexed
- Foreign keys are explicitly indexed for join performance

### Search Indexes
- `products.normalized_name` + `brand` for text search
- `products.price` for price-based filtering
- `searches.query` for search analytics

### Performance Indexes
- Composite indexes on frequently queried field combinations
- Partial indexes on active records only where applicable

## Data Integrity

### Foreign Key Constraints
- All relationships enforced with foreign key constraints
- Cascading deletes configured where appropriate

### Check Constraints
- Price values must be positive
- Relevance scores between 0.0 and 1.0
- Status fields limited to valid enum values

### Unique Constraints
- Category slugs must be unique
- Vendor IDs must be unique

## Partitioning Strategy (Future)

### Time-based Partitioning
- `product_price_history`: Partition by month for historical data
- `search_analytics`: Partition by month for analytics data
- `searches`: Partition by month for old search cleanup

### Hash Partitioning
- `products`: Potential partitioning by vendor_id for large datasets
- `search_results`: Potential partitioning by search_id

## Maintenance Procedures

### Data Cleanup
- Archive old search records (>6 months)
- Compress old price history data
- Remove inactive products after extended periods

### Statistics Updates
- Daily aggregation of search analytics
- Weekly vendor performance reports
- Monthly data quality assessments

### Index Maintenance
- Regular REINDEX operations for heavily updated tables
- VACUUM operations for deleted record cleanup
- ANALYZE operations for query planner statistics

## Security Considerations

### Data Access
- No sensitive user data stored in Phase 1
- IP addresses stored for rate limiting only
- Search queries may contain personal preferences

### Backup Strategy
- Daily full database backups
- Point-in-time recovery capability
- Encrypted backup storage

### Compliance
- GDPR-ready for future user data
- Data retention policies implemented
- Audit trail for data modifications

