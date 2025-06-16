# System Architecture Design

## Overview
The dondelocompro.gt backend follows a microservices-inspired architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   PostgreSQL    │
│   (Svelte)      │◄──►│   Backend       │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Celery        │◄──►│   Redis         │
                       │   Workers       │    │   Broker        │
                       └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Web Scraping  │
                       │   Engine        │
                       └─────────────────┘
```

## Core Components

### 1. FastAPI Application
- **Main API Server**: Handles HTTP requests and WebSocket connections
- **WebSocket Manager**: Real-time communication for search results
- **CORS Configuration**: Cross-origin support for frontend
- **Authentication**: Future-ready for user management

### 2. Web Scraping Engine
- **Base Scraper Class**: Abstract interface for all scrapers
- **Site-Specific Scrapers**: Individual scrapers for each e-commerce site
- **Anti-Detection**: Rotating user agents, delays, proxy support
- **Data Extraction**: Product name, price, vendor, direct link
- **Error Handling**: Retry mechanisms and graceful failures

### 3. Database Layer
- **PostgreSQL**: Primary data store for products and search history
- **SQLAlchemy ORM**: Object-relational mapping with async support
- **Alembic Migrations**: Database schema versioning
- **Connection Pooling**: Efficient database connections

### 4. Task Queue System
- **Celery Workers**: Asynchronous scraping tasks
- **Redis Broker**: Message queue for task distribution
- **Result Backend**: Task result storage and retrieval
- **Monitoring**: Task status and progress tracking

### 5. Search System
- **Keyword Processing**: Text normalization and matching
- **Real-time Results**: WebSocket streaming of search findings
- **Result Aggregation**: Price comparison and vendor analysis
- **Caching**: Redis-based result caching for performance

## Data Flow

### Search Request Flow
1. **User Input**: Search query received via WebSocket or REST API
2. **Query Processing**: Keyword normalization and validation
3. **Task Dispatch**: Celery tasks created for each target site
4. **Parallel Scraping**: Multiple scrapers execute concurrently
5. **Real-time Updates**: Results streamed via WebSocket as found
6. **Data Storage**: Products saved to PostgreSQL
7. **Result Aggregation**: Final comparison data compiled

### Scraping Workflow (per site)
1. **Site Detection**: Identify target e-commerce platform
2. **Search Execution**: Submit search query to site
3. **Page Parsing**: Extract product listings
4. **Data Extraction**: Parse product details
5. **Validation**: Verify data quality and completeness
6. **Storage**: Save to database with metadata
7. **Notification**: Send results via WebSocket

## Scalability Considerations

### Horizontal Scaling
- **Stateless API**: FastAPI instances can be load-balanced
- **Worker Scaling**: Celery workers can be distributed across machines
- **Database Sharding**: Future partitioning by vendor or category
- **Cache Distribution**: Redis clustering for high availability

### Performance Optimization
- **Connection Pooling**: Database and Redis connection reuse
- **Async Operations**: Non-blocking I/O throughout the stack
- **Result Caching**: Frequently searched products cached
- **Rate Limiting**: Prevent abuse and manage scraping load

### Anti-Scraping Strategy
- **User Agent Rotation**: Mimic different browsers and devices
- **Request Delays**: Randomized delays between requests
- **Proxy Support**: IP rotation for high-volume scraping
- **Session Management**: Maintain cookies and state
- **Fallback Mechanisms**: Alternative scraping methods

## Security Measures

### Data Protection
- **Input Validation**: Sanitize all user inputs
- **SQL Injection Prevention**: Parameterized queries via ORM
- **XSS Protection**: Output encoding and CSP headers
- **Rate Limiting**: Prevent API abuse

### Scraping Ethics
- **Robots.txt Compliance**: Respect site scraping policies
- **Request Rate Limiting**: Avoid overwhelming target sites
- **Error Handling**: Graceful failures without retries on blocks
- **Legal Compliance**: Adhere to Guatemalan data protection laws

## Monitoring and Logging

### Application Monitoring
- **Health Checks**: API and database connectivity
- **Performance Metrics**: Response times and throughput
- **Error Tracking**: Exception logging and alerting
- **Resource Usage**: CPU, memory, and disk monitoring

### Scraping Monitoring
- **Success Rates**: Track scraping effectiveness per site
- **Error Analysis**: Identify and resolve scraping issues
- **Data Quality**: Monitor extracted data completeness
- **Site Changes**: Detect when sites modify their structure

## Future Enhancements

### Phase 2 Features
- **User Authentication**: Account management and preferences
- **Search History**: Personal search tracking and recommendations
- **Price Alerts**: Notifications for price changes
- **Advanced Filtering**: Category, brand, and price range filters

### Phase 3 Features
- **Machine Learning**: Product matching and recommendation engine
- **API Partnerships**: Direct integrations with major retailers
- **Mobile App**: Native mobile application support
- **Analytics Dashboard**: Business intelligence and reporting

