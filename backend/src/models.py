import enum
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

# ---------------------------------------------------------
# Enums
# ---------------------------------------------------------


class StepType(str, enum.Enum):
    """Type of campaign step."""

    PROMPT_GEN = 'prompt_gen'
    IMAGE_GEN = 'image_gen'
    ANALYTICS = 'analytics'


class AnalyticsGoalMetric(str, enum.Enum):
    """Goal metric for analytics."""

    CTR = 'ctr'
    CONVERSION_RATE = 'conversion_rate'
    CONVERSIONS = 'conversions'
    CPC = 'cpc'
    CPA = 'cpa'


class AssetType(str, enum.Enum):
    """Type of asset."""

    BACKGROUND = 'background'
    PRODUCT = 'product'
    MODEL = 'model'
    LOGO = 'logo'


# ---------------------------------------------------------
# Base Model
# ---------------------------------------------------------


class BaseModel(SQLModel):
    """Base model with common fields."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------
# Assets
# ---------------------------------------------------------


class Asset(BaseModel, table=True):
    """Asset (image file)."""

    name: str  # e.g., "Running shoe packshot 1"
    file_name: str = Field(index=True)  # path or URL
    asset_type: AssetType = Field(index=True)  # enum: background, product, model, logo

    # Textual representation of the asset for embeddings (merged from AssetCaption)
    caption: str  # short description for embedding
    tags: list[str] = Field(default_factory=list, sa_column_kwargs={'type_': 'JSON'})  # e.g., ["running", "shoe", "outdoor"]

    # Embedding for assets (text-based for now, merged from AssetEmbedding)
    embedding_model: str | None = None  # e.g., "text-embedding-3-large"
    embedding: list[float] | None = Field(
        default=None, sa_column_kwargs={'type_': 'JSON'}
    )  # embedding vector (optional, may not be generated yet)
