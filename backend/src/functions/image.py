"""
Image description utilities.

Functions for generating textual descriptions of images using vision models.
All functions are async for non-blocking operation.
"""

import base64
import os
import sys
from pathlib import Path

from openai import (
    APIConnectionError,
    APIError,
    AsyncOpenAI,
    RateLimitError,
)

from .types import ImageDescriptionInput, ImageDescriptionOutput

DEFAULT_MODEL = 'gpt-4o-mini'

FALLBACK_DESCRIPTION = (
    'A generic image whose detailed description could not be generated '
    'because the AI service was unavailable.'
)

SYSTEM_PROMPT = (
    'You are a precise computer vision assistant. '
    'Given an image, you write a detailed, factual description. '
    'Mention: overall scene, objects, colors, text in the image, '
    'spatial relationships, and any relevant fine details. '
    'Do not speculate beyond what is visible.'
)

USER_PROMPT = (
    'Look at this image and describe it in detail. '
    'Include all notable objects, their colors, approximate positions, '
    'any visible text, and how elements relate to each other.'
)


def _encode_image_to_base64(image_path: str) -> str:
    """Read image bytes from disk and return base64-encoded string."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f'Image not found: {image_path}')
    with path.open('rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def _get_image_data_url(input_data: ImageDescriptionInput) -> str:
    """Get the image data URL from the input."""
    if input_data.image_base64:
        return f'data:image/jpeg;base64,{input_data.image_base64}'
    elif input_data.image_path:
        b64 = _encode_image_to_base64(input_data.image_path)
        return f'data:image/jpeg;base64,{b64}'
    elif input_data.image_url:
        return input_data.image_url
    else:
        raise ValueError("No image source provided")


async def describe_image(input_data: ImageDescriptionInput) -> ImageDescriptionOutput:
    """
    Generate a detailed description of an image using a vision model.

    Args:
        input_data: ImageDescriptionInput with image source and model settings

    Returns:
        ImageDescriptionOutput with the description and metadata
    """
    if 'OPENAI_API_KEY' not in os.environ:
        print(
            '[warn] OPENAI_API_KEY not set, using fallback description.',
            file=sys.stderr,
        )
        return ImageDescriptionOutput(
            description=FALLBACK_DESCRIPTION,
            model_used=input_data.model,
            used_fallback=True,
        )

    client = AsyncOpenAI()
    image_url = _get_image_data_url(input_data)

    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': USER_PROMPT},
                {'type': 'image_url', 'image_url': {'url': image_url}},
            ],
        },
    ]

    try:
        response = await client.chat.completions.create(
            model=input_data.model,
            messages=messages,
            max_tokens=input_data.max_tokens,
        )
        description = response.choices[0].message.content.strip()
        return ImageDescriptionOutput(
            description=description,
            model_used=input_data.model,
            used_fallback=False,
        )

    except (RateLimitError, APIConnectionError, APIError) as e:
        print(
            f'[warn] OpenAI API error ({type(e).__name__}): {e}. Using fallback.',
            file=sys.stderr,
        )
        return ImageDescriptionOutput(
            description=FALLBACK_DESCRIPTION,
            model_used=input_data.model,
            used_fallback=True,
        )

    except Exception as e:
        print(
            f'[warn] Unexpected error describing image: {e}. Using fallback.',
            file=sys.stderr,
        )
        return ImageDescriptionOutput(
            description=FALLBACK_DESCRIPTION,
            model_used=input_data.model,
            used_fallback=True,
        )


async def describe_image_from_url(
    url: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 600,
) -> ImageDescriptionOutput:
    """
    Convenience function to describe an image from a URL.

    Args:
        url: The URL of the image to describe
        model: Vision model to use
        max_tokens: Maximum tokens for the description

    Returns:
        ImageDescriptionOutput with the description
    """
    input_data = ImageDescriptionInput(
        image_url=url,
        model=model,
        max_tokens=max_tokens,
    )
    return await describe_image(input_data)


async def describe_image_from_path(
    path: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 600,
) -> ImageDescriptionOutput:
    """
    Convenience function to describe an image from a local file path.

    Args:
        path: Local file path to the image
        model: Vision model to use
        max_tokens: Maximum tokens for the description

    Returns:
        ImageDescriptionOutput with the description
    """
    input_data = ImageDescriptionInput(
        image_path=path,
        model=model,
        max_tokens=max_tokens,
    )
    return await describe_image(input_data)
