from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
import logging

from app.api.dependencies import get_supabase, get_current_user
from app.api.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse
from app.crud.campaign import campaign_crud

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Create a new campaign for the authenticated user.
    """
    try:
        data = campaign_data.model_dump()
        campaign = await campaign_crud.create(supabase, data, user_id)
        return campaign
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        raise


@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    List all campaigns for the authenticated user.
    """
    campaigns = await campaign_crud.list_by_user(supabase, user_id, limit, offset)
    return campaigns


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Get a specific campaign by ID.
    Only returns if the campaign belongs to the authenticated user.
    """
    campaign = await campaign_crud.get_or_404(supabase, campaign_id, user_id)
    return campaign


@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign_data: CampaignUpdate,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Update a campaign.
    Only allows updating if the campaign belongs to the authenticated user.
    """
    # Update with only provided fields
    data = campaign_data.model_dump(exclude_unset=True)
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated_campaign = await campaign_crud.update(supabase, campaign_id, data, user_id)
    return updated_campaign


@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: str,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Delete a campaign.
    Only allows deletion if the campaign belongs to the authenticated user.
    """
    await campaign_crud.delete(supabase, campaign_id, user_id)
    return None
