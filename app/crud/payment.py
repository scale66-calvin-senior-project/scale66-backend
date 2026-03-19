from typing import List, Dict, Any, Optional
from supabase import Client
from fastapi import HTTPException, status
import logging

from app.crud.base import CRUDBase

logger = logging.getLogger(__name__)


class CRUDPaymentTransaction(CRUDBase):
    """CRUD operations for payment_transactions table."""
    
    def __init__(self):
        super().__init__("payment_transactions")
    
    async def list_by_user(
        self, 
        supabase: Client, 
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all payment transactions for a user.
        
        Args:
            supabase: Supabase client
            user_id: User ID
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of payment transactions
        """
        return await self.list(
            supabase, 
            user_id=user_id,
            limit=limit,
            offset=offset,
            order_by="created_at",
            ascending=False
        )
    
    async def get_by_stripe_payment_intent(
        self, 
        supabase: Client, 
        stripe_payment_intent_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get payment transaction by Stripe payment intent ID.
        
        Args:
            supabase: Supabase client
            stripe_payment_intent_id: Stripe payment intent ID
            
        Returns:
            Payment transaction if found, None otherwise
        """
        try:
            response = supabase.table(self.table_name).select("*").eq("stripe_payment_intent_id", stripe_payment_intent_id).execute()
            
            if not response.data:
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error getting transaction for payment intent {stripe_payment_intent_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get payment transaction"
            )
    
    async def update_status(
        self, 
        supabase: Client, 
        stripe_payment_intent_id: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Update payment transaction status by Stripe payment intent ID.
        
        Args:
            supabase: Supabase client
            stripe_payment_intent_id: Stripe payment intent ID
            status: New status
            
        Returns:
            Updated transaction
        """
        try:
            response = supabase.table(self.table_name).update({"status": status}).eq("stripe_payment_intent_id", stripe_payment_intent_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment transaction not found"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating transaction status for {stripe_payment_intent_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update transaction status"
            )


# Create singleton instance
payment_transaction_crud = CRUDPaymentTransaction()
