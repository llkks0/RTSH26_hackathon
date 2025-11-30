"""
Async asset processor.

Processes assets by generating descriptions and embeddings asynchronously.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from sqlmodel import Session

from models import Asset

from .embedding import create_embedding_simple
from .image import describe_image_from_path, describe_image_from_url
from .types import (
    AssetProcessingInput,
    AssetProcessingOutput,
    EmbeddingInput,
    ImageDescriptionInput,
)


DEFAULT_DESCRIPTION_MODEL = 'gpt-4o-mini'
DEFAULT_EMBEDDING_MODEL = 'text-embedding-3-small'


def _process_single_asset(
    asset: Asset,
    description_model: str = DEFAULT_DESCRIPTION_MODEL,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> AssetProcessingOutput:
    """
    Process a single asset: generate description and embedding.

    This is a synchronous function that handles one asset.

    Args:
        asset: The asset to process
        description_model: Vision model for description
        embedding_model: Model for embedding

    Returns:
        AssetProcessingOutput with description and embedding
    """
    used_fallback = False

    # Step 1: Generate description from image
    file_name = asset.file_name
    if file_name.startswith('http://') or file_name.startswith('https://'):
        description_output = describe_image_from_url(
            url=file_name,
            model=description_model,
        )
    else:
        description_output = describe_image_from_path(
            path=file_name,
            model=description_model,
        )

    description = description_output.description
    if description_output.used_fallback:
        used_fallback = True

    # Step 2: Create embedding from description
    # Combine caption, tags, and generated description for richer embedding
    embedding_text_parts = []

    if asset.caption:
        embedding_text_parts.append(asset.caption)
    if asset.tags:
        embedding_text_parts.append(f"Tags: {', '.join(asset.tags)}")
    embedding_text_parts.append(f"Visual description: {description}")

    embedding_text = "\n".join(embedding_text_parts)
    embedding = create_embedding_simple(embedding_text, model=embedding_model)

    # Check if embedding is fallback (all zeros)
    if all(v == 0.0 for v in embedding):
        used_fallback = True

    return AssetProcessingOutput(
        asset_id=asset.id,
        description=description,
        embedding=embedding,
        description_model=description_model,
        embedding_model=embedding_model,
        used_fallback=used_fallback,
    )


async def process_asset_async(
    asset: Asset,
    description_model: str = DEFAULT_DESCRIPTION_MODEL,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    executor: ThreadPoolExecutor | None = None,
) -> AssetProcessingOutput:
    """
    Process a single asset asynchronously.

    Runs the synchronous processing in a thread pool to avoid blocking.

    Args:
        asset: The asset to process
        description_model: Vision model for description
        embedding_model: Model for embedding
        executor: Optional thread pool executor (creates one if not provided)

    Returns:
        AssetProcessingOutput with description and embedding
    """
    loop = asyncio.get_event_loop()

    if executor is None:
        executor = ThreadPoolExecutor(max_workers=4)

    return await loop.run_in_executor(
        executor,
        _process_single_asset,
        asset,
        description_model,
        embedding_model,
    )


async def process_assets_batch(
    assets: list[Asset],
    description_model: str = DEFAULT_DESCRIPTION_MODEL,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    max_concurrency: int = 5,
) -> list[AssetProcessingOutput]:
    """
    Process multiple assets asynchronously with controlled concurrency.

    Args:
        assets: List of assets to process
        description_model: Vision model for description
        embedding_model: Model for embedding
        max_concurrency: Maximum number of concurrent API calls

    Returns:
        List of AssetProcessingOutput for each asset
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def process_with_semaphore(asset: Asset) -> AssetProcessingOutput:
        async with semaphore:
            return await process_asset_async(
                asset=asset,
                description_model=description_model,
                embedding_model=embedding_model,
            )

    tasks = [process_with_semaphore(asset) for asset in assets]
    return await asyncio.gather(*tasks)


def process_and_update_asset(
    session: Session,
    asset: Asset,
    description_model: str = DEFAULT_DESCRIPTION_MODEL,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> AssetProcessingOutput:
    """
    Process an asset and update it in the database.

    This is a synchronous function that processes the asset and
    updates its caption (with description) and embedding fields.

    Args:
        session: Database session
        asset: The asset to process and update
        description_model: Vision model for description
        embedding_model: Model for embedding

    Returns:
        AssetProcessingOutput with the generated data
    """
    output = _process_single_asset(
        asset=asset,
        description_model=description_model,
        embedding_model=embedding_model,
    )

    # Update asset fields
    # Append generated description to caption if caption exists
    if asset.caption:
        asset.caption = f"{asset.caption}\n\nGenerated description: {output.description}"
    else:
        asset.caption = output.description

    asset.embedding = output.embedding

    session.add(asset)
    session.commit()
    session.refresh(asset)

    return output


async def process_and_update_assets_batch(
    session: Session,
    assets: list[Asset],
    description_model: str = DEFAULT_DESCRIPTION_MODEL,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    max_concurrency: int = 5,
) -> list[AssetProcessingOutput]:
    """
    Process multiple assets and update them in the database.

    This processes assets asynchronously but updates the database
    synchronously after all processing is complete.

    Args:
        session: Database session
        assets: List of assets to process and update
        description_model: Vision model for description
        embedding_model: Model for embedding
        max_concurrency: Maximum number of concurrent API calls

    Returns:
        List of AssetProcessingOutput for each asset
    """
    # Process all assets asynchronously
    outputs = await process_assets_batch(
        assets=assets,
        description_model=description_model,
        embedding_model=embedding_model,
        max_concurrency=max_concurrency,
    )

    # Update assets in database
    output_map = {output.asset_id: output for output in outputs}

    for asset in assets:
        output = output_map.get(asset.id)
        if output:
            if asset.caption:
                asset.caption = f"{asset.caption}\n\nGenerated description: {output.description}"
            else:
                asset.caption = output.description

            asset.embedding = output.embedding
            session.add(asset)

    session.commit()

    # Refresh all assets
    for asset in assets:
        session.refresh(asset)

    return outputs


def get_assets_needing_processing(
    session: Session,
    require_embedding: bool = True,
    require_description: bool = True,
) -> list[Asset]:
    """
    Get assets that need processing (missing embedding or description).

    Args:
        session: Database session
        require_embedding: Only return assets missing embeddings
        require_description: Only return assets with empty/short captions

    Returns:
        List of assets needing processing
    """
    from sqlmodel import select

    statement = select(Asset)

    if require_embedding:
        statement = statement.where(Asset.embedding.is_(None))

    assets = list(session.exec(statement).all())

    if require_description:
        # Filter to assets with empty or very short captions
        assets = [
            a for a in assets
            if not a.caption or len(a.caption.strip()) < 50
        ]

    return assets
