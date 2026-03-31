import base64
from typing import Optional, List
from google import genai
from google.genai import types

from app.core.config import settings


class GeminiServiceError(Exception):
    pass


class GeminiService:
    _instance: Optional['GeminiService'] = None
    _client: Optional[genai.Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self): 
        if self._client is None:
            try:
                self._client = genai.Client(api_key=settings.gemini_api_key)
            except Exception as e:
                raise GeminiServiceError(f"Failed to initialize Gemini client: {e}")
    
    async def generate_image_with_reference(
        self,
        prompt: str,
        images_base64: List[str],
        aspect_ratio: str = "4:5",
        image_size: str = "1K",
    ) -> str:
        try:
            parts = []
            
            for img_b64 in images_base64:
                img_bytes = base64.b64decode(img_b64)
                parts.append(
                    types.Part(
                        inline_data=types.Blob(
                            mime_type="image/png",
                            data=img_bytes
                        )
                    )
                )
            
            parts.append(types.Part(text=prompt))
            
            config = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=image_size,
                )
            )
            
            response = self._client.models.generate_content(
                model=settings.gemini_image_model,
                contents=types.Content(
                    role="user",
                    parts=parts
                ),
                config=config
            )
            
            image_part = None
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_part = part
                    break
            
            if not image_part:
                raise GeminiServiceError("No image found in Gemini response")
            
            image_bytes = image_part.inline_data.data
            return base64.b64encode(image_bytes).decode("utf-8")
                
        except GeminiServiceError:
            raise
        except Exception as e:
            raise GeminiServiceError(f"Failed to generate image from input: {e}")


gemini_service = GeminiService()
