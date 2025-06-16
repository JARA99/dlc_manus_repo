import asyncio
import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
import websockets
from app.schemas.search import SearchRequest


async def test_search_api():
    """Test the search API with real request."""
    print("=== Testing Search API ===")
    
    # Test search initiation
    search_data = {
        "query": "iPhone 15",
        "filters": {
            "min_price": 1000,
            "max_price": 10000,
            "vendors": ["cemaco", "max"]
        },
        "options": {
            "max_results": 5,
            "timeout": 30
        }
    }
    
    async with aiohttp.ClientSession() as session:
        # Initiate search
        async with session.post(
            "http://localhost:8000/api/v1/search",
            json=search_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                search_id = result["search_id"]
                websocket_url = result["websocket_url"]
                
                print(f"Search initiated: {search_id}")
                print(f"WebSocket URL: {websocket_url}")
                
                # Test WebSocket connection
                await test_websocket(search_id)
                
                # Wait a bit for search to progress
                await asyncio.sleep(10)
                
                # Get final results
                async with session.get(
                    f"http://localhost:8000/api/v1/search/{search_id}/results"
                ) as results_response:
                    if results_response.status == 200:
                        results = await results_response.json()
                        print(f"\nFinal Results:")
                        print(f"Status: {results['status']}")
                        print(f"Total Results: {results['total_results']}")
                        print(f"Search Time: {results['search_time']:.2f}s")
                        
                        if results['results']:
                            print(f"\nFirst few products:")
                            for i, product in enumerate(results['results'][:3], 1):
                                print(f"{i}. {product['name']} - Q{product['price']:.2f} ({product['vendor_name']})")
                    else:
                        print(f"Error getting results: {results_response.status}")
            else:
                print(f"Error initiating search: {response.status}")
                error = await response.text()
                print(f"Error details: {error}")


async def test_websocket(search_id: str):
    """Test WebSocket connection for real-time updates."""
    print(f"\n=== Testing WebSocket for {search_id} ===")
    
    websocket_url = f"ws://localhost:8000/ws/search/{search_id}"
    
    try:
        async with websockets.connect(websocket_url) as websocket:
            print("WebSocket connected successfully")
            
            # Listen for messages for a short time
            timeout = 8  # seconds
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    msg_type = data.get("type")
                    if msg_type == "search_started":
                        print(f"Search started with {data['vendors_count']} vendors")
                    elif msg_type == "vendor_started":
                        print(f"Started scraping {data['vendor_name']}")
                    elif msg_type == "product_found":
                        product = data['product']
                        print(f"Found: {product['name']} - Q{product['price']:.2f}")
                    elif msg_type == "vendor_completed":
                        print(f"Completed {data['vendor']} - {data['results_count']} products in {data['duration']:.2f}s")
                    elif msg_type == "search_completed":
                        print(f"Search completed! Total: {data['total_results']} products in {data['total_duration']:.2f}s")
                        break
                    elif msg_type == "error":
                        print(f"Error from {data.get('vendor', 'unknown')}: {data['error']}")
                    
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("WebSocket connection closed")
                    break
                    
    except Exception as e:
        print(f"WebSocket error: {str(e)}")


async def main():
    """Main test function."""
    print("Starting API tests...")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    
    await test_search_api()
    
    print("\nAPI tests completed!")


if __name__ == "__main__":
    asyncio.run(main())

