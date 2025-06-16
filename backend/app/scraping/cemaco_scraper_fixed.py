from typing import List, Optional
from urllib.parse import quote
import logging
import aiohttp
from app.scraping.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class CemacoScraperFixed(BaseScraper):
    """Fixed Cemaco scraper using proven working configuration."""
    
    async def init_session(self):
        """Initialize HTTP session with working configuration for Cemaco."""
        # Use the exact configuration that works
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
    
    async def _search_products(self, query: str, max_results: int) -> List[ScrapedProduct]:
        """Search for products on Cemaco website using VTEX API."""
        products = []
        
        try:
            # Direct API call to VTEX endpoint
            api_url = f"https://www.cemaco.com/api/catalog_system/pub/products/search?ft={quote(query)}&_from=0&_to={max_results-1}"
            
            # API-specific headers
            api_headers = {
                'Accept': 'application/json',
                'Referer': 'https://www.cemaco.com/',
                'Origin': 'https://www.cemaco.com'
            }
            
            # Make the API request
            async with self.session.get(api_url, headers=api_headers) as response:
                logger.info(f"API response status: {response.status}")
                
                if response.status in [200, 206]:  # Accept partial content
                    json_data = await response.json()
                    logger.info(f"Found {len(json_data)} products via API on Cemaco")
                    
                    for item in json_data[:max_results]:
                        product = self._parse_api_product(item)
                        if product:
                            products.append(product)
                else:
                    logger.warning(f"Unexpected API status: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error searching Cemaco: {str(e)}")
            raise
        
        return products
    
    def _parse_api_product(self, item: dict) -> Optional[ScrapedProduct]:
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
            
            # Extract availability
            availability = "unknown"
            available_quantity = price_info.get('AvailableQuantity', 0)
            if available_quantity > 0:
                availability = "in_stock"
            elif available_quantity == 0:
                availability = "out_of_stock"
            
            # Extract model from name
            brand_extracted, model = self.extract_brand_model(product_name)
            if not brand and brand_extracted:
                brand = brand_extracted
            
            # Get original price if on sale
            original_price = price_info.get('ListPrice')
            discount_percentage = None
            if original_price and original_price > price:
                discount_percentage = round(((original_price - price) / original_price) * 100, 2)
            
            return ScrapedProduct(
                name=product_name,
                price=float(price),
                vendor_id=self.vendor_id,
                vendor_url=product_url or f"https://www.cemaco.com/search?q={quote(product_name)}",
                currency="GTQ",
                image_url=image_url,
                availability=availability,
                brand=brand,
                model=model,
                original_price=float(original_price) if original_price else None,
                discount_percentage=discount_percentage
            )
            
        except Exception as e:
            logger.error(f"Error parsing Cemaco API product: {str(e)}")
            return None


    
    def _parse_product_element(self, element, base_url: str) -> Optional[ScrapedProduct]:
        """Parse a single product element from HTML (not used for API-based scraping)."""
        # This method is required by the abstract base class but not used for VTEX API
        return None

