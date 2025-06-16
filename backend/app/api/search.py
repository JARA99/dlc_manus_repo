from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
from app.database import get_async_db
from app.schemas.search import (
    SearchRequest, SearchInitResponse, SearchResultResponse, 
    SearchHistory, SearchStatus
)
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search", response_model=SearchInitResponse)
async def initiate_search(
    search_request: SearchRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Initiate a new product search across all vendors.
    
    This endpoint starts a search and returns immediately with a search ID.
    Use the WebSocket endpoint or polling to get real-time results.
    """
    try:
        # Get client IP
        client_ip = request.client.host
        
        # Create search service
        search_service = SearchService(db)
        
        # Initiate search
        search_id = await search_service.initiate_search(search_request, client_ip)
        
        # Build WebSocket URL
        websocket_url = f"ws://localhost:8000/ws/search/{search_id}"
        
        return SearchInitResponse(
            search_id=search_id,
            status=SearchStatus.INITIATED,
            estimated_time=30,  # Estimated time in seconds
            websocket_url=websocket_url
        )
        
    except Exception as e:
        logger.error(f"Error initiating search: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate search")


@router.get("/search/{search_id}/results", response_model=SearchResultResponse)
async def get_search_results(
    search_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get current search results for a specific search.
    
    Returns the current state of the search including any products found so far.
    """
    try:
        search_service = SearchService(db)
        results = await search_service.get_search_results(search_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="Search not found")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting search results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get search results")


@router.get("/search/history", response_model=SearchHistory)
async def get_search_history(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get recent search history.
    
    Returns a paginated list of recent searches.
    """
    try:
        # For now, return empty history since we don't have user authentication
        # In future phases, this will return user-specific search history
        
        return SearchHistory(
            searches=[],
            total=0,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Error getting search history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get search history")

