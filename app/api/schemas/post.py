from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class PostPlatform(str, Enum):
    """Social media platforms."""
    instagram = "instagram"
    tiktok = "tiktok"
    linkedin = "linkedin"
    twitter = "twitter"


class PostStatus(str, Enum):
    """Post status."""
    draft = "draft"
    scheduled = "scheduled"
    published = "published"
    failed = "failed"


class PostBase(BaseModel):
    """Base post schema with common fields."""
    campaign_id: str
    final_caption: Optional[str] = None
    final_hashtags: Optional[str] = None
    image_urls: Optional[str] = None
    carousel_slides: List[Dict[str, Any]] = Field(default_factory=list)
    carousel_metadata: Dict[str, Any] = Field(default_factory=dict)
    platform: PostPlatform = PostPlatform.instagram
    status: PostStatus = PostStatus.draft
    scheduled_for: Optional[datetime] = None


class PostCreate(PostBase):
    """Schema for creating a post."""
    pass


class PostUpdate(BaseModel):
    """Schema for updating a post (all fields optional)."""
    campaign_id: Optional[str] = None
    final_caption: Optional[str] = None
    final_hashtags: Optional[str] = None
    image_urls: Optional[str] = None
    carousel_slides: Optional[List[Dict[str, Any]]] = None
    carousel_metadata: Optional[Dict[str, Any]] = None
    platform: Optional[PostPlatform] = None
    status: Optional[PostStatus] = None
    scheduled_for: Optional[datetime] = None
    published_at: Optional[datetime] = None


class PostResponse(PostBase):
    """Schema for post responses."""
    id: str
    user_id: str
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Post Variations

class PostVariationBase(BaseModel):
    """Base post variation schema."""
    variation_number: int
    caption: Optional[str] = None
    hashtags: Optional[str] = None
    image_urls: Optional[str] = None
    is_posted: bool = False
    posted_platforms: Optional[str] = None


class PostVariationCreate(PostVariationBase):
    """Schema for creating a post variation."""
    post_id: str


class PostVariationUpdate(BaseModel):
    """Schema for updating a post variation."""
    caption: Optional[str] = None
    hashtags: Optional[str] = None
    image_urls: Optional[str] = None
    is_posted: Optional[bool] = None
    posted_platforms: Optional[str] = None


class PostVariationResponse(PostVariationBase):
    """Schema for post variation responses."""
    id: str
    post_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Carousel Creation

class CarouselCreateRequest(BaseModel):
    """Schema for creating a carousel post via the agentic pipeline."""
    campaign_id: str = Field(..., description="Campaign ID to associate the post with")
    brand_kit_id: str = Field(..., description="Brand kit ID to use for generation")
    user_prompt: str = Field(..., min_length=1, max_length=2000, description="User prompt for carousel generation")
    platform: PostPlatform = Field(default=PostPlatform.instagram, description="Target platform")
