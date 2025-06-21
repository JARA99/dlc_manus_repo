"""
DondeLoCompro.gt API - Simple FastAPI application with Server-Sent Events
"""

import asyncio
import uuid
import json
import os
from datetime import datetime, timezone
from typing import Dict, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .models import SearchRequest, SearchResponse, SearchEvent, ScrapingResult
from .scrapers import SCRAPERS, get_scraper_registry

# Get the global registry
_registry = get_scraper_registry()


# Load environment variables
load_dotenv()

# Global storage for active searches (in production, use Redis or database)
active_searches: Dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    print("🚀 DondeLoCompro.gt API starting up...")
    yield
    # Shutdown
    print("🛑 DondeLoCompro.gt API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="DondeLoCompro.gt API",
    description="Simple product price comparison API for Guatemala",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "DondeLoCompro.gt API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "scrapers": list(SCRAPERS.keys())
    }


@app.post("/search", response_model=SearchResponse)
async def start_search(search_request: SearchRequest, request: Request):
    """Start a new product search."""
    search_id = str(uuid.uuid4())
    
    # Store search info
    active_searches[search_id] = {
        "query": search_request.query,
        "max_results": search_request.max_results,
        "status": "initiated",
        "created_at": datetime.now(timezone.utc)
    }
    
    # Start background search task
    asyncio.create_task(execute_search(search_id, search_request))
    
    # Return SSE endpoint
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    sse_url = f"{base_url}/search/{search_id}/events"
    
    return SearchResponse(
        search_id=search_id,
        sse_url=sse_url,
        message=f"Search initiated for '{search_request.query}'"
    )


@app.get("/search/{search_id}/events")
async def search_events(search_id: str):
    """Server-Sent Events endpoint for search updates."""
    
    if search_id not in active_searches:
        raise HTTPException(status_code=404, detail="Search not found")
    
    async def event_generator():
        """Generate SSE events for the search."""
        try:
            # Send initial connection event
            yield format_sse_event("connected", {
                "search_id": search_id,
                "message": "Connected to search updates"
            })
            
            # Wait for search to complete and send events
            while True:
                search_info = active_searches.get(search_id)
                if not search_info:
                    break
                
                status = search_info.get("status")
                
                if status == "completed":
                    # Send final results and close
                    results = search_info.get("results", [])
                    yield format_sse_event("completed", {
                        "search_id": search_id,
                        "total_results": len(results),
                        "results": [product.model_dump() for product in results]
                    })
                    break
                
                elif status == "failed":
                    # Send error and close
                    yield format_sse_event("error", {
                        "search_id": search_id,
                        "error": search_info.get("error", "Unknown error")
                    })
                    break
                
                # Check for new events
                events = search_info.get("events", [])
                sent_events = search_info.get("sent_events", 0)
                
                # Send new events
                for i in range(sent_events, len(events)):
                    event = events[i]
                    yield format_sse_event(event["event"], event["data"])
                
                # Update sent events counter
                search_info["sent_events"] = len(events)
                
                # Wait before checking again
                await asyncio.sleep(0.1)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            yield format_sse_event("error", {
                "search_id": search_id,
                "error": f"Stream error: {str(e)}"
            })
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


async def execute_search(search_id: str, search_request: SearchRequest):
    """Execute the actual search across scrapers."""
    try:
        search_info = active_searches[search_id]
        search_info["status"] = "running"
        search_info["events"] = []
        search_info["sent_events"] = 0
        
        # Send search started event
        add_search_event(search_id, "started", {
            "query": search_request.query,
            "vendors": list(SCRAPERS.keys())
        })
        
        # Execute scrapers
        all_products = []
        
        for vendor_id, scraper_class in SCRAPERS.items():
            # Send vendor started event
            scraper = _registry.get_scraper(vendor_id)  # Use registry to get singleton
            add_search_event(search_id, "vendor_started", {
                "vendor_id": vendor_id,
                "vendor_name": scraper.vendor.name
            })
            
            # Execute scraper
            result = await scraper.search(search_request.query, search_request.max_results)
            
            if result.success:
                # Send products immediately as they're found
                for product in result.products:
                    add_search_event(search_id, "product_found", {
                        "vendor_id": vendor_id,
                        "product": product.model_dump()
                    })
                    all_products.append(product)
                
                # Send vendor completed event
                add_search_event(search_id, "vendor_completed", {
                    "vendor_id": vendor_id,
                    "products_found": len(result.products),
                    "duration": result.duration
                })
            else:
                # Send vendor error event
                add_search_event(search_id, "vendor_error", {
                    "vendor_id": vendor_id,
                    "error": result.error_message
                })
        
        # Mark search as completed
        search_info["status"] = "completed"
        search_info["results"] = all_products
        
    except Exception as e:
        # Mark search as failed
        search_info = active_searches.get(search_id, {})
        search_info["status"] = "failed"
        search_info["error"] = str(e)


def add_search_event(search_id: str, event_type: str, data: dict):
    """Add an event to the search."""
    search_info = active_searches.get(search_id)
    if search_info:
        events = search_info.setdefault("events", [])
        events.append({
            "event": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })


def format_sse_event(event_type: str, data: dict) -> str:
    """Format data as Server-Sent Event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def main():
    """Main entry point."""
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("API_DEBUG", "false").lower() == "true"
    
    print(f"🚀 Starting DondeLoCompro.gt API on {host}:{port}")
    
    uvicorn.run(
        "dlc_api.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )


if __name__ == "__main__":
    main()

