"""
Embedding utilities.

Functions for creating and manipulating text embeddings.
"""

import os
import sys

from openai import (
    APIConnectionError,
    APIError,
    OpenAI,
    RateLimitError,
)

from .types import EmbeddingInput, EmbeddingOutput


DEFAULT_MODEL = 'text-embedding-3-small'
FALLBACK_DIM = 1536  # text-embedding-3-small has 1536 dimensions
FALLBACK_EMBEDDING = [0.0] * FALLBACK_DIM


def create_embedding(input_data: EmbeddingInput) -> EmbeddingOutput:
    """
    Create an embedding for the given text using OpenAI's embedding API.

    Args:
        input_data: EmbeddingInput with text and model settings

    Returns:
        EmbeddingOutput with the embedding vector and metadata
    """
    text = input_data.text.strip()
    if not text:
        raise ValueError('Text is empty after stripping whitespace.')

    if 'OPENAI_API_KEY' not in os.environ:
        print(
            '[warn] OPENAI_API_KEY not set, using fallback embedding.',
            file=sys.stderr,
        )
        return EmbeddingOutput(
            embedding=FALLBACK_EMBEDDING,
            model_used=input_data.model,
            input_length=len(text),
            used_fallback=True,
        )

    client = OpenAI()

    try:
        response = client.embeddings.create(
            model=input_data.model,
            input=text,
        )
        embedding = response.data[0].embedding
        return EmbeddingOutput(
            embedding=embedding,
            model_used=input_data.model,
            input_length=len(text),
            used_fallback=False,
        )

    except (RateLimitError, APIConnectionError, APIError) as e:
        print(
            f'[warn] OpenAI API error ({type(e).__name__}): {e}. Using fallback.',
            file=sys.stderr,
        )
        return EmbeddingOutput(
            embedding=FALLBACK_EMBEDDING,
            model_used=input_data.model,
            input_length=len(text),
            used_fallback=True,
        )

    except Exception as e:
        print(
            f'[warn] Unexpected error creating embedding: {e}. Using fallback.',
            file=sys.stderr,
        )
        return EmbeddingOutput(
            embedding=FALLBACK_EMBEDDING,
            model_used=input_data.model,
            input_length=len(text),
            used_fallback=True,
        )


def create_embedding_simple(
    text: str,
    model: str = DEFAULT_MODEL,
) -> list[float]:
    """
    Convenience function to create an embedding from text.

    Args:
        text: The text to embed
        model: Embedding model to use

    Returns:
        The embedding vector as a list of floats
    """
    input_data = EmbeddingInput(text=text, model=model)
    output = create_embedding(input_data)
    return output.embedding


def compute_mean_embedding(embeddings: list[list[float]]) -> list[float]:
    """
    Compute the mean (average) embedding from a list of embeddings.

    This is useful for combining multiple asset embeddings into a single
    representative vector.

    Args:
        embeddings: List of embedding vectors (all must have the same dimension)

    Returns:
        The mean embedding vector

    Raises:
        ValueError: If embeddings list is empty or dimensions don't match
    """
    if not embeddings:
        raise ValueError("Cannot compute mean of empty embeddings list")

    dim = len(embeddings[0])
    if not all(len(e) == dim for e in embeddings):
        raise ValueError("All embeddings must have the same dimension")

    n = len(embeddings)
    mean_embedding = [0.0] * dim

    for embedding in embeddings:
        for i, val in enumerate(embedding):
            mean_embedding[i] += val

    for i in range(dim):
        mean_embedding[i] /= n

    return mean_embedding


def embeddings_are_valid(embeddings: list[list[float]]) -> bool:
    """
    Check if embeddings are valid (not all zeros, i.e., not fallback embeddings).

    Args:
        embeddings: List of embedding vectors to check

    Returns:
        True if all embeddings appear to be valid (not fallback)
    """
    for embedding in embeddings:
        # Check if embedding is all zeros (fallback embedding)
        if all(v == 0.0 for v in embedding):
            return False
    return True