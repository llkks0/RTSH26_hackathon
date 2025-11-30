"""
Type definitions for functions module.

All input/output types are defined here for strong typing and documentation.
"""

from dataclasses import dataclass, field
from typing import Literal
from uuid import UUID

from models import Asset, AssetType, TargetGroup


# ---------------------------------------------------------
# Image Description Types
# ---------------------------------------------------------


@dataclass
class ImageDescriptionInput:
    """Input for describing an image."""

    image_path: str | None = None  # Local file path
    image_url: str | None = None   # Remote URL
    image_base64: str | None = None  # Base64 encoded image
    model: str = 'gpt-4o-mini'
    max_tokens: int = 600

    def __post_init__(self) -> None:
        sources = [self.image_path, self.image_url, self.image_base64]
        if not any(sources):
            raise ValueError("At least one of image_path, image_url, or image_base64 must be provided")


@dataclass
class ImageDescriptionOutput:
    """Output from describing an image."""

    description: str
    model_used: str
    used_fallback: bool = False


# ---------------------------------------------------------
# Embedding Types
# ---------------------------------------------------------


@dataclass
class EmbeddingInput:
    """Input for creating an embedding."""

    text: str
    model: str = 'text-embedding-3-small'


@dataclass
class EmbeddingOutput:
    """Output from creating an embedding."""

    embedding: list[float]
    model_used: str
    input_length: int
    used_fallback: bool = False


# ---------------------------------------------------------
# Analytics Types
# ---------------------------------------------------------


@dataclass
class GeneratedAnalytics:
    """Analytics data for a single image."""

    image_id: UUID
    impressions: int
    clicks: int
    conversions: int
    cost: float
    ctr: float
    conversion_rate: float
    avg_cpc: float
    cpm: float
    conversion_value: float
    value_per_conversion: float
    interaction_rate: float
    interactions: int
    reasoning: str | None = None  # LLM's reasoning for these metrics


@dataclass
class AnalyticsGenerationInput:
    """Input for generating analytics using OpenAI."""

    image_descriptions: list[tuple[UUID, str]]  # (image_id, description)
    target_group: TargetGroup
    model: str = 'gpt-4o-mini'
    impressions_range: tuple[int, int] = (10, 100_000)


@dataclass
class AnalyticsGenerationOutput:
    """Output from generating analytics."""

    analytics: list[GeneratedAnalytics]
    model_used: str
    used_fallback: bool = False


# ---------------------------------------------------------
# Asset Selection Types
# ---------------------------------------------------------


@dataclass
class AssetSet:
    """A set of assets, one per asset type."""

    assets: dict[AssetType, Asset]

    @property
    def asset_ids(self) -> list[UUID]:
        """Get list of asset IDs in this set."""
        return [asset.id for asset in self.assets.values()]

    @property
    def asset_list(self) -> list[Asset]:
        """Get list of assets in this set."""
        return list(self.assets.values())


@dataclass
class AssetSelectionInput:
    """Input for selecting asset sets."""

    assets: list[Asset]
    num_sets: int = 5
    used_asset_ids: set[UUID] = field(default_factory=set)  # Assets to deprioritize


@dataclass
class AssetSelectionOutput:
    """Output from selecting asset sets."""

    asset_sets: list[AssetSet]
    assets_by_type: dict[AssetType, list[Asset]]


# ---------------------------------------------------------
# Similarity Types
# ---------------------------------------------------------


@dataclass
class AssetWithScore:
    """An asset with its similarity score."""

    asset: Asset
    score: float


@dataclass
class SimilarityInput:
    """Input for computing similarity and filtering assets."""

    target_embedding: list[float]
    assets: list[Asset]
    top_fraction: float = 0.5  # Keep top 50% most similar


@dataclass
class SimilarityOutput:
    """Output from similarity filtering."""

    filtered_assets: list[Asset]
    scored_assets: list[AssetWithScore]
    threshold_score: float


# ---------------------------------------------------------
# Prompt Types
# ---------------------------------------------------------


@dataclass
class PromptGenerationInput:
    """Input for generating an initial prompt."""

    base_prompt: str
    asset_set: AssetSet
    base_asset_type: AssetType = AssetType.MODEL  # Which asset type is the base


@dataclass
class PromptGenerationOutput:
    """Output from generating a prompt."""

    prompt: str
    base_asset: Asset
    reference_assets: list[Asset]


@dataclass
class PromptModificationInput:
    """Input for modifying a prompt based on analysis."""

    current_prompt: str
    winning_image_descriptions: list[str]
    losing_image_descriptions: list[str]
    visual_similarities: str  # What the winning images have in common
    target_group: TargetGroup
    model: str = 'gpt-4o-mini'


@dataclass
class PromptModificationOutput:
    """Output from modifying a prompt."""

    modified_prompt: str
    modification_notes: str  # LLM's reasoning for the changes
    model_used: str


# ---------------------------------------------------------
# Image Analysis Types
# ---------------------------------------------------------


@dataclass
class ImageAnalysisInput:
    """Input for analyzing winning images."""

    winning_image_descriptions: list[tuple[UUID, str]]  # (image_id, description)
    losing_image_descriptions: list[tuple[UUID, str]]   # (image_id, description)
    model: str = 'gpt-4o-mini'


@dataclass
class ImageAnalysisOutput:
    """Output from analyzing winning images."""

    visual_similarities: str  # What winning images have in common
    differentiation_tags: list[str]  # Concise tags like ["warm colors", "close-up"]
    success_factors: str  # Why these images performed better
    model_used: str


# ---------------------------------------------------------
# Asset Processing Types (for async processor)
# ---------------------------------------------------------


@dataclass
class AssetProcessingInput:
    """Input for processing an asset (description + embedding)."""

    asset: Asset
    description_model: str = 'gpt-4o-mini'
    embedding_model: str = 'text-embedding-3-small'


@dataclass
class AssetProcessingOutput:
    """Output from processing an asset."""

    asset_id: UUID
    description: str
    embedding: list[float]
    description_model: str
    embedding_model: str
    used_fallback: bool = False