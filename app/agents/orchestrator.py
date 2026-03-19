import base64
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.agents.base_agent import BaseAgent, ValidationError, ExecutionError
from app.core.config import settings
from app.models.pipeline import (
    OrchestratorInput,
    OrchestratorOutput,
    FormatDeciderInput,
    TemplateDeciderInput,
    CaptionGeneratorInput,
    SlideGeneratorInput,
)
from app.models.brand_kit import BrandKit
from app.agents.format_decider import format_decider
from app.agents.template_decider import template_decider
from app.agents.caption_generator import caption_generator
from app.agents.slide_generator import slide_generator
from app.core.supabase import get_supabase_admin_client


class Orchestrator(BaseAgent[OrchestratorInput, OrchestratorOutput]):
    """Orchestrates the complete carousel generation pipeline by coordinating all agents."""
    
    # Singleton pattern implementation
    _instance: Optional['Orchestrator'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        super().__init__()
    
    async def _validate_input(self, input_data: OrchestratorInput) -> None:
        """Validate orchestrator input."""
        if not input_data.brand_kit_id or not input_data.brand_kit_id.strip():
            raise ValidationError("brand_kit_id is required")
        if not input_data.user_prompt or not input_data.user_prompt.strip():
            raise ValidationError("user_prompt is required")
    
    async def _execute(self, input_data: OrchestratorInput) -> OrchestratorOutput:
        # Step 1: Fetch brand kit data
        brand_kit = await self._fetch_brand_kit(input_data.brand_kit_id)
        
        # Step 2: Decide format and number of slides
        format_result = await format_decider.run(
            FormatDeciderInput(
                user_prompt=input_data.user_prompt,
                brand_kit=brand_kit,
            )
        )
        
        # Step 3: Select template based on format
        template_result = await template_decider.run(
            TemplateDeciderInput(
                user_prompt=input_data.user_prompt,
                brand_kit=brand_kit,
                format_type=format_result.format_type,
                num_body_slides=format_result.num_body_slides,
                include_cta=format_result.include_cta,
            )
        )
        
        # Step 4: Generate captions for all slides
        caption_result = await caption_generator.run(
            CaptionGeneratorInput(
                format_type=format_result.format_type,
                user_prompt=input_data.user_prompt,
                brand_kit=brand_kit,
                num_body_slides=format_result.num_body_slides,
                template_id=template_result.template_id,
                hook_slide=template_result.hook_slide,
                body_slide=template_result.body_slide,
                cta_slide=template_result.cta_slide,
            )
        )
        
        # Step 5: Generate slide images
        slide_result = await slide_generator.run(
            SlideGeneratorInput(
                format_type=format_result.format_type,
                num_body_slides=format_result.num_body_slides,
                brand_kit=brand_kit,
                user_prompt=input_data.user_prompt,
                hook_text=caption_result.hook_text,
                body_texts=caption_result.body_texts,
                cta_text=caption_result.cta_text,
                template_id=template_result.template_id,
                hook_slide=template_result.hook_slide,
                body_slide=template_result.body_slide,
                cta_slide=template_result.cta_slide,
            )
        )
        
        # Step 6: Upload images to Supabase storage
        carousel_id = str(uuid.uuid4())
        slide_urls = await self._upload_images_to_storage(
            carousel_id=carousel_id,
            hook_image=slide_result.hook_image,
            body_images=slide_result.body_images,
            cta_image=slide_result.cta_image,
            user_id=input_data.user_id if hasattr(input_data, 'user_id') else None,
        )
        
        # Step 7: Optionally save images locally for debugging
        if settings.save_local_output:
            self._save_images_locally(
                hook_image=slide_result.hook_image,
                body_images=slide_result.body_images,
                cta_image=slide_result.cta_image,
                brand_kit_id=input_data.brand_kit_id,
            )
        
        return OrchestratorOutput(
            step_name="orchestrator",
            success=True,
            carousel_id=carousel_id,
            carousel_slides_urls=slide_urls,
            hook_text=caption_result.hook_text,
            body_texts=caption_result.body_texts,
            cta_text=caption_result.cta_text,
            template_id=template_result.template_id,
            format_type=format_result.format_type,
            num_body_slides=format_result.num_body_slides,
            include_cta=format_result.include_cta,
        )
    
    async def _fetch_brand_kit(self, brand_kit_id: str) -> BrandKit:
        """Fetch brand kit data from Supabase and convert to BrandKit model."""
        try:
            supabase = get_supabase_admin_client()
            response = supabase.table("brand_kits").select("*").eq("id", brand_kit_id).execute()
            
            if not response.data:
                raise ExecutionError(f"Brand kit not found: {brand_kit_id}")
            
            brand_data = response.data[0]
            
            # Handle pain_points which may be stored as string or list
            pain_points = brand_data.get("customer_pain_points", [])
            if isinstance(pain_points, str):
                pain_points = [pain_points] if pain_points else []
            
            brand_kit = BrandKit(
                brand_name=brand_data.get("brand_name", ""),
                brand_niche=brand_data.get("brand_niche", ""),
                brand_style=brand_data.get("brand_style", ""),
                customer_pain_points=pain_points,
                product_service_desc=brand_data.get("product_service_description", ""),
            )
            
            return brand_kit
            
        except ExecutionError:
            raise
        except Exception as e:
            raise ExecutionError(f"Failed to fetch brand kit: {str(e)}")
    
    async def _upload_images_to_storage(
        self,
        carousel_id: str,
        hook_image: str,
        body_images: List[str],
        cta_image: Optional[str],
        user_id: Optional[str] = None,
    ) -> List[str]:
        """Upload generated images to Supabase storage and return public URLs."""
        supabase = get_supabase_admin_client()
        bucket_name = "carousels"
        slide_urls: List[str] = []
        
        try:
            storage = supabase.storage.from_(bucket_name)
            
            # Upload hook slide (always first)
            hook_path = f"{carousel_id}/1_hook.png"
            hook_bytes = base64.b64decode(hook_image)
            storage.upload(
                hook_path,
                hook_bytes,
                file_options={"content-type": "image/png"}
            )
            hook_url = storage.get_public_url(hook_path)
            slide_urls.append(hook_url)
            
            # Upload body slides (numbered starting from 2)
            for i, body_img in enumerate(body_images):
                body_path = f"{carousel_id}/{i + 2}_body.png"
                body_bytes = base64.b64decode(body_img)
                storage.upload(
                    body_path,
                    body_bytes,
                    file_options={"content-type": "image/png"}
                )
                body_url = storage.get_public_url(body_path)
                slide_urls.append(body_url)
            
            # Upload CTA slide if present (last slide)
            if cta_image:
                cta_path = f"{carousel_id}/{len(body_images) + 2}_cta.png"
                cta_bytes = base64.b64decode(cta_image)
                storage.upload(
                    cta_path,
                    cta_bytes,
                    file_options={"content-type": "image/png"}
                )
                cta_url = storage.get_public_url(cta_path)
                slide_urls.append(cta_url)
            
            return slide_urls
            
        except Exception as e:
            error_msg = f"Failed to upload images to storage: {str(e)}"
            raise ExecutionError(error_msg)
    
    def _save_images_locally(
        self,
        hook_image: str,
        body_images: List[str],
        cta_image: Optional[str],
        brand_kit_id: str,
    ) -> Path:
        """Save generated images to local filesystem with timestamped directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        brand_id_short = brand_kit_id[:8]
        output_dir = Path(settings.output_dir) / "carousels" / f"{timestamp}_{brand_id_short}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save hook slide (always first)
        hook_path = output_dir / "1_hook.png"
        with open(hook_path, "wb") as f:
            f.write(base64.b64decode(hook_image))
        
        # Save body slides (numbered starting from 2)
        for i, body_img in enumerate(body_images):
            body_path = output_dir / f"{i + 2}_body.png"
            with open(body_path, "wb") as f:
                f.write(base64.b64decode(body_img))
        
        # Save CTA slide if present (last slide)
        if cta_image:
            cta_path = output_dir / f"{len(body_images) + 2}_cta.png"
            with open(cta_path, "wb") as f:
                f.write(base64.b64decode(cta_image))
        
        return output_dir


orchestrator = Orchestrator()
