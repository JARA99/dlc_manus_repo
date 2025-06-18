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
            "http://localhost:8000/api/v1/search",
            json=search_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                search_id = result["search_id"]
                websocket_url = result["websocket_url"]
                
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
                                # Wait for message with timeout
                                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                                data = json.loads(message)
                                
                                print(f"Received: {data['type']}")
                                
                                if data['type'] == 'product_found':
                                    product = data['product']
                                    print(f"  Product: {product['name']}")
                                    print(f"  Price: Q{product['price']:.2f}")
                                    print(f"  Vendor: {product['vendor_name']}")
                                    print()
                                
                                elif data['type'] == 'search_completed':
                                    print(f"Search completed! Total results: {data['total_results']}")
                                    print(f"Duration: {data['total_duration']:.2f}s")
                                    break
                                
                                elif data['type'] == 'error':
                                    print(f"Error: {data['error']}")
                                    break
                                    
                            except asyncio.TimeoutError:
                                timeout_count += 1
                                print(".", end="", flush=True)
                                continue
                        
                        if timeout_count >= max_timeout:
                            print("\nWebSocket timeout reached")
                            
                except Exception as e:
                    print(f"WebSocket error: {str(e)}")
                
                # Get final results via REST API
                await asyncio.sleep(2)
                async with session.get(f"http://localhost:8000/api/v1/search/{search_id}/results") as response:
                    if response.status == 200:
                        results = await response.json()
                        print(f"\nFinal Results:")
                        print(f"Status: {results['status']}")
                        print(f"Total Results: {results['total_results']}")
                        print(f"Search Time: {results['search_time']:.2f}s")
                        
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
                print(f"Failed to initiate search: {response.status}")


async def test_multi_vendor_search():
    """Test search across multiple vendors."""
    print("\n=== Testing Multi-Vendor Search ===")
    
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        # Start a multi-vendor search
        search_data = {
            "query": "iPhone",
            "options": {
                "max_results": 3
            }
        }
        
        async with session.post(
            "http://localhost:8000/api/v1/search",
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
                async with session.get(f"http://localhost:8000/api/v1/search/{search_id}/results") as response:
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
                        for vendor_id, products in vendor_results.items():
                            print(f"\n{vendor_id.upper()}: {len(products)} products")
                            for product in products:
                                print(f"  - {product['name']} - Q{product['price']:.2f}")
                    else:
                        print(f"Failed to get results: {response.status}")
            else:
                print(f"Failed to initiate search: {response.status}")


async def main():
    """Run all tests."""
    try:
        await test_websocket_integration()
        await test_multi_vendor_search()
    except Exception as e:
        print(f"Test failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())

