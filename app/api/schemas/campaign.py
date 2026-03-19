from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CampaignBase(BaseModel):
    """Base campaign schema with common fields."""
    campaign_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class CampaignCreate(CampaignBase):
    """Schema for creating a campaign."""
    pass


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign (all fields optional)."""
    campaign_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class CampaignResponse(CampaignBase):
    """Schema for campaign responses."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
