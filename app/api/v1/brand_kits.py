from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
import logging

from app.api.dependencies import get_supabase, get_current_user
from app.api.schemas.brand_kit import BrandKitCreate, BrandKitUpdate, BrandKitResponse
from app.crud.brand_kit import brand_kit_crud

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/brand-kits", response_model=BrandKitResponse, status_code=status.HTTP_201_CREATED)
async def create_brand_kit(
    brand_kit_data: BrandKitCreate,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Create a new brand kit for the authenticated user.
    This is typically done during onboarding.
    """
    try:
        data = brand_kit_data.model_dump()
        brand_kit = await brand_kit_crud.create(supabase, data, user_id)
        return brand_kit
    except Exception as e:
        logger.error(f"Error creating brand kit: {str(e)}")
        raise


@router.get("/brand-kits/me", response_model=BrandKitResponse)
async def get_my_brand_kit(
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Get the authenticated user's brand kit.
    """
    brand_kit = await brand_kit_crud.get_by_user(supabase, user_id)
    
    if not brand_kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand kit not found. Please complete onboarding."
        )
    
    return brand_kit


@router.put("/brand-kits/me", response_model=BrandKitResponse)
async def update_my_brand_kit(
    brand_kit_data: BrandKitUpdate,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Update the authenticated user's brand kit.
    """
    # Get existing brand kit
    existing = await brand_kit_crud.get_by_user(supabase, user_id)
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand kit not found. Please create one first."
        )
    
    # Update with only provided fields
    data = brand_kit_data.model_dump(exclude_unset=True)
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated_brand_kit = await brand_kit_crud.update(supabase, existing["id"], data, user_id)
    return updated_brand_kit
