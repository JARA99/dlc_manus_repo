from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urljoin, urlparse
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ScrapedProduct:
    """Data class for scraped product information."""
    name: str
    price: float
    vendor_id: str
    vendor_url: str
    currency: str = "GTQ"
    image_url: Optional[str] = None
    availability: str = "unknown"
    brand: Optional[str] = None
    model: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    delivery_cost: Optional[float] = None
    delivery_time: Optional[str] = None
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None


@dataclass
class ScrapingResult:
    """Result of a scraping operation."""
    vendor_id: str
    query: str
    products: List[ScrapedProduct]
    success: bool
    error_message: Optional[str] = None
    duration: float = 0.0
    total_found: int = 0
    pages_scraped: int = 0


class BaseScraper(ABC):
    """Abstract base class for all vendor scrapers."""
    
    def __init__(self, vendor_id: str, config: Dict[str, Any]):
        self.vendor_id = vendor_id
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_session()
    
    async def init_session(self):
        """Initialize HTTP session with proper headers."""
        timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Override session initialization for Cemaco
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(ssl=False, limit=10)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
            connector=connector
        )
    
    async def close_session(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
    
    async def search(self, query: str, max_results: int = 50) -> ScrapingResult:
        """
        Search for products on the vendor's website.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            ScrapingResult with found products
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting search for '{query}' on {self.vendor_id}")
            
            # Normalize query
            normalized_query = self.normalize_query(query)
            
            # Perform search
            products = await self._search_products(normalized_query, max_results)
            
            duration = time.time() - start_time
            
            result = ScrapingResult(
                vendor_id=self.vendor_id,
                query=query,
                products=products,
                success=True,
                duration=duration,
                total_found=len(products),
                pages_scraped=1  # Will be updated by specific implementations
            )
            
            logger.info(f"Search completed for {self.vendor_id}: {len(products)} products found in {duration:.2f}s")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Search failed for {self.vendor_id}: {str(e)}")
            
            return ScrapingResult(
                vendor_id=self.vendor_id,
                query=query,
                products=[],
                success=False,
                error_message=str(e),
                duration=duration
            )
    
    def normalize_query(self, query: str) -> str:
        """Normalize search query for better matching."""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Convert to lowercase for processing
        query_lower = query.lower()
        
        # Common brand name normalizations
        brand_mappings = {
            'iphone': 'iPhone',
            'samsung': 'Samsung',
            'lg': 'LG',
            'sony': 'Sony',
            'hp': 'HP',
            'dell': 'Dell',
            'lenovo': 'Lenovo',
            'asus': 'ASUS',
            'acer': 'Acer'
        }
        
        for old_brand, new_brand in brand_mappings.items():
            if old_brand in query_lower:
                query = re.sub(re.escape(old_brand), new_brand, query, flags=re.IGNORECASE)
        
        return query
    
    async def make_request(self, url: str, headers: dict = None, **kwargs) -> aiohttp.ClientResponse:
        """Make HTTP request with retry logic and rate limiting."""
        if not self.session:
            await self.init_session()
        
        # Merge provided headers with session headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        # Apply rate limiting
        delay = self.config.get('delay', 1.0)
        await asyncio.sleep(delay + random.uniform(0, 0.5))
        
        # Retry logic
        max_retries = self.config.get('max_retries', 3)
        for attempt in range(max_retries + 1):
            try:
                async with self.session.get(url, headers=request_headers, **kwargs) as response:
                    if response.status in [200, 206]:  # Accept both 200 and 206 (partial content)
                        return response
                    elif response.status == 429:  # Rate limited
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited on {self.vendor_id}, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Request error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
        
        raise Exception(f"Failed to fetch {url} after {max_retries + 1} attempts")
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text."""
        if not price_text:
            return None
        
        # Remove common currency symbols and text
        price_text = re.sub(r'[Q$,\s]', '', price_text)
        price_text = re.sub(r'GTQ|USD|quetzales?|dolares?', '', price_text, flags=re.IGNORECASE)
        
        # Extract numeric value
        price_match = re.search(r'(\d+\.?\d*)', price_text)
        if price_match:
            try:
                return float(price_match.group(1))
            except ValueError:
                pass
        
        return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted characters
        text = re.sub(r'[^\w\s\-\.\(\)\/]', '', text)
        
        return text
    
    def extract_brand_model(self, product_name: str) -> tuple[Optional[str], Optional[str]]:
        """Extract brand and model from product name."""
        name_lower = product_name.lower()
        
        # Common brand patterns
        brand_patterns = {
            'apple': r'\b(apple|iphone|ipad|macbook|imac)\b',
            'samsung': r'\bsamsung\b',
            'lg': r'\blg\b',
            'sony': r'\bsony\b',
            'hp': r'\bhp\b',
            'dell': r'\bdell\b',
            'lenovo': r'\blenovo\b',
            'asus': r'\basus\b',
            'acer': r'\bacer\b'
        }
        
        brand = None
        for brand_name, pattern in brand_patterns.items():
            if re.search(pattern, name_lower):
                brand = brand_name.title()
                break
        
        # Extract model (simplified approach)
        model_match = re.search(r'\b([A-Z0-9\-]+\s*\d+[A-Z0-9\-]*)\b', product_name)
        model = model_match.group(1) if model_match else None
        
        return brand, model
    
    @abstractmethod
    async def _search_products(self, query: str, max_results: int) -> List[ScrapedProduct]:
        """
        Implement vendor-specific product search logic.
        
        Args:
            query: Normalized search query
            max_results: Maximum number of results to return
            
        Returns:
            List of ScrapedProduct objects
        """
        pass
    
    @abstractmethod
    def _parse_product_element(self, element, base_url: str) -> Optional[ScrapedProduct]:
        """
        Parse a single product element from search results.
        
        Args:
            element: BeautifulSoup element containing product data
            base_url: Base URL for resolving relative links
            
        Returns:
            ScrapedProduct object or None if parsing fails
        """
        pass

