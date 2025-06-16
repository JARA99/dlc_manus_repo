from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging
from app.database import get_async_db
from app.models import Product
from app.schemas.search import Product as ProductSchema, ProductDetail

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/products/{product_id}", response_model=ProductDetail)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get detailed information about a specific product.
    
    Returns comprehensive product information including specifications,
    price history, and vendor details.
    """
    try:
        # Get product from database
        product = await db.get(Product, product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get vendor name
        from app.models import Vendor
        vendor = await db.get(Vendor, product.vendor_id)
        vendor_name = vendor.name if vendor else product.vendor_id
        
        # Convert to response format
        product_detail = ProductDetail(
            id=str(product.id),
            name=product.name,
            price=float(product.price),
            currency=product.currency,
            vendor_id=product.vendor_id,
            vendor_name=vendor_name,
            url=product.vendor_url,
            image_url=product.image_url,
            availability=product.availability,
            brand=product.brand,
            model=product.model,
            delivery_cost=float(product.delivery_cost) if product.delivery_cost else None,
            delivery_time=product.delivery_time,
            last_updated=product.last_updated_at or product.first_seen_at,
            description=product.description,
            specifications=product.specifications,
            original_price=float(product.original_price) if product.original_price else None,
            discount_percentage=float(product.discount_percentage) if product.discount_percentage else None,
            price_history=[]  # TODO: Implement price history retrieval
        )
        
        return product_detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get product details")

