"""
Module for analyzing differences between top-performing and lower-performing ad images.

This module provides functionality to compare image performance metrics and generate
AI-powered insights about what makes certain images more successful than others.

Example:
    >>> from src.steps.evaluate_image_groups import analyze_image_differences
    >>> from src.schemas import ImageData, AnalyticsData
    >>> 
    >>> # Prepare your image data with analytics
    >>> images = [
    ...     ImageData(
    ...         id="img1",
    ...         file_name="image1.jpg",
    ...         metadata_tags=["warm colors", "lifestyle"],
    ...         final_prompt="A person running in a park",
    ...         analytics=AnalyticsData(...)
    ...     ),
    ...     # ... more images
    ... ]
    >>> 
    >>> # Analyze differences
    >>> result = analyze_image_differences(images, top_n=2)
    >>> print(result['differentiation_text'])
    >>> print(result['differentiation_tags'])
"""
import json
import os
import sys
from typing import List, TypedDict

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from openai import (
    APIConnectionError,
    APIError,
    OpenAI,
    RateLimitError,
)

from ..schemas import AnalyticsData, ImageData
from .select_top_images import select_top_images

__all__ = ['analyze_image_differences', 'ImageAnalysisResult', 'DEFAULT_MODEL']

DEFAULT_MODEL = 'gpt-4o-mini'

FALLBACK_ANALYSIS = {
    'differentiation_text': (
        'Analysis could not be generated because the AI service was unavailable. '
        'Please try again later or check your OpenAI connection and quota.'
    ),
    'differentiation_tags': ['analysis_unavailable'],
}


class ImageAnalysisResult(TypedDict):
    """
    Result structure returned by analyze_image_differences.
    
    Attributes:
        differentiation_text: Human-readable explanation of what makes top images
            perform better. Contains detailed analysis of metrics, metadata, and patterns.
        differentiation_tags: List of concise, actionable tags describing key success
            factors (e.g., ["warm colors", "close-up shots", "high contrast"]).
        top_image_ids: List of image IDs that were identified as top performers.
        bottom_image_ids: List of image IDs that were identified as lower performers.
    """
    differentiation_text: str
    differentiation_tags: list[str]
    top_image_ids: list[str]
    bottom_image_ids: list[str]


def analyze_image_differences(
    analytics_data: List[AnalyticsData] | List[ImageData],
    top_n: int = 2,
    model: str = DEFAULT_MODEL,
) -> ImageAnalysisResult:
    """
    Analyzes differences between top-performing and lower-performing ad images using AI.
    
    This function compares image performance metrics and uses OpenAI's ChatGPT to
    generate insights about what makes certain images more successful. It identifies
    patterns in analytics data, metadata tags, and generation prompts.
    
    Args:
        analytics_data: List of image data objects to analyze. Can be either:
            - List[AnalyticsData]: Direct analytics data objects, each with:
                - id (str): Unique image identifier
                - impressions, clicks, ctr, interactions, interaction_rate
                - conversions, conversion_rate, conversion_value
                - cost, avg_cpc, cpm, value_per_conversion
            - List[ImageData]: Image objects with embedded analytics, each with:
                - id (str): Unique image identifier
                - file_name (str): Image filename or path
                - metadata_tags (list[str] | None): Image metadata tags
                - final_prompt (str | None): Prompt used to generate the image
                - analytics (AnalyticsData): Analytics data object (required)
        
        top_n: Number of top-performing images to compare against the rest.
            Must be at least 1, and the total number of images must be at least
            top_n + 1. Default: 2.
        
        model: OpenAI model identifier to use for analysis. Default: 'gpt-4o-mini'.
            Other options: 'gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', etc.
    
    Returns:
        ImageAnalysisResult: A dictionary containing:
            - differentiation_text (str): Detailed explanation of what makes top
              images successful, including analysis of metrics, metadata, prompts,
              and patterns. Typically 200-500 words.
            - differentiation_tags (list[str]): Concise, actionable tags describing
              key success factors. Examples: ["warm colors", "close-up shots",
              "clear product focus", "high contrast", "lifestyle context"].
            - top_image_ids (list[str]): IDs of the top N performing images.
            - bottom_image_ids (list[str]): IDs of the remaining lower-performing images.
    
    Raises:
        ValueError: If:
            - Any ImageData object has no analytics data
            - Not enough images provided (need at least top_n + 1 images)
        TypeError: If analytics_data contains unsupported object types.
    
    Example:
        >>> from src.steps.evaluate_image_groups import analyze_image_differences
        >>> from src.schemas import ImageData, AnalyticsData
        >>> 
        >>> # Create sample data
        >>> images = [
        ...     ImageData(
        ...         id="img1",
        ...         file_name="image1.jpg",
        ...         metadata_tags=["warm colors", "outdoor"],
        ...         final_prompt="A person running in a park",
        ...         analytics=AnalyticsData(
        ...             id="img1",
        ...             impressions=20000,
        ...             clicks=1200,
        ...             ctr=0.06,
        ...             interactions=1800,
        ...             interaction_rate=0.09,
        ...             conversions=300,
        ...             conversion_rate=0.015,
        ...             cost=300.0,
        ...             avg_cpc=0.25,
        ...             cpm=15.0,
        ...             conversion_value=12000.0,
        ...             value_per_conversion=40.0,
        ...         )
        ...     ),
        ...     # ... add more images
        ... ]
        >>> 
        >>> # Analyze differences
        >>> result = analyze_image_differences(images, top_n=2, model='gpt-4o-mini')
        >>> 
        >>> # Access results
        >>> print(f"Top performers: {result['top_image_ids']}")
        >>> print(f"Key factors: {result['differentiation_tags']}")
        >>> print(f"Analysis: {result['differentiation_text']}")
    
    Note:
        - Requires OPENAI_API_KEY environment variable or .env file configuration
        - Falls back to default analysis if API is unavailable or returns errors
        - Uses composite scoring based on interactions, conversion value, and CTR
        - Analysis quality depends on the OpenAI model used
    """
    # Extract AnalyticsData and map to ImageData if needed
    analytics_list: List[AnalyticsData] = []
    image_data_map: dict[str, ImageData] = {}
    
    for item in analytics_data:
        if isinstance(item, ImageData):
            if item.analytics is None:
                raise ValueError(f"ImageData with id '{item.id}' has no analytics data")
            analytics_list.append(item.analytics)
            image_data_map[item.analytics.id] = item
        elif isinstance(item, AnalyticsData):
            analytics_list.append(item)
        else:
            raise TypeError(f"Unsupported type: {type(item)}")
    
    if len(analytics_list) < top_n + 1:
        raise ValueError(
            f"Not enough images to compare. Need at least {top_n + 1} images, "
            f"but only {len(analytics_list)} provided."
        )
    
    # Select top N images
    top_analytics = select_top_images(analytics_list, top_n=top_n)
    top_ids = {analytics.id for analytics in top_analytics}
    
    # Get bottom images (non-selected)
    bottom_analytics = [a for a in analytics_list if a.id not in top_ids]
    
    # Prepare data for ChatGPT analysis
    top_images_data = []
    for analytics in top_analytics:
        img_data = image_data_map.get(analytics.id)
        top_images_data.append({
            'id': analytics.id,
            'file_name': img_data.file_name if img_data else 'unknown',
            'metadata_tags': img_data.metadata_tags if img_data else None,
            'final_prompt': img_data.final_prompt if img_data else None,
            'analytics': {
                'impressions': analytics.impressions,
                'clicks': analytics.clicks,
                'ctr': analytics.ctr,
                'interactions': analytics.interactions,
                'interaction_rate': analytics.interaction_rate,
                'conversions': analytics.conversions,
                'conversion_rate': analytics.conversion_rate,
                'conversion_value': analytics.conversion_value,
            }
        })
    
    bottom_images_data = []
    for analytics in bottom_analytics:
        img_data = image_data_map.get(analytics.id)
        bottom_images_data.append({
            'id': analytics.id,
            'file_name': img_data.file_name if img_data else 'unknown',
            'metadata_tags': img_data.metadata_tags if img_data else None,
            'final_prompt': img_data.final_prompt if img_data else None,
            'analytics': {
                'impressions': analytics.impressions,
                'clicks': analytics.clicks,
                'ctr': analytics.ctr,
                'interactions': analytics.interactions,
                'interaction_rate': analytics.interaction_rate,
                'conversions': analytics.conversions,
                'conversion_rate': analytics.conversion_rate,
                'conversion_value': analytics.conversion_value,
            }
        })
    
    # Call ChatGPT for analysis
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print(
            '[warn] OPENAI_API_KEY not set in environment or .env file, using fallback analysis.',
            file=sys.stderr,
        )
        return {
            **FALLBACK_ANALYSIS,
            'top_image_ids': [img['id'] for img in top_images_data],
            'bottom_image_ids': [img['id'] for img in bottom_images_data],
        }
    
    client = OpenAI(api_key=api_key)
    
    # Build prompt for ChatGPT
    system_prompt = (
        "You are an expert marketing analyst specializing in ad creative performance. "
        "Your task is to analyze why certain ad images perform better than others "
        "based on their analytics metrics and metadata."
    )
    
    user_prompt = f"""Analyze the following ad images and explain what makes the top-performing images successful compared to the lower-performing ones.

TOP-PERFORMING IMAGES ({len(top_images_data)} images):
{json.dumps(top_images_data, indent=2)}

LOWER-PERFORMING IMAGES ({len(bottom_images_data)} images):
{json.dumps(bottom_images_data, indent=2)}

Please provide:
1. A detailed explanation (differentiation_text) of what makes the top images perform better. Consider:
   - Analytics metrics (CTR, interaction rate, conversion rate, conversion value)
   - Image metadata tags and characteristics
   - Prompts used to generate the images
   - Any patterns or commonalities among top performers
   - Key differences from lower performers

2. A list of concise differentiation tags (differentiation_tags) that capture the key success factors. These should be short, actionable tags like:
   - "warm colors", "close-up shots", "clear product focus", "high contrast", etc.

Respond in JSON format with this structure:
{{
    "differentiation_text": "Your detailed explanation here...",
    "differentiation_tags": ["tag1", "tag2", "tag3", ...]
}}"""
    
    try:
        response = client.chat.completions.create(
            model=model,
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
        
        # Validate and return result
        return {
            'differentiation_text': result.get('differentiation_text', ''),
            'differentiation_tags': result.get('differentiation_tags', []),
            'top_image_ids': [img['id'] for img in top_images_data],
            'bottom_image_ids': [img['id'] for img in bottom_images_data],
        }
        
    except (RateLimitError, APIConnectionError, APIError) as e:
        print(
            f'[warn] OpenAI API error ({type(e).__name__}): {e}. Using fallback analysis.',
            file=sys.stderr,
        )
        return {
            **FALLBACK_ANALYSIS,
            'top_image_ids': [img['id'] for img in top_images_data],
            'bottom_image_ids': [img['id'] for img in bottom_images_data],
        }
    
    except json.JSONDecodeError as e:
        print(
            f'[warn] Failed to parse ChatGPT response as JSON: {e}. Using fallback analysis.',
            file=sys.stderr,
        )
        return {
            **FALLBACK_ANALYSIS,
            'top_image_ids': [img['id'] for img in top_images_data],
            'bottom_image_ids': [img['id'] for img in bottom_images_data],
        }
    
    except Exception as e:
        print(
            f'[warn] Unexpected error during analysis: {e}. Using fallback analysis.',
            file=sys.stderr,
        )
        return {
            **FALLBACK_ANALYSIS,
            'top_image_ids': [img['id'] for img in top_images_data],
            'bottom_image_ids': [img['id'] for img in bottom_images_data],
        }


if __name__ == "__main__":
    # Test mode
    from .get_analytics import get_analytics
    
    test_images = [
        ImageData(
            id="image_1",
            file_name="img1.jpg",
            metadata_tags=["warm colors", "outdoor", "lifestyle"],
            final_prompt="A person running in a park with modern running shoes",
        ),
        ImageData(
            id="image_2",
            file_name="img2.jpg",
            metadata_tags=["cool colors", "indoor", "product focus"],
            final_prompt="Close-up of running shoes on a white background",
        ),
        ImageData(
            id="image_3",
            file_name="img3.jpg",
            metadata_tags=["neutral colors", "studio", "minimalist"],
            final_prompt="Running shoes displayed in a minimalist studio setting",
        ),
        ImageData(
            id="image_4",
            file_name="img4.jpg",
            metadata_tags=["warm colors", "lifestyle", "action"],
            final_prompt="Athlete in action wearing running shoes during a race",
        ),
        ImageData(
            id="image_5",
            file_name="img5.jpg",
            metadata_tags=["dark colors", "evening", "urban"],
            final_prompt="Running shoes in an urban evening setting",
        ),
    ]
    
    # Get analytics for all images
    analytics = get_analytics(test_images)
    
    # Attach analytics to images
    for img, analytics_item in zip(test_images, analytics):
        img.analytics = analytics_item
    
    # Analyze differences
    print("Analyzing image performance differences...\n")
    result = analyze_image_differences(test_images, top_n=2)
    
    print("=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    print(f"\nTop Image IDs: {result['top_image_ids']}")
    print(f"Bottom Image IDs: {result['bottom_image_ids']}")
    print(f"\nDifferentiation Tags: {result['differentiation_tags']}")
    print(f"\nDifferentiation Text:\n{result['differentiation_text']}")

