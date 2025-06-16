from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import json
import logging
import asyncio
from datetime import datetime
from app.schemas.search import WSMessage, WSSearchStarted, WSVendorStarted, WSProductFound, WSVendorCompleted, WSSearchCompleted, WSError

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket connection manager."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, search_id: str):
        """Accept a WebSocket connection and add to search group."""
        await websocket.accept()
        
        if search_id not in self.active_connections:
            self.active_connections[search_id] = set()
        
        self.active_connections[search_id].add(websocket)
        logger.info(f"WebSocket connected for search {search_id}")
    
    def disconnect(self, websocket: WebSocket, search_id: str):
        """Remove WebSocket connection from search group."""
        if search_id in self.active_connections:
            self.active_connections[search_id].discard(websocket)
            
            # Clean up empty groups
            if not self.active_connections[search_id]:
                del self.active_connections[search_id]
        
        logger.info(f"WebSocket disconnected for search {search_id}")
    
    async def send_to_search(self, search_id: str, message: WSMessage):
        """Send message to all connections for a specific search."""
        if search_id not in self.active_connections:
            return
        
        message_data = message.model_dump_json()
        disconnected = set()
        
        for websocket in self.active_connections[search_id]:
            try:
                await websocket.send_text(message_data)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {str(e)}")
                disconnected.add(websocket)
        
        # Remove disconnected websockets
        for websocket in disconnected:
            self.active_connections[search_id].discard(websocket)
    
    async def send_search_started(self, search_id: str, vendors_count: int):
        """Send search started message."""
        message = WSSearchStarted(
            search_id=search_id,
            timestamp=datetime.utcnow(),
            vendors_count=vendors_count
        )
        await self.send_to_search(search_id, message)
    
    async def send_vendor_started(self, search_id: str, vendor_id: str, vendor_name: str):
        """Send vendor started message."""
        message = WSVendorStarted(
            search_id=search_id,
            timestamp=datetime.utcnow(),
            vendor=vendor_id,
            vendor_name=vendor_name
        )
        await self.send_to_search(search_id, message)
    
    async def send_product_found(self, search_id: str, vendor_id: str, product_data: dict):
        """Send product found message."""
        message = WSProductFound(
            search_id=search_id,
            timestamp=datetime.utcnow(),
            vendor=vendor_id,
            product=product_data
        )
        await self.send_to_search(search_id, message)
    
    async def send_vendor_completed(self, search_id: str, vendor_id: str, results_count: int, duration: float):
        """Send vendor completed message."""
        message = WSVendorCompleted(
            search_id=search_id,
            timestamp=datetime.utcnow(),
            vendor=vendor_id,
            results_count=results_count,
            duration=duration
        )
        await self.send_to_search(search_id, message)
    
    async def send_search_completed(self, search_id: str, total_results: int, total_duration: float, comparison: dict = None):
        """Send search completed message."""
        message = WSSearchCompleted(
            search_id=search_id,
            timestamp=datetime.utcnow(),
            total_results=total_results,
            total_duration=total_duration,
            comparison=comparison
        )
        await self.send_to_search(search_id, message)
    
    async def send_error(self, search_id: str, error_message: str, vendor_id: str = None):
        """Send error message."""
        message = WSError(
            search_id=search_id,
            timestamp=datetime.utcnow(),
            vendor=vendor_id,
            error=error_message
        )
        await self.send_to_search(search_id, message)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/search/{search_id}")
async def websocket_search(websocket: WebSocket, search_id: str):
    """
    WebSocket endpoint for real-time search updates.
    
    Clients connect to this endpoint to receive real-time updates
    about search progress and results.
    """
    await manager.connect(websocket, search_id)
    
    try:
        # Keep connection alive and handle any incoming messages
        while True:
            try:
                # Wait for messages from client (ping/pong, etc.)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle client messages if needed
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except json.JSONDecodeError:
                    pass
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text(json.dumps({"type": "ping"}))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, search_id)
    except Exception as e:
        logger.error(f"WebSocket error for search {search_id}: {str(e)}")
        manager.disconnect(websocket, search_id)


# Export manager for use in other modules
__all__ = ["manager", "ConnectionManager"]

