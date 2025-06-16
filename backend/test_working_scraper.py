import asyncio
import aiohttp
import ssl
import sys
import os
from urllib.parse import quote

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scraping.base_scraper import ScrapedProduct
import logging

logger = logging.getLogger(__name__)


class WorkingCemacoScraper:
    """Working Cemaco scraper using proven configuration."""
    
    def __init__(self):
        self.vendor_id = "cemaco"
        self.session = None
    
    async def init_session(self):
        """Initialize HTTP session with working configuration."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(ssl=False, limit=10)
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
            connector=connector
        )
    
    async def close_session(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
    
    async def search(self, query: str, max_results: int = 5):
        """Search for products."""
        if not self.session:
            await self.init_session()
        
        try:
            # Direct API call
            api_url = f"https://www.cemaco.com/api/catalog_system/pub/products/search?ft={quote(query)}&_from=0&_to={max_results-1}"
            
            api_headers = {
                'Accept': 'application/json',
                'Referer': 'https://www.cemaco.com/',
                'Origin': 'https://www.cemaco.com'
            }
            
            async with self.session.get(api_url, headers=api_headers) as response:
                print(f"Status: {response.status}")
                
                if response.status in [200, 206]:
                    json_data = await response.json()
                    print(f"Found {len(json_data)} products")
                    
                    products = []
                    for item in json_data:
                        product = self._parse_api_product(item)
                        if product:
                            products.append(product)
                    
                    return products
                else:
                    print(f"Unexpected status: {response.status}")
                    return []
                    
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_api_product(self, item: dict):
        """Parse a product from VTEX API response."""
        try:
            # Extract basic information
            product_name = item.get('productName', '')
            if not product_name:
                return None
            
            # Get the first SKU for pricing
            skus = item.get('items', [])
            if not skus:
                return None
            
            sku = skus[0]
            sellers = sku.get('sellers', [])
            if not sellers:
                return None
            
            seller = sellers[0]
            price_info = seller.get('commertialOffer', {})
            
            price = price_info.get('Price')
            if price is None:
                return None
            
            # Build product URL
            link_text = item.get('linkText', '')
            product_url = f"https://www.cemaco.com/{link_text}/p" if link_text else None
            
            # Get image
            image_url = None
            images = item.get('items', [{}])[0].get('images', [])
            if images:
                image_url = images[0].get('imageUrl', '')
                if image_url and not image_url.startswith('http'):
                    image_url = f"https:{image_url}"
            
            # Extract brand
            brand = item.get('brand', '')
            
            return {
                'name': product_name,
                'price': float(price),
                'brand': brand,
                'url': product_url,
                'image': image_url
            }
            
        except Exception as e:
            print(f"Error parsing product: {str(e)}")
            return None


async def test_working_scraper():
    """Test the working scraper."""
    print("=== Testing Working Cemaco Scraper ===")
    
    scraper = WorkingCemacoScraper()
    
    try:
        products = await scraper.search("iPhone", 5)
        
        print(f"\nFound {len(products)} products:")
        for i, product in enumerate(products, 1):
            print(f"{i}. {product['name']}")
            print(f"   Price: Q{product['price']:.2f}")
            print(f"   Brand: {product['brand'] or 'N/A'}")
            print(f"   URL: {product['url'] or 'N/A'}")
            print()
            
    finally:
        await scraper.close_session()


if __name__ == "__main__":
    asyncio.run(test_working_scraper())

