"""
Search API endpoints
"""

import asyncio
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from ..models import SearchRequest, SearchResponse
from ..core import SearchManager, SSEManager


class SearchAPI:
    """Search API endpoints with dependency injection."""
    
    def __init__(self, search_manager: SearchManager, sse_manager: SSEManager):
        self.router = APIRouter()
        self.search_manager = search_manager
        self.sse_manager = sse_manager
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.router.post("/search", response_model=SearchResponse)
        async def start_search(search_request: SearchRequest, request: Request):
            """Start a new product search."""
            # Create search
            search = await self.search_manager.create_search(search_request)
            
            # Build SSE URL
            base_url = f"{request.url.scheme}://{request.url.netloc}"
            sse_url = f"{base_url}/search/{search.id}/events"
            
            # Start monitoring search events
            asyncio.create_task(self._monitor_search_events(search.id))
            
            return SearchResponse(
                search_id=search.id,
                sse_url=sse_url,
                message=f"Search initiated for '{search_request.query}'"
            )
        
        @self.router.get("/search/{search_id}/events")
        async def search_events(search_id: str):
            """Server-Sent Events endpoint for search updates."""
            
            # Check if search exists
            search = self.search_manager.get_search(search_id)
            if not search:
                raise HTTPException(status_code=404, detail="Search not found")
            
            # Return SSE stream
            return StreamingResponse(
                self.sse_manager.subscribe_to_search(search_id),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control"
                }
            )
        
        @self.router.get("/search/{search_id}/results")
        async def get_search_results(search_id: str):
            """Get search results."""
            results = self.search_manager.get_search_results(search_id)
            if not results:
                raise HTTPException(status_code=404, detail="Search not found")
            return results
    
    async def _monitor_search_events(self, search_id: str):
        """Monitor search events and notify SSE subscribers."""
        last_event_index = 0
        
        while True:
            search = self.search_manager.get_search(search_id)
            if not search:
                break
            
            # Notify new events
            await self.sse_manager.notify_search_events(search, last_event_index)
            last_event_index = len(search.events)
            
            # Check if search is completed
            if search.status.value in ["completed", "failed"]:
                break
            
            # Wait before checking again
            await asyncio.sleep(0.1)
        
        # Final notification for any remaining events
        if search:
            await self.sse_manager.notify_search_events(search, last_event_index)

