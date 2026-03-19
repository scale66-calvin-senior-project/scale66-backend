from typing import List, Dict, Any, Optional
from supabase import Client
from fastapi import HTTPException, status
import logging

from app.crud.base import CRUDBase

logger = logging.getLogger(__name__)


class CRUDSocialAccount(CRUDBase):
    """CRUD operations for social_media_accounts table."""
    
    def __init__(self):
        super().__init__("social_media_accounts")
    
    async def list_by_user(
        self, 
        supabase: Client, 
        user_id: str,
        active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List all social media accounts for a user.
        
        Args:
            supabase: Supabase client
            user_id: User ID
            active_only: If True, return only active accounts
            
        Returns:
            List of social media accounts
        """
        filters = {}
        if active_only:
            filters["is_active"] = True
        
        return await self.list(
            supabase, 
            user_id=user_id,
            filters=filters,
            order_by="created_at",
            ascending=False
        )
    
    async def get_by_platform(
        self, 
        supabase: Client, 
        user_id: str,
        platform: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get social media account by platform for a user.
        
        Args:
            supabase: Supabase client
            user_id: User ID
            platform: Platform name (instagram, tiktok, etc.)
            
        Returns:
            Social account if found, None otherwise
        """
        try:
            response = supabase.table(self.table_name).select("*").eq("user_id", user_id).eq("platform", platform).execute()
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error getting {platform} account for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get {platform} account"
            )
    
    async def deactivate(
        self, 
        supabase: Client, 
        id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Deactivate (soft delete) a social media account.
        
        Args:
            supabase: Supabase client
            id: Account ID
            user_id: User ID (for authorization)
            
        Returns:
            Updated account
        """
        return await self.update(supabase, id, {"is_active": False}, user_id)


# Create singleton instance
social_account_crud = CRUDSocialAccount()
