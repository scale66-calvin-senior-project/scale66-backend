from typing import Optional

from app.agents.base_agent import BaseAgent
from app.models.pipeline import CaptionGeneratorInput, CaptionGeneratorOutput
from app.models.structured import ClaudeSlidesTextOutput
from app.constants import FORMAT_TEXT_GUIDES


class CaptionGenerator(BaseAgent[CaptionGeneratorInput, CaptionGeneratorOutput]):
    """Generates hook and body slide captions using AI."""
    
    # Singleton pattern implementation
    _instance: Optional['CaptionGenerator'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        super().__init__()
    
    async def _validate_input(self, input_data: CaptionGeneratorInput) -> None:
        pass
    
    async def _execute(self, input_data: CaptionGeneratorInput) -> CaptionGeneratorOutput:
        prompt = self._build_prompt(input_data)
        
        output = await self.anthropic.generate_structured_output(
            prompt=prompt,
            output_model=ClaudeSlidesTextOutput,
        )
        
        # Ensure body_texts matches expected count (pad or truncate if needed)
        expected_body_count = input_data.num_body_slides
        body_texts = output.body_texts
        if len(body_texts) != expected_body_count:
            if len(body_texts) < expected_body_count:
                while len(body_texts) < expected_body_count:
                    body_texts.append("[Content continues...]")
            else:
                body_texts = body_texts[:expected_body_count]
        
        return CaptionGeneratorOutput(
            step_name="caption_generator",
            success=True,
            hook_text=output.hook_text,
            body_texts=body_texts,
        )
    
    def _build_prompt(self, input_data: CaptionGeneratorInput) -> str:
        """Build combined prompt for hook and body slide generation."""
        format_text_guide = FORMAT_TEXT_GUIDES.get(input_data.format_type, "")
        
        return f"""You are an expert strategist and caption text writer for social media carousel slides.

HOW TO CREATE CAPTIONS:
    1. CREATE the captions for each section, PRIMARILY using the FORMAT TEXT GUIDE below.
    3. Additionally, use the USER REQUEST if the user has any requests for the captions.

FORMAT TYPE: {input_data.format_type}
FORMAT TEXT GUIDE:{format_text_guide}

USER REQUEST: {input_data.user_prompt}

Generate:
1. One hook slide caption text
2. {input_data.num_body_slides} body slide caption texts
"""


caption_generator = CaptionGenerator()
