import asyncio
import aiohttp
import ssl
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scraping.cemaco_scraper import CemacoScraper


async def test_direct_api_call():
    """Test direct API call using the same approach as the simple test."""
    print("=== Testing Direct API Call ===")
    
    # Use the exact same configuration that worked in the simple test
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'es-GT,es;q=0.9,en;q=0.8',
        'Referer': 'https://www.cemaco.com/',
        'Origin': 'https://www.cemaco.com'
    }
    
    connector = aiohttp.TCPConnector(ssl=False, limit=10)
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers=headers
    ) as session:
        
        url = "https://www.cemaco.com/api/catalog_system/pub/products/search?ft=iPhone&_from=0&_to=4"
        
        try:
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status in [200, 206]:
                    json_data = await response.json()
                    print(f"✓ JSON parsed successfully, {len(json_data)} items")
                    
                    # Parse using the same logic as the scraper
                    for item in json_data:
                        product_name = item.get('productName', '')
                        skus = item.get('items', [])
                        if skus:
                            sku = skus[0]
                            sellers = sku.get('sellers', [])
                            if sellers:
                                seller = sellers[0]
                                price_info = seller.get('commertialOffer', {})
                                price = price_info.get('Price')
                                
                                print(f"Product: {product_name}")
                                print(f"Price: Q{price}")
                                print(f"Brand: {item.get('brand', 'N/A')}")
                                print("---")
                else:
                    print(f"Unexpected status: {response.status}")
                    
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()


async def test_scraper_with_fixed_session():
    """Test scraper with manually fixed session configuration."""
    print("\n=== Testing Scraper with Fixed Session ===")
    
    # Create a custom scraper instance with working configuration
    config = {
        'delay': 1.0,
        'timeout': 30,
        'max_retries': 3
    }
    
    scraper = CemacoScraper("cemaco", config)
    
    # Override the session initialization to use working configuration
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
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
    
    scraper.session = aiohttp.ClientSession(
        timeout=timeout,
        headers=headers,
        connector=connector
    )
    
    try:
        result = await scraper.search("iPhone", max_results=5)
        
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
                print()
        else:
            print("No products found")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close_session()


async def main():
    await test_direct_api_call()
    await test_scraper_with_fixed_session()


if __name__ == "__main__":
    asyncio.run(main())

