"""
SSE Manager - Core business logic for Server-Sent Events
"""

import asyncio
import json
from typing import Dict, List, AsyncGenerator
from ..models import Search, SearchEvent


class SSEManager:
    """Manages Server-Sent Events for real-time search updates."""
    
    def __init__(self):
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
    
    async def subscribe_to_search(self, search_id: str) -> AsyncGenerator[str, None]:
        """Subscribe to search events via Server-Sent Events."""
        queue = asyncio.Queue()
        
        # Add subscriber
        if search_id not in self.subscribers:
            self.subscribers[search_id] = []
        self.subscribers[search_id].append(queue)
        
        try:
            # Send initial connection event
            yield self._format_sse_event("connected", {
                "search_id": search_id,
                "message": "Connected to search updates"
            })
            
            # Listen for events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield self._format_sse_event(event.event, event.data)
                    
                    # If it's a completion event, break the loop
                    if event.event in ["completed", "error"]:
                        break
                        
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield self._format_sse_event("heartbeat", {
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    
        except asyncio.CancelledError:
            pass
        finally:
            # Remove subscriber
            if search_id in self.subscribers:
                if queue in self.subscribers[search_id]:
                    self.subscribers[search_id].remove(queue)
                if not self.subscribers[search_id]:
                    del self.subscribers[search_id]
    
    async def notify_search_event(self, search_id: str, event: SearchEvent):
        """Notify all subscribers of a search event."""
        if search_id in self.subscribers:
            # Send event to all subscribers
            for queue in self.subscribers[search_id]:
                try:
                    await queue.put(event)
                except Exception:
                    # Handle queue errors (subscriber disconnected)
                    pass
    
    async def notify_search_events(self, search: Search, last_event_index: int = 0):
        """Notify all new events from a search."""
        new_events = search.get_new_events(last_event_index)
        for event in new_events:
            await self.notify_search_event(search.id, event)
    
    def _format_sse_event(self, event_type: str, data: dict) -> str:
        """Format data as Server-Sent Event."""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    
    def get_subscriber_count(self, search_id: str) -> int:
        """Get number of subscribers for a search."""
        return len(self.subscribers.get(search_id, []))
    
    def get_total_subscribers(self) -> int:
        """Get total number of active subscribers."""
        return sum(len(queues) for queues in self.subscribers.values())

