from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from supabase import Client
import logging

from app.api.dependencies import get_supabase, get_current_user
from app.api.schemas.payment import (
    PaymentTransactionCreate, PaymentTransactionUpdate, 
    PaymentTransactionResponse, StripeWebhookEvent
)
from app.crud.payment import payment_transaction_crud
from app.crud.user import user_crud

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/payments/transactions", response_model=PaymentTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_transaction(
    transaction_data: PaymentTransactionCreate,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Record a new payment transaction.
    
    This is typically called when initiating a payment with Stripe.
    The transaction status can be updated later via webhook.
    """
    try:
        data = transaction_data.model_dump()
        transaction = await payment_transaction_crud.create(supabase, data, user_id)
        return transaction
    except Exception as e:
        logger.error(f"Error creating payment transaction: {str(e)}")
        raise


@router.get("/payments/transactions", response_model=List[PaymentTransactionResponse])
async def list_payment_transactions(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    List all payment transactions for the authenticated user.
    """
    transactions = await payment_transaction_crud.list_by_user(supabase, user_id, limit, offset)
    return transactions


@router.get("/payments/transactions/{transaction_id}", response_model=PaymentTransactionResponse)
async def get_payment_transaction(
    transaction_id: str,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Get a specific payment transaction by ID.
    """
    transaction = await payment_transaction_crud.get_or_404(supabase, transaction_id, user_id)
    return transaction


@router.post("/payments/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    supabase: Client = Depends(get_supabase)
):
    """
    Handle Stripe webhook events.
    
    This endpoint processes payment events from Stripe such as:
    - payment_intent.succeeded
    - payment_intent.payment_failed
    - charge.refunded
    
    Note: In production, you should verify the webhook signature using
    Stripe's webhook secret and the request headers.
    """
    try:
        # Get the raw body for signature verification
        payload = await request.body()
        
        # In production, verify the signature:
        # sig_header = request.headers.get('stripe-signature')
        # stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        
        # Parse the event
        event = await request.json()
        event_type = event.get("type")
        
        logger.info(f"Received Stripe webhook event: {event_type}")
        
        # Handle payment intent events
        if event_type == "payment_intent.succeeded":
            payment_intent = event.get("data", {}).get("object", {})
            payment_intent_id = payment_intent.get("id")
            
            if payment_intent_id:
                # Update transaction status to succeeded
                transaction = await payment_transaction_crud.update_status(
                    supabase, payment_intent_id, "succeeded"
                )
                
                # Update user subscription tier if transaction includes metadata
                if transaction:
                    user_id = transaction.get("user_id")
                    subscription_tier = transaction.get("subscription_tier")
                    
                    if user_id and subscription_tier:
                        await user_crud.update_subscription_tier(
                            supabase, user_id, subscription_tier
                        )
                        logger.info(f"Updated user {user_id} subscription to {subscription_tier}")
        
        elif event_type == "payment_intent.payment_failed":
            payment_intent = event.get("data", {}).get("object", {})
            payment_intent_id = payment_intent.get("id")
            
            if payment_intent_id:
                # Update transaction status to failed
                await payment_transaction_crud.update_status(
                    supabase, payment_intent_id, "failed"
                )
        
        elif event_type == "charge.refunded":
            charge = event.get("data", {}).get("object", {})
            payment_intent_id = charge.get("payment_intent")
            
            if payment_intent_id:
                # Update transaction status to refunded
                await payment_transaction_crud.update_status(
                    supabase, payment_intent_id, "refunded"
                )
        
        return {"status": "success", "event_type": event_type}
        
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {str(e)}")
        # Return 200 to acknowledge receipt even if processing fails
        # to prevent Stripe from retrying
        return {"status": "error", "message": str(e)}
