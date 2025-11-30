from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from campaigns.models import (
    AnalysisResult,
    Campaign,
    CampaignFlow,
    FlowStep,
    GeneratedImage,
    GeneratedImageAsset,
    GenerationResult,
    GenerationResultAsset,
    ImageMetrics,
)


class CampaignRepository:
    """Data access layer for Campaign entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ---------------------------------------------------------
    # Campaign
    # ---------------------------------------------------------

    def create_campaign(self, campaign: Campaign) -> Campaign:
        """Create a new campaign."""
        self.session.add(campaign)
        self.session.commit()
        self.session.refresh(campaign)
        return campaign

    def get_campaign(self, campaign_id: UUID) -> Campaign | None:
        """Get a campaign by ID."""
        return self.session.get(Campaign, campaign_id)

    def get_campaigns(self, skip: int = 0, limit: int = 100) -> list[Campaign]:
        """Get all campaigns with pagination."""
        statement = select(Campaign).offset(skip).limit(limit)
        return list(self.session.exec(statement).all())

    def get_campaigns_by_spec(self, campaign_spec_id: UUID) -> list[Campaign]:
        """Get all campaigns for a spec."""
        statement = select(Campaign).where(Campaign.campaign_spec_id == campaign_spec_id)
        return list(self.session.exec(statement).all())

    # ---------------------------------------------------------
    # CampaignFlow
    # ---------------------------------------------------------

    def create_flow(self, flow: CampaignFlow) -> CampaignFlow:
        """Create a new campaign flow."""
        self.session.add(flow)
        self.session.commit()
        self.session.refresh(flow)
        return flow

    def get_flow(self, flow_id: UUID) -> CampaignFlow | None:
        """Get a flow by ID."""
        return self.session.get(CampaignFlow, flow_id)

    def get_flows_by_campaign(self, campaign_id: UUID) -> list[CampaignFlow]:
        """Get all flows for a campaign."""
        statement = select(CampaignFlow).where(CampaignFlow.campaign_id == campaign_id)
        return list(self.session.exec(statement).all())

    # ---------------------------------------------------------
    # FlowStep
    # ---------------------------------------------------------

    def create_step(self, step: FlowStep) -> FlowStep:
        """Create a new flow step."""
        self.session.add(step)
        self.session.commit()
        self.session.refresh(step)
        return step

    def get_step(self, step_id: UUID) -> FlowStep | None:
        """Get a step by ID."""
        return self.session.get(FlowStep, step_id)

    def get_steps_by_flow(self, flow_id: UUID) -> list[FlowStep]:
        """Get all steps for a flow, ordered by iteration."""
        statement = (
            select(FlowStep)
            .where(FlowStep.flow_id == flow_id)
            .order_by(FlowStep.iteration)
        )
        return list(self.session.exec(statement).all())

    def get_latest_step(self, flow_id: UUID) -> FlowStep | None:
        """Get the latest step for a flow."""
        statement = (
            select(FlowStep)
            .where(FlowStep.flow_id == flow_id)
            .order_by(FlowStep.iteration.desc())
            .limit(1)
        )
        return self.session.exec(statement).first()

    def update_step(self, step: FlowStep) -> FlowStep:
        """Update a step."""
        self.session.add(step)
        self.session.commit()
        self.session.refresh(step)
        return step

    # ---------------------------------------------------------
    # GenerationResult
    # ---------------------------------------------------------

    def create_generation_result(self, result: GenerationResult) -> GenerationResult:
        """Create a generation result."""
        self.session.add(result)
        self.session.commit()
        self.session.refresh(result)
        return result

    def get_generation_result(self, result_id: UUID) -> GenerationResult | None:
        """Get a generation result by ID."""
        return self.session.get(GenerationResult, result_id)

    def get_generation_result_by_step(self, step_id: UUID) -> GenerationResult | None:
        """Get the generation result for a step."""
        statement = select(GenerationResult).where(GenerationResult.step_id == step_id)
        return self.session.exec(statement).first()

    def add_generation_result_asset(self, result_id: UUID, asset_id: UUID) -> None:
        """Link an asset to a generation result."""
        link = GenerationResultAsset(generation_result_id=result_id, asset_id=asset_id)
        self.session.add(link)
        self.session.commit()

    # ---------------------------------------------------------
    # GeneratedImage
    # ---------------------------------------------------------

    def create_generated_image(self, image: GeneratedImage) -> GeneratedImage:
        """Create a generated image."""
        self.session.add(image)
        self.session.commit()
        self.session.refresh(image)
        return image

    def get_generated_image(self, image_id: UUID) -> GeneratedImage | None:
        """Get a generated image by ID."""
        return self.session.get(GeneratedImage, image_id)

    def get_images_by_generation_result(self, result_id: UUID) -> list[GeneratedImage]:
        """Get all images for a generation result."""
        statement = select(GeneratedImage).where(
            GeneratedImage.generation_result_id == result_id
        )
        return list(self.session.exec(statement).all())

    def add_generated_image_asset(self, image_id: UUID, asset_id: UUID) -> None:
        """Link a source asset to a generated image."""
        link = GeneratedImageAsset(generated_image_id=image_id, asset_id=asset_id)
        self.session.add(link)
        self.session.commit()

    # ---------------------------------------------------------
    # ImageMetrics
    # ---------------------------------------------------------

    def create_image_metrics(self, metrics: ImageMetrics) -> ImageMetrics:
        """Create metrics for an image."""
        metrics.compute_derived_metrics()
        self.session.add(metrics)
        self.session.commit()
        self.session.refresh(metrics)
        return metrics

    def get_image_metrics(self, image_id: UUID) -> ImageMetrics | None:
        """Get metrics for an image."""
        statement = select(ImageMetrics).where(ImageMetrics.image_id == image_id)
        return self.session.exec(statement).first()

    def update_image_metrics(self, metrics: ImageMetrics) -> ImageMetrics:
        """Update metrics for an image."""
        metrics.compute_derived_metrics()
        self.session.add(metrics)
        self.session.commit()
        self.session.refresh(metrics)
        return metrics

    # ---------------------------------------------------------
    # AnalysisResult
    # ---------------------------------------------------------

    def create_analysis_result(self, result: AnalysisResult) -> AnalysisResult:
        """Create an analysis result."""
        self.session.add(result)
        self.session.commit()
        self.session.refresh(result)
        return result

    def get_analysis_result(self, result_id: UUID) -> AnalysisResult | None:
        """Get an analysis result by ID."""
        return self.session.get(AnalysisResult, result_id)

    def get_analysis_result_by_step(self, step_id: UUID) -> AnalysisResult | None:
        """Get the analysis result for a step."""
        statement = select(AnalysisResult).where(AnalysisResult.step_id == step_id)
        return self.session.exec(statement).first()

    # ---------------------------------------------------------
    # Full Campaign (with eager loading)
    # ---------------------------------------------------------

    def get_campaign_full(self, campaign_id: UUID) -> Campaign | None:
        """Get a campaign with all nested relationships eagerly loaded."""
        statement = (
            select(Campaign)
            .where(Campaign.id == campaign_id)
            .options(
                selectinload(Campaign.campaign_spec),
                selectinload(Campaign.campaign_flows)
                .selectinload(CampaignFlow.target_group),
                selectinload(Campaign.campaign_flows)
                .selectinload(CampaignFlow.steps)
                .selectinload(FlowStep.generation_result)
                .selectinload(GenerationResult.selected_assets),
                selectinload(Campaign.campaign_flows)
                .selectinload(CampaignFlow.steps)
                .selectinload(FlowStep.generation_result)
                .selectinload(GenerationResult.generated_images)
                .selectinload(GeneratedImage.source_assets),
                selectinload(Campaign.campaign_flows)
                .selectinload(CampaignFlow.steps)
                .selectinload(FlowStep.generation_result)
                .selectinload(GenerationResult.generated_images)
                .selectinload(GeneratedImage.metrics),
                selectinload(Campaign.campaign_flows)
                .selectinload(CampaignFlow.steps)
                .selectinload(FlowStep.analysis_result),
            )
        )
        return self.session.exec(statement).first()
