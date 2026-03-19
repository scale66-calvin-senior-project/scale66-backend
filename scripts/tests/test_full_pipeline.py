import asyncio
import sys
import base64
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.brand_kit import BrandKit
from app.core.config import settings
from app.models.pipeline import (
    FormatDeciderInput,
    TemplateDeciderInput,
    CaptionGeneratorInput,
    SlideGeneratorInput,
)
from app.agents.format_decider import format_decider
from app.agents.template_decider import template_decider
from app.agents.caption_generator import caption_generator
from app.agents.slide_generator import slide_generator


USER_PROMPT = "Create a carousel talking about 3 important reasons for social media marketing as a solopreneur"

BRAND_KIT = BrandKit(
    brand_name="Scale66",
    brand_niche="Social Media Marketing for online businesses",
    brand_style="professional",
    customer_pain_points=[
        "I don't know how to get started with social media marketing",
        "I don't have the time to manage social media",
        "I don't have the budget to hire a marketing agency"
    ],
    product_service_desc="Helps speed up the process of social media marketing for brand awareness at the fraction of the cost of a marketing agency"
)


async def main():
    # Step 1: Format Decision
    format_result = await format_decider.run(
        FormatDeciderInput(
            user_prompt=USER_PROMPT,
            brand_kit=BRAND_KIT,
        )
    )
    
    # Step 2: Template Decision
    template_result = await template_decider.run(
        TemplateDeciderInput(
            user_prompt=USER_PROMPT,
            brand_kit=BRAND_KIT,
            format_type=format_result.format_type,
            num_body_slides=format_result.num_body_slides,
            include_cta=format_result.include_cta,
        )
    )
    
    # Step 3: Caption Generation
    caption_result = await caption_generator.run(
        CaptionGeneratorInput(
            format_type=format_result.format_type,
            user_prompt=USER_PROMPT,
            brand_kit=BRAND_KIT,
            num_body_slides=format_result.num_body_slides,
            template_id=template_result.template_id,
            hook_slide=template_result.hook_slide,
            body_slide=template_result.body_slide,
            cta_slide=template_result.cta_slide,
        )
    )
    
    # Step 4: Slide Generation
    slide_result = await slide_generator.run(
        SlideGeneratorInput(
            format_type=format_result.format_type,
            num_body_slides=format_result.num_body_slides,
            brand_kit=BRAND_KIT,
            user_prompt=USER_PROMPT,
            hook_text=caption_result.hook_text,
            body_texts=caption_result.body_texts,
            cta_text=caption_result.cta_text,
            template_id=template_result.template_id,
            hook_slide=template_result.hook_slide,
            body_slide=template_result.body_slide,
            cta_slide=template_result.cta_slide,
        )
    )
    
    print("FULL PIPELINE OUTPUT")
    
    print(f"\n  Format Type:       {format_result.format_type}")
    print(f"  Template ID:       {template_result.template_id}")
    print(f"  Num Body Slides:   {format_result.num_body_slides}")
    print(f"  Include CTA:       {format_result.include_cta}")
    print(f"  Total Slides:      {1 + format_result.num_body_slides + (1 if format_result.include_cta else 0)}")
    
    print("\n  Captions:")
    print(f"\n    Hook Text:")
    print(f"      {caption_result.hook_text}")
    
    print(f"\n    Body Texts:")
    for i, text in enumerate(caption_result.body_texts, 1):
        print(f"      {i}. {text}")
    
    if caption_result.cta_text:
        print(f"\n    CTA Text:")
        print(f"      {caption_result.cta_text}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    carousel_dir = Path(settings.output_dir) / "carousels" / f"carousel_{timestamp}"
    carousel_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n  Carousel Folder:   {carousel_dir}")
    print(f"\n  Saved Images:")
    
    # Save hook
    hook_path = carousel_dir / "1_hook.png"
    hook_path.write_bytes(base64.b64decode(slide_result.hook_image))
    print(f"    1. {hook_path}")
    
    # Save body slides
    for i, body_image in enumerate(slide_result.body_images, 2):
        body_path = carousel_dir / f"{i}_body.png"
        body_path.write_bytes(base64.b64decode(body_image))
        print(f"    {i}. {body_path}")
    
    # Save CTA if exists
    if slide_result.cta_image:
        cta_num = len(slide_result.body_images) + 2
        cta_path = carousel_dir / f"{cta_num}_cta.png"
        cta_path.write_bytes(base64.b64decode(slide_result.cta_image))
        print(f"    {cta_num}. {cta_path}")
    
    if slide_result.error_message:
        print(f"\n  Error Message:     {slide_result.error_message}")


if __name__ == "__main__":
    asyncio.run(main())
