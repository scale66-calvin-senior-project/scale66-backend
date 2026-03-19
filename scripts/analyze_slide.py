"""
Analyze carousel templates and update templates.json with descriptions.

Usage:
  python backend/scripts/analyze_slide.py carousel-1 [carousel-2 ...]
  python backend/scripts/analyze_slide.py carousel-1 --description-only

Notes:
  - Overrides existing descriptions for specified carousels
  - --description-only preserves existing hook/body/cta values
"""

import sys
import json
import base64
import argparse
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ai.gemini_service import gemini_service


class SlideAnalysis(BaseModel):
    """Analysis result for a slide category"""
    description: str


class TemplateAnalysis(BaseModel):
    """Complete analysis of a template"""
    description: str
    hook: str
    body: str
    cta: str


def read_image_base64(image_path: Path) -> str:
    """Read an image file and return base64 encoded string"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def analyze_slides(
    images_base64: List[str],
    slide_type: str,
    carousel_id: str
) -> str:
    """Analyze a collection of slides and return description"""
    if not images_base64:
        return ""
    
    prompt = f"""You are an expert social media graphic designer, capable of analyzing visual design, layout, typography, color scheme, and overall aesthetic style.
    
    Analyze these {slide_type} slide images from carousel template {carousel_id}.
    
RULES FOR ANALYSIS:
1. Focus on the design elements that make this template unique and suitable for social media carousel content. Talk about these elements and NOTHING ELSE:
    1. Balance
    2. Unity
    3. Contrast
    4. Repetition
    5. Pattern
    6. Rythym
2. AVOID describing the content of the slides, only the design elements."""

    result = gemini_service.generate_text_with_image_analysis(
        prompt=prompt,
        images_base64=images_base64,
        output_model=SlideAnalysis
    )
    
    return result.description


def analyze_template(carousel_id: str, templates_dir: Path, description_only: bool = False) -> TemplateAnalysis:
    """Analyze a complete template carousel"""
    carousel_dir = templates_dir / carousel_id
    
    if not carousel_dir.exists():
        raise ValueError(f"Carousel directory not found: {carousel_dir}")
    
    # Collect hook images
    hook_dir = carousel_dir / "hook"
    hook_images = []
    if hook_dir.exists():
        hook_files = sorted(hook_dir.glob("*.png"))
        hook_images = [read_image_base64(img) for img in hook_files]
    
    # Collect body images
    body_dir = carousel_dir / "body"
    body_images = []
    if body_dir.exists():
        body_files = sorted(body_dir.glob("*.png"))
        body_images = [read_image_base64(img) for img in body_files]
    
    # Collect cta images
    cta_dir = carousel_dir / "cta"
    cta_images = []
    if cta_dir.exists():
        cta_files = sorted(cta_dir.glob("*.png"))
        cta_images = [read_image_base64(img) for img in cta_files]
    
    # Analyze each category (skip if description_only is True)
    if description_only:
        hook_description = ""
        body_description = ""
        cta_description = ""
    else:
        hook_description = analyze_slides(hook_images, "hook", carousel_id) if hook_images else ""
        body_description = analyze_slides(body_images, "body", carousel_id) if body_images else ""
        cta_description = analyze_slides(cta_images, "cta", carousel_id) if cta_images else ""
    
    # Generate overall description

    all_images = hook_images + body_images + cta_images
    
    if not all_images:
        raise ValueError(f"No images found for carousel {carousel_id}")
    
    overall_prompt = f"""Analyze this complete carousel template {carousel_id} consisting of hook, body, and cta slides.
    
Provide a comprehensive description of the overall design system, visual consistency, and aesthetic approach.
Describe how the different slide types work together to create a cohesive carousel experience."""

    overall_result = gemini_service.generate_text_with_image_analysis(
        prompt=overall_prompt,
        images_base64=all_images[:3], 
        output_model=SlideAnalysis
    )
    
    return TemplateAnalysis(
        description=overall_result.description,
        hook=hook_description,
        body=body_description,
        cta=cta_description
    )


def update_templates_json(
    carousel_ids: List[str],
    templates_dir: Path,
    analysis_results: dict,
    description_only: bool = False
) -> None:
    """Update templates.json with analysis results"""
    templates_json_path = templates_dir / "templates.json"
    
    # Load existing templates
    if templates_json_path.exists():
        with open(templates_json_path, 'r') as f:
            data = json.load(f)
    else:
        data = {"templates": []}
    
    # Update or add templates
    template_dict = {t["id"]: t for t in data["templates"]}
    
    for carousel_id in carousel_ids:
        if carousel_id in analysis_results:
            analysis = analysis_results[carousel_id]
            
            if carousel_id in template_dict:
                # Update existing template (preserve carousel_format)
                existing_format = template_dict[carousel_id].get("carousel_format", "listicle_tips")
                update_data = {
                    "description": analysis.description,
                    "carousel_format": existing_format  # Preserve existing format
                }
                
                # Only update hook/body/cta if not description_only mode
                if not description_only:
                    update_data.update({
                        "hook": analysis.hook,
                        "body": analysis.body,
                        "cta": analysis.cta
                    })
                else:
                    # Preserve existing hook/body/cta values
                    update_data.update({
                        "hook": template_dict[carousel_id].get("hook", ""),
                        "body": template_dict[carousel_id].get("body", ""),
                        "cta": template_dict[carousel_id].get("cta", "")
                    })
                
                template_dict[carousel_id].update(update_data)
            else:
                # Add new template
                template_dict[carousel_id] = {
                    "id": carousel_id,
                    "carousel_format": "listicle_tips",  # Default format
                    "description": analysis.description,
                    "hook": analysis.hook if not description_only else "",
                    "body": analysis.body if not description_only else "",
                    "cta": analysis.cta if not description_only else ""
                }
    
    # Write back to file
    data["templates"] = list(template_dict.values())
    with open(templates_json_path, 'w') as f:
        json.dump(data, f, indent="\t")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze carousel templates and update templates.json"
    )
    parser.add_argument(
        "carousels",
        nargs="+",
        help="Carousel IDs to analyze (e.g., carousel-1 carousel-2)"
    )
    parser.add_argument(
        "--description-only",
        action="store_true",
        help="Only fill out the general description, skip hook/body/cta analysis"
    )
    
    args = parser.parse_args()
    
    # Get templates directory
    script_dir = Path(__file__).parent
    templates_dir = script_dir.parent / "templates"
    
    if not templates_dir.exists():
        print(f"Error: Templates directory not found: {templates_dir}")
        sys.exit(1)
    
    # Analyze each carousel
    analysis_results = {}
    
    for carousel_id in args.carousels:
        print(f"Analyzing {carousel_id}...")
        try:
            analysis = analyze_template(carousel_id, templates_dir, description_only=args.description_only)
            analysis_results[carousel_id] = analysis
            print(f"✓ Completed {carousel_id}")
        except Exception as e:
            print(f"✗ Error analyzing {carousel_id}: {e}")
            continue
    
    # Update templates.json
    if analysis_results:
        print("\nUpdating templates.json...")
        update_templates_json(args.carousels, templates_dir, analysis_results, description_only=args.description_only)
        print("✓ templates.json updated successfully")
    else:
        print("\nNo analysis results to update")


if __name__ == "__main__":
    main()
