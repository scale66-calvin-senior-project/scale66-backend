from typing import List, Optional

from app.agents.base_agent import BaseAgent
from app.models.pipeline import TemplateDeciderInput, TemplateDeciderOutput
from app.models.structured import ClaudeTemplateSelectionOutput
from app.services.template_service import template_service, TemplateMetadata


class TemplateDecider(BaseAgent[TemplateDeciderInput, TemplateDeciderOutput]):
    """Selects the optimal template for a given format and content request."""
    
    # Singleton pattern implementation
    _instance: Optional['TemplateDecider'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        super().__init__()
    
    async def _validate_input(self, input_data: TemplateDeciderInput) -> None:
        pass
    
    async def _execute(self, input_data: TemplateDeciderInput) -> TemplateDeciderOutput:
        matching_templates = template_service.get_templates_for_format(input_data.format_type)
        
        prompt = self._build_prompt(
            input_data=input_data,
            templates=matching_templates
        )
        
        template_output = await self.anthropic.generate_structured_output(
            prompt=prompt,
            output_model=ClaudeTemplateSelectionOutput,
            max_tokens=500,
            temperature=0.3,
        )
        
        # Validate selected template exists, fallback to first available if not
        selected_template_id = template_output.template_id
        selected_template = template_service.get_template(selected_template_id)
        if not selected_template:
            selected_template = matching_templates[0]
            selected_template_id = selected_template.id
        
        # Include CTA slide filename only if CTA is requested and available
        cta_slide_filename = None
        if input_data.include_cta and selected_template.cta_slide:
            cta_slide_filename = selected_template.cta_slide
        
        return TemplateDeciderOutput(
            step_name="template_decider",
            success=True,
            template_id=selected_template_id,
            hook_slide=selected_template.hook_slide,
            body_slide=selected_template.body_slide,
            cta_slide=cta_slide_filename,
        )
    
    def _build_prompt(
        self,
        input_data: TemplateDeciderInput,
        templates: List[TemplateMetadata]
    ) -> str:
        # Build formatted list of template descriptions for AI selection
        template_details = []
        for t in templates:
            template_detail = f"""Template: {t.id}
   - Overview: {t.description}"""
            template_details.append(template_detail)
        
        template_info = "\n\n".join(template_details)
        valid_ids = [t.id for t in templates]
        
        return f"""You are an expert social media designer selecting the optimal TEMPLATE according to the CONTENT REQUEST.
    
CONTENT REQUEST: "{input_data.user_prompt}"
CAROUSEL FORMAT: {input_data.format_type}

HOW TO CHOOSE template:
    1. EXAMINE the list of AVAILABLE TEMPLATES and fit each one to the CONTENT REQUEST. The templates are all for the given CAROUSEL FORMAT.
    2. SELECT the TEMPLATE that best fits the CONTENT REQUEST.
        - YOU MUST select a template from the list of AVAILABLE TEMPLATES. IF no template fits the criteria, pick the closest template that fits the most criteria.
        - the valid template ids are: {valid_ids}
---

AVAILABLE TEMPLATES WITH DETAILED DESCRIPTIONS:

{template_info}
"""


template_decider = TemplateDecider()
