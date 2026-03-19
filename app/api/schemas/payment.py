from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from enum import Enum


class SubscriptionTier(str, Enum):
    """Subscription tiers."""
    free = "free"
    starter = "starter"
    growth = "growth"
    agency = "agency"


class PaymentStatus(str, Enum):
    """Payment transaction status."""
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    refunded = "refunded"


class PaymentTransactionBase(BaseModel):
    """Base payment transaction schema."""
    stripe_payment_intent_id: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    subscription_tier: SubscriptionTier
    currency: str = Field(default="usd", max_length=3)
    payment_method: Optional[str] = None


class PaymentTransactionCreate(PaymentTransactionBase):
    """Schema for creating a payment transaction."""
    status: PaymentStatus = PaymentStatus.pending


class PaymentTransactionUpdate(BaseModel):
    """Schema for updating a payment transaction."""
    status: Optional[PaymentStatus] = None
    payment_method: Optional[str] = None


class PaymentTransactionResponse(PaymentTransactionBase):
    """Schema for payment transaction responses."""
    id: str
    user_id: str
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StripeWebhookEvent(BaseModel):
    """Schema for Stripe webhook events."""
    type: str
    data: dict
