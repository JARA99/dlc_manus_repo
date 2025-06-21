"""
Cemaco Scraper - Functional implementation for VTEX-based e-commerce
"""

import asyncio
import aiohttp
import time
from typing import List
from bs4 import BeautifulSoup
from ..models import Vendor, Product, ScrapingResult
from .base import BaseScraper


class CemacoScraper(BaseScraper):
    """Scraper for Cemaco.com (VTEX platform)."""
    
    # Vendor information defined at class level
    VENDOR_INFO = Vendor(
        id="cemaco",
        name="Cemaco",
        base_url="https://www.cemaco.com",
        country="GT",
        currency="GTQ",
        active=True
    )
    
    def __init__(self):
        super().__init__()  # Initializes self.vendor from VENDOR_INFO
        self.api_url = f"{self.vendor.base_url}/api/catalog_system/pub/products/search"
    
    async def search(self, query: str, max_results: int = 10) -> ScrapingResult:
        """Search for products on Cemaco."""
        start_time = time.time()
        
        try:
            # Create session with proper headers
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                
                # Search via VTEX API
                params = {
                    "ft": query,
                    "_from": "0",
                    "_to": str(max_results - 1)
                }
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                    "Referer": f"{self.vendor.base_url}/",
                    "Origin": self.vendor.base_url
                }
                
                async with session.get(
                    self.api_url,
                    params=params,
                    headers=headers
                ) as response:
                    
                    # Accept both 200 and 206 (partial content)
                    if response.status in [200, 206]:
                        data = await response.json()
                        products = self._parse_products(data)
                        
                        duration = time.time() - start_time
                        
                        return ScrapingResult(
                            vendor_id=self.vendor.id,
                            vendor_name=self.vendor.name,
                            success=True,
                            products=products,
                            duration=duration
                        )
                    else:
                        error_msg = f"HTTP {response.status}: {await response.text()}"
                        return self._error_result(error_msg, start_time)
        
        except Exception as e:
            return self._error_result(str(e), start_time)
    
    def _parse_products(self, data: List[dict]) -> List[Product]:
        """Parse products from VTEX API response."""
        products = []
        
        for item in data:
            try:
                # Extract basic product info
                product_name = item.get("productName", "").strip()
                if not product_name:
                    continue
                
                # Get price from first available SKU
                price = 0.0
                availability = "unknown"
                
                items = item.get("items", [])
                if items:
                    first_item = items[0]
                    sellers = first_item.get("sellers", [])
                    if sellers:
                        first_seller = sellers[0]
                        commercial_offer = first_seller.get("commertialOffer", {})
                        price = float(commercial_offer.get("Price", 0))
                        available_quantity = commercial_offer.get("AvailableQuantity", 0)
                        availability = "in_stock" if available_quantity > 0 else "out_of_stock"
                
                # Get product URL
                link_text = item.get("linkText", "")
                product_url = f"{self.vendor.base_url}/{link_text}/p" if link_text else ""
                
                # Get image URL
                image_url = None
                if items:
                    images = items[0].get("images", [])
                    if images:
                        image_url = images[0].get("imageUrl", "")
                
                # Extract brand
                brand = item.get("brand", "")
                
                # Create product
                product = Product(
                    name=product_name,
                    price=price,
                    currency=self.vendor.currency,
                    vendor_id=self.vendor.id,
                    vendor_name=self.vendor.name,
                    url=product_url,
                    image_url=image_url,
                    availability=availability,
                    brand=brand
                )
                
                products.append(product)
                
            except Exception as e:
                # Skip invalid products
                continue
        
        return products
    
    def _error_result(self, error_message: str, start_time: float) -> ScrapingResult:
        """Create error result."""
        duration = time.time() - start_time
        return ScrapingResult(
            vendor_id=self.vendor.id,
            vendor_name=self.vendor.name,
            success=False,
            products=[],
            error_message=error_message,
            duration=duration
        )

