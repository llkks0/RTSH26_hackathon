import enum
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, Column, Float, String
from sqlmodel import Field, Relationship, SQLModel


# ---------------------------------------------------------
# Enums
# ---------------------------------------------------------


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
    SLOGAN = 'slogan'
    TAGLINE = 'tagline'
    HEADLINE = 'headline'
    DESCRIPTION = 'description'
    CTA = 'cta'


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


class AssetBase(SQLModel):
    """Base schema for Asset - shared fields for create/read operations."""

    name: str  # e.g., "Running shoe packshot 1"
    file_name: str  # path or URL
    asset_type: AssetType  # enum: background, product, model, logo
    caption: str  # short description for embedding
    tags: list[str] = Field(default_factory=list)
    embedding: list[float] | None = None


class Asset(BaseModel, AssetBase, table=True):
    """Asset (image file) - database table model."""

    # Override fields that need database-specific config
    file_name: str = Field(index=True)
    asset_type: AssetType = Field(index=True)
    tags: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    embedding: list[float] | None = Field(default=None, sa_column=Column(ARRAY(Float)))


# AssetCreate is just the base - no id/created_at needed
AssetCreate = AssetBase


class AssetUpdate(SQLModel):
    """Schema for partial updates - all fields optional."""

    name: str | None = None
    file_name: str | None = None
    asset_type: AssetType | None = None
    caption: str | None = None
    tags: list[str] | None = None
    embedding: list[float] | None = None


# ---------------------------------------------------------
# Link Tables (must be defined before models that use them)
# ---------------------------------------------------------


class CampaignSpecAsset(SQLModel, table=True):
    """Link table between CampaignSpec and Asset (many-to-many)."""

    campaign_spec_id: UUID = Field(foreign_key='campaignspec.id', primary_key=True)
    asset_id: UUID = Field(foreign_key='asset.id', primary_key=True)


class CampaignSpecTargetGroup(SQLModel, table=True):
    """Link table between CampaignSpec and TargetGroup (many-to-many)."""

    campaign_spec_id: UUID = Field(foreign_key='campaignspec.id', primary_key=True)
    target_group_id: UUID = Field(foreign_key='targetgroup.id', primary_key=True)


# ---------------------------------------------------------
# Target Groups
# ---------------------------------------------------------


class TargetGroupBase(SQLModel):
    """Base schema for TargetGroup."""

    name: str
    city: str | None = None
    age_group: str | None = None
    economic_status: str | None = None
    description: str | None = None


class TargetGroup(BaseModel, TargetGroupBase, table=True):
    """Target group for campaigns."""

    name: str = Field(index=True)


TargetGroupCreate = TargetGroupBase


class TargetGroupUpdate(SQLModel):
    """Schema for partial updates."""

    name: str | None = None
    city: str | None = None
    age_group: str | None = None
    economic_status: str | None = None
    description: str | None = None


# ---------------------------------------------------------
# Campaign Specs (user-configured templates)
# ---------------------------------------------------------


class CampaignSpecBase(SQLModel):
    """Base schema for CampaignSpec."""

    name: str
    base_prompt: str
    max_iterations: int = 2


class CampaignSpec(BaseModel, CampaignSpecBase, table=True):
    """Campaign specification - user-configured template."""

    name: str = Field(index=True)

    # Relationships (many-to-many via link tables)
    base_assets: list[Asset] = Relationship(link_model=CampaignSpecAsset)
    target_groups: list[TargetGroup] = Relationship(link_model=CampaignSpecTargetGroup)
    # Note: campaigns relationship is defined in campaigns/models.py to avoid circular imports


class CampaignSpecResponse(CampaignSpecBase):
    """Response model for CampaignSpec with target_group_ids."""

    id: UUID
    created_at: datetime
    target_group_ids: list[UUID] = Field(default_factory=list)

    @classmethod
    def from_campaign_spec(cls, spec: CampaignSpec) -> 'CampaignSpecResponse':
        """Create response from CampaignSpec model."""
        return cls(
            id=spec.id,
            created_at=spec.created_at,
            name=spec.name,
            base_prompt=spec.base_prompt,
            max_iterations=spec.max_iterations,
            target_group_ids=[tg.id for tg in spec.target_groups],
        )


class CampaignSpecCreate(CampaignSpecBase):
    """Schema for creating a campaign spec."""

    target_group_ids: list[UUID] = Field(default_factory=list)


class CampaignSpecUpdate(SQLModel):
    """Schema for partial updates."""

    name: str | None = None
    base_prompt: str | None = None
    max_iterations: int | None = None
    target_group_ids: list[UUID] | None = None
