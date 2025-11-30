import logging
import math
from typing import List
from uuid import UUID

from sqlmodel import Session, select

try:
    from ..assets.create_embedding import create_embedding
    from ..models import Asset, AssetType
except ImportError:  # pragma: no cover - fallback for standalone scripts
    from assets.create_embedding import create_embedding  # type: ignore
    from models import Asset, AssetType  # type: ignore

DEFAULT_EMBEDDING_MODEL = 'text-embedding-3-small'
DEFAULT_TOP_K = 5


logger = logging.getLogger(__name__)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Parameters:
        vec1: First vector
        vec2: Second vector
    
    Returns:
        Cosine similarity score between -1 and 1 (typically 0 to 1 for normalized embeddings)
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"Vectors must have the same length. Got {len(vec1)} and {len(vec2)}")
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(a * a for a in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


def search_new_assets(
    session: Session,
    prompt: str | None = None,
    prompt_embedding: List[float] | None = None,
    top_k: int = DEFAULT_TOP_K,
    asset_type: AssetType | None = None,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> List[tuple[Asset, float]]:
    """
    Search for assets that are most similar to a given prompt using embedding similarity.
    
    This function:
    1. Creates an embedding for the prompt (if not provided)
    2. Retrieves all assets with embeddings from the database
    3. Computes cosine similarity between prompt embedding and each asset embedding
    4. Returns the top K most similar assets with their similarity scores
    
    Parameters:
        session: Database session
        prompt: Text prompt to search for (required if prompt_embedding is None)
        prompt_embedding: Pre-computed embedding vector (optional, if provided, prompt is ignored)
        top_k: Number of top assets to return (default: 5)
        asset_type: Optional filter by asset type
        embedding_model: OpenAI embedding model to use (default: 'text-embedding-3-small')
    
    Returns:
        List of tuples (Asset, similarity_score) sorted by similarity (highest first)
    """
    # Get prompt embedding
    if prompt_embedding is None:
        if prompt is None or not prompt.strip():
            raise ValueError("Either 'prompt' or 'prompt_embedding' must be provided")
        
        try:
            prompt_embedding = create_embedding(prompt.strip(), embedding_model)
        except Exception as e:
            raise RuntimeError(f"Failed to create embedding for prompt: {e}") from e
    
    if not prompt_embedding:
        raise ValueError("Prompt embedding cannot be empty")
    
    # Query assets with embeddings
    # SQLModel columns support isnot() method directly
    statement = select(Asset).where(Asset.embedding.isnot(None))
    
    if asset_type:
        statement = statement.where(Asset.asset_type == asset_type)
    
    assets = list(session.exec(statement).all())
    
    if not assets:
        logger.info("No assets with embeddings available for search")
        return []
    
    # Compute similarity scores
    scored_assets: List[tuple[Asset, float]] = []
    
    logger.info(
        "Computing similarity against %s assets (top_k=%s)", len(assets), top_k
    )

    for asset in assets:
        # Double-check embedding exists (defensive programming)
        if asset.embedding is None or len(asset.embedding) == 0:
            continue
        
        try:
            similarity = cosine_similarity(prompt_embedding, asset.embedding)
            scored_assets.append((asset, similarity))
        except ValueError as e:
            # Skip assets with incompatible embedding dimensions
            logger.warning(
                "Skipping asset %s due to embedding dimension mismatch: %s",
                asset.id,
                e,
            )
            continue
    
    # Sort by similarity (highest first) and return top K
    scored_assets.sort(key=lambda x: x[1], reverse=True)
    
    results = scored_assets[:top_k]
    logger.info("Returning %s similar assets", len(results))
    return results


def search_new_assets_by_ids(
    session: Session,
    prompt: str | None = None,
    prompt_embedding: List[float] | None = None,
    top_k: int = DEFAULT_TOP_K,
    asset_type: AssetType | None = None,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> List[UUID]:
    """
    Convenience function that returns only asset IDs (not full Asset objects).
    
    Parameters are the same as search_new_assets.
    
    Returns:
        List of asset UUIDs sorted by similarity (highest first)
    """
    results = search_new_assets(
        session=session,
        prompt=prompt,
        prompt_embedding=prompt_embedding,
        top_k=top_k,
        asset_type=asset_type,
        embedding_model=embedding_model,
    )
    return [asset.id for asset, _ in results]


if __name__ == "__main__":
    # Test mode
    try:
        from ..database import engine
    except ImportError:  # pragma: no cover
        from database import engine  # type: ignore
    from sqlmodel import Session
    
    # Example usage
    test_prompt = "A person running in a park with modern running shoes"
    
    print(f"Searching for assets similar to: '{test_prompt}'\n")
    
    # Create a session directly for testing
    with Session(engine) as session:
        try:
            # Search for assets
            results = search_new_assets(
                session=session,
                prompt=test_prompt,
                top_k=5,
            )
            
            if results:
                print(f"Found {len(results)} similar assets:\n")
                for i, (asset, similarity) in enumerate(results, 1):
                    print(f"{i}. {asset.name} (ID: {asset.id})")
                    print(f"   Type: {asset.asset_type}")
                    print(f"   Similarity: {similarity:.4f}")
                    print(f"   Tags: {asset.tags}")
                    print(f"   Caption: {asset.caption[:100]}..." if len(asset.caption) > 100 else f"   Caption: {asset.caption}")
                    print()
            else:
                print("No assets found with embeddings in the database.")
                print("Make sure assets have been created with embeddings.")
        except Exception as e:
            print(f"Error: {e}", file=__import__('sys').stderr)

