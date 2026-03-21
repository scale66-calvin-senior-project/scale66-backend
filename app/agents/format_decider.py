from typing import Optional

from app.agents.base_agent import BaseAgent, ExecutionError
from app.models.pipeline import FormatDeciderInput, FormatDeciderOutput
from app.models.structured import ClaudeFormatSelectionOutput
from app.constants import FORMAT_DESCRIPTIONS
from app.services.template_service import template_service


class FormatDecider(BaseAgent[FormatDeciderInput, FormatDeciderOutput]):
    """Decides the optimal carousel format and number of body slides based on user prompt."""
    
    # Singleton pattern implementation
    _instance: Optional['FormatDecider'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        super().__init__()
    
    async def _validate_input(self, input_data: FormatDeciderInput) -> None:
        pass
    
    async def _execute(self, input_data: FormatDeciderInput) -> FormatDeciderOutput:
        prompt = self._build_prompt(input_data)

        format_output = await self.anthropic.generate_structured_output(
            prompt=prompt,
            output_model=ClaudeFormatSelectionOutput,
            max_tokens=500,
            temperature=0.3,
        )

        # Ensure the selected format has templates; fall back to the first available format if not
        available_format_names = {t.carousel_format for t in template_service.list_all_templates()}
        format_type = format_output.format_type
        if format_type not in available_format_names:
            if not available_format_names:
                raise ExecutionError("No carousel formats available — no templates loaded")
            format_type = next(iter(available_format_names))

        return FormatDeciderOutput(
            step_name="format_decider",
            success=True,
            format_type=format_type,
            num_body_slides=format_output.num_body_slides,
            include_cta=False,
        )
    
    def _build_prompt(self, input_data: FormatDeciderInput) -> str:
        # Only include formats that have at least one template in the template service
        available_format_names = {t.carousel_format for t in template_service.list_all_templates()}

        # Build formatted list of available formats with descriptions
        format_list = "\n".join([
            f"### {fmt.value}\n{desc}"
            for fmt, desc in FORMAT_DESCRIPTIONS.items()
            if fmt.value in available_format_names
        ])

        if not format_list:
            raise ExecutionError("No carousel formats available — no templates loaded")
        
        return f"""You are an expert social media marketing strategist selecting the optimal carousel format for a CONTENT REQUEST.

CONTENT REQUEST:
"{input_data.user_prompt}"

HOW TO CHOOSE carousel format:
    1. EXAMINE the list of AVAILABLE FORMATS and compare the CONTENT REQUEST to the KEY CRITERIA of each format.
    2. SELECT the AVAILABLE FORMAT that meets the most criteria.
        - YOU MUST select a format from the list of AVAILABLE FORMATS. IF no format meets the criteria, pick the closest format that meets the most criteria.

HOW TO CHOOSE number of body slides:
    - IF the CONTENT REQUEST is explicit about the number of body slides, use that number.
        - NOTE: The number of body slides is NOT total slides.
    - IF THE CONTENT REQUEST is not explicit about the number of body slides, pick the ideal number of body slides based on the judgement of a social media expert. 
        - THE NUMBER OF BODY SLIDES SHOULD BE BETWEEN 1 AND 8.

---

AVAILABLE FORMATS:
{format_list}

"""


format_decider = FormatDecider()

