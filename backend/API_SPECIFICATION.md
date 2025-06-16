# API Structure and Endpoints

## Overview
The dondelocompro.gt API provides both REST endpoints and WebSocket connections for real-time product search and comparison across Guatemalan e-commerce sites.

## Base Configuration
- **Base URL**: `https://api.dondelocompro.gt` (production) / `http://localhost:8000` (development)
- **API Version**: v1
- **Content Type**: `application/json`
- **CORS**: Enabled for frontend domains

## Authentication
Phase 1 does not include authentication. Future phases will implement:
- JWT token-based authentication
- API key authentication for partners
- Rate limiting per user/IP

## REST API Endpoints

### Health Check
```
GET /health
```
**Description**: Check API health and database connectivity
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-16T00:00:00Z",
  "database": "connected",
  "redis": "connected"
}
```

### Product Search
```
POST /api/v1/search
```
**Description**: Initiate a product search across all configured e-commerce sites
**Request Body**:
```json
{
  "query": "iPhone 15 Pro",
  "filters": {
    "min_price": 5000,
    "max_price": 15000,
    "categories": ["electronics", "phones"],
    "vendors": ["cemaco", "max"]
  },
  "options": {
    "include_delivery": true,
    "max_results": 50,
    "timeout": 30
  }
}
```
**Response**:
```json
{
  "search_id": "uuid-search-id",
  "status": "initiated",
  "estimated_time": 15,
  "websocket_url": "ws://localhost:8000/ws/search/uuid-search-id"
}
```

### Search Results
```
GET /api/v1/search/{search_id}/results
```
**Description**: Get current search results for a specific search
**Response**:
```json
{
  "search_id": "uuid-search-id",
  "status": "completed",
  "total_results": 25,
  "search_time": 12.5,
  "results": [
    {
      "id": "product-uuid",
      "name": "iPhone 15 Pro 256GB",
      "price": 12500.00,
      "currency": "GTQ",
      "vendor": "cemaco",
      "vendor_name": "Cemaco",
      "url": "https://cemaco.com/product/iphone-15-pro",
      "image_url": "https://cemaco.com/images/iphone15pro.jpg",
      "availability": "in_stock",
      "delivery_cost": 50.00,
      "delivery_time": "2-3 días",
      "last_updated": "2025-06-16T00:00:00Z"
    }
  ],
  "comparison": {
    "lowest_price": 11800.00,
    "highest_price": 13200.00,
    "average_price": 12450.00,
    "price_range": 1400.00
  }
}
```

### Search History
```
GET /api/v1/search/history
```
**Description**: Get recent search history (future: user-specific)
**Query Parameters**:
- `limit`: Number of results (default: 20, max: 100)
- `offset`: Pagination offset (default: 0)

**Response**:
```json
{
  "searches": [
    {
      "search_id": "uuid",
      "query": "iPhone 15 Pro",
      "timestamp": "2025-06-16T00:00:00Z",
      "results_count": 25,
      "status": "completed"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

### Product Details
```
GET /api/v1/products/{product_id}
```
**Description**: Get detailed information about a specific product
**Response**:
```json
{
  "id": "product-uuid",
  "name": "iPhone 15 Pro 256GB",
  "description": "Latest iPhone with Pro features",
  "price": 12500.00,
  "currency": "GTQ",
  "vendor": "cemaco",
  "vendor_name": "Cemaco",
  "url": "https://cemaco.com/product/iphone-15-pro",
  "images": [
    "https://cemaco.com/images/iphone15pro-1.jpg",
    "https://cemaco.com/images/iphone15pro-2.jpg"
  ],
  "specifications": {
    "brand": "Apple",
    "model": "iPhone 15 Pro",
    "storage": "256GB",
    "color": "Natural Titanium"
  },
  "availability": "in_stock",
  "delivery_cost": 50.00,
  "delivery_time": "2-3 días",
  "price_history": [
    {
      "price": 12500.00,
      "date": "2025-06-16T00:00:00Z"
    }
  ],
  "last_updated": "2025-06-16T00:00:00Z"
}
```

### Vendors
```
GET /api/v1/vendors
```
**Description**: Get list of supported vendors/stores
**Response**:
```json
{
  "vendors": [
    {
      "id": "cemaco",
      "name": "Cemaco",
      "website": "https://cemaco.com",
      "logo": "https://api.dondelocompro.gt/logos/cemaco.png",
      "categories": ["electronics", "home", "appliances"],
      "delivery_areas": ["Guatemala City", "Antigua", "Quetzaltenango"],
      "status": "active",
      "last_scraped": "2025-06-16T00:00:00Z"
    }
  ]
}
```

### Categories
```
GET /api/v1/categories
```
**Description**: Get product categories for filtering
**Response**:
```json
{
  "categories": [
    {
      "id": "electronics",
      "name": "Electrónicos",
      "subcategories": [
        {
          "id": "phones",
          "name": "Teléfonos"
        },
        {
          "id": "computers",
          "name": "Computadoras"
        }
      ]
    }
  ]
}
```

## WebSocket API

### Real-time Search Updates
```
WS /ws/search/{search_id}
```
**Description**: Real-time updates for search progress and results

**Connection Flow**:
1. Client connects to WebSocket endpoint
2. Server sends initial status
3. Server streams results as they are found
4. Server sends completion status

**Message Types**:

#### Search Started
```json
{
  "type": "search_started",
  "search_id": "uuid",
  "timestamp": "2025-06-16T00:00:00Z",
  "vendors_count": 5
}
```

#### Vendor Started
```json
{
  "type": "vendor_started",
  "search_id": "uuid",
  "vendor": "cemaco",
  "vendor_name": "Cemaco",
  "timestamp": "2025-06-16T00:00:00Z"
}
```

#### Product Found
```json
{
  "type": "product_found",
  "search_id": "uuid",
  "vendor": "cemaco",
  "product": {
    "id": "product-uuid",
    "name": "iPhone 15 Pro 256GB",
    "price": 12500.00,
    "currency": "GTQ",
    "url": "https://cemaco.com/product/iphone-15-pro",
    "image_url": "https://cemaco.com/images/iphone15pro.jpg"
  },
  "timestamp": "2025-06-16T00:00:00Z"
}
```

#### Vendor Completed
```json
{
  "type": "vendor_completed",
  "search_id": "uuid",
  "vendor": "cemaco",
  "results_count": 5,
  "duration": 3.2,
  "timestamp": "2025-06-16T00:00:00Z"
}
```

#### Search Completed
```json
{
  "type": "search_completed",
  "search_id": "uuid",
  "total_results": 25,
  "total_duration": 12.5,
  "comparison": {
    "lowest_price": 11800.00,
    "highest_price": 13200.00,
    "average_price": 12450.00
  },
  "timestamp": "2025-06-16T00:00:00Z"
}
```

#### Error
```json
{
  "type": "error",
  "search_id": "uuid",
  "vendor": "cemaco",
  "error": "Connection timeout",
  "timestamp": "2025-06-16T00:00:00Z"
}
```

## Error Handling

### HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "Search query cannot be empty",
    "details": {
      "field": "query",
      "value": ""
    },
    "timestamp": "2025-06-16T00:00:00Z"
  }
}
```

### Common Error Codes
- `INVALID_QUERY`: Search query validation failed
- `SEARCH_TIMEOUT`: Search took too long to complete
- `VENDOR_UNAVAILABLE`: One or more vendors are not accessible
- `RATE_LIMIT_EXCEEDED`: Too many requests from client
- `INTERNAL_ERROR`: Unexpected server error

## Rate Limiting

### Current Limits (Phase 1)
- **Search requests**: 10 per minute per IP
- **Result requests**: 60 per minute per IP
- **WebSocket connections**: 5 concurrent per IP

### Headers
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in window
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

## Data Models

### Search Request
```python
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    filters: Optional[SearchFilters] = None
    options: Optional[SearchOptions] = None

class SearchFilters(BaseModel):
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    categories: Optional[List[str]] = None
    vendors: Optional[List[str]] = None

class SearchOptions(BaseModel):
    include_delivery: bool = True
    max_results: int = Field(50, ge=1, le=100)
    timeout: int = Field(30, ge=5, le=60)
```

### Product Model
```python
class Product(BaseModel):
    id: str
    name: str
    price: float
    currency: str = "GTQ"
    vendor: str
    vendor_name: str
    url: str
    image_url: Optional[str] = None
    availability: str
    delivery_cost: Optional[float] = None
    delivery_time: Optional[str] = None
    last_updated: datetime
```

## Future Enhancements

### Phase 2 Features
- User authentication and personalized searches
- Search alerts and notifications
- Advanced filtering and sorting
- Product comparison tools
- Price history tracking

### Phase 3 Features
- Machine learning recommendations
- Bulk search API for partners
- Webhook notifications
- Advanced analytics API
- Mobile app specific endpoints

