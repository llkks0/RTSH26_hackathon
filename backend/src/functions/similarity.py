"""
Similarity calculation utilities.

Functions for computing cosine similarity and filtering assets by similarity.
"""

import math

from models import Asset

from .types import AssetWithScore, SimilarityInput, SimilarityOutput


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score between -1 and 1 (typically 0 to 1 for normalized embeddings)

    Raises:
        ValueError: If vectors have different lengths
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"Vectors must have the same length. Got {len(vec1)} and {len(vec2)}")

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(a * a for a in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def filter_assets_by_similarity(input_data: SimilarityInput) -> SimilarityOutput:
    """
    Filter assets by similarity to a target embedding.

    Keeps only the top fraction of assets that are most similar to the target.

    Args:
        input_data: SimilarityInput with target embedding, assets, and top fraction

    Returns:
        SimilarityOutput with filtered assets, scored assets, and threshold

    Note:
        Assets without embeddings are excluded from the result.
    """
    scored_assets: list[AssetWithScore] = []

    for asset in input_data.assets:
        if asset.embedding is None or len(asset.embedding) == 0:
            continue

        try:
            score = cosine_similarity(input_data.target_embedding, asset.embedding)
            scored_assets.append(AssetWithScore(asset=asset, score=score))
        except ValueError:
            # Skip assets with incompatible embedding dimensions
            continue

    # Sort by score descending
    scored_assets.sort(key=lambda x: x.score, reverse=True)

    # Calculate how many to keep
    num_to_keep = max(1, int(len(scored_assets) * input_data.top_fraction))
    filtered = scored_assets[:num_to_keep]

    # Determine threshold score
    threshold_score = filtered[-1].score if filtered else 0.0

    return SimilarityOutput(
        filtered_assets=[item.asset for item in filtered],
        scored_assets=scored_assets,
        threshold_score=threshold_score,
    )


def get_top_k_similar_assets(
    target_embedding: list[float],
    assets: list[Asset],
    top_k: int = 5,
) -> list[AssetWithScore]:
    """
    Get the top K most similar assets to a target embedding.

    Args:
        target_embedding: The embedding to compare against
        assets: List of assets to search
        top_k: Number of top assets to return

    Returns:
        List of AssetWithScore, sorted by similarity (highest first)
    """
    input_data = SimilarityInput(
        target_embedding=target_embedding,
        assets=assets,
        top_fraction=1.0,  # Keep all for now, we'll slice
    )
    output = filter_assets_by_similarity(input_data)
    return output.scored_assets[:top_k]


def filter_assets_by_iteration(
    target_embedding: list[float],
    assets: list[Asset],
    iteration: int,
    type_embeddings: dict[str, list[float]] | None = None,
) -> list[Asset]:
    """
    Filter assets based on iteration number, per asset type.

    For iteration 0: keep all assets
    For iteration 1: keep top 1/2 of each asset type
    For iteration 2: keep top 1/3 of each asset type
    etc.

    Each asset type is filtered against its own average embedding from winners,
    or falls back to the global target_embedding if not available.

    Args:
        target_embedding: The fallback embedding to compare against
        assets: List of assets to filter
        iteration: Current iteration number (0-based)
        type_embeddings: Optional dict mapping asset type to average embedding
                         from winner assets of that type

    Returns:
        Filtered list of assets
    """
    if iteration == 0:
        return assets

    fraction = 1.0 / (iteration + 1)

    # Group assets by type
    assets_by_type: dict[str, list[Asset]] = {}
    for asset in assets:
        asset_type = asset.asset_type.value if asset.asset_type else "unknown"
        if asset_type not in assets_by_type:
            assets_by_type[asset_type] = []
        assets_by_type[asset_type].append(asset)

    # Filter each type separately
    filtered_assets: list[Asset] = []

    for asset_type, type_assets in assets_by_type.items():
        # Get the embedding for this type (from winners) or fallback to global
        if type_embeddings and asset_type in type_embeddings:
            embedding = type_embeddings[asset_type]
        else:
            embedding = target_embedding

        # Filter this type's assets
        input_data = SimilarityInput(
            target_embedding=embedding,
            assets=type_assets,
            top_fraction=fraction,
        )
        output = filter_assets_by_similarity(input_data)
        filtered_assets.extend(output.filtered_assets)

    return filtered_assets


def compute_type_embeddings_from_winners(
    winner_assets: list[Asset],
) -> dict[str, list[float]]:
    """
    Compute average embeddings per asset type from winner assets.

    Args:
        winner_assets: List of assets from winning images

    Returns:
        Dict mapping asset type to average embedding vector
    """
    from .embedding import compute_mean_embedding

    # Group embeddings by type
    embeddings_by_type: dict[str, list[list[float]]] = {}

    for asset in winner_assets:
        if asset.embedding is None or len(asset.embedding) == 0:
            continue

        asset_type = asset.asset_type.value if asset.asset_type else "unknown"
        if asset_type not in embeddings_by_type:
            embeddings_by_type[asset_type] = []
        embeddings_by_type[asset_type].append(asset.embedding)

    # Compute mean for each type
    type_embeddings: dict[str, list[float]] = {}
    for asset_type, embeddings in embeddings_by_type.items():
        if embeddings:
            type_embeddings[asset_type] = compute_mean_embedding(embeddings)

    return type_embeddings
