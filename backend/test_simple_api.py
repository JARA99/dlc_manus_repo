"""
Simple test script for the DondeLoCompro.gt API
"""

import asyncio
import aiohttp
import json
import time


async def test_api():
    """Test the simplified API."""
    print("🧪 Testing DondeLoCompro.gt Simplified API")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("1. Testing health endpoint...")
        async with session.get(f"{base_url}/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"   ✅ Health: {data['status']}")
                print(f"   📊 Scrapers: {', '.join(data['scrapers'])}")
            else:
                print(f"   ❌ Health check failed: {response.status}")
                return
        
        # Start search
        print("\n2. Starting search...")
        search_data = {"query": "iPhone", "max_results": 3}
        
        async with session.post(
            f"{base_url}/search",
            json=search_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                search_id = result["search_id"]
                sse_url = result["sse_url"]
                print(f"   ✅ Search started: {search_id}")
                print(f"   📡 SSE URL: {sse_url}")
            else:
                print(f"   ❌ Search failed: {response.status}")
                return
        
        # Connect to SSE
        print("\n3. Connecting to Server-Sent Events...")
        start_time = time.time()
        event_count = 0
        products_found = 0
        
        try:
            async with session.get(sse_url) as response:
                if response.status == 200:
                    print("   ✅ SSE connected, listening for events...")
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        if line.startswith('event: '):
                            event_type = line[7:]
                        elif line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                event_count += 1
                                elapsed = time.time() - start_time
                                
                                print(f"   📨 [{elapsed:.2f}s] {event_type}")
                                
                                if event_type == "connected":
                                    print(f"      🔗 {data['message']}")
                                
                                elif event_type == "started":
                                    print(f"      🔍 Query: {data['query']}")
                                    print(f"      🏪 Vendors: {', '.join(data['vendors'])}")
                                
                                elif event_type == "vendor_started":
                                    print(f"      🏪 Started: {data['vendor_name']}")
                                
                                elif event_type == "product_found":
                                    products_found += 1
                                    product = data['product']
                                    print(f"      📦 {product['name']} - Q{product['price']:.2f}")
                                    print(f"          🏪 {product['vendor_name']}")
                                    print(f"          🔗 {product['url'][:60]}...")
                                
                                elif event_type == "vendor_completed":
                                    print(f"      ✅ {data['vendor_id']}: {data['products_found']} products in {data['duration']:.2f}s")
                                
                                elif event_type == "vendor_error":
                                    print(f"      ❌ {data['vendor_id']}: {data['error']}")
                                
                                elif event_type == "completed":
                                    total_results = data['total_results']
                                    print(f"      🎉 Search completed!")
                                    print(f"      📊 Total results: {total_results}")
                                    break
                                
                                elif event_type == "error":
                                    print(f"      ❌ Error: {data['error']}")
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                else:
                    print(f"   ❌ SSE connection failed: {response.status}")
        
        except asyncio.TimeoutError:
            print("   ⏰ SSE connection timed out")
        except Exception as e:
            print(f"   ❌ SSE error: {str(e)}")
        
        # Summary
        total_time = time.time() - start_time
        print(f"\n📊 Test Summary:")
        print(f"   ⏱️  Total time: {total_time:.2f}s")
        print(f"   📨 Events received: {event_count}")
        print(f"   📦 Products found: {products_found}")
        print(f"   ⚡ Performance: {'Excellent' if total_time < 3 else 'Good' if total_time < 10 else 'Needs improvement'}")


async def main():
    """Main test function."""
    try:
        await test_api()
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")


if __name__ == "__main__":
    print("🚀 Make sure the API is running: python -m dlc_api.main")
    print("⏳ Starting test in 3 seconds...")
    time.sleep(3)
    asyncio.run(main())

