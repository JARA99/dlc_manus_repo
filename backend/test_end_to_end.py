import asyncio
import websockets
import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_websocket_integration():
    """Test WebSocket integration for real-time search updates."""
    print("=== Testing WebSocket Integration ===")
    
    # First, initiate a search
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        # Start a search
        search_data = {
            "query": "Samsung",
            "options": {
                "max_results": 5,
                "vendors": ["cemaco"]
            }
        }
        
        async with session.post(
            "http://localhost:8001/api/v1/search",
            json=search_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                search_id = result["search_id"]
                websocket_url = result["websocket_url"].replace("localhost:8000", "localhost:8001")
                
                print(f"Search initiated: {search_id}")
                print(f"WebSocket URL: {websocket_url}")
                
                # Connect to WebSocket for real-time updates
                try:
                    async with websockets.connect(websocket_url) as websocket:
                        print("Connected to WebSocket")
                        
                        # Listen for updates
                        timeout_count = 0
                        max_timeout = 30  # 30 seconds timeout
                        
                        while timeout_count < max_timeout:
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                                data = json.loads(message)
                                
                                print(f"Received update: {data['type']}")
                                
                                if data['type'] == 'search_complete':
                                    print(f"Search completed! Found {data['total_results']} products")
                                    break
                                elif data['type'] == 'vendor_complete':
                                    print(f"Vendor {data['vendor_id']} completed: {data['product_count']} products")
                                elif data['type'] == 'product_found':
                                    print(f"Product found: {data['product']['name']} - Q{data['product']['price']}")
                                elif data['type'] == 'error':
                                    print(f"Error: {data['message']}")
                                    break
                                    
                            except asyncio.TimeoutError:
                                timeout_count += 1
                                if timeout_count % 5 == 0:
                                    print(f"Waiting for updates... ({timeout_count}s)")
                        
                        if timeout_count >= max_timeout:
                            print("Timeout reached, checking final results...")
                            
                except Exception as e:
                    print(f"WebSocket connection failed: {str(e)}")
                    print("Checking results via REST API...")
                
                # Get final results via REST API
                await asyncio.sleep(2)
                async with session.get(f"http://localhost:8001/api/v1/search/{search_id}/results") as response:
                    if response.status == 200:
                        results = await response.json()
                        print(f"\nFinal Results:")
                        print(f"Status: {results['status']}")
                        print(f"Total Results: {results['total_results']}")
                        print(f"Search Time: {results['search_time']:.2f}ms")
                        
                        if results['results']:
                            print("\nProducts found:")
                            for i, product in enumerate(results['results'], 1):
                                print(f"{i}. {product['name']}")
                                print(f"   Price: Q{product['price']:.2f}")
                                print(f"   Brand: {product['brand'] or 'N/A'}")
                                print(f"   Availability: {product['availability']}")
                                print(f"   URL: {product['url']}")
                                print()
                        else:
                            print("No products found")
                    else:
                        print(f"Failed to get results: {response.status}")
            else:
                print(f"Failed to initiate search: {response.status}")


async def test_multiple_vendor_search():
    """Test search across multiple vendors (when available)."""
    print("\n=== Testing Multiple Vendor Search ===")
    
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        # Test with all available vendors
        search_data = {
            "query": "iPhone",
            "options": {
                "max_results": 3
                # No vendor filter - should search all available vendors
            }
        }
        
        async with session.post(
            "http://localhost:8001/api/v1/search",
            json=search_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                search_id = result["search_id"]
                
                print(f"Multi-vendor search initiated: {search_id}")
                
                # Wait for completion
                await asyncio.sleep(15)
                
                # Get results
                async with session.get(f"http://localhost:8001/api/v1/search/{search_id}/results") as response:
                    if response.status == 200:
                        results = await response.json()
                        print(f"Status: {results['status']}")
                        print(f"Total Results: {results['total_results']}")
                        
                        # Group results by vendor
                        vendor_results = {}
                        for product in results.get('results', []):
                            vendor = product['vendor_id']
                            if vendor not in vendor_results:
                                vendor_results[vendor] = []
                            vendor_results[vendor].append(product)
                        
                        print(f"\nResults by vendor:")
                        for vendor, products in vendor_results.items():
                            print(f"\n{vendor.upper()} ({len(products)} products):")
                            for product in products:
                                print(f"  - {product['name']} - Q{product['price']:.2f}")
                    else:
                        print(f"Failed to get results: {response.status}")
            else:
                print(f"Failed to initiate search: {response.status}")


async def main():
    """Main test function."""
    print("Starting end-to-end integration tests...")
    
    try:
        await test_websocket_integration()
        await test_multiple_vendor_search()
        print("\n✅ End-to-end integration tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

