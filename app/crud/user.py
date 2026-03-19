from typing import Optional, Dict, Any
from supabase import Client
from fastapi import HTTPException, status
import logging

from app.crud.base import CRUDBase

logger = logging.getLogger(__name__)


class CRUDUser(CRUDBase):
    """CRUD operations for users table."""
    
    def __init__(self):
        super().__init__("users")
    
    async def get_by_id(
        self, 
        supabase: Client, 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            supabase: Supabase client
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        return await self.get(supabase, user_id)
    
    async def get_by_email(
        self, 
        supabase: Client, 
        email: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user by email.
        
        Args:
            supabase: Supabase client
            email: User email
            
        Returns:
            User if found, None otherwise
        """
        try:
            response = supabase.table(self.table_name).select("*").eq("email", email).execute()
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user"
            )
    
    async def update_subscription_tier(
        self, 
        supabase: Client, 
        user_id: str,
        subscription_tier: str
    ) -> Dict[str, Any]:
        """
        Update user's subscription tier.
        
        Args:
            supabase: Supabase client
            user_id: User ID
            subscription_tier: New subscription tier
            
        Returns:
            Updated user
        """
        return await self.update(supabase, user_id, {"subscription_tier": subscription_tier})
    
    async def mark_onboarding_complete(
        self, 
        supabase: Client, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Mark user's onboarding as complete.
        
        Args:
            supabase: Supabase client
            user_id: User ID
            
        Returns:
            Updated user
        """
        return await self.update(supabase, user_id, {"onboarding_completed": True})
    
    async def set_stripe_customer_id(
        self, 
        supabase: Client, 
        user_id: str,
        stripe_customer_id: str
    ) -> Dict[str, Any]:
        """
        Set user's Stripe customer ID.
        
        Args:
            supabase: Supabase client
            user_id: User ID
            stripe_customer_id: Stripe customer ID
            
        Returns:
            Updated user
        """
        return await self.update(supabase, user_id, {"stripe_customer_id": stripe_customer_id})


# Create singleton instance
user_crud = CRUDUser()
