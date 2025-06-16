from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging
from app.database import get_async_db
from app.models import Category
from app.schemas.search import Category as CategorySchema

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/categories", response_model=List[CategorySchema])
async def get_categories(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get product categories for filtering.
    
    Returns a hierarchical list of product categories that can be
    used for filtering search results.
    """
    try:
        # Get all active categories
        stmt = select(Category).where(Category.is_active == True).order_by(Category.sort_order, Category.name)
        result = await db.execute(stmt)
        categories = result.scalars().all()
        
        # Build category hierarchy
        category_dict = {}
        root_categories = []
        
        # First pass: create all category objects
        for category in categories:
            category_schema = CategorySchema(
                id=category.id,
                name=category.name,
                name_en=category.name_en,
                parent_id=category.parent_id,
                level=int(category.level) if category.level else 0,
                path=category.path,
                subcategories=[]
            )
            category_dict[category.id] = category_schema
            
            if not category.parent_id:
                root_categories.append(category_schema)
        
        # Second pass: build hierarchy
        for category in categories:
            if category.parent_id and category.parent_id in category_dict:
                parent = category_dict[category.parent_id]
                child = category_dict[category.id]
                parent.subcategories.append(child)
        
        return root_categories
        
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get categories")

