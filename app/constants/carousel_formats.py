"""
Carousel Format Definitions and Text Generation Guides.

This module contains all format-related configuration for carousel generation:
- CarouselFormat enum defining available formats
- FORMAT_DESCRIPTIONS for format selection prompts
- FORMAT_TEXT_GUIDES for caption generation prompts
"""

from typing import Dict
from enum import Enum


class CarouselFormat(str, Enum):
    LISTICLE_TIPS = "listicle_tips"
    EDUCATIONAL_TUTORIAL = "educational_tutorial"
    DATA_INSIGHT_AUTHORITY = "data_insight_authority"


FORMAT_DESCRIPTIONS: Dict[str, str] = {
    CarouselFormat.LISTICLE_TIPS: """Numbered collection of discrete, standalone tips/insights, one per slide.
KEY CRITERIA (ALL must apply):
1. Content breaks into discrete, standalone items (each tip works independently)
2. Items are relatively unrelated to each other (no narrative thread required)
3. Natural numbered framing ("X ways to...", "X tips for...", "X mistakes...")
4. Each slide delivers complete value without needing other slides

NOT SUITABLE FOR:
- Sequential stories or journeys with a narrative arc
- Before/after transformations requiring context buildup
- Deep-dive explanations of a single concept
- Personal stories or case studies
- Content requiring progressive revelation""",

    CarouselFormat.EDUCATIONAL_TUTORIAL: """Step-by-step walkthrough to solving a problem in someone's life.
KEY CRITERIA (ALL must apply):
1. Content follows a sequential, progressive structure (each step builds on previous steps)
2. Focuses on solving a specific problem or achieving a specific outcome
3. Steps are logically ordered and interconnected (later steps depend on earlier ones)
4. Each slide represents a distinct step in the problem-solving process
5. Content guides the reader through a complete journey from problem to solution

NOT SUITABLE FOR:
- Standalone tips or insights that work independently
- Numbered lists of unrelated items
- Content where order doesn't matter
- General advice without a clear problem-solution structure
- Tips that don't build on each other sequentially""",

    CarouselFormat.DATA_INSIGHT_AUTHORITY: """Carousel built around research, statistics, trend data, or analytical findings with clear visualization.
KEY CRITERIA (ALL must apply):
1. Content is built around genuine research, statistics, trend data, or analytical findings (no fabrication)
2. Requires actual data or research to back all claims and insights
3. Structure follows: bold headline statistic → context/methodology → supporting data points visualized → implications/analysis → actionable conclusions → CTA
4. Establishes thought leadership and authority through substantiated insights
5. Data visualization is central to the content presentation

NOT SUITABLE FOR:
- Content without actual data, research, or statistics to support claims
- Fabricated or made-up statistics or research findings
- Opinion-based content without data backing
- Emotional content without data foundation
- General tips or advice not supported by research
- Content where data visualization isn't central to the message"""
}


FORMAT_TEXT_GUIDES: Dict[str, str] = {
    CarouselFormat.LISTICLE_TIPS: """
    HOOK GUIDELINES:
    1. The hook should be a clear offer of value that immediately singles out the relevant audience and their pain points.
    
    BODY GUIDELINES:
    1. The body provides the value in the form of a tip or insight.
    2. The body should be a standalone tip that doesn't have a narrative thread or context that wouldn't be available to the average audience.
    """,
}