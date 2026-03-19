from typing import List, Dict, Any, Optional
from supabase import Client
from fastapi import HTTPException, status
import logging

from app.crud.base import CRUDBase

logger = logging.getLogger(__name__)


class CRUDPost(CRUDBase):
    """CRUD operations for posts table."""
    
    def __init__(self):
        super().__init__("posts")
    
    async def list_by_campaign(
        self, 
        supabase: Client, 
        campaign_id: str,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all posts for a campaign.
        
        Args:
            supabase: Supabase client
            campaign_id: Campaign ID
            user_id: User ID (for authorization)
            limit: Maximum number of posts to return
            offset: Number of posts to skip
            
        Returns:
            List of posts
        """
        return await self.list(
            supabase, 
            user_id=user_id,
            filters={"campaign_id": campaign_id},
            limit=limit,
            offset=offset,
            order_by="created_at",
            ascending=False
        )


class CRUDPostVariation(CRUDBase):
    """CRUD operations for post_variations table."""
    
    def __init__(self):
        super().__init__("post_variations")
    
    async def list_by_post(
        self, 
        supabase: Client, 
        post_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List all variations for a post.
        
        Args:
            supabase: Supabase client
            post_id: Post ID
            limit: Maximum number of variations to return
            
        Returns:
            List of post variations
        """
        try:
            response = supabase.table(self.table_name).select("*").eq("post_id", post_id).order("variation_number").limit(limit).execute()
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error listing variations for post {post_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list post variations"
            )
    
    async def get_next_variation_number(
        self, 
        supabase: Client, 
        post_id: str
    ) -> int:
        """
        Get the next variation number for a post.
        
        Args:
            supabase: Supabase client
            post_id: Post ID
            
        Returns:
            Next variation number
        """
        try:
            response = supabase.table(self.table_name).select("variation_number").eq("post_id", post_id).order("variation_number", desc=True).limit(1).execute()
            
            if response.data:
                return response.data[0]["variation_number"] + 1
            else:
                return 1
            
        except Exception as e:
            logger.error(f"Error getting next variation number for post {post_id}: {str(e)}")
            # Default to 1 if error
            return 1


# Create singleton instances
post_crud = CRUDPost()
post_variation_crud = CRUDPostVariation()
