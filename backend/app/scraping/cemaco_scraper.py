from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import logging
import re
from app.scraping.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class CemacoScraper(BaseScraper):
    """Scraper for Cemaco (cemaco.com) - VTEX platform."""
    
    async def _search_products(self, query: str, max_results: int) -> List[ScrapedProduct]:
        """Search for products on Cemaco website."""
        products = []
        
        try:
            # Skip the main page request and go directly to API
            # VTEX API endpoint for Cemaco
            api_url = f"https://www.cemaco.com/api/catalog_system/pub/products/search?ft={quote(query)}&_from=0&_to={max_results-1}"
            
            # Use simpler headers for API request
            api_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'es-GT,es;q=0.9,en;q=0.8',
                'Referer': 'https://www.cemaco.com/',
                'Origin': 'https://www.cemaco.com'
            }
            
            try:
                api_response = await self.make_request(api_url, headers=api_headers)
                
                if api_response.status in [200, 206]:  # Accept partial content responses
                    # Try to parse JSON response
                    try:
                        json_data = await api_response.json()
                        logger.info(f"Found {len(json_data)} products via API on Cemaco")
                        
                        for item in json_data[:max_results]:
                            product = self._parse_api_product(item)
                            if product:
                                products.append(product)
                        
                        return products
                    except Exception as e:
                        logger.warning(f"Failed to parse API response: {str(e)}")
                        
            except Exception as e:
                logger.warning(f"API request failed: {str(e)}")
                raise  # Re-raise the exception since API is our primary method
                    
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
        """Parse a single product element from Cemaco HTML."""
        try:
            # Extract product name from VTEX structure
            name_element = (
                element.find('span', class_=lambda x: x and 'vtex-product-summary' in x and 'productBrand' in x) or
                element.find('a', class_=lambda x: x and 'vtex-product-summary' in x) or
                element.find('h3') or
                element.find('h2')
            )
            
            if not name_element:
                return None
            
            name = self.clean_text(name_element.get_text())
            if not name:
                return None
            
            # Extract price from VTEX structure
            price_element = (
                element.find('span', class_=lambda x: x and 'vtex-product-price' in x and 'sellingPriceValue' in x) or
                element.find('span', class_=lambda x: x and 'price' in str(x).lower()) or
                element.find('div', class_=lambda x: x and 'price' in str(x).lower())
            )
            
            if not price_element:
                return None
            
            price_text = price_element.get_text()
            price = self.extract_price(price_text)
            
            if not price:
                return None
            
            # Extract product URL
            link_element = element.find('a', href=True)
            product_url = None
            if link_element:
                href = link_element['href']
                if href.startswith('/'):
                    product_url = urljoin(base_url, href)
                elif href.startswith('http'):
                    product_url = href
            
            # Extract image URL
            img_element = element.find('img')
            image_url = None
            if img_element:
                image_url = img_element.get('src') or img_element.get('data-src')
                if image_url and not image_url.startswith('http'):
                    if image_url.startswith('//'):
                        image_url = f"https:{image_url}"
                    else:
                        image_url = urljoin(base_url, image_url)
            
            # Extract brand and model
            brand, model = self.extract_brand_model(name)
            
            # Default availability
            availability = "unknown"
            
            return ScrapedProduct(
                name=name,
                price=price,
                vendor_id=self.vendor_id,
                vendor_url=product_url or f"https://www.cemaco.com/search?q={quote(name)}",
                currency="GTQ",
                image_url=image_url,
                availability=availability,
                brand=brand,
                model=model
            )
            
        except Exception as e:
            logger.error(f"Error parsing Cemaco product element: {str(e)}")
            return None

