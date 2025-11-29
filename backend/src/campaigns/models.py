import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import ARRAY, Column, Float, String
from sqlmodel import Field, Relationship, SQLModel

from models import Asset, BaseModel, CampaignSpec, TargetGroup


# ---------------------------------------------------------
# Enums
# ---------------------------------------------------------


class FlowStepState(str, enum.Enum):
    """State of a flow step in the iteration cycle."""

    GENERATING = 'generating'      # Creating prompt + generating images
    COLLECTING_DATA = 'collecting'  # Gathering metrics for images
    ANALYZING = 'analyzing'        # Picking winners, computing insights
    COMPLETED = 'completed'        # Step finished, ready for next iteration


# ---------------------------------------------------------
# Link Tables (defined first for forward references)
# ---------------------------------------------------------


class GenerationResultAsset(SQLModel, table=True):
    """Link table: assets selected for prompt generation."""

    generation_result_id: UUID = Field(foreign_key='generationresult.id', primary_key=True)
    asset_id: UUID = Field(foreign_key='asset.id', primary_key=True)


class GeneratedImageAsset(SQLModel, table=True):
    """Link table: source assets used to compose a generated image."""

    generated_image_id: UUID = Field(foreign_key='generatedimage.id', primary_key=True)
    asset_id: UUID = Field(foreign_key='asset.id', primary_key=True)


# ---------------------------------------------------------
# Campaign (run instance of CampaignSpec)
# ---------------------------------------------------------


class Campaign(BaseModel, table=True):
    """Campaign - a generated run instance of a CampaignSpec."""

    campaign_spec_id: UUID = Field(foreign_key='campaignspec.id', index=True)

    # Relationships
    campaign_spec: Optional[CampaignSpec] = Relationship()
    campaign_flows: list['CampaignFlow'] = Relationship(back_populates='campaign')


# ---------------------------------------------------------
# CampaignFlow (per target group)
# ---------------------------------------------------------


class CampaignFlow(BaseModel, table=True):
    """Campaign flow - one per target group within a campaign run."""

    campaign_id: UUID = Field(foreign_key='campaign.id', index=True)
    target_group_id: UUID = Field(foreign_key='targetgroup.id', index=True)

    # Relationships
    campaign: Optional['Campaign'] = Relationship(back_populates='campaign_flows')
    target_group: Optional[TargetGroup] = Relationship()
    steps: list['FlowStep'] = Relationship(back_populates='flow')

    @property
    def current_step(self) -> 'FlowStep | None':
        """Get the latest step (highest iteration)."""
        if not self.steps:
            return None
        return max(self.steps, key=lambda s: s.iteration)

    @property
    def current_state(self) -> FlowStepState | None:
        """Derive current state from latest step."""
        step = self.current_step
        return step.state if step else None


# ---------------------------------------------------------
# FlowStep (core iteration unit with state machine)
# ---------------------------------------------------------


class FlowStep(BaseModel, table=True):
    """Flow step - one iteration in the optimization loop."""

    flow_id: UUID = Field(foreign_key='campaignflow.id', index=True)
    iteration: int = Field(index=True)  # 0, 1, 2, ...
    state: FlowStepState = Field(default=FlowStepState.GENERATING)

    # Input from previous step's analysis (null for iteration 0)
    input_embedding: list[float] | None = Field(default=None, sa_column=Column(ARRAY(Float)))
    input_insights: str | None = None

    # Relationships
    flow: Optional['CampaignFlow'] = Relationship(back_populates='steps')
    generation_result: Optional['GenerationResult'] = Relationship(
        back_populates='step',
        sa_relationship_kwargs={'uselist': False},
    )
    analysis_result: Optional['AnalysisResult'] = Relationship(
        back_populates='step',
        sa_relationship_kwargs={'uselist': False},
    )


# ---------------------------------------------------------
# GenerationResult (GENERATING state output)
# ---------------------------------------------------------


class GenerationResult(BaseModel, table=True):
    """Result of the GENERATING state - prompt and images."""

    step_id: UUID = Field(foreign_key='flowstep.id', unique=True, index=True)
    prompt: str  # Generated prompt for image creation
    prompt_notes: str | None = None  # LLM reasoning/explanation

    # Relationships
    step: Optional['FlowStep'] = Relationship(back_populates='generation_result')
    selected_assets: list[Asset] = Relationship(link_model=GenerationResultAsset)
    generated_images: list['GeneratedImage'] = Relationship(back_populates='generation_result')


# ---------------------------------------------------------
# GeneratedImage
# ---------------------------------------------------------


class GeneratedImage(BaseModel, table=True):
    """A generated image from the GENERATING state."""

    generation_result_id: UUID = Field(foreign_key='generationresult.id', index=True)
    file_name: str = Field(index=True)  # Path or URL
    metadata_tags: list[str] | None = Field(default=None, sa_column=Column(ARRAY(String)))
    model_version: str | None = None

    # Relationships
    generation_result: Optional['GenerationResult'] = Relationship(back_populates='generated_images')
    source_assets: list[Asset] = Relationship(link_model=GeneratedImageAsset)
    metrics: Optional['ImageMetrics'] = Relationship(
        back_populates='image',
        sa_relationship_kwargs={'uselist': False},
    )


# ---------------------------------------------------------
# ImageMetrics (COLLECTING_DATA state output)
# ---------------------------------------------------------


class ImageMetrics(BaseModel, table=True):
    """Metrics collected for a generated image."""

    image_id: UUID = Field(foreign_key='generatedimage.id', unique=True, index=True)

    # Raw metrics
    impressions: int = Field(default=0)
    clicks: int = Field(default=0)
    conversions: int = Field(default=0)
    cost: float = Field(default=0.0)

    # Derived metrics (computed on save)
    ctr: float = Field(default=0.0)  # clicks / impressions
    conversion_rate: float = Field(default=0.0)  # conversions / clicks
    cpc: float = Field(default=0.0)  # cost / clicks
    cpa: float = Field(default=0.0)  # cost / conversions

    # Relationships
    image: Optional['GeneratedImage'] = Relationship(back_populates='metrics')

    def compute_derived_metrics(self) -> None:
        """Compute derived metrics from raw values."""
        self.ctr = self.clicks / self.impressions if self.impressions > 0 else 0.0
        self.conversion_rate = self.conversions / self.clicks if self.clicks > 0 else 0.0
        self.cpc = self.cost / self.clicks if self.clicks > 0 else 0.0
        self.cpa = self.cost / self.conversions if self.conversions > 0 else 0.0


# ---------------------------------------------------------
# AnalysisResult (ANALYZING state output)
# ---------------------------------------------------------


class AnalysisResult(BaseModel, table=True):
    """Result of the ANALYZING state - winners and insights."""

    step_id: UUID = Field(foreign_key='flowstep.id', unique=True, index=True)

    # Winners (top 2 image IDs, ordered best first)
    winner_image_ids: list[UUID] = Field(sa_column=Column(ARRAY(String)))

    # Output for next iteration
    # Mean embedding of source assets from winning images
    output_embedding: list[float] = Field(sa_column=Column(ARRAY(Float)))
    qualitative_diff: str  # What made winners better
    diff_tags: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))

    # Relationships
    step: Optional['FlowStep'] = Relationship(back_populates='analysis_result')


# ---------------------------------------------------------
# API Schemas
# ---------------------------------------------------------


class CampaignCreate(SQLModel):
    """Schema for creating a campaign from a spec."""

    campaign_spec_id: UUID


class FlowStepCreate(SQLModel):
    """Schema for creating a new flow step."""

    flow_id: UUID
    input_embedding: list[float] | None = None
    input_insights: str | None = None


class GenerationResultCreate(SQLModel):
    """Schema for creating a generation result."""

    step_id: UUID
    prompt: str
    prompt_notes: str | None = None
    selected_asset_ids: list[UUID] = Field(default_factory=list)


class GeneratedImageCreate(SQLModel):
    """Schema for creating a generated image."""

    generation_result_id: UUID
    file_name: str
    metadata_tags: list[str] | None = None
    model_version: str | None = None
    source_asset_ids: list[UUID] = Field(default_factory=list)


class ImageMetricsCreate(SQLModel):
    """Schema for creating/updating image metrics."""

    image_id: UUID
    impressions: int
    clicks: int
    conversions: int
    cost: float


class AnalysisResultCreate(SQLModel):
    """Schema for creating an analysis result."""

    step_id: UUID
    winner_image_ids: list[UUID]
    output_embedding: list[float]
    qualitative_diff: str
    diff_tags: list[str] = Field(default_factory=list)
