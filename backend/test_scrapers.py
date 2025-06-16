import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scraping import scraping_engine
from app.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_scraper(vendor_id: str, query: str):
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
        result = await scraping_engine.search_vendor(vendor_id, query, config, max_results=5)
        
        print(f"Success: {result.success}")
        print(f"Duration: {result.duration:.2f}s")
        print(f"Products found: {len(result.products)}")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        for i, product in enumerate(result.products[:3], 1):
            print(f"\nProduct {i}:")
            print(f"  Name: {product.name}")
            print(f"  Price: Q{product.price:.2f}")
            print(f"  Brand: {product.brand or 'N/A'}")
            print(f"  Availability: {product.availability}")
            print(f"  URL: {product.vendor_url}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")


async def test_all_scrapers():
    """Test all available scrapers."""
    test_queries = [
        "iPhone 15",
        "Samsung Galaxy",
        "laptop HP",
        "refrigeradora LG"
    ]
    
    vendors = scraping_engine.get_supported_vendors()
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing query: '{query}'")
        print(f"{'='*60}")
        
        for vendor_id in vendors:
            await test_scraper(vendor_id, query)
            await asyncio.sleep(2)  # Delay between vendors


async def test_search_all():
    """Test searching all vendors simultaneously."""
    query = "iPhone 15 Pro"
    
    print(f"\n=== Testing Multi-Vendor Search ===")
    print(f"Query: {query}")
    
    # Mock vendor configurations
    vendor_configs = {
        'cemaco': {'delay': 1.0},
        'max': {'delay': 1.5},
        'elektra': {'delay': 2.0},
        'walmart': {'delay': 1.0}
    }
    
    try:
        results = await scraping_engine.search_all_vendors(
            query=query,
            vendor_configs=vendor_configs,
            max_results_per_vendor=3
        )
        
        print(f"\nResults from {len(results)} vendors:")
        
        total_products = 0
        for result in results:
            print(f"\n{result.vendor_id.upper()}:")
            print(f"  Success: {result.success}")
            print(f"  Products: {len(result.products)}")
            print(f"  Duration: {result.duration:.2f}s")
            
            if result.error_message:
                print(f"  Error: {result.error_message}")
            
            total_products += len(result.products)
            
            # Show first product from each vendor
            if result.products:
                product = result.products[0]
                print(f"  Sample: {product.name} - Q{product.price:.2f}")
        
        print(f"\nTotal products found: {total_products}")
        
    except Exception as e:
        print(f"Multi-vendor search failed: {str(e)}")


async def main():
    """Main test function."""
    print("Starting scraper tests...")
    
    # Test individual scrapers
    await test_scraper("cemaco", "iPhone")
    await asyncio.sleep(3)
    
    await test_scraper("max", "Samsung")
    await asyncio.sleep(3)
    
    # Test multi-vendor search
    await test_search_all()
    
    print("\nScraper tests completed!")


if __name__ == "__main__":
    asyncio.run(main())

