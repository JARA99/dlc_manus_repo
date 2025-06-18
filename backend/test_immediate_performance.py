import asyncio
import sys
import os
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_immediate_search():
    """Test the immediate search architecture."""
    print("=== Testing IMMEDIATE Search Architecture ===")
    
    import aiohttp
    import websockets
    import json
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Start a search
        search_data = {
            "query": "iPhone",
            "options": {
                "max_results": 3,
                "vendors": ["cemaco"]
            }
        }
        
        print(f"🚀 Starting search at {time.time() - start_time:.3f}s")
        
        async with session.post(
            "http://localhost:8000/api/v1/search",
            json=search_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                search_id = result["search_id"]
                websocket_url = result["websocket_url"]
                
                print(f"✅ Search initiated at {time.time() - start_time:.3f}s: {search_id}")
                print(f"🔌 Connecting to WebSocket...")
                
                # Connect to WebSocket and measure timing
                try:
                    ws_start = time.time()
                    async with websockets.connect(websocket_url) as websocket:
                        print(f"✅ WebSocket connected at {time.time() - start_time:.3f}s (connection took {time.time() - ws_start:.3f}s)")
                        
                        # Listen for updates with precise timing
                        message_count = 0
                        first_product_time = None
                        
                        while True:
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                                data = json.loads(message)
                                message_count += 1
                                current_time = time.time() - start_time
                                
                                print(f"📨 [{current_time:.3f}s] {data['type']}")
                                
                                if data['type'] == 'search_started':
                                    print(f"   🔍 Searching {data['vendors_count']} vendors")
                                
                                elif data['type'] == 'vendor_started':
                                    print(f"   🏪 Started: {data['vendor_name']}")
                                
                                elif data['type'] == 'product_found':
                                    if first_product_time is None:
                                        first_product_time = current_time
                                        print(f"   ⚡ FIRST PRODUCT at {current_time:.3f}s!")
                                    
                                    product = data['product']
                                    print(f"   📦 {product['name']} - Q{product['price']:.2f}")
                                
                                elif data['type'] == 'vendor_completed':
                                    print(f"   ✅ Completed: {data['vendor_id']} ({data['products_found']} products in {data['duration']:.2f}s)")
                                
                                elif data['type'] == 'search_completed':
                                    total_time = current_time
                                    print(f"🎉 SEARCH COMPLETED at {total_time:.3f}s!")
                                    print(f"   📊 Total results: {data['total_results']}")
                                    print(f"   ⚡ First product: {first_product_time:.3f}s")
                                    print(f"   📈 Messages received: {message_count}")
                                    break
                                
                                elif data['type'] == 'error':
                                    print(f"❌ Error: {data['error']}")
                                    break
                                    
                            except asyncio.TimeoutError:
                                print(f"⏰ WebSocket timeout at {time.time() - start_time:.3f}s")
                                break
                        
                except Exception as e:
                    print(f"❌ WebSocket error: {str(e)}")
                
            else:
                print(f"❌ Failed to initiate search: {response.status}")


async def test_comparison_old_vs_new():
    """Compare old vs new architecture timing."""
    print("\n=== PERFORMANCE COMPARISON ===")
    
    # Test multiple searches to get average
    queries = ["iPhone", "Samsung", "laptop"]
    
    for query in queries:
        print(f"\n🔍 Testing query: '{query}'")
        
        import aiohttp
        import websockets
        import json
        
        async with aiohttp.ClientSession() as session:
            search_data = {
                "query": query,
                "options": {
                    "max_results": 2,
                    "vendors": ["cemaco"]
                }
            }
            
            start_time = time.time()
            
            async with session.post(
                "http://localhost:8000/api/v1/search",
                json=search_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    search_id = result["search_id"]
                    websocket_url = result["websocket_url"]
                    
                    try:
                        async with websockets.connect(websocket_url) as websocket:
                            first_message_time = None
                            first_product_time = None
                            completion_time = None
                            
                            while True:
                                try:
                                    message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                                    data = json.loads(message)
                                    current_time = time.time() - start_time
                                    
                                    if first_message_time is None:
                                        first_message_time = current_time
                                    
                                    if data['type'] == 'product_found' and first_product_time is None:
                                        first_product_time = current_time
                                    
                                    if data['type'] == 'search_completed':
                                        completion_time = current_time
                                        break
                                        
                                except asyncio.TimeoutError:
                                    break
                            
                            print(f"   ⚡ First message: {first_message_time:.3f}s")
                            print(f"   📦 First product: {first_product_time:.3f}s" if first_product_time else "   📦 No products found")
                            print(f"   🏁 Completion: {completion_time:.3f}s" if completion_time else "   🏁 Did not complete")
                            
                    except Exception as e:
                        print(f"   ❌ Error: {str(e)}")


async def main():
    """Run all tests."""
    try:
        await test_immediate_search()
        await test_comparison_old_vs_new()
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())

