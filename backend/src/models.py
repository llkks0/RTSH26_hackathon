import enum
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, Column, Float, String
from sqlmodel import Field, Relationship, SQLModel

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


class Asset(BaseModel, table=True):
    """Asset (image file)."""

    name: str  # e.g., "Running shoe packshot 1"
    file_name: str = Field(index=True)  # path or URL
    asset_type: AssetType = Field(index=True)  # enum: background, product, model, logo

    # Textual representation of the asset for embeddings (merged from AssetCaption)
    caption: str  # short description for embedding
    tags: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))  # e.g., ["running", "shoe", "outdoor"]

    embedding: list[float] | None = Field(
        default=None, sa_column=Column(ARRAY(Float))
    )  # embedding vector (optional, may not be generated yet)


class AssetCreate(SQLModel):
    """Schema for creating an asset."""

    name: str
    file_name: str
    asset_type: AssetType
    caption: str
    tags: list[str] = Field(default_factory=list)
    embedding: list[float] | None = None


class AssetUpdate(SQLModel):
    """Schema for updating an asset."""

    name: str | None = None
    file_name: str | None = None
    asset_type: AssetType | None = None
    caption: str | None = None
    tags: list[str] | None = None
    embedding: list[float] | None = None


# ---------------------------------------------------------
# Target Groups
# ---------------------------------------------------------


class TargetGroup(BaseModel, table=True):
    """Target group for campaigns."""

    name: str = Field(index=True)  # e.g., "Berlin - Young Professionals"
    city: str | None = None
    age_group: str | None = None  # e.g., "25-35"
    economic_status: str | None = None  # e.g., "mid to high income"
    description: str | None = None  # free text description

    # Relationships
    campaign_flows: list[CampaignFlow] = Relationship(back_populates='target_group')


# ---------------------------------------------------------
# Campaigns and Flows
# ---------------------------------------------------------


class Campaign(BaseModel, table=True):
    """Campaign."""

    name: str = Field(index=True)
    base_prompt: str  # generic prompt template for the campaign

    # Relationships
    campaign_flows: list[CampaignFlow] = Relationship(back_populates='campaign')


class CampaignFlow(BaseModel, table=True):
    """Campaign flow per target group."""

    campaign_id: UUID = Field(foreign_key='campaign.id', index=True)
    target_group_id: UUID = Field(foreign_key='targetgroup.id', index=True)
    initial_prompt: str  # starting prompt for this flow
    max_iterations: int  # e.g., 2 or 3

    # Relationships
    campaign: Campaign | None = Relationship(back_populates='campaign_flows')
    target_group: TargetGroup | None = Relationship(back_populates='campaign_flows')
    campaign_steps: list[CampaignStep] = Relationship(back_populates='campaign_flow')


# ---------------------------------------------------------
# Steps and Step Results
# ---------------------------------------------------------


class CampaignStep(BaseModel, table=True):
    """Campaign step (prompt_gen, image_gen, or analytics)."""

    campaign_flow_id: UUID = Field(foreign_key='campaignflow.id', index=True)
    step_type: StepType = Field(index=True)
    order_index: int = Field(index=True)  # iteration and within-iteration ordering
    input_step_id: UUID | None = Field(default=None, foreign_key='campaignstep.id')

    # For debugging and analysis of LLM calls
    raw_llm_prompt: str | None = None  # text sent to LLM (system + user serialized)
    raw_llm_response: str | None = None  # raw JSON string or original response

    # Relationships
    campaign_flow: CampaignFlow | None = Relationship(back_populates='campaign_steps')
    prompt_gen_result: PromptGenResult | None = Relationship(back_populates='step', sa_relationship_kwargs={'uselist': False})
    prompt_embedding: PromptEmbedding | None = Relationship(back_populates='step', sa_relationship_kwargs={'uselist': False})
    campaign_images: list[CampaignImage] = Relationship(back_populates='step')
    analytics_result: AnalyticsResult | None = Relationship(back_populates='step', sa_relationship_kwargs={'uselist': False})


class PromptGenResult(BaseModel, table=True):
    """Prompt generation result."""

    step_id: UUID = Field(foreign_key='campaignstep.id', unique=True)
    prompt: str  # final prompt string used for image generation
    notes: str | None = None  # explanation from LLM, if any

    # Relationships
    step: CampaignStep | None = Relationship(back_populates='prompt_gen_result')
    prompt_gen_result_assets: list[PromptGenResultAsset] = Relationship(back_populates='prompt_gen_result')


class PromptGenResultAsset(BaseModel, table=True):
    """Assets selected for a prompt generation result."""

    step_id: UUID = Field(foreign_key='campaignstep.id', index=True)
    asset_id: UUID = Field(foreign_key='asset.id', index=True)

    # Relationships
    prompt_gen_result: PromptGenResult | None = Relationship(back_populates='prompt_gen_result_assets')
    asset: Asset | None = Relationship(back_populates='prompt_gen_result_assets')


class PromptEmbedding(BaseModel, table=True):
    """Prompt embedding (optional but useful)."""

    step_id: UUID = Field(foreign_key='campaignstep.id', unique=True)
    model: str  # e.g., "text-embedding-3-large"
    embedding: list[float] = Field(sa_column=Column(ARRAY(Float)))  # embedding vector

    # Relationships
    step: CampaignStep | None = Relationship(back_populates='prompt_embedding')


# ---------------------------------------------------------
# Image Generation
# ---------------------------------------------------------


class GeneratedImage(BaseModel, table=True):
    """Generated image."""

    file_name: str = Field(index=True)  # path or URL of the generated image
    metadata_tags: list[str] | None = Field(
        default=None, sa_column=Column(ARRAY(String))
    )  # e.g., ["warm colors", "close-up", "indoor", "person visible"]
    model_version: str | None = None  # image model version identifier

    # Relationships
    generated_image_assets: list[GeneratedImageAsset] = Relationship(back_populates='generated_image')
    campaign_images: list[CampaignImage] = Relationship(back_populates='generated_image')


class GeneratedImageAsset(BaseModel, table=True):
    """Link between a generated image and assets that were used to compose it."""

    generated_image_id: UUID = Field(foreign_key='generatedimage.id', index=True)
    asset_id: UUID = Field(foreign_key='asset.id', index=True)

    # Relationships
    generated_image: GeneratedImage | None = Relationship(back_populates='generated_image_assets')
    asset: Asset | None = Relationship(back_populates='generated_image_assets')


# ---------------------------------------------------------
# CampaignImage and Analytics Metrics
# ---------------------------------------------------------


class CampaignImage(BaseModel, table=True):
    """Campaign image - a generated image as an ad creative within a specific ImageGen step."""

    step_id: UUID = Field(foreign_key='campaignstep.id', index=True)
    generated_image_id: UUID = Field(foreign_key='generatedimage.id', index=True)

    # Optional text components for the ad (can be LLM generated)
    headline: str | None = None
    description_line1: str | None = None
    description_line2: str | None = None

    # Prompt that was used to generate this image
    final_prompt: str

    # Mocked analytics metrics for this creative
    impressions: int = Field(default=0)  # total impressions
    clicks: int = Field(default=0)  # total clicks
    conversions: int = Field(default=0)  # total conversions
    cost: float = Field(default=0.0)  # total cost in campaign currency

    # Derived metrics for convenience
    ctr: float = Field(default=0.0)  # clicks / impressions
    conversion_rate: float = Field(default=0.0)  # conversions / clicks
    cpc: float = Field(default=0.0)  # cost / clicks
    cpa: float = Field(default=0.0)  # cost / conversions

    # Relationships
    step: CampaignStep | None = Relationship(back_populates='campaign_images')
    generated_image: GeneratedImage | None = Relationship(back_populates='campaign_images')
    analytics_best_images: list[AnalyticsBestImage] = Relationship(back_populates='campaign_image')


# ---------------------------------------------------------
# Analytics Results
# ---------------------------------------------------------


class AnalyticsResult(BaseModel, table=True):
    """Analytics result."""

    step_id: UUID = Field(foreign_key='campaignstep.id', unique=True)
    goal_metric: AnalyticsGoalMetric  # e.g., "ctr" or "conversions"

    # LLM derived explanation and tags
    differentiation_text: str  # human readable explanation from LLM
    differentiation_tags: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))  # concise tags describing what works

    # Relationships
    step: CampaignStep | None = Relationship(back_populates='analytics_result')
    analytics_best_images: list[AnalyticsBestImage] = Relationship(back_populates='analytics_result')


class AnalyticsBestImage(BaseModel, table=True):
    """Best images for a given analytics result."""

    analytics_result_id: UUID = Field(foreign_key='analyticsresult.id', index=True)
    campaign_image_id: UUID = Field(foreign_key='campaignimage.id', index=True)
    rank: int  # 1, 2, 3...

    # Relationships
    analytics_result: AnalyticsResult | None = Relationship(back_populates='analytics_best_images')
    campaign_image: CampaignImage | None = Relationship(back_populates='analytics_best_images')
