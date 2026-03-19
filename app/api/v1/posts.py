from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
import logging

from app.api.dependencies import get_supabase, get_current_user
from app.api.schemas.post import (
    PostCreate, PostUpdate, PostResponse,
    PostVariationCreate, PostVariationUpdate, PostVariationResponse,
    CarouselCreateRequest
)
from app.crud.post import post_crud, post_variation_crud
from app.crud.campaign import campaign_crud
from app.crud.brand_kit import brand_kit_crud
from app.agents.orchestrator import orchestrator
from app.models.pipeline import OrchestratorInput
from app.agents.base_agent import ExecutionError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


# Post endpoints

@router.post("/campaigns/{campaign_id}/carousel", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_carousel_post(
    campaign_id: str,
    carousel_data: CarouselCreateRequest,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Create a new carousel post using the AI agentic pipeline.
    
    This endpoint:
    1. Validates campaign and brand kit ownership
    2. Runs the orchestrator pipeline to generate carousel slides
    3. Uploads images to Supabase storage
    4. Creates a post record with carousel metadata
    """
    # Verify campaign exists and belongs to user
    await campaign_crud.get_or_404(supabase, campaign_id, user_id)
    
    # Verify brand kit exists and belongs to user
    await brand_kit_crud.get_or_404(supabase, carousel_data.brand_kit_id, user_id)
    
    # Ensure campaign_id matches URL parameter
    if carousel_data.campaign_id != campaign_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="campaign_id in body must match URL parameter"
        )
    
    try:
        # Run orchestrator pipeline
        orchestrator_input = OrchestratorInput(
            brand_kit_id=carousel_data.brand_kit_id,
            user_prompt=carousel_data.user_prompt,
            user_id=user_id,
        )
        
        orchestrator_result = await orchestrator.run(orchestrator_input)
        
        if not orchestrator_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=orchestrator_result.error_message or "Failed to generate carousel"
            )
        
        # Build carousel slides data structure
        carousel_slides = []
        
        # Hook slide
        carousel_slides.append({
            "slide_number": 1,
            "slide_type": "hook",
            "image_url": orchestrator_result.carousel_slides_urls[0] if orchestrator_result.carousel_slides_urls else None,
            "caption": orchestrator_result.hook_text,
        })
        
        # Body slides
        body_start_idx = 1
        for i, body_text in enumerate(orchestrator_result.body_texts):
            slide_idx = body_start_idx + i
            carousel_slides.append({
                "slide_number": slide_idx + 1,
                "slide_type": "body",
                "image_url": orchestrator_result.carousel_slides_urls[slide_idx] if slide_idx < len(orchestrator_result.carousel_slides_urls) else None,
                "caption": body_text,
            })
        
        # CTA slide if present
        if orchestrator_result.include_cta and orchestrator_result.cta_text:
            cta_idx = len(carousel_slides)
            carousel_slides.append({
                "slide_number": cta_idx + 1,
                "slide_type": "cta",
                "image_url": orchestrator_result.carousel_slides_urls[cta_idx] if cta_idx < len(orchestrator_result.carousel_slides_urls) else None,
                "caption": orchestrator_result.cta_text,
            })
        
        # Build carousel metadata
        carousel_metadata = {
            "carousel_id": orchestrator_result.carousel_id,
            "template_id": orchestrator_result.template_id,
            "format_type": orchestrator_result.format_type,
            "num_body_slides": orchestrator_result.num_body_slides,
            "include_cta": orchestrator_result.include_cta,
            "total_slides": len(carousel_slides),
        }
        
        # Combine all captions for final_caption
        captions = [orchestrator_result.hook_text]
        captions.extend(orchestrator_result.body_texts)
        if orchestrator_result.cta_text:
            captions.append(orchestrator_result.cta_text)
        final_caption = "\n\n".join(captions)
        
        # Create post record
        post_data = {
            "campaign_id": campaign_id,
            "final_caption": final_caption,
            "image_urls": ",".join(orchestrator_result.carousel_slides_urls),
            "carousel_slides": carousel_slides,
            "carousel_metadata": carousel_metadata,
            "platform": carousel_data.platform.value,
            "status": "draft",
        }
        
        post = await post_crud.create(supabase, post_data, user_id)
        return post
        
    except ValidationError as e:
        logger.error(f"Validation error creating carousel: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ExecutionError as e:
        logger.error(f"Execution error creating carousel: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate carousel: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating carousel: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the carousel"
        )


@router.post("/campaigns/{campaign_id}/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    campaign_id: str,
    post_data: PostCreate,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Create a new post within a campaign.
    """
    # Verify campaign exists and belongs to user
    await campaign_crud.get_or_404(supabase, campaign_id, user_id)
    
    try:
        data = post_data.model_dump()
        # Ensure campaign_id matches the URL parameter
        data["campaign_id"] = campaign_id
        post = await post_crud.create(supabase, data, user_id)
        return post
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        raise


@router.get("/campaigns/{campaign_id}/posts", response_model=List[PostResponse])
async def list_posts_in_campaign(
    campaign_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    List all posts in a campaign.
    """
    # Verify campaign exists and belongs to user
    await campaign_crud.get_or_404(supabase, campaign_id, user_id)
    
    posts = await post_crud.list_by_campaign(supabase, campaign_id, user_id, limit, offset)
    return posts


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Get a specific post by ID.
    Only returns if the post belongs to the authenticated user.
    """
    post = await post_crud.get_or_404(supabase, post_id, user_id)
    return post


@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    post_data: PostUpdate,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Update a post.
    Only allows updating if the post belongs to the authenticated user.
    """
    # Update with only provided fields
    data = post_data.model_dump(exclude_unset=True)
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated_post = await post_crud.update(supabase, post_id, data, user_id)
    return updated_post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: str,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Delete a post.
    Only allows deletion if the post belongs to the authenticated user.
    """
    await post_crud.delete(supabase, post_id, user_id)
    return None


# Post Variation endpoints

@router.post("/posts/{post_id}/variations", response_model=PostVariationResponse, status_code=status.HTTP_201_CREATED)
async def create_post_variation(
    post_id: str,
    variation_data: PostVariationCreate,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Create a new variation for a post.
    """
    # Verify post exists and belongs to user
    await post_crud.get_or_404(supabase, post_id, user_id)
    
    try:
        data = variation_data.model_dump()
        # Ensure post_id matches the URL parameter
        data["post_id"] = post_id
        
        # If variation_number not provided or is 0, auto-generate it
        if data.get("variation_number", 0) == 0:
            data["variation_number"] = await post_variation_crud.get_next_variation_number(supabase, post_id)
        
        variation = await post_variation_crud.create(supabase, data)
        return variation
    except Exception as e:
        logger.error(f"Error creating post variation: {str(e)}")
        raise


@router.get("/posts/{post_id}/variations", response_model=List[PostVariationResponse])
async def list_post_variations(
    post_id: str,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    List all variations for a post.
    """
    # Verify post exists and belongs to user
    await post_crud.get_or_404(supabase, post_id, user_id)
    
    variations = await post_variation_crud.list_by_post(supabase, post_id)
    return variations


@router.get("/posts/{post_id}/variations/{variation_id}", response_model=PostVariationResponse)
async def get_post_variation(
    post_id: str,
    variation_id: str,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Get a specific post variation.
    """
    # Verify post exists and belongs to user
    await post_crud.get_or_404(supabase, post_id, user_id)
    
    variation = await post_variation_crud.get_or_404(supabase, variation_id)
    
    # Verify variation belongs to the specified post
    if variation["post_id"] != post_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post variation not found"
        )
    
    return variation


@router.put("/posts/{post_id}/variations/{variation_id}", response_model=PostVariationResponse)
async def update_post_variation(
    post_id: str,
    variation_id: str,
    variation_data: PostVariationUpdate,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Update a post variation.
    """
    # Verify post exists and belongs to user
    await post_crud.get_or_404(supabase, post_id, user_id)
    
    # Update with only provided fields
    data = variation_data.model_dump(exclude_unset=True)
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Get existing variation to verify it belongs to the post
    existing = await post_variation_crud.get_or_404(supabase, variation_id)
    
    if existing["post_id"] != post_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post variation not found"
        )
    
    updated_variation = await post_variation_crud.update(supabase, variation_id, data)
    return updated_variation


@router.delete("/posts/{post_id}/variations/{variation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post_variation(
    post_id: str,
    variation_id: str,
    supabase: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Delete a post variation.
    """
    # Verify post exists and belongs to user
    await post_crud.get_or_404(supabase, post_id, user_id)
    
    # Get existing variation to verify it belongs to the post
    existing = await post_variation_crud.get_or_404(supabase, variation_id)
    
    if existing["post_id"] != post_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post variation not found"
        )
    
    await post_variation_crud.delete(supabase, variation_id)
    return None
