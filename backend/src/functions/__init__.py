"""
Functions module - strongly typed utility functions for the image generation pipeline.

This module contains reusable functions extracted from the steps/ folder,
organized by domain with clear input/output types.
"""

from .types import (
    # Image description types
    ImageDescriptionInput,
    ImageDescriptionOutput,
    # Embedding types
    EmbeddingInput,
    EmbeddingOutput,
    # Analytics types
    AnalyticsGenerationInput,
    AnalyticsGenerationOutput,
    GeneratedAnalytics,
    # Asset selection types
    AssetSelectionInput,
    AssetSelectionOutput,
    AssetSet,
    # Similarity types
    SimilarityInput,
    SimilarityOutput,
    AssetWithScore,
    # Prompt types
    PromptGenerationInput,
    PromptGenerationOutput,
    PromptModificationInput,
    PromptModificationOutput,
    # Image analysis types
    ImageAnalysisInput,
    ImageAnalysisOutput,
    # Asset processing types
    AssetProcessingInput,
    AssetProcessingOutput,
)

from .image import describe_image, describe_image_from_url, describe_image_from_path
from .embedding import create_embedding, compute_mean_embedding, create_embedding_simple
from .similarity import (
    cosine_similarity,
    filter_assets_by_similarity,
    get_top_k_similar_assets,
    filter_assets_by_iteration,
)
from .asset_selection import (
    select_asset_sets,
    group_assets_by_type,
    select_single_asset_set,
    get_base_and_reference_assets,
)
from .analytics import generate_analytics_for_images
from .prompt import generate_initial_prompt, modify_prompt_from_analysis, build_flux_prompt
from .analysis import analyze_winning_images, select_top_images_by_score
from .asset_processor import (
    process_asset_async,
    process_assets_batch,
    process_and_update_asset,
    process_and_update_assets_batch,
    get_assets_needing_processing,
)
from .image_generator import (
    generate_image_with_flux,
    generate_images_batch,
    ImageGenerationResult,
    FluxGenerationError,
)
from .orchestrator import (
    FlowOrchestrator,
    OrchestrationConfig,
    Job,
    JobType,
    JobResult,
    CampaignInitResult,
)

__all__ = [
    # Types
    'ImageDescriptionInput',
    'ImageDescriptionOutput',
    'EmbeddingInput',
    'EmbeddingOutput',
    'AnalyticsGenerationInput',
    'AnalyticsGenerationOutput',
    'GeneratedAnalytics',
    'AssetSelectionInput',
    'AssetSelectionOutput',
    'AssetSet',
    'SimilarityInput',
    'SimilarityOutput',
    'AssetWithScore',
    'PromptGenerationInput',
    'PromptGenerationOutput',
    'PromptModificationInput',
    'PromptModificationOutput',
    'ImageAnalysisInput',
    'ImageAnalysisOutput',
    'AssetProcessingInput',
    'AssetProcessingOutput',
    # Image functions
    'describe_image',
    'describe_image_from_url',
    'describe_image_from_path',
    # Embedding functions
    'create_embedding',
    'compute_mean_embedding',
    'create_embedding_simple',
    # Similarity functions
    'cosine_similarity',
    'filter_assets_by_similarity',
    'get_top_k_similar_assets',
    'filter_assets_by_iteration',
    # Asset selection functions
    'select_asset_sets',
    'group_assets_by_type',
    'select_single_asset_set',
    'get_base_and_reference_assets',
    # Analytics functions
    'generate_analytics_for_images',
    # Prompt functions
    'generate_initial_prompt',
    'modify_prompt_from_analysis',
    'build_flux_prompt',
    # Analysis functions
    'analyze_winning_images',
    'select_top_images_by_score',
    # Asset processor functions
    'process_asset_async',
    'process_assets_batch',
    'process_and_update_asset',
    'process_and_update_assets_batch',
    'get_assets_needing_processing',
    # Image generator functions
    'generate_image_with_flux',
    'generate_images_batch',
    'ImageGenerationResult',
    'FluxGenerationError',
    # Orchestrator
    'FlowOrchestrator',
    'OrchestrationConfig',
    'Job',
    'JobType',
    'JobResult',
    'CampaignInitResult',
]