from typing import List, Dict, Any
from supabase import Client
import logging

from app.crud.base import CRUDBase

logger = logging.getLogger(__name__)


class CRUDCampaign(CRUDBase):
    """CRUD operations for campaigns table."""
    
    def __init__(self):
        super().__init__("campaigns")
    
    async def list_by_user(
        self, 
        supabase: Client, 
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all campaigns for a user.
        
        Args:
            supabase: Supabase client
            user_id: User ID
            limit: Maximum number of campaigns to return
            offset: Number of campaigns to skip
            
        Returns:
            List of campaigns
        """
        return await self.list(
            supabase, 
            user_id=user_id,
            limit=limit,
            offset=offset,
            order_by="created_at",
            ascending=False
        )


# Create singleton instance
campaign_crud = CRUDCampaign()
