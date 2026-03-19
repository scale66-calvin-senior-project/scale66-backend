from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum


class SubscriptionTier(str, Enum):
    """Subscription tiers."""
    free = "free"
    starter = "starter"
    growth = "growth"
    agency = "agency"


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    subscription_tier: Optional[SubscriptionTier] = None
    onboarding_completed: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user responses."""
    id: str
    subscription_tier: SubscriptionTier = SubscriptionTier.free
    stripe_customer_id: Optional[str] = None
    onboarding_completed: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
