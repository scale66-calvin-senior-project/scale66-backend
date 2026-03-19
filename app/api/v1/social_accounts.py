from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
import logging

from app.api.dependencies import get_supabase, get_current_user
from app.api.schemas.social_account import (
    SocialAccountCreate, SocialAccountUpdate, SocialAccountResponse
)
from app.crud.social_account import social_account_crud

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/social-accounts", response_model=SocialAccountResponse, status_code=status.HTTP_201_CREATED)
async def connect_social_account(
    account_data: SocialAccountCreate,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Connect a new social media account.
    
    This endpoint is typically called after OAuth flow completion
    with the access tokens and user information.
    """
    # Check if account already exists for this platform
    existing = await social_account_crud.get_by_platform(
        supabase, user_id, account_data.platform.value
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A {account_data.platform.value} account is already connected. Please update or disconnect it first."
        )
    
    try:
        data = account_data.model_dump()
        account = await social_account_crud.create(supabase, data, user_id)
        return account
    except Exception as e:
        logger.error(f"Error connecting social account: {str(e)}")
        raise


@router.get("/social-accounts", response_model=List[SocialAccountResponse])
async def list_social_accounts(
    active_only: bool = Query(default=False, description="Return only active accounts"),
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    List all connected social media accounts for the authenticated user.
    """
    accounts = await social_account_crud.list_by_user(supabase, user_id, active_only)
    return accounts


@router.get("/social-accounts/{account_id}", response_model=SocialAccountResponse)
async def get_social_account(
    account_id: str,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Get a specific social media account by ID.
    """
    account = await social_account_crud.get_or_404(supabase, account_id, user_id)
    return account


@router.put("/social-accounts/{account_id}", response_model=SocialAccountResponse)
async def update_social_account(
    account_id: str,
    account_data: SocialAccountUpdate,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Update a social media account.
    
    This is typically used to refresh access tokens or update account status.
    """
    # Update with only provided fields
    data = account_data.model_dump(exclude_unset=True)
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated_account = await social_account_crud.update(supabase, account_id, data, user_id)
    return updated_account


@router.delete("/social-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_social_account(
    account_id: str,
    soft_delete: bool = Query(default=True, description="Deactivate instead of permanently deleting"),
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Disconnect a social media account.
    
    By default, this performs a soft delete (deactivation).
    Set soft_delete=false to permanently delete the record.
    """
    if soft_delete:
        # Soft delete - just mark as inactive
        await social_account_crud.deactivate(supabase, account_id, user_id)
    else:
        # Hard delete - permanently remove
        await social_account_crud.delete(supabase, account_id, user_id)
    
    return None
