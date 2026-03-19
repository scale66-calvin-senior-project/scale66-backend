from typing import List
from pydantic import BaseModel


class BrandKit(BaseModel):
    brand_name: str
    brand_niche: str
    brand_style: str
    customer_pain_points: List[str]
    product_service_desc: str
