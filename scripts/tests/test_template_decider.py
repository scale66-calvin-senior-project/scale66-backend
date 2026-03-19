import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.brand_kit import BrandKit
from app.models.pipeline import TemplateDeciderInput
from app.agents.template_decider import template_decider


USER_PROMPT = "8 things to prepare when going camping"

BRAND_KIT = BrandKit(
   brand_name="",
   brand_niche="",
   brand_style="",
   customer_pain_points=[],
   product_service_desc=""
)

FORMAT_TYPE = "listicle_tips"
NUM_BODY_SLIDES = 5
INCLUDE_CTA = False


async def main():
    input_data = TemplateDeciderInput(
        user_prompt=USER_PROMPT,
        brand_kit=BRAND_KIT,
        format_type=FORMAT_TYPE,
        num_body_slides=NUM_BODY_SLIDES,
        include_cta=INCLUDE_CTA,
    )
    
    result = await template_decider.run(input_data)
    
    print(f"Template ID:  {result.template_id}")


if __name__ == "__main__":
    asyncio.run(main())

