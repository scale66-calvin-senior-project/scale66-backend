from typing import List, Optional
from pydantic import Field
from app.models.brand_kit import BrandKit
from app.models.common import BasePipelineStep


class OrchestratorInput(BasePipelineStep):
    brand_kit_id: str = Field(...)
    user_prompt: str = Field(...)
    user_id: Optional[str] = Field(None, description="User ID for storage organization")


class OrchestratorOutput(BasePipelineStep):
    carousel_id: str = Field(...)
    carousel_slides_urls: List[str] = Field(...)
    hook_text: str = Field(..., description="Hook slide caption text")
    body_texts: List[str] = Field(..., description="Body slide caption texts")
    cta_text: Optional[str] = Field(None, description="CTA slide caption text if exists")
    template_id: str = Field(..., description="Template ID used")
    format_type: str = Field(..., description="Format type selected")
    num_body_slides: int = Field(..., description="Number of body slides generated")
    include_cta: bool = Field(False, description="Whether CTA slide was included")


class FormatDeciderInput(BasePipelineStep):
    user_prompt: str = Field(...)
    brand_kit: BrandKit = Field(...)


class FormatDeciderOutput(BasePipelineStep):
    format_type: str = Field(...)
    num_body_slides: int = Field(..., ge=1, le=8, description="Number of body slides (content slides)")
    include_cta: bool = Field(False, description="Whether to include a CTA slide")


class TemplateDeciderInput(BasePipelineStep):
    user_prompt: str = Field(...)
    brand_kit: BrandKit = Field(...)
    format_type: str = Field(...)
    num_body_slides: int = Field(..., ge=1, le=8, description="Number of body slides")
    include_cta: bool = Field(..., description="Whether to include a CTA slide")


class TemplateDeciderOutput(BasePipelineStep):
    template_id: str = Field(...)
    hook_slide: str = Field(..., description="Hook slide filename (e.g., '1_hook.png')")
    body_slide: str = Field(..., description="Selected body slide filename (e.g., '1_body.png')")
    cta_slide: Optional[str] = Field(None, description="CTA slide filename if exists (e.g., '1_cta.png')")


class CaptionGeneratorInput(BasePipelineStep):
    format_type: str = Field(...)
    user_prompt: str = Field(...)
    brand_kit: BrandKit = Field(...)
    num_body_slides: int = Field(..., ge=1, le=8, description="Number of body slides")
    template_id: str = Field(..., description="Template ID for future template access")
    hook_slide: str = Field(..., description="Hook slide filename")
    body_slide: str = Field(..., description="Body slide filename")
    cta_slide: Optional[str] = Field(None, description="CTA slide filename if exists")
    
    @property
    def num_slides(self) -> int:
        """Total slides: 1 hook + num_body_slides + (1 if cta else 0)"""
        return 1 + self.num_body_slides + (1 if self.cta_slide else 0)


class CaptionGeneratorOutput(BasePipelineStep):
    hook_text: str = Field(..., description="Hook slide caption text")
    body_texts: List[str] = Field(..., description="Body slide caption texts")
    cta_text: Optional[str] = Field(None, description="CTA slide caption text if exists")


class SlideGeneratorInput(BasePipelineStep):
    format_type: str = Field(...)
    num_body_slides: int = Field(..., ge=1, le=8, description="Number of body slides")
    brand_kit: BrandKit = Field(...)
    user_prompt: str = Field(...)
    hook_text: str = Field(..., description="Hook slide caption text")
    body_texts: List[str] = Field(..., description="Body slide caption texts")
    cta_text: Optional[str] = Field(None, description="CTA slide caption text if exists")
    template_id: str = Field(...)
    hook_slide: str = Field(..., description="Hook slide filename")
    body_slide: str = Field(..., description="Body slide filename")
    cta_slide: Optional[str] = Field(None, description="CTA slide filename if exists")
    
    @property
    def num_slides(self) -> int:
        """Total slides: 1 hook + num_body_slides + (1 if cta else 0)"""
        return 1 + self.num_body_slides + (1 if self.cta_slide else 0)


class SlideGeneratorOutput(BasePipelineStep):
    hook_image: str = Field(..., description="Hook slide image (base64)")
    body_images: List[str] = Field(..., description="Body slide images (base64)")
    cta_image: Optional[str] = Field(None, description="CTA slide image (base64) if exists")
