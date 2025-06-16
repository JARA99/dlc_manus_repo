import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scraping.cemaco_scraper import CemacoScraper
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_cemaco_scraper():
    """Test the updated Cemaco scraper."""
    print("=== Testing Updated Cemaco Scraper ===")
    
    # Test queries that we know have results
    test_queries = [
        "iPhone",
        "Samsung",
        "laptop"
    ]
    
    config = {
        'delay': 2.0,  # Increased delay to be respectful
        'timeout': 30,
        'max_retries': 3
    }
    
    for query in test_queries:
        print(f"\n--- Testing query: '{query}' ---")
        
        try:
            async with CemacoScraper("cemaco", config) as scraper:
                result = await scraper.search(query, max_results=5)
                
                print(f"Success: {result.success}")
                print(f"Duration: {result.duration:.2f}s")
                print(f"Products found: {len(result.products)}")
                
                if result.error_message:
                    print(f"Error: {result.error_message}")
                
                if result.products:
                    print("\nProducts found:")
                    for i, product in enumerate(result.products, 1):
                        print(f"{i}. {product.name}")
                        print(f"   Price: Q{product.price:.2f}")
                        print(f"   Brand: {product.brand or 'N/A'}")
                        print(f"   URL: {product.vendor_url}")
                        print(f"   Image: {product.image_url or 'N/A'}")
                        print()
                else:
                    print("No products found")
                    
        except Exception as e:
            print(f"Test failed for '{query}': {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Wait between queries
        await asyncio.sleep(3)


async def main():
    """Main test function."""
    print("Starting Cemaco scraper tests...")
    await test_cemaco_scraper()
    print("\nCemaco scraper tests completed!")


if __name__ == "__main__":
    asyncio.run(main())

