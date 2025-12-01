"""
Analytics generation utilities.

Functions for generating realistic analytics data using OpenAI.
All functions are async for non-blocking operation.
"""

import json
import os
import random
import sys
from uuid import UUID

from openai import (
    APIConnectionError,
    APIError,
    AsyncOpenAI,
    RateLimitError,
)

from models import TargetGroup

from .types import (
    AnalyticsGenerationInput,
    AnalyticsGenerationOutput,
    GeneratedAnalytics,
)

DEFAULT_MODEL = 'gpt-4o-mini'


def _build_target_group_context(target_group: TargetGroup) -> str:
    """Build a textual description of the target group for the prompt."""
    parts = [f"Target Group: {target_group.name}"]

    if target_group.city:
        parts.append(f"Location: {target_group.city}")
    if target_group.age_group:
        parts.append(f"Age Group: {target_group.age_group}")
    if target_group.economic_status:
        parts.append(f"Economic Status: {target_group.economic_status}")
    if target_group.description:
        parts.append(f"Description: {target_group.description}")

    return "\n".join(parts)


def _generate_fallback_analytics(
    image_descriptions: list[tuple[UUID, str]],
    impressions_range: tuple[int, int],
) -> list[GeneratedAnalytics]:
    """Generate random analytics as fallback when OpenAI is unavailable."""
    analytics_list = []

    for image_id, _ in image_descriptions:
        impressions = random.randint(impressions_range[0], impressions_range[1])
        clicks = random.randint(int(impressions * 0.015), int(impressions * 0.06))
        interactions = int(clicks * random.uniform(1.1, 1.6))
        conversions = random.randint(int(clicks * 0.05), int(clicks * 0.25))
        cost = round(random.uniform(150.0, 400.0), 2)

        ctr = clicks / impressions if impressions > 0 else 0.0
        interaction_rate = interactions / impressions if impressions > 0 else 0.0
        conversion_rate = conversions / impressions if impressions > 0 else 0.0
        avg_cpc = cost / clicks if clicks > 0 else 0.0
        cpm = (cost / impressions * 1000) if impressions > 0 else 0.0

        value_per_conversion = round(random.uniform(25.0, 60.0), 2)
        conversion_value = round(conversions * value_per_conversion, 2)

        analytics_list.append(
            GeneratedAnalytics(
                image_id=image_id,
                impressions=impressions,
                clicks=clicks,
                conversions=conversions,
                cost=cost,
                ctr=ctr,
                conversion_rate=conversion_rate,
                avg_cpc=avg_cpc,
                cpm=cpm,
                conversion_value=conversion_value,
                value_per_conversion=value_per_conversion,
                interaction_rate=interaction_rate,
                interactions=interactions,
                reasoning="Fallback random analytics (OpenAI unavailable)",
            )
        )

    return analytics_list


async def generate_analytics_for_images(
    input_data: AnalyticsGenerationInput,
) -> AnalyticsGenerationOutput:
    """
    Generate realistic analytics for images using OpenAI.

    The LLM considers the target group characteristics and image descriptions
    to generate plausible performance metrics that reflect how well each image
    might resonate with the target audience.

    Args:
        input_data: AnalyticsGenerationInput with image descriptions and target group

    Returns:
        AnalyticsGenerationOutput with generated analytics for each image
    """
    if 'OPENAI_API_KEY' not in os.environ:
        print(
            '[warn] OPENAI_API_KEY not set, using fallback analytics.',
            file=sys.stderr,
        )
        return AnalyticsGenerationOutput(
            analytics=_generate_fallback_analytics(
                input_data.image_descriptions,
                input_data.impressions_range,
            ),
            model_used=input_data.model,
            used_fallback=True,
        )

    client = AsyncOpenAI()
    target_group_context = _build_target_group_context(input_data.target_group)

    # Build image descriptions for the prompt
    images_context = []
    for i, (image_id, description) in enumerate(input_data.image_descriptions, 1):
        images_context.append(f"Image {i} (ID: {image_id}):\n{description}")

    system_prompt = """You are an expert digital marketing analyst specializing in ad performance prediction.
Given a target audience profile and descriptions of ad images, you predict realistic performance metrics.

Your predictions should:
1. Reflect how well each image would resonate with the specific target audience
2. Show realistic variance between images (some should perform significantly better than others)
3. Be internally consistent (e.g., higher CTR should correlate with higher engagement)
4. Consider factors like visual appeal, relevance to target group, and clarity of message

Respond with valid JSON only."""

    user_prompt = f"""Analyze these ad images for the following target audience and predict realistic Google Ads performance metrics.

{target_group_context}

Images to analyze:
{chr(10).join(images_context)}

For each image, generate realistic analytics with the following constraints:
- Impressions: between {input_data.impressions_range[0]:,} and {input_data.impressions_range[1]:,}
- CTR: typically 1.5% to 6% (but can vary based on image quality)
- Conversion rate (from impressions): typically 0.05% to 0.5%
- Cost per impression: typically $0.005 to $0.02

Return a JSON object with this exact structure:
{{
    "analytics": [
        {{
            "image_id": "<uuid>",
            "impressions": <int>,
            "clicks": <int>,
            "conversions": <int>,
            "cost": <float>,
            "ctr": <float between 0 and 1>,
            "conversion_rate": <float between 0 and 1>,
            "avg_cpc": <float>,
            "cpm": <float>,
            "conversion_value": <float>,
            "value_per_conversion": <float>,
            "interaction_rate": <float between 0 and 1>,
            "interactions": <int>,
            "reasoning": "<brief explanation of why this image would perform this way for this target group>"
        }}
    ]
}}

Ensure the metrics are internally consistent:
- clicks = impressions * ctr
- cpm = (cost / impressions) * 1000
- avg_cpc = cost / clicks
- interactions should be 1.1x to 1.6x of clicks
- interaction_rate = interactions / impressions

Make sure images that would appeal more to the target group have noticeably better metrics."""

    try:
        response = await client.chat.completions.create(
            model=input_data.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            response_format={'type': 'json_object'},
            temperature=0.8,  # Some creativity in predictions
            max_tokens=2000,
        )

        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)

        analytics_list = []
        for item in result.get('analytics', []):
            analytics_list.append(
                GeneratedAnalytics(
                    image_id=UUID(item['image_id']),
                    impressions=item['impressions'],
                    clicks=item['clicks'],
                    conversions=item['conversions'],
                    cost=item['cost'],
                    ctr=item['ctr'],
                    conversion_rate=item['conversion_rate'],
                    avg_cpc=item['avg_cpc'],
                    cpm=item['cpm'],
                    conversion_value=item['conversion_value'],
                    value_per_conversion=item['value_per_conversion'],
                    interaction_rate=item['interaction_rate'],
                    interactions=item['interactions'],
                    reasoning=item.get('reasoning'),
                )
            )

        return AnalyticsGenerationOutput(
            analytics=analytics_list,
            model_used=input_data.model,
            used_fallback=False,
        )

    except (RateLimitError, APIConnectionError, APIError) as e:
        print(
            f'[warn] OpenAI API error ({type(e).__name__}): {e}. Using fallback.',
            file=sys.stderr,
        )
        return AnalyticsGenerationOutput(
            analytics=_generate_fallback_analytics(
                input_data.image_descriptions,
                input_data.impressions_range,
            ),
            model_used=input_data.model,
            used_fallback=True,
        )

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(
            f'[warn] Failed to parse analytics response: {e}. Using fallback.',
            file=sys.stderr,
        )
        return AnalyticsGenerationOutput(
            analytics=_generate_fallback_analytics(
                input_data.image_descriptions,
                input_data.impressions_range,
            ),
            model_used=input_data.model,
            used_fallback=True,
        )

    except Exception as e:
        print(
            f'[warn] Unexpected error generating analytics: {e}. Using fallback.',
            file=sys.stderr,
        )
        return AnalyticsGenerationOutput(
            analytics=_generate_fallback_analytics(
                input_data.image_descriptions,
                input_data.impressions_range,
            ),
            model_used=input_data.model,
            used_fallback=True,
        )
