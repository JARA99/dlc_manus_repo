"""
Test script for the new OOP-based DondeLoCompro.gt API
"""

import asyncio
import aiohttp
import json
import time


async def test_new_api():
    """Test the new API architecture."""
    
    print("🧪 Testing DondeLoCompro.gt API v2.0.0 (OOP Architecture)")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health endpoint
        print("1. Testing health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Health: {data['status']}")
                    print(f"   📊 Scrapers: {', '.join(data['scrapers'])}")
                    print(f"   🟢 Active: {', '.join(data.get('active_scrapers', []))}")
                else:
                    print(f"   ❌ Health check failed: {response.status}")
                    return
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return
        
        # Test 2: Start search
        print("2. Starting search...")
        search_data = {
            "query": "iPhone",
            "max_results": 10
        }
        
        try:
            async with session.post(f"{base_url}/search", json=search_data) as response:
                if response.status == 200:
                    search_response = await response.json()
                    search_id = search_response["search_id"]
                    sse_url = search_response["sse_url"]
                    print(f"   ✅ Search started: {search_id}")
                    print(f"   📡 SSE URL: {sse_url}")
                else:
                    print(f"   ❌ Search failed: {response.status}")
                    return
        except Exception as e:
            print(f"   ❌ Search error: {e}")
            return
        
        # Test 3: SSE Events
        print("3. Connecting to Server-Sent Events...")
        try:
            start_time = time.time()
            event_count = 0
            product_count = 0
            
            async with session.get(sse_url) as response:
                print("   ✅ SSE connected, listening for events...")
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('event:'):
                        event_type = line.split(':', 1)[1].strip()
                    elif line.startswith('data:'):
                        try:
                            data = json.loads(line.split(':', 1)[1].strip())
                            event_count += 1
                            elapsed = time.time() - start_time
                            
                            print(f"   📨 [{elapsed:.2f}s] {event_type}")
                            
                            if event_type == "connected":
                                print(f"      🔗 {data.get('message', 'Connected')}")
                            elif event_type == "started":
                                print(f"      🔍 Query: {data.get('query')}")
                                vendors = data.get('vendors', [])
                                if vendors:
                                    print(f"      🏪 Vendors: {', '.join(vendors)}")
                            elif event_type == "vendor_started":
                                print(f"      🏪 Started: {data.get('vendor_name')}")
                            elif event_type == "product_found":
                                product = data.get('product', {})
                                product_count += 1
                                print(f"      📦 {product.get('name', 'Unknown')} - Q{product.get('price', 0):.2f}")
                                print(f"          🏪 {product.get('vendor_name')}")
                                if product.get('url'):
                                    url = product['url']
                                    if len(url) > 60:
                                        url = url[:57] + "..."
                                    print(f"          🔗 {url}")
                            elif event_type == "vendor_completed":
                                vendor_id = data.get('vendor_id')
                                products_found = data.get('products_found', 0)
                                duration = data.get('duration', 0)
                                print(f"      ✅ {vendor_id}: {products_found} products in {duration:.2f}s")
                            elif event_type == "completed":
                                total_results = data.get('total_results', 0)
                                total_duration = data.get('duration', 0)
                                print(f"      🎉 Search completed!")
                                print(f"      📊 Total results: {total_results}")
                                print(f"      ⏱️  Total duration: {total_duration:.2f}s")
                                break
                            elif event_type == "error":
                                print(f"      ❌ Error: {data.get('error')}")
                                break
                                
                        except json.JSONDecodeError:
                            pass
                        except Exception as e:
                            print(f"      ⚠️  Event processing error: {e}")
                            
        except Exception as e:
            print(f"   ❌ SSE error: {e}")
            return
        
        # Test 4: Get final results
        print("4. Getting final results...")
        try:
            async with session.get(f"{base_url}/search/{search_id}/results") as response:
                if response.status == 200:
                    results = await response.json()
                    print(f"   ✅ Results retrieved")
                    print(f"   📊 Status: {results.get('status')}")
                    print(f"   📦 Products: {len(results.get('products', []))}")
                    print(f"   📨 Events: {len(results.get('events', []))}")
                else:
                    print(f"   ❌ Results retrieval failed: {response.status}")
        except Exception as e:
            print(f"   ❌ Results error: {e}")
    
    # Summary
    total_time = time.time() - start_time
    print(f"\n📊 Test Summary:")
    print(f"   ⏱️  Total time: {total_time:.2f}s")
    print(f"   📨 Events received: {event_count}")
    print(f"   📦 Products found: {product_count}")
    
    if total_time < 3.0 and product_count > 0:
        print(f"   ⚡ Performance: Excellent")
    elif total_time < 5.0 and product_count > 0:
        print(f"   ✅ Performance: Good")
    else:
        print(f"   ⚠️  Performance: Needs improvement")


if __name__ == "__main__":
    print("🚀 Make sure the API is running: python -m dlc_api.main_new")
    print("⏳ Starting test in 3 seconds...")
    time.sleep(3)
    
    try:
        asyncio.run(test_new_api())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

