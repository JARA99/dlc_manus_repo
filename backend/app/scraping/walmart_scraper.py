from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import logging
import re
from app.scraping.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class WalmartScraper(BaseScraper):
    """Scraper for Walmart Guatemala (walmart.com.gt)."""
    
    async def _search_products(self, query: str, max_results: int) -> List[ScrapedProduct]:
        """Search for products on Walmart Guatemala website."""
        products = []
        
        try:
            # Build search URL
            search_url = f"https://walmart.com.gt/search?q={quote(query)}"
            
            # Make request with additional headers for Walmart
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-GT,es;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            response = await self.make_request(search_url, headers=headers)
            html = await response.text()
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find product containers (Walmart uses specific data attributes)
            product_elements = soup.find_all('div', attrs={'data-testid': 'product-tile'})
            
            if not product_elements:
                # Try alternative selectors
                product_elements = soup.find_all('article', class_='product-tile')
                
            if not product_elements:
                # Try generic selectors
                product_elements = soup.find_all('div', class_=['product', 'item', 'product-item'])
            
            logger.info(f"Found {len(product_elements)} product elements on Walmart")
            
            for element in product_elements[:max_results]:
                product = self._parse_product_element(element, "https://walmart.com.gt")
                if product:
                    products.append(product)
                    
        except Exception as e:
            logger.error(f"Error searching Walmart: {str(e)}")
            raise
        
        return products
    
    def _parse_product_element(self, element, base_url: str) -> Optional[ScrapedProduct]:
        """Parse a single product element from Walmart."""
        try:
            # Extract product name
            name_element = (
                element.find('span', attrs={'data-testid': 'product-title'}) or
                element.find('h3', class_='product-title') or
                element.find('a', class_='product-name') or
                element.find('h4') or
                element.find('h3')
            )
            
            if not name_element:
                return None
            
            name = self.clean_text(name_element.get_text())
            if not name:
                return None
            
            # Extract price
            price_element = (
                element.find('span', attrs={'data-testid': 'price-current'}) or
                element.find('span', class_='price-current') or
                element.find('div', class_='price-current') or
                element.find('span', class_='price')
            )
            
            if not price_element:
                return None
            
            price_text = price_element.get_text()
            price = self.extract_price(price_text)
            
            if not price:
                return None
            
            # Extract product URL
            link_element = (
                element.find('a', href=True) or
                name_element.find_parent('a', href=True) if name_element else None
            )
            
            if not link_element:
                return None
            
            product_url = urljoin(base_url, link_element['href'])
            
            # Extract image URL
            img_element = element.find('img')
            image_url = None
            if img_element:
                image_url = (
                    img_element.get('src') or 
                    img_element.get('data-src') or 
                    img_element.get('data-lazy-src')
                )
                if image_url:
                    image_url = urljoin(base_url, image_url)
            
            # Extract availability
            availability = "unknown"
            stock_element = element.find(['span', 'div'], attrs={'data-testid': 'availability'})
            if not stock_element:
                stock_element = element.find(['span', 'div'], class_=['stock', 'availability', 'inventory-status'])
            
            if stock_element:
                stock_text = stock_element.get_text().lower()
                if 'disponible' in stock_text or 'en stock' in stock_text or 'available' in stock_text:
                    availability = "in_stock"
                elif 'agotado' in stock_text or 'out of stock' in stock_text or 'no disponible' in stock_text:
                    availability = "out_of_stock"
                elif 'limitado' in stock_text or 'limited' in stock_text:
                    availability = "limited"
            
            # Extract brand and model
            brand, model = self.extract_brand_model(name)
            
            # Check for original price (sale items)
            original_price = None
            original_price_element = (
                element.find('span', attrs={'data-testid': 'price-was'}) or
                element.find('span', class_='price-was') or
                element.find('del', class_='price-original')
            )
            if original_price_element:
                original_price = self.extract_price(original_price_element.get_text())
            
            # Calculate discount if applicable
            discount_percentage = None
            discount_element = element.find(['span', 'div'], class_=['discount', 'savings', 'percent-off'])
            if discount_element:
                discount_text = discount_element.get_text()
                discount_match = re.search(r'(\d+)%', discount_text)
                if discount_match:
                    discount_percentage = float(discount_match.group(1))
            elif original_price and price and original_price > price:
                discount_percentage = round(((original_price - price) / original_price) * 100, 2)
            
            # Extract delivery information
            delivery_element = element.find(['span', 'div'], class_=['shipping', 'delivery', 'fulfillment'])
            delivery_time = None
            delivery_cost = None
            if delivery_element:
                delivery_text = delivery_element.get_text().lower()
                if 'gratis' in delivery_text or 'free' in delivery_text:
                    delivery_cost = 0.0
                    delivery_time = "Envío gratis"
                elif 'días' in delivery_text or 'days' in delivery_text:
                    delivery_time = self.clean_text(delivery_element.get_text())
            
            # Extract rating if available
            rating_element = element.find(['span', 'div'], class_=['rating', 'stars', 'review-stars'])
            rating = None
            if rating_element:
                rating_text = rating_element.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Build specifications with rating if available
            specifications = {}
            if rating:
                specifications['rating'] = rating
            
            return ScrapedProduct(
                name=name,
                price=price,
                vendor_id=self.vendor_id,
                vendor_url=product_url,
                currency="GTQ",
                image_url=image_url,
                availability=availability,
                brand=brand,
                model=model,
                original_price=original_price,
                discount_percentage=discount_percentage,
                delivery_time=delivery_time,
                delivery_cost=delivery_cost,
                specifications=specifications if specifications else None
            )
            
        except Exception as e:
            logger.error(f"Error parsing Walmart product element: {str(e)}")
            return None

