import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scraping.base_scraper import BaseScraper, ScrapedProduct, ScrapingResult
from app.scraping.cemaco_scraper import CemacoScraper
from app.scraping.max_scraper import MaxScraper
from app.scraping.elektra_scraper import ElektraScraper
from app.scraping.walmart_scraper import WalmartScraper
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_scraper(scraper_class, vendor_id: str, query: str):
    """Test a specific scraper."""
    print(f"\n=== Testing {vendor_id.upper()} Scraper ===")
    print(f"Query: {query}")
    
    # Mock vendor configuration
    config = {
        'delay': 1.0,
        'timeout': 30,
        'max_retries': 2
    }
    
    try:
        async with scraper_class(vendor_id, config) as scraper:
            result = await scraper.search(query, max_results=3)
            
            print(f"Success: {result.success}")
            print(f"Duration: {result.duration:.2f}s")
            print(f"Products found: {len(result.products)}")
            
            if result.error_message:
                print(f"Error: {result.error_message}")
            
            for i, product in enumerate(result.products, 1):
                print(f"\nProduct {i}:")
                print(f"  Name: {product.name}")
                print(f"  Price: Q{product.price:.2f}")
                print(f"  Brand: {product.brand or 'N/A'}")
                print(f"  Availability: {product.availability}")
                print(f"  URL: {product.vendor_url[:80]}...")
                
    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("Starting scraper tests...")
    
    # Test individual scrapers
    scrapers = [
        (CemacoScraper, "cemaco"),
        (MaxScraper, "max"),
        (ElektraScraper, "elektra"),
        (WalmartScraper, "walmart")
    ]
    
    test_queries = ["iPhone", "Samsung Galaxy", "laptop"]
    
    for scraper_class, vendor_id in scrapers:
        for query in test_queries[:1]:  # Test with first query only
            await test_scraper(scraper_class, vendor_id, query)
            await asyncio.sleep(2)  # Delay between tests
    
    print("\nScraper tests completed!")


if __name__ == "__main__":
    asyncio.run(main())

