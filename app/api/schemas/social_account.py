from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SocialPlatform(str, Enum):
    """Social media platforms."""
    instagram = "instagram"
    tiktok = "tiktok"
    facebook = "facebook"
    twitter = "twitter"
    linkedin = "linkedin"
    youtube = "youtube"


class SocialAccountBase(BaseModel):
    """Base social account schema."""
    platform: SocialPlatform
    platform_user_id: str = Field(..., min_length=1)
    platform_username: Optional[str] = None
    is_active: bool = True


class SocialAccountCreate(SocialAccountBase):
    """Schema for creating/connecting a social account."""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None


class SocialAccountUpdate(BaseModel):
    """Schema for updating a social account."""
    platform_username: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class SocialAccountResponse(SocialAccountBase):
    """Schema for social account responses."""
    id: str
    user_id: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Exclude sensitive tokens from response
    class Config:
        from_attributes = True
