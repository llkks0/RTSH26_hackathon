#!/usr/bin/env python3
"""
create_embedding.py

Generate an OpenAI embedding for a description so it can be stored or compared later.
If the OpenAI call fails (quota/network/etc.), use a fallback embedding instead.
"""

import argparse
import json
import logging
import os
import sys

from openai import (
    APIConnectionError,
    APIError,
    OpenAI,
    RateLimitError,
)

DEFAULT_MODEL = 'text-embedding-3-small'

# NOTE: text-embedding-3-large has 3072 dimensions, small has 1536.
# Adjust this if you know the exact dim you want.
FALLBACK_DIM = 1536

# Fallback embedding: simple zero vector
FALLBACK_EMBEDDING = [0.0] * FALLBACK_DIM


logger = logging.getLogger(__name__)


def create_embedding(text: str, model: str) -> list[float]:
    if not text:
        raise ValueError('Description text is empty after stripping whitespace.')

    if 'OPENAI_API_KEY' not in os.environ:
        raise RuntimeError('OPENAI_API_KEY is not set in the environment.')

    client = OpenAI()
    response = client.embeddings.create(model=model, input=text)
    return response.data[0].embedding


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Produce an OpenAI embedding for a description string.')
    parser.add_argument(
        'description',
        type=str,
        help='The description text to embed (wrap in quotes).',
    )
    parser.add_argument(
        '--model',
        '-m',
        type=str,
        default=DEFAULT_MODEL,
        help='Embedding model to use (default: %(default)s).',
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    text = args.description.strip()
    if not text:
        print('[error] Description must not be empty.', file=sys.stderr)
        sys.exit(1)

    try:
        embedding = create_embedding(text, args.model)
        used_fallback = False
        logger.info("Created embedding using %s", args.model)
    except (RateLimitError, APIConnectionError, APIError) as exc:
        # Same idea as description.py: log and fall back
        print(
            f'[warn] OpenAI API error ({type(exc).__name__}): {exc}. Using fallback embedding.',
            file=sys.stderr,
        )
        embedding = FALLBACK_EMBEDDING
        used_fallback = True
        logger.warning("OpenAI embedding error (%s): %s", type(exc).__name__, exc)
    except (RuntimeError, ValueError) as exc:
        # These are our own validation/env errors – still fatal
        print(f'[error] Failed to create embedding: {exc}', file=sys.stderr)
        sys.exit(1)

    payload = {
        'model': args.model,
        'input_length': len(text),
        'description': text,
        'embedding': embedding,
        'used_fallback': used_fallback,
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == '__main__':
    main()
