#!/usr/bin/env python3
"""
describe_image.py

Use an OpenAI vision-capable chat model (e.g. gpt-4o, gpt-4o-mini)
to produce a detailed description of a local image file.

If the OpenAI call fails (quota, network, etc.), it returns a
prewritten fallback description instead of crashing.
"""

import argparse
import base64
import logging
import os
import sys
from pathlib import Path

from openai import (
    APIConnectionError,
    APIError,
    OpenAI,
    RateLimitError,
)

DEFAULT_MODEL = 'gpt-4o-mini'


FALLBACK_DESCRIPTION = (
    'A generic image showing a scene whose detailed description could not be '
    'generated because the AI service was unavailable. Please try again later '
    'or check your OpenAI connection and quota.'
)


logger = logging.getLogger(__name__)


def encode_image_to_base64(image_path: str) -> str:
    """Read image bytes from disk and return base64-encoded string."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f'Image not found: {image_path}')
    with path.open('rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def describe_image(
    image_path: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 600,
    fallback_description: str = FALLBACK_DESCRIPTION,
) -> str:
    """
    Send the image to an OpenAI vision model and get a detailed description.

    If any OpenAI-related error occurs, return `fallback_description`.
    """
    if 'OPENAI_API_KEY' not in os.environ:
        # No key at all – just return fallback
        msg = 'OPENAI_API_KEY not set, using fallback description.'
        print(f'[warn] {msg}', file=sys.stderr)
        logger.warning(msg)
        return fallback_description

    client = OpenAI()  # uses OPENAI_API_KEY

    # Encode local image as base64 and wrap in data URL
    b64_image = encode_image_to_base64(image_path)
    data_url = f'data:image/jpeg;base64,{b64_image}'

    messages = [
        {
            'role': 'system',
            'content': (
                'You are a precise computer vision assistant. '
                'Given an image, you write a detailed, factual description. '
                'Mention: overall scene, objects, colors, text in the image, '
                'spatial relationships, and any relevant fine details. '
                'Do not speculate beyond what is visible.'
            ),
        },
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': (
                        'Look at this image and describe it in detail. '
                        'Include all notable objects, their colors, approximate positions, '
                        'any visible text, and how elements relate to each other.'
                    ),
                },
                {
                    'type': 'image_url',
                    'image_url': {'url': data_url},
                },
            ],
        },
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
        )
        description = response.choices[0].message.content.strip()
        logger.info("Generated description for %s", image_path)
        return description

    except (RateLimitError, APIConnectionError, APIError) as e:
        # Known OpenAI / network / quota problems
        print(
            f'[warn] OpenAI API error ({type(e).__name__}): {e}. Using fallback description.',
            file=sys.stderr,
        )
        logger.warning("OpenAI description error (%s): %s", type(e).__name__, e)
        return fallback_description

    except Exception as e:
        # Any other unexpected error
        print(
            f'[warn] Unexpected error while describing image: {e}. Using fallback description.',
            file=sys.stderr,
        )
        logger.warning("Unexpected error while describing %s: %s", image_path, e)
        return fallback_description


def parse_args():
    parser = argparse.ArgumentParser(description='Generate a detailed description of an image using OpenAI vision models.')
    parser.add_argument(
        'image_path',
        type=str,
        help='Path to the image file (jpg, png, etc.).',
    )
    parser.add_argument(
        '--model',
        type=str,
        default=DEFAULT_MODEL,
        help=f'OpenAI model to use (default: {DEFAULT_MODEL}). Must be vision-capable, e.g. gpt-4o or gpt-4o-mini.',
    )
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=600,
        help='Maximum number of tokens for the description (default: 600).',
    )
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    description = describe_image(
        image_path=args.image_path,
        model=args.model,
        max_tokens=args.max_tokens,
    )
    print(description)


if __name__ == '__main__':
    main()
