import asyncio
import sys
import base64
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.brand_kit import BrandKit
from app.core.config import settings
from app.models.pipeline import SlideGeneratorInput
from app.agents.slide_generator import slide_generator


USER_PROMPT = "A carousel talking about the benefits of social connection"

BRAND_KIT = BrandKit(
    brand_name="Hiver",
    brand_niche="Event discovery and social connection platform",
    brand_style="vibrant and community-driven",
    customer_pain_points=[
        "Struggling to find local events and activities happening nearby",
        "Feeling isolated and lacking meaningful in-person social connections",
        "Event organizers having difficulty reaching their target audience"
    ],
    product_service_desc="An app that connects businesses organizing events with people looking to attend, fostering genuine in-person social connections and building vibrant local communities"
)

FORMAT_TYPE = "listicle_tips"
NUM_BODY_SLIDES = 3
TEMPLATE_ID = "carousel-3"

HOOK_TEXT = "3 things you never knew about social connection"

BODY_TEXTS = [
    "Strong social connections can increase your lifespan by up to 50 percent, making social interaction as important to longevity as quitting smoking or exercising regularly",
    "Regular in-person social interaction reduces stress hormones and inflammation, lowering your risk of heart disease, depression, and cognitive decline as you age",
    "Face-to-face social connections boost your immune system by releasing feel-good hormones that help your body fight off illness and recover faster from health challenges",
]


async def main():
    input_data = SlideGeneratorInput(
        user_prompt=USER_PROMPT,
        brand_kit=BRAND_KIT,
        format_type=FORMAT_TYPE,
        num_body_slides=NUM_BODY_SLIDES,
        template_id=TEMPLATE_ID,
        hook_text=HOOK_TEXT,
        body_texts=BODY_TEXTS,
        hook_slide="1_hook.png",
        body_slide="1_body.png",
    )
    
    result = await slide_generator.run(input_data)
    
    print("SLIDE GENERATOR OUTPUT")
    
    print(f"\n  Format Type:       {input_data.format_type}")
    print(f"  Template ID:       {input_data.template_id}")
    print(f"  Num Body Slides:   {input_data.num_body_slides}")
    print(f"  Total Slides:      {input_data.num_slides}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    carousel_dir = Path(settings.output_dir) / "carousels" / f"carousel_{timestamp}"
    carousel_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n  Carousel Folder:   {carousel_dir}")
    print(f"\n  Saved Images:")
    
    # Save hook
    hook_path = carousel_dir / "1_hook.png"
    hook_path.write_bytes(base64.b64decode(result.hook_image))
    print(f"    1. {hook_path}")
    
    # Save body slides
    for i, body_image in enumerate(result.body_images, 2):
        body_path = carousel_dir / f"{i}_body.png"
        body_path.write_bytes(base64.b64decode(body_image))
        print(f"    {i}. {body_path}")
    
    # Save CTA if exists
    if result.cta_image:
        cta_num = len(result.body_images) + 2
        cta_path = carousel_dir / f"{cta_num}_cta.png"
        cta_path.write_bytes(base64.b64decode(result.cta_image))
        print(f"    {cta_num}. {cta_path}")
    
    if result.error_message:
        print(f"\n  Error Message:     {result.error_message}")


if __name__ == "__main__":
    asyncio.run(main())

