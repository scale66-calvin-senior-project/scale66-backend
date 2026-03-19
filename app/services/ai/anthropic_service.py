from typing import Optional, TypeVar, Type
from pydantic import BaseModel
from anthropic import AsyncAnthropic
from app.core.config import settings

T = TypeVar('T', bound=BaseModel)


class AnthropicServiceError(Exception):
    pass


class AnthropicService:
    _instance: Optional['AnthropicService'] = None
    _client: Optional[AsyncAnthropic] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            try:
                self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            except Exception as e:
                raise AnthropicServiceError(f"Failed to initialize Anthropic client: {e}")
    
    async def generate_structured_output(
        self,
        prompt: str,
        output_model: Type[T],
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> T:
        try:
            response = await self._client.beta.messages.parse(
                model=settings.anthropic_model,
                max_tokens=max_tokens,
                temperature=temperature,
                betas=["structured-outputs-2025-11-13"],
                messages=[{"role": "user", "content": prompt}],
                output_format=output_model,
            )
            
            if response.stop_reason == "refusal":
                raise AnthropicServiceError(
                    "Claude refused the request. The output may not match the schema."
                )
            
            if response.stop_reason == "max_tokens":
                raise AnthropicServiceError(
                    "Response exceeded max_tokens limit. Increase max_tokens and retry."
                )
            
            parsed_output = response.parsed_output
            return parsed_output
        
        except AnthropicServiceError:
            raise
        except Exception as e:
            raise AnthropicServiceError(f"Failed to generate structured output: {e}")


anthropic_service = AnthropicService()
