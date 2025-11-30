import logging
from uuid import UUID

from campaigns.models import (
    AnalysisResult,
    AnalysisResultCreate,
    Campaign,
    CampaignCreate,
    CampaignFlow,
    FlowStep,
    FlowStepCreate,
    FlowStepState,
    GeneratedImage,
    GeneratedImageCreate,
    GenerationResult,
    GenerationResultCreate,
    ImageMetrics,
    ImageMetricsCreate,
)
from campaigns.repository import CampaignRepository
from models import CampaignSpec

logger = logging.getLogger(__name__)


class CampaignNotFoundError(Exception):
    """Raised when a campaign is not found."""

    def __init__(self, campaign_id: UUID) -> None:
        self.campaign_id = campaign_id
        super().__init__(f'Campaign with id {campaign_id} not found')


class CampaignAlreadyExistsError(Exception):
    """Raised when attempting to create a campaign for a spec that already has one."""

    def __init__(self, campaign_spec_id: UUID) -> None:
        self.campaign_spec_id = campaign_spec_id
        super().__init__(f'A campaign already exists for campaign spec {campaign_spec_id}')


class FlowNotFoundError(Exception):
    """Raised when a flow is not found."""

    def __init__(self, flow_id: UUID) -> None:
        self.flow_id = flow_id
        super().__init__(f'CampaignFlow with id {flow_id} not found')


class StepNotFoundError(Exception):
    """Raised when a step is not found."""

    def __init__(self, step_id: UUID) -> None:
        self.step_id = step_id
        super().__init__(f'FlowStep with id {step_id} not found')


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, current_state: FlowStepState, target_state: FlowStepState) -> None:
        self.current_state = current_state
        self.target_state = target_state
        super().__init__(f'Cannot transition from {current_state} to {target_state}')


class CampaignService:
    """Business logic layer for Campaign operations."""

    def __init__(self, repository: CampaignRepository) -> None:
        self.repository = repository

    # ---------------------------------------------------------
    # Campaign Operations
    # ---------------------------------------------------------

    def create_campaign(self, data: CampaignCreate, spec: CampaignSpec) -> Campaign:
        """Create a new campaign from a spec and initialize flows for each target group."""
        logger.info(f"Creating campaign from spec: {spec.id} ({spec.name})")

        # Check if a campaign already exists for this spec
        existing_campaigns = self.repository.get_campaigns_by_spec(data.campaign_spec_id)
        if existing_campaigns:
            logger.warning(f"Campaign already exists for spec {data.campaign_spec_id}")
            raise CampaignAlreadyExistsError(data.campaign_spec_id)

        logger.info(f"Spec base_prompt: {spec.base_prompt[:50]}...")
        logger.info(f"Spec target_groups attribute: {spec.target_groups}")
        logger.info(f"Spec target_groups type: {type(spec.target_groups)}")
        logger.info(f"Spec target_groups len: {len(spec.target_groups) if spec.target_groups else 'None'}")

        campaign = Campaign(campaign_spec_id=data.campaign_spec_id)
        campaign = self.repository.create_campaign(campaign)
        logger.info(f"Created campaign: {campaign.id}")

        # Create a flow for each target group in the spec
        flow_count = 0
        for target_group in spec.target_groups:
            logger.info(f"Creating flow for target group: {target_group.id} ({target_group.name})")
            flow = CampaignFlow(
                campaign_id=campaign.id,
                target_group_id=target_group.id,
                initial_prompt=spec.base_prompt,
            )
            self.repository.create_flow(flow)
            flow_count += 1
            logger.info(f"Created flow: {flow.id}")

        logger.info(f"Total flows created: {flow_count}")
        return campaign

    def get_campaign(self, campaign_id: UUID) -> Campaign:
        """Get a campaign by ID."""
        campaign = self.repository.get_campaign(campaign_id)
        if not campaign:
            raise CampaignNotFoundError(campaign_id)
        return campaign

    def list_campaigns(self, skip: int = 0, limit: int = 100) -> list[Campaign]:
        """List all campaigns."""
        return self.repository.get_campaigns(skip=skip, limit=limit)

    def get_campaign_full(self, campaign_id: UUID) -> Campaign:
        """Get a campaign with all nested relationships (flows, steps, results)."""
        campaign = self.repository.get_campaign_full(campaign_id)
        if not campaign:
            raise CampaignNotFoundError(campaign_id)
        return campaign

    # ---------------------------------------------------------
    # Flow Operations
    # ---------------------------------------------------------

    def get_flow(self, flow_id: UUID) -> CampaignFlow:
        """Get a flow by ID."""
        flow = self.repository.get_flow(flow_id)
        if not flow:
            raise FlowNotFoundError(flow_id)
        return flow

    def get_flows_by_campaign(self, campaign_id: UUID) -> list[CampaignFlow]:
        """Get all flows for a campaign."""
        return self.repository.get_flows_by_campaign(campaign_id)

    def get_current_step(self, flow_id: UUID) -> FlowStep | None:
        """Get the current (latest) step for a flow."""
        return self.repository.get_latest_step(flow_id)

    # ---------------------------------------------------------
    # Step Operations
    # ---------------------------------------------------------

    def create_step(self, data: FlowStepCreate) -> FlowStep:
        """Create a new step for a flow."""
        # Get the latest step to determine iteration
        latest_step = self.repository.get_latest_step(data.flow_id)
        iteration = (latest_step.iteration + 1) if latest_step else 0

        step = FlowStep(
            flow_id=data.flow_id,
            iteration=iteration,
            state=FlowStepState.GENERATING,
            input_embedding=data.input_embedding,
            input_insights=data.input_insights,
        )
        return self.repository.create_step(step)

    def get_step(self, step_id: UUID) -> FlowStep:
        """Get a step by ID."""
        step = self.repository.get_step(step_id)
        if not step:
            raise StepNotFoundError(step_id)
        return step

    def get_steps_by_flow(self, flow_id: UUID) -> list[FlowStep]:
        """Get all steps for a flow."""
        return self.repository.get_steps_by_flow(flow_id)

    # ---------------------------------------------------------
    # State Transitions
    # ---------------------------------------------------------

    def transition_to_collecting(self, step_id: UUID) -> FlowStep:
        """Transition step from GENERATING to COLLECTING_DATA."""
        step = self.get_step(step_id)
        if step.state != FlowStepState.GENERATING:
            raise InvalidStateTransitionError(step.state, FlowStepState.COLLECTING_DATA)

        # Verify generation result exists
        gen_result = self.repository.get_generation_result_by_step(step_id)
        if not gen_result:
            raise ValueError('Cannot transition: generation result not created')

        step.state = FlowStepState.COLLECTING_DATA
        return self.repository.update_step(step)

    def transition_to_analyzing(self, step_id: UUID) -> FlowStep:
        """Transition step from COLLECTING_DATA to ANALYZING."""
        step = self.get_step(step_id)
        if step.state != FlowStepState.COLLECTING_DATA:
            raise InvalidStateTransitionError(step.state, FlowStepState.ANALYZING)

        step.state = FlowStepState.ANALYZING
        return self.repository.update_step(step)

    def transition_to_completed(self, step_id: UUID) -> FlowStep:
        """Transition step from ANALYZING to COMPLETED."""
        step = self.get_step(step_id)
        if step.state != FlowStepState.ANALYZING:
            raise InvalidStateTransitionError(step.state, FlowStepState.COMPLETED)

        # Verify analysis result exists
        analysis = self.repository.get_analysis_result_by_step(step_id)
        if not analysis:
            raise ValueError('Cannot transition: analysis result not created')

        step.state = FlowStepState.COMPLETED
        return self.repository.update_step(step)

    # ---------------------------------------------------------
    # Generation Result Operations
    # ---------------------------------------------------------

    def create_generation_result(self, data: GenerationResultCreate) -> GenerationResult:
        """Create a generation result for a step."""
        result = GenerationResult(
            step_id=data.step_id,
            prompt=data.prompt,
            prompt_notes=data.prompt_notes,
        )
        result = self.repository.create_generation_result(result)

        # Link selected assets
        for asset_id in data.selected_asset_ids:
            self.repository.add_generation_result_asset(result.id, asset_id)

        return result

    def get_generation_result(self, step_id: UUID) -> GenerationResult | None:
        """Get the generation result for a step."""
        return self.repository.get_generation_result_by_step(step_id)

    # ---------------------------------------------------------
    # Generated Image Operations
    # ---------------------------------------------------------

    def create_generated_image(self, data: GeneratedImageCreate) -> GeneratedImage:
        """Create a generated image."""
        image = GeneratedImage(
            generation_result_id=data.generation_result_id,
            file_name=data.file_name,
            metadata_tags=data.metadata_tags,
            model_version=data.model_version,
        )
        image = self.repository.create_generated_image(image)

        # Link source assets
        for asset_id in data.source_asset_ids:
            self.repository.add_generated_image_asset(image.id, asset_id)

        return image

    def get_images_by_step(self, step_id: UUID) -> list[GeneratedImage]:
        """Get all generated images for a step."""
        gen_result = self.repository.get_generation_result_by_step(step_id)
        if not gen_result:
            return []
        return self.repository.get_images_by_generation_result(gen_result.id)

    # ---------------------------------------------------------
    # Image Metrics Operations
    # ---------------------------------------------------------

    def create_image_metrics(self, data: ImageMetricsCreate) -> ImageMetrics:
        """Create metrics for an image."""
        metrics = ImageMetrics(
            image_id=data.image_id,
            impressions=data.impressions,
            clicks=data.clicks,
            conversions=data.conversions,
            cost=data.cost,
        )
        return self.repository.create_image_metrics(metrics)

    def get_image_metrics(self, image_id: UUID) -> ImageMetrics | None:
        """Get metrics for an image."""
        return self.repository.get_image_metrics(image_id)

    # ---------------------------------------------------------
    # Analysis Result Operations
    # ---------------------------------------------------------

    def create_analysis_result(self, data: AnalysisResultCreate) -> AnalysisResult:
        """Create an analysis result for a step."""
        result = AnalysisResult(
            step_id=data.step_id,
            winner_image_ids=data.winner_image_ids,
            output_embedding=data.output_embedding,
            qualitative_diff=data.qualitative_diff,
            diff_tags=data.diff_tags,
        )
        return self.repository.create_analysis_result(result)

    def get_analysis_result(self, step_id: UUID) -> AnalysisResult | None:
        """Get the analysis result for a step."""
        return self.repository.get_analysis_result_by_step(step_id)

    # ---------------------------------------------------------
    # Iteration Helpers
    # ---------------------------------------------------------

    def start_next_iteration(self, flow_id: UUID) -> FlowStep:
        """Start the next iteration for a flow using previous analysis results."""
        latest_step = self.repository.get_latest_step(flow_id)

        if latest_step is None:
            # First iteration - no input from previous step
            return self.create_step(FlowStepCreate(flow_id=flow_id))

        if latest_step.state != FlowStepState.COMPLETED:
            raise ValueError(
                f'Cannot start next iteration: current step is in state {latest_step.state}'
            )

        # Get analysis result from previous step
        analysis = self.repository.get_analysis_result_by_step(latest_step.id)
        if not analysis:
            raise ValueError('Cannot start next iteration: no analysis result found')

        # Create new step with input from previous analysis
        return self.create_step(
            FlowStepCreate(
                flow_id=flow_id,
                input_embedding=analysis.output_embedding,
                input_insights=analysis.qualitative_diff,
            )
        )
