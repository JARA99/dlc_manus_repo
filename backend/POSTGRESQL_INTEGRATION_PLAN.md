# PostgreSQL Integration Plan - DondeLoCompro.gt API

## 🎯 **Objetivo**

Integrar PostgreSQL a la arquitectura OOP existente para:
- **Persistir búsquedas** y resultados para analytics
- **Tracking de precios** históricos de productos
- **Cache inteligente** de resultados frecuentes
- **Escalabilidad** para múltiples usuarios concurrentes
- **Analytics** de patrones de búsqueda y performance

---

## 🏗️ **Arquitectura Propuesta**

### **🔄 Patrón: Search-First, Save-Later**
```
1. Usuario inicia búsqueda → Scraping inmediato (como ahora)
2. Resultados vía SSE → Experiencia en tiempo real
3. Background save → PostgreSQL (sin afectar performance)
4. Analytics async → Procesamiento de datos
```

### **📊 Esquema de Base de Datos**

```sql
-- Vendors (catálogo de tiendas)
CREATE TABLE vendors (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    base_url VARCHAR(255) NOT NULL,
    country VARCHAR(2) DEFAULT 'GT',
    currency VARCHAR(3) DEFAULT 'GTQ',
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Categories (categorías de productos)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    parent_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Products (productos únicos por vendor)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    vendor_id VARCHAR(50) REFERENCES vendors(id),
    vendor_product_id VARCHAR(255), -- ID del producto en el vendor
    name TEXT NOT NULL,
    brand VARCHAR(100),
    category_id INTEGER REFERENCES categories(id),
    url TEXT,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(vendor_id, vendor_product_id)
);

-- Product Prices (historial de precios)
CREATE TABLE product_prices (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'GTQ',
    availability VARCHAR(20) DEFAULT 'unknown',
    scraped_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_product_scraped (product_id, scraped_at)
);

-- Searches (búsquedas de usuarios)
CREATE TABLE searches (
    id UUID PRIMARY KEY,
    query TEXT NOT NULL,
    max_results INTEGER DEFAULT 10,
    status VARCHAR(20) DEFAULT 'initiated',
    total_products INTEGER DEFAULT 0,
    total_vendors INTEGER DEFAULT 0,
    duration_seconds DECIMAL(5,3),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT,
    INDEX idx_query_created (query, created_at),
    INDEX idx_status_created (status, created_at)
);

-- Search Results (productos encontrados por búsqueda)
CREATE TABLE search_results (
    id SERIAL PRIMARY KEY,
    search_id UUID REFERENCES searches(id),
    product_id INTEGER REFERENCES products(id),
    position INTEGER, -- posición en resultados
    relevance_score DECIMAL(3,2), -- futuro: scoring de relevancia
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_search_position (search_id, position)
);

-- Search Events (eventos de búsqueda para debugging)
CREATE TABLE search_events (
    id SERIAL PRIMARY KEY,
    search_id UUID REFERENCES searches(id),
    event_type VARCHAR(50) NOT NULL,
    vendor_id VARCHAR(50),
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_search_created (search_id, created_at)
);

-- Vendor Performance (métricas de performance por vendor)
CREATE TABLE vendor_performance (
    id SERIAL PRIMARY KEY,
    vendor_id VARCHAR(50) REFERENCES vendors(id),
    date DATE NOT NULL,
    total_searches INTEGER DEFAULT 0,
    total_products INTEGER DEFAULT 0,
    avg_duration_seconds DECIMAL(5,3),
    success_rate DECIMAL(3,2),
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(vendor_id, date)
);
```

---

## 🔧 **Implementación por Fases**

### **📅 FASE 1: Database Setup & Models (2-3 días)**

#### **1.1 Dependencies & Configuration**
```python
# Nuevas dependencias
pip install sqlalchemy asyncpg alembic

# .env additions
DATABASE_URL=postgresql://user:pass@localhost/dondelocompro
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

#### **1.2 Database Models**
```python
# dlc_api/database/
├── __init__.py
├── connection.py      # Database connection & session management
├── models/
│   ├── __init__.py
│   ├── base.py        # SQLAlchemy base model
│   ├── vendor.py      # Vendor SQLAlchemy model
│   ├── product.py     # Product & ProductPrice models
│   ├── search.py      # Search & SearchResult models
│   └── analytics.py   # VendorPerformance model
└── migrations/        # Alembic migrations
    ├── env.py
    └── versions/
```

#### **1.3 Repository Pattern**
```python
# dlc_api/repositories/
├── __init__.py
├── base.py           # Base repository with common operations
├── search.py         # SearchRepository
├── product.py        # ProductRepository
└── analytics.py      # AnalyticsRepository
```

### **📅 FASE 2: Core Integration (2-3 días)**

#### **2.1 Enhanced SearchManager**
```python
class SearchManager:
    def __init__(self, scraper_registry, search_repo=None):
        self.scraper_registry = scraper_registry
        self.search_repo = search_repo or InMemorySearchRepo()
        self.active_searches: Dict[str, Search] = {}
    
    async def create_search(self, request: SearchRequest) -> Search:
        # 1. Create search in memory (immediate)
        search = Search(query=request.query, max_results=request.max_results)
        self.active_searches[search.id] = search
        
        # 2. Save to database (background)
        asyncio.create_task(self._save_search_to_db(search))
        
        # 3. Start scraping (immediate)
        asyncio.create_task(self._execute_search(search))
        
        return search
    
    async def _save_search_to_db(self, search: Search):
        """Background task to save search to database."""
        try:
            await self.search_repo.create_search(search)
        except Exception as e:
            # Log error but don't affect user experience
            logger.error(f"Failed to save search {search.id}: {e}")
```

#### **2.2 Product Persistence**
```python
class ProductManager:
    def __init__(self, product_repo):
        self.product_repo = product_repo
    
    async def save_search_results(self, search: Search):
        """Save products and prices from search results."""
        for product in search.products:
            # 1. Get or create product
            db_product = await self.product_repo.get_or_create_product(
                vendor_id=product.vendor_id,
                name=product.name,
                brand=product.brand,
                url=product.url
            )
            
            # 2. Save current price
            await self.product_repo.save_price(
                product_id=db_product.id,
                price=product.price,
                currency=product.currency,
                availability=product.availability
            )
            
            # 3. Link to search
            await self.search_repo.add_search_result(
                search_id=search.id,
                product_id=db_product.id
            )
```

### **📅 FASE 3: Analytics & Optimization (2-3 días)**

#### **3.1 Analytics Service**
```python
class AnalyticsService:
    def __init__(self, analytics_repo):
        self.analytics_repo = analytics_repo
    
    async def update_vendor_performance(self, vendor_id: str, duration: float, success: bool, products_found: int):
        """Update daily vendor performance metrics."""
        await self.analytics_repo.update_daily_performance(
            vendor_id=vendor_id,
            duration=duration,
            success=success,
            products_found=products_found
        )
    
    async def get_popular_searches(self, days: int = 7) -> List[str]:
        """Get most popular search queries."""
        return await self.analytics_repo.get_popular_queries(days)
    
    async def get_price_trends(self, product_id: int, days: int = 30) -> List[PriceTrend]:
        """Get price history for a product."""
        return await self.analytics_repo.get_price_history(product_id, days)
```

#### **3.2 Smart Caching**
```python
class CacheService:
    def __init__(self, search_repo):
        self.search_repo = search_repo
    
    async def get_cached_results(self, query: str, max_age_minutes: int = 30) -> Optional[List[Product]]:
        """Get recent search results for the same query."""
        recent_search = await self.search_repo.get_recent_search(
            query=query,
            max_age_minutes=max_age_minutes
        )
        
        if recent_search:
            return await self.search_repo.get_search_products(recent_search.id)
        
        return None
```

### **📅 FASE 4: API Enhancements (1-2 días)**

#### **4.1 New Endpoints**
```python
# Analytics endpoints
@router.get("/analytics/popular-searches")
async def get_popular_searches(days: int = 7):
    """Get most popular search queries."""
    
@router.get("/analytics/vendor-performance")
async def get_vendor_performance(vendor_id: str, days: int = 30):
    """Get vendor performance metrics."""

@router.get("/products/{product_id}/price-history")
async def get_price_history(product_id: int, days: int = 30):
    """Get price history for a product."""

# Enhanced search with caching
@router.post("/search")
async def start_search(request: SearchRequest, use_cache: bool = True):
    """Start search with optional caching."""
```

#### **4.2 Database Health Check**
```python
@router.get("/health")
async def health():
    """Enhanced health check with database status."""
    db_status = await check_database_connection()
    
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "scrapers": scraper_registry.get_vendor_ids(),
        "timestamp": datetime.now(timezone.utc)
    }
```

---

## 🔄 **Migration Strategy**

### **🎯 Zero-Downtime Migration**
```python
# 1. Deploy with database support (optional)
DATABASE_ENABLED = os.getenv("DATABASE_ENABLED", "false").lower() == "true"

class SearchManager:
    def __init__(self, scraper_registry, search_repo=None):
        self.scraper_registry = scraper_registry
        
        if DATABASE_ENABLED and search_repo:
            self.search_repo = search_repo
            self.use_database = True
        else:
            self.search_repo = InMemorySearchRepo()
            self.use_database = False

# 2. Gradual rollout
# - Week 1: Deploy with DATABASE_ENABLED=false (current behavior)
# - Week 2: Enable database for 10% of searches
# - Week 3: Enable database for 50% of searches  
# - Week 4: Enable database for 100% of searches
```

### **🔧 Backward Compatibility**
```python
# Keep existing API contracts
# Add new features as optional parameters
# Maintain current performance characteristics
```

---

## 📊 **Performance Considerations**

### **⚡ Optimization Strategies**

#### **1. Async Database Operations**
```python
# Non-blocking database saves
asyncio.create_task(self._save_search_to_db(search))

# Connection pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

#### **2. Smart Indexing**
```sql
-- Query performance
CREATE INDEX idx_searches_query_created ON searches(query, created_at);
CREATE INDEX idx_products_vendor_name ON products(vendor_id, name);
CREATE INDEX idx_prices_product_scraped ON product_prices(product_id, scraped_at DESC);

-- Analytics performance  
CREATE INDEX idx_vendor_performance_date ON vendor_performance(vendor_id, date);
CREATE INDEX idx_search_events_search_created ON search_events(search_id, created_at);
```

#### **3. Batch Operations**
```python
# Batch insert products and prices
async def save_search_results_batch(self, search: Search):
    """Save all products from search in a single transaction."""
    async with self.db.transaction():
        # Batch insert products
        products = await self.product_repo.bulk_create_products(search.products)
        
        # Batch insert prices
        await self.product_repo.bulk_create_prices(products)
        
        # Batch insert search results
        await self.search_repo.bulk_create_search_results(search.id, products)
```

---

## 🧪 **Testing Strategy**

### **🔧 Database Testing**
```python
# Test database setup
@pytest.fixture
async def test_db():
    """Create test database for each test."""
    engine = create_async_engine("postgresql://test:test@localhost/test_dlc")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Integration tests
async def test_search_with_database(test_db):
    """Test complete search flow with database."""
    search_repo = SearchRepository(test_db)
    search_manager = SearchManager(scraper_registry, search_repo)
    
    # Execute search
    search = await search_manager.create_search(SearchRequest(query="test"))
    
    # Verify database persistence
    db_search = await search_repo.get_search(search.id)
    assert db_search.query == "test"
```

### **🎯 Performance Testing**
```python
# Load testing with database
async def test_concurrent_searches_with_db():
    """Test 100 concurrent searches with database."""
    tasks = []
    for i in range(100):
        task = search_manager.create_search(SearchRequest(query=f"test{i}"))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    assert len(results) == 100
```

---

## 🚀 **Deployment Plan**

### **📅 Timeline (7-10 días total)**
- **Días 1-3:** Fase 1 (Database setup & models)
- **Días 4-6:** Fase 2 (Core integration)
- **Días 7-9:** Fase 3 (Analytics & optimization)
- **Día 10:** Fase 4 (API enhancements & testing)

### **🎯 Success Metrics**
- **Performance:** Mantener <1s tiempo de respuesta
- **Reliability:** 99.9% uptime durante migración
- **Data integrity:** 100% de búsquedas persistidas
- **Analytics:** Dashboards funcionales en 1 semana

### **🔧 Rollback Plan**
```python
# Emergency rollback
DATABASE_ENABLED=false  # Instant fallback to in-memory
# Previous version deployment ready
# Database can be dropped without affecting core functionality
```

---

## 💡 **Benefits Expected**

### **📊 Analytics & Insights**
- **Popular products:** Trending searches and products
- **Vendor performance:** Response times and success rates
- **Price trends:** Historical price tracking
- **User patterns:** Search behavior analysis

### **⚡ Performance Improvements**
- **Smart caching:** Avoid repeated scraping for popular queries
- **Batch operations:** Efficient database writes
- **Connection pooling:** Optimal database resource usage

### **🎯 Business Value**
- **Data-driven decisions:** Analytics for business strategy
- **User experience:** Faster responses via caching
- **Scalability:** Ready for thousands of concurrent users
- **Monetization ready:** Data foundation for premium features

---

## ❓ **Discussion Points**

### **🤔 Questions for Review:**

1. **Database Choice:** ¿PostgreSQL vs MySQL vs MongoDB?
2. **Caching Strategy:** ¿Redis adicional o solo PostgreSQL?
3. **Migration Timeline:** ¿7-10 días es realista?
4. **Performance Impact:** ¿Acceptable overhead for persistence?
5. **Analytics Scope:** ¿Qué métricas son más importantes inicialmente?
6. **Data Retention:** ¿Cuánto tiempo mantener historical data?
7. **Backup Strategy:** ¿Daily backups sufficient?
8. **Monitoring:** ¿Qué alertas necesitamos?

### **🎯 Decisions Needed:**
- **Database hosting:** Local vs Cloud (AWS RDS, Google Cloud SQL)
- **Environment setup:** Development, staging, production databases
- **Security:** Database credentials management
- **Monitoring:** Database performance monitoring tools

---

**¿Estás listo para discutir este plan y comenzar la implementación?** 🚀

