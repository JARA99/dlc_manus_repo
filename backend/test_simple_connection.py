import asyncio
import aiohttp
import ssl


async def test_simple_connection():
    """Test simple connection to Cemaco API."""
    print("=== Testing Simple Connection to Cemaco ===")
    
    # Create SSL context that's more permissive
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Test different connection approaches
    urls_to_test = [
        "https://www.cemaco.com/",
        "https://www.cemaco.com/api/catalog_system/pub/products/search?ft=iPhone&_from=0&_to=4"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Test with different configurations
    configs = [
        {"name": "Default", "ssl": None, "connector": None},
        {"name": "No SSL Verify", "ssl": False, "connector": None},
        {"name": "Custom SSL Context", "ssl": ssl_context, "connector": None},
        {"name": "Custom Connector", "ssl": False, "connector": aiohttp.TCPConnector(ssl=False, limit=10)},
    ]
    
    for config in configs:
        print(f"\n--- Testing with {config['name']} ---")
        
        try:
            connector = config["connector"]
            if not connector:
                connector = aiohttp.TCPConnector(ssl=config["ssl"], limit=10)
            
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            ) as session:
                
                for url in urls_to_test:
                    print(f"Testing: {url}")
                    try:
                        async with session.get(url) as response:
                            print(f"  Status: {response.status}")
                            print(f"  Headers: {dict(response.headers)}")
                            
                            if response.status == 200:
                                content = await response.text()
                                print(f"  Content length: {len(content)}")
                                
                                if "iPhone" in content:
                                    print("  ✓ Found iPhone in content!")
                                else:
                                    print("  ✗ No iPhone found in content")
                                    
                                # If it's JSON, try to parse it
                                if url.endswith("_to=4"):
                                    try:
                                        json_data = await response.json()
                                        print(f"  ✓ JSON parsed successfully, {len(json_data)} items")
                                        if json_data:
                                            print(f"  First item: {json_data[0].get('productName', 'No name')}")
                                    except Exception as e:
                                        print(f"  ✗ JSON parse failed: {str(e)}")
                            
                    except Exception as e:
                        print(f"  ✗ Error: {str(e)}")
                    
                    await asyncio.sleep(1)  # Be respectful
                        
        except Exception as e:
            print(f"Session creation failed: {str(e)}")


async def main():
    await test_simple_connection()


if __name__ == "__main__":
    asyncio.run(main())

