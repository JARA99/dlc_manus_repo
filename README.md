# dondelocompro.gt - Product Comparison Platform

A comprehensive product comparison platform for the Guatemalan market, allowing users to search for products across multiple e-commerce vendors and compare prices, availability, and delivery options.

## Project Structure

```
dlc_manus_repo/
├── backend/                 # Backend API and scraping engine
│   ├── app/                # FastAPI application
│   ├── alembic/            # Database migrations
│   ├── tests/              # Test files
│   └── docs/               # Documentation
├── frontend/               # Frontend application (future)
└── docs/                   # Project documentation
```

## Backend

The backend is built with FastAPI and includes:

- **Web Scraping Engine**: Scrapes product data from major Guatemalan e-commerce sites
- **REST API**: Provides product search and comparison endpoints
- **WebSocket Support**: Real-time search results streaming
- **PostgreSQL Database**: Stores product data, search history, and analytics
- **Celery Task Queue**: Handles asynchronous scraping operations

### Supported Vendors

- **Cemaco** (cemaco.com) - Electronics, home, appliances
- **Max** (max.com.gt) - Electronics, computers, phones
- **Elektra** (elektra.com.gt) - Electronics, appliances, furniture
- **Walmart Guatemala** (walmart.com.gt) - General merchandise

### Key Features

- Real-time product search across multiple vendors
- Price comparison and trend tracking
- Delivery cost and time information
- Product categorization and filtering
- Search analytics and reporting
- Scalable architecture for high traffic

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. Run database migrations:
   ```bash
   poetry run alembic upgrade head
   ```

5. Start the development server:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

### API Documentation

Once running, visit:
- API Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Development

### Tech Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- PostgreSQL (Database)
- Celery + Redis (Task queue)
- BeautifulSoup4 + aiohttp (Web scraping)
- Alembic (Database migrations)

**Infrastructure:**
- Docker (Containerization)
- Google Cloud Platform (Database hosting)
- Poetry (Dependency management)

### Contributing

1. Clone the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

Private - dondelocompro.gt

## Contact

For questions or support, contact the development team.

