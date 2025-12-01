"""
Image analysis utilities.

Functions for analyzing images and finding visual patterns.
All functions are async for non-blocking operation.
"""

import json
import os
import sys
from uuid import UUID

from openai import (
    APIConnectionError,
    APIError,
    AsyncOpenAI,
    RateLimitError,
)

from .types import ImageAnalysisInput, ImageAnalysisOutput

DEFAULT_MODEL = 'gpt-4o-mini'

FALLBACK_ANALYSIS = ImageAnalysisOutput(
    visual_similarities="Unable to analyze visual similarities (AI service unavailable).",
    differentiation_tags=["analysis_unavailable"],
    success_factors="Analysis could not be generated.",
    model_used=DEFAULT_MODEL,
)


async def analyze_winning_images(input_data: ImageAnalysisInput) -> ImageAnalysisOutput:
    """
    Analyze winning images to find visual similarities that differentiate them.

    Uses OpenAI to compare descriptions of top-performing and lower-performing
    images to identify what visual elements make certain images more successful.

    Args:
        input_data: ImageAnalysisInput with winning and losing image descriptions

    Returns:
        ImageAnalysisOutput with visual similarities, tags, and success factors
    """
    if 'OPENAI_API_KEY' not in os.environ:
        print(
            '[warn] OPENAI_API_KEY not set, using fallback analysis.',
            file=sys.stderr,
        )
        return ImageAnalysisOutput(
            visual_similarities=FALLBACK_ANALYSIS.visual_similarities,
            differentiation_tags=FALLBACK_ANALYSIS.differentiation_tags,
            success_factors=FALLBACK_ANALYSIS.success_factors,
            model_used=input_data.model,
        )

    client = AsyncOpenAI()

    # Build context for winning images
    winning_context = []
    for i, (image_id, description) in enumerate(input_data.winning_image_descriptions, 1):
        winning_context.append(f"Winner {i} (ID: {str(image_id)[:8]}):\n{description}")

    # Build context for losing images
    losing_context = []
    for i, (image_id, description) in enumerate(input_data.losing_image_descriptions, 1):
        losing_context.append(f"Lower Performer {i} (ID: {str(image_id)[:8]}):\n{description}")

    system_prompt = """You are an expert visual analyst specializing in advertising effectiveness.
Your task is to compare high-performing and lower-performing ad images to identify:
1. What visual elements the winning images share that the others lack
2. Specific, actionable characteristics that contribute to success
3. Patterns that can be applied to future image generation

Focus on concrete visual attributes like:
- Color palettes and lighting
- Composition and framing
- Subject positioning and body language
- Background and environment
- Product visibility and prominence
- Overall mood and aesthetic

Respond with valid JSON only."""

    user_prompt = f"""Analyze these ad image descriptions to identify what makes the winners successful.

TOP-PERFORMING IMAGES:
{chr(10).join(winning_context)}

LOWER-PERFORMING IMAGES:
{chr(10).join(losing_context)}

Compare the visual characteristics and identify:
1. What do the winning images have in common that the lower performers lack?
2. What specific visual elements contribute to their success?
3. What actionable tags summarize these success factors?

Return a JSON object with this structure:
{{
    "visual_similarities": "<detailed description of what visual elements the winning images share that differentiate them from the lower performers>",
    "differentiation_tags": ["<tag1>", "<tag2>", ...],
    "success_factors": "<explanation of why these visual elements likely contributed to better performance>"
}}

The differentiation_tags should be concise (2-4 words each) and actionable, like:
- "warm color palette"
- "close-up framing"
- "dynamic poses"
- "clean backgrounds"
- "strong lighting contrast"
"""

    try:
        response = await client.chat.completions.create(
            model=input_data.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            response_format={'type': 'json_object'},
            temperature=0.7,
            max_tokens=1500,
        )

        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)

        return ImageAnalysisOutput(
            visual_similarities=result.get('visual_similarities', ''),
            differentiation_tags=result.get('differentiation_tags', []),
            success_factors=result.get('success_factors', ''),
            model_used=input_data.model,
        )

    except (RateLimitError, APIConnectionError, APIError) as e:
        print(
            f'[warn] OpenAI API error ({type(e).__name__}): {e}. Using fallback.',
            file=sys.stderr,
        )
        return ImageAnalysisOutput(
            visual_similarities=FALLBACK_ANALYSIS.visual_similarities,
            differentiation_tags=FALLBACK_ANALYSIS.differentiation_tags,
            success_factors=FALLBACK_ANALYSIS.success_factors,
            model_used=input_data.model,
        )

    except (json.JSONDecodeError, KeyError) as e:
        print(
            f'[warn] Failed to parse analysis response: {e}. Using fallback.',
            file=sys.stderr,
        )
        return ImageAnalysisOutput(
            visual_similarities=FALLBACK_ANALYSIS.visual_similarities,
            differentiation_tags=FALLBACK_ANALYSIS.differentiation_tags,
            success_factors=FALLBACK_ANALYSIS.success_factors,
            model_used=input_data.model,
        )

    except Exception as e:
        print(
            f'[warn] Unexpected error analyzing images: {e}. Using fallback.',
            file=sys.stderr,
        )
        return ImageAnalysisOutput(
            visual_similarities=FALLBACK_ANALYSIS.visual_similarities,
            differentiation_tags=FALLBACK_ANALYSIS.differentiation_tags,
            success_factors=FALLBACK_ANALYSIS.success_factors,
            model_used=input_data.model,
        )


def select_top_images_by_score(
    image_analytics: list[tuple[UUID, dict]],
    top_n: int = 2,
) -> tuple[list[UUID], list[UUID]]:
    """
    Select top N images based on composite analytics score.

    Args:
        image_analytics: List of (image_id, analytics_dict) tuples
        top_n: Number of top images to select

    Returns:
        Tuple of (top_image_ids, bottom_image_ids)
    """
    scored_images = []

    for image_id, analytics in image_analytics:
        # Composite scoring:
        # - Interactions: 40% (both count and rate)
        # - Conversion value: 30%
        # - Conversion rate: 20%
        # - CTR: 10%

        interaction_score = (
            analytics.get('interaction_rate', 0) * 0.6 +
            (analytics.get('interactions', 0) / 1000.0) * 0.4
        )
        conversion_value_score = min(analytics.get('conversion_value', 0) / 1000.0, 1.0)
        conversion_rate_score = analytics.get('conversion_rate', 0)
        ctr_score = min(analytics.get('ctr', 0) * 10, 1.0)

        composite_score = (
            interaction_score * 0.4 +
            conversion_value_score * 0.3 +
            conversion_rate_score * 0.2 +
            ctr_score * 0.1
        )

        scored_images.append((composite_score, image_id))

    # Sort by score descending
    scored_images.sort(key=lambda x: x[0], reverse=True)

    top_ids = [image_id for _, image_id in scored_images[:top_n]]
    bottom_ids = [image_id for _, image_id in scored_images[top_n:]]

    return top_ids, bottom_ids
