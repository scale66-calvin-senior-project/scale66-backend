from typing import Optional, Dict, Any
from supabase import Client
from fastapi import HTTPException, status
import logging

from app.crud.base import CRUDBase

logger = logging.getLogger(__name__)


class CRUDBrandKit(CRUDBase):
    """CRUD operations for brand_kits table."""
    
    def __init__(self):
        super().__init__("brand_kits")
    
    async def get_by_user(
        self, 
        supabase: Client, 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get brand kit for a specific user.
        Users typically have one brand kit.
        
        Args:
            supabase: Supabase client
            user_id: User ID
            
        Returns:
            Brand kit if found, None otherwise
        """
        try:
            response = supabase.table(self.table_name).select("*").eq("user_id", user_id).execute()
            
            if not response.data:
                return None
            
            # Return the first brand kit (users typically have one)
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error getting brand kit for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get brand kit"
            )
    
    async def create_or_update_for_user(
        self, 
        supabase: Client, 
        user_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create or update brand kit for a user.
        If brand kit exists, update it. Otherwise, create it.
        
        Args:
            supabase: Supabase client
            user_id: User ID
            data: Brand kit data
            
        Returns:
            Created or updated brand kit
        """
        existing = await self.get_by_user(supabase, user_id)
        
        if existing:
            # Update existing brand kit
            return await self.update(supabase, existing["id"], data, user_id)
        else:
            # Create new brand kit
            return await self.create(supabase, data, user_id)


# Create singleton instance
brand_kit_crud = CRUDBrandKit()
