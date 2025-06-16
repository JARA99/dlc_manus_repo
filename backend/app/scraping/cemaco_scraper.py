from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import logging
import re
from app.scraping.base_scraper import BaseScraper, ScrapedProduct

logger = logging.getLogger(__name__)


class CemacoScraper(BaseScraper):
    """Scraper for Cemaco (cemaco.com)."""
    
    async def _search_products(self, query: str, max_results: int) -> List[ScrapedProduct]:
        """Search for products on Cemaco website."""
        products = []
        
        try:
            # Build search URL
            search_url = f"https://cemaco.com/search?q={quote(query)}"
            
            # Make request
            response = await self.make_request(search_url)
            html = await response.text()
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find product containers
            product_elements = soup.find_all('div', class_=['product-item', 'product-tile', 'item'])
            
            if not product_elements:
                # Try alternative selectors
                product_elements = soup.find_all('article', class_='product')
                
            if not product_elements:
                # Try generic selectors
                product_elements = soup.find_all('div', attrs={'data-product-id': True})
            
            logger.info(f"Found {len(product_elements)} product elements on Cemaco")
            
            for element in product_elements[:max_results]:
                product = self._parse_product_element(element, "https://cemaco.com")
                if product:
                    products.append(product)
                    
        except Exception as e:
            logger.error(f"Error searching Cemaco: {str(e)}")
            raise
        
        return products
    
    def _parse_product_element(self, element, base_url: str) -> Optional[ScrapedProduct]:
        """Parse a single product element from Cemaco."""
        try:
            # Extract product name
            name_element = (
                element.find('h3', class_='product-name') or
                element.find('h2', class_='product-title') or
                element.find('a', class_='product-link') or
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
                element.find('span', class_='price') or
                element.find('div', class_='price') or
                element.find('span', class_='precio') or
                element.find('p', class_='price')
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
                image_url = img_element.get('src') or img_element.get('data-src')
                if image_url:
                    image_url = urljoin(base_url, image_url)
            
            # Extract availability
            availability = "unknown"
            stock_element = element.find(['span', 'div'], class_=['stock', 'availability', 'disponible'])
            if stock_element:
                stock_text = stock_element.get_text().lower()
                if 'disponible' in stock_text or 'stock' in stock_text:
                    availability = "in_stock"
                elif 'agotado' in stock_text or 'sin stock' in stock_text:
                    availability = "out_of_stock"
            
            # Extract brand and model
            brand, model = self.extract_brand_model(name)
            
            # Check for original price (sale items)
            original_price = None
            original_price_element = element.find(['span', 'div'], class_=['original-price', 'was-price', 'precio-anterior'])
            if original_price_element:
                original_price = self.extract_price(original_price_element.get_text())
            
            # Calculate discount if applicable
            discount_percentage = None
            if original_price and price and original_price > price:
                discount_percentage = round(((original_price - price) / original_price) * 100, 2)
            
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
                discount_percentage=discount_percentage
            )
            
        except Exception as e:
            logger.error(f"Error parsing Cemaco product element: {str(e)}")
            return None

