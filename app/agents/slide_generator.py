from typing import List, Optional, Literal
from app.agents.base_agent import BaseAgent
from app.models.pipeline import SlideGeneratorInput, SlideGeneratorOutput
from app.services.template_service import template_service


class SlideGenerator(BaseAgent[SlideGeneratorInput, SlideGeneratorOutput]):
    """Generates slide images using AI, maintaining visual consistency across the carousel."""
    
    # Singleton pattern implementation
    _instance: Optional['SlideGenerator'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        super().__init__()
    
    async def _validate_input(self, input_data: SlideGeneratorInput) -> None:
        pass
    
    async def _execute(self, input_data: SlideGeneratorInput) -> SlideGeneratorOutput:
        # Generate hook slide (uses template as reference)
        hook_template_base64 = self._load_template_image(
            input_data.template_id, 
            input_data.hook_slide
        )
        hook_image = await self._generate_slide_image(
            input_data=input_data,
            slide_index=0,
            slide_text=input_data.hook_text,
            template_image_base64=hook_template_base64,
            previous_slide_base64=None,
            slide_type="hook",
        )
        
        # Generate body slides (each references the previous slide for consistency)
        body_template_base64 = self._load_template_image(
            input_data.template_id, 
            input_data.body_slide
        )
        
        body_images: List[str] = []
        previous_body_slide = None
        
        for i, body_text in enumerate(input_data.body_texts):
            body_image = await self._generate_slide_image(
                input_data=input_data,
                slide_index=i + 1,
                slide_text=body_text,
                template_image_base64=body_template_base64,
                previous_slide_base64=previous_body_slide,
                slide_type="body",
            )
            body_images.append(body_image)
            previous_body_slide = body_image
        
        # Generate CTA slide if needed (uses template as reference)
        cta_image = None
        if input_data.cta_slide and input_data.cta_text:
            cta_template_base64 = self._load_template_image(
                input_data.template_id, 
                input_data.cta_slide
            )
            cta_image = await self._generate_slide_image(
                input_data=input_data,
                slide_index=input_data.num_slides - 1,
                slide_text=input_data.cta_text,
                template_image_base64=cta_template_base64,
                previous_slide_base64=None,
                slide_type="cta",
            )
        
        return SlideGeneratorOutput(
            step_name="slide_generator",
            success=True,
            hook_image=hook_image,
            body_images=body_images,
            cta_image=cta_image,
        )
    
    def _load_template_image(self, template_id: str, slide_filename: str) -> str:
        """Load template image as base64 string."""
        return template_service.get_template_image_base64(template_id, slide_filename)
    
    async def _generate_slide_image(
        self,
        input_data: SlideGeneratorInput,
        slide_index: int,
        slide_text: str,
        template_image_base64: str,
        previous_slide_base64: Optional[str],
        slide_type: Literal["hook", "body", "cta"],
    ) -> str:
        """Generate a single slide image using AI with appropriate reference image."""
        has_previous_slide = previous_slide_base64 is not None
        is_body_slide = slide_type == "body"
        
        prompt = self._build_slide_prompt(
            input_data=input_data,
            slide_index=slide_index,
            slide_text=slide_text,
            has_previous_slide=has_previous_slide,
            slide_type=slide_type,
        )
        
        # Use previous slide for consistency, or template for first slide
        if has_previous_slide:
            images_to_reference = [previous_slide_base64]
        else:
            images_to_reference = [template_image_base64]
        
        return await self.gemini.generate_image_with_reference(
            prompt=prompt,
            images_base64=images_to_reference,
            image_size="1K",
        )
    
    def _get_common_avoidance_rules(self) -> str:
        """Returns common rules about what to avoid in slide generation."""
        return """
WHAT TO AVOID:
- Broken letters
- Broken text
- Broken images
- Broken formatting"""
    
    def _build_slide_prompt(
        self,
        input_data: SlideGeneratorInput,
        slide_index: int,
        slide_text: str,
        has_previous_slide: bool = False,
        slide_type: Literal["hook", "body", "cta"] = "body",
    ) -> str:
        common_rules = self._get_common_avoidance_rules()
        
        if has_previous_slide:
            return f"""Create a carousel slide by EXACTLY replicating the previous slide's visual style.

RULES FOR USING THE PREVIOUS SLIDE:
1. PRESERVE EXACTLY the same visual style and formatting from the previous slide.
2. ONLY Change the content of the slide to match the new content.

CONTENT RULES:
Use PRIMARILY this text: {slide_text}{f"""

NUMBERING RULES:
PRIMARY RULE: NEVER ADD NUMBERING UNLESS THE PREVIOUS SLIDE HAS A NUMBERING FORMAT.
- Continue the numbering sequence from previous slide (IF PRESENT)
- Use number (IF NEEDED): {slide_index}
- Match exact numbering style and placement""" if slide_type == "body" else ""}
{common_rules}"""
        else:
            return f"""Create a carousel slide using the template as style reference.

RULES FOR USING THE TEMPLATE:
1. PRESERVE the template's exact visual style and formatting while removing any branding.
2. REMOVE ALL branding such as logos, social handles, website URLs, names, dates, etc.

PRESERVATION RULES:
1. Styling information should be preserved, capturing the nuance and details of:
    - Color palette
    - Typography, font styles, and sizes
    - Indicators to move on to the next slide
    - Layout structure and hierarchy
Preserve every aspect of these elements, DO NOT change, add, or deviate from these elements.
2. For a TEMPLATE that has a background image:
    - IF background image matches the CONTENT, PRESERVE IT.
    - IF background image is similar to the CONTENT, make slight changes to the background image to match the CONTENT.
    - IF background image is DOES NOT match the CONTENT, CHANGE the background image to a relevant one, exactly preserving the style, colors and layout of the original background image.
 The content of the background image can be changed to match the CONTENT, howeverm the style, colors and layout of the original background image should be EXPLICITLY PRESERVED.

CONTENT RULES:
Use PRIMARILY this text: {slide_text}{f"""

NUMBERING RULES:
- ONLY add numbering if template shows clear numbering format
- If present, use number: {slide_index}
- Match template's numbering style exactly""" if slide_type == "body" else ""}
{common_rules}"""


slide_generator = SlideGenerator()
