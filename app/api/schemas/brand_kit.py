from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class BrandKitBase(BaseModel):
    """Base brand kit schema with common fields."""
    brand_name: str = Field(..., min_length=1, max_length=255)
    brand_niche: Optional[str] = None
    brand_style: Optional[str] = None
    customer_pain_points: List[str] = Field(default_factory=list)
    product_service_description: Optional[str] = None


class BrandKitCreate(BrandKitBase):
    """Schema for creating a brand kit."""
    pass


class BrandKitUpdate(BaseModel):
    """Schema for updating a brand kit (all fields optional)."""
    brand_name: Optional[str] = Field(None, min_length=1, max_length=255)
    brand_niche: Optional[str] = None
    brand_style: Optional[str] = None
    customer_pain_points: Optional[List[str]] = None
    product_service_description: Optional[str] = None


class BrandKitResponse(BrandKitBase):
    """Schema for brand kit responses."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
