# dondelocompro.gt Backend

Backend system for dondelocompro.gt - a comprehensive product comparison platform for the Guatemalan market.

## Overview

This backend provides:
- Web scraping engine for Guatemalan e-commerce sites
- FastAPI REST API with WebSocket support
- Real-time product search and comparison
- PostgreSQL database for product data storage
- Scalable architecture for future growth

## Features

- **Web Scraping Engine**: Resilient scraping system for extracting product data from various e-commerce sites
- **Real-time Search**: WebSocket-based real-time search results delivery
- **Product Comparison**: Comprehensive price and vendor comparison across multiple stores
- **Scalable Architecture**: Designed for high traffic and data volume growth
- **Anti-scraping Measures**: Robust handling of website protection mechanisms

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Web Scraping**: Requests, BeautifulSoup4, Playwright
- **Task Queue**: Celery with Redis
- **WebSockets**: Native FastAPI WebSocket support
- **Deployment**: Docker containerization

## Project Structure

```
dondelocompro-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection and setup
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API routes
│   ├── scraping/            # Web scraping engine
│   ├── services/            # Business logic services
│   └── utils/               # Utility functions
├── alembic/                 # Database migrations
├── tests/                   # Test files
├── docker/                  # Docker configuration
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Installation

1. Clone the repository
2. Install dependencies with Poetry:
   ```bash
   poetry install
   ```
3. Set up environment variables (see .env.example)
4. Run database migrations:
   ```bash
   poetry run alembic upgrade head
   ```
5. Start the development server:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

## Development

- **Code Formatting**: Black, isort
- **Linting**: Flake8
- **Testing**: pytest with async support
- **Database**: PostgreSQL with Alembic migrations

## API Documentation

Once running, visit:
- API Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## License

Private - dondelocompro.gt

