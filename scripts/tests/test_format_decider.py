import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.brand_kit import BrandKit
from app.models.pipeline import FormatDeciderInput
from app.agents.format_decider import format_decider


USER_PROMPT = "3 important reasons why you need social connection in your life"

BRAND_KIT = BrandKit(
   brand_name="",
   brand_niche="",
   brand_style="",
   customer_pain_points=[],
   product_service_desc=""
)


async def main():
    input_data = FormatDeciderInput(
        user_prompt=USER_PROMPT,
        brand_kit=BRAND_KIT
    )
    
    result = await format_decider.run(input_data)
    
    print(f"Format Type:      {result.format_type}")
    print(f"Num Body Slides:  {result.num_body_slides}")


if __name__ == "__main__":
    asyncio.run(main())

