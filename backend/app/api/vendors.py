from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging
from app.database import get_async_db
from app.models import Vendor
from app.schemas.search import Vendor as VendorSchema

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/vendors", response_model=List[VendorSchema])
async def get_vendors(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get list of supported vendors/stores.
    
    Returns information about all e-commerce vendors that are
    currently supported for product scraping.
    """
    try:
        # Get all active vendors
        stmt = select(Vendor).where(Vendor.is_active == True).order_by(Vendor.name)
        result = await db.execute(stmt)
        vendors = result.scalars().all()
        
        # Convert to response format
        vendor_list = []
        for vendor in vendors:
            vendor_schema = VendorSchema(
                id=vendor.id,
                name=vendor.name,
                website=vendor.website,
                logo_url=vendor.logo_url,
                categories=vendor.supported_categories or [],
                delivery_areas=vendor.delivery_areas or [],
                status=vendor.status,
                last_scraped=vendor.last_scraped_at
            )
            vendor_list.append(vendor_schema)
        
        return vendor_list
        
    except Exception as e:
        logger.error(f"Error getting vendors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get vendors")

