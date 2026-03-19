import base64
from typing import Optional, List, TypeVar, Type
from pydantic import BaseModel
from google import genai
from google.genai import types

from app.core.config import settings

T = TypeVar('T', bound=BaseModel)


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
    
    def generate_text_with_image_analysis(
        self,
        prompt: str,
        images_base64: List[str],
        output_model: Type[T],
    ) -> T:
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
                response_mime_type="application/json",
                response_json_schema=output_model.model_json_schema(),
            )
            
            response = self._client.models.generate_content(
                model=settings.gemini_text_model,
                contents=types.Content(
                    role="user",
                    parts=parts
                ),
                config=config
            )
            
            # Extract text from response - handle different response structures
            response_text = None
            if hasattr(response, 'text') and response.text:
                response_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text = part.text
                                break
            
            if response_text is None:
                raise GeminiServiceError(
                    f"No text found in Gemini response. Response structure: {type(response)}, "
                    f"has text attr: {hasattr(response, 'text')}, "
                    f"candidates: {hasattr(response, 'candidates') and len(response.candidates) if hasattr(response, 'candidates') else 0}"
                )
            
            parsed_output = output_model.model_validate_json(response_text)
            return parsed_output
                
        except GeminiServiceError:
            raise
        except Exception as e:
            raise GeminiServiceError(f"Failed to analyze images with structured output: {e}")


gemini_service = GeminiService()
