"""
Flow Orchestrator - Job-Based Scheduler.

Uses a job-based approach where the orchestrator finds and executes
the next available job across all campaigns/flows.

Jobs are determined by the current state of each flow step:
- No step exists → Create first step (GENERATING)
- GENERATING → Execute generation, transition to COLLECTING_DATA
- COLLECTING_DATA → Execute data collection, transition to ANALYZING
- ANALYZING → Execute analysis, transition to COMPLETED
- COMPLETED → Check if more iterations needed, create next step

All job execution methods are async for non-blocking operation.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID

from sqlmodel import Session

logger = logging.getLogger(__name__)

from campaigns.models import (
    AnalysisResultCreate,
    Campaign,
    CampaignCreate,
    CampaignFlow,
    FlowStepCreate,
    FlowStepState,
    GeneratedImageCreate,
    GenerationResultCreate,
    ImageMetricsCreate,
)
from campaigns.repository import CampaignRepository
from campaigns.service import CampaignService
from models import Asset, CampaignSpec

from .analysis import analyze_winning_images, select_top_images_by_score
from .analytics import generate_analytics_for_images
from .asset_selection import get_base_and_reference_assets, select_asset_sets
from .embedding import compute_mean_embedding
from .image import describe_image_from_path, describe_image_from_url
from .image_generator import generate_image_with_flux
from .prompt import generate_initial_prompt, modify_prompt_from_analysis
from .similarity import compute_type_embeddings_from_winners, filter_assets_by_iteration
from .types import (
    AnalyticsGenerationInput,
    AssetSelectionInput,
    ImageAnalysisInput,
    PromptGenerationInput,
    PromptModificationInput,
)


class JobType(str, Enum):
    """Types of jobs the orchestrator can execute."""

    CREATE_FIRST_STEP = "create_first_step"
    RUN_GENERATING = "run_generating"
    RUN_COLLECTING_DATA = "run_collecting_data"
    RUN_ANALYZING = "run_analyzing"
    CREATE_NEXT_ITERATION = "create_next_iteration"
    CAMPAIGN_COMPLETE = "campaign_complete"


@dataclass
class OrchestrationConfig:
    """Configuration for the orchestrator."""

    num_images_per_step: int = 5
    top_n_winners: int = 2
    description_model: str = 'gpt-4o-mini'
    embedding_model: str = 'text-embedding-3-small'
    analytics_model: str = 'gpt-4o-mini'
    analysis_model: str = 'gpt-4o-mini'
    image_width: int = 1024
    image_height: int = 1024


@dataclass
class Job:
    """Represents a job to be executed."""

    job_type: JobType
    flow_id: UUID
    step_id: UUID | None = None
    priority: int = 0  # Lower is higher priority

    def __lt__(self, other: Job) -> bool:
        return self.priority < other.priority


@dataclass
class JobResult:
    """Result of executing a job."""

    job: Job
    success: bool
    next_job: Job | None = None
    error: str | None = None
    data: dict = field(default_factory=dict)


@dataclass
class CampaignInitResult:
    """Result of initializing a campaign."""

    campaign: Campaign
    campaign_id: UUID
    flow_ids: list[UUID]
    initial_jobs: list[Job]
    target_groups: list[str]


class FlowOrchestrator:
    """
    Job-based orchestrator for the image generation pipeline.

    Instead of running flows sequentially, this orchestrator:
    1. Scans all flows to find available jobs
    2. Returns the highest priority job to execute
    3. Executes jobs one at a time, returning the result

    This allows for:
    - Async/distributed execution
    - Better error recovery
    - Progress tracking
    - Prioritization across campaigns
    """

    def __init__(
        self,
        session: Session,
        config: OrchestrationConfig | None = None,
    ) -> None:
        self.session = session
        self.config = config or OrchestrationConfig()
        self.repository = CampaignRepository(session)
        self.service = CampaignService(self.repository)

    # ---------------------------------------------------------
    # Campaign Initialization
    # ---------------------------------------------------------

    def initialize_campaign(
        self,
        campaign_spec: CampaignSpec,
    ) -> CampaignInitResult:
        """
        Initialize a new campaign from a campaign spec.

        Creates the campaign, flows for each target group, and returns
        the initial jobs that need to be executed.

        Args:
            campaign_spec: The campaign specification to use

        Returns:
            CampaignInitResult with campaign, flows, and initial jobs
        """
        # Create the campaign (this also creates flows for each target group)
        campaign = self.service.create_campaign(
            CampaignCreate(campaign_spec_id=campaign_spec.id),
            campaign_spec,
        )

        # Refresh to get the flows
        self.session.refresh(campaign)

        # Collect flow IDs and target group names
        flow_ids: list[UUID] = []
        target_groups: list[str] = []

        for flow in campaign.campaign_flows:
            flow_ids.append(flow.id)
            if flow.target_group:
                target_groups.append(flow.target_group.name)

        # Get initial jobs (CREATE_FIRST_STEP for each flow)
        initial_jobs = self.get_all_pending_jobs(campaign.id)

        return CampaignInitResult(
            campaign=campaign,
            campaign_id=campaign.id,
            flow_ids=flow_ids,
            initial_jobs=initial_jobs,
            target_groups=target_groups,
        )

    async def initialize_campaign_with_first_steps(
        self,
        campaign_spec: CampaignSpec,
    ) -> CampaignInitResult:
        """
        Initialize a campaign and create the first step for each flow.

        This is a convenience method that:
        1. Creates the campaign and flows
        2. Executes CREATE_FIRST_STEP for each flow
        3. Returns the campaign with RUN_GENERATING jobs ready

        Args:
            campaign_spec: The campaign specification to use

        Returns:
            CampaignInitResult with campaign and RUN_GENERATING jobs
        """
        # First initialize the campaign
        init_result = self.initialize_campaign(campaign_spec)

        # Execute all CREATE_FIRST_STEP jobs
        for job in init_result.initial_jobs:
            if job.job_type == JobType.CREATE_FIRST_STEP:
                await self._execute_create_first_step(job, campaign_spec)

        # Get the updated jobs (should now be RUN_GENERATING)
        updated_jobs = self.get_all_pending_jobs(init_result.campaign_id)

        return CampaignInitResult(
            campaign=init_result.campaign,
            campaign_id=init_result.campaign_id,
            flow_ids=init_result.flow_ids,
            initial_jobs=updated_jobs,
            target_groups=init_result.target_groups,
        )

    # ---------------------------------------------------------
    # Job Discovery
    # ---------------------------------------------------------

    def get_next_job(self, campaign_id: UUID | None = None) -> Job | None:
        """
        Find the next job to execute.

        Scans all flows (or flows for a specific campaign) and returns
        the highest priority job that needs to be executed.

        Args:
            campaign_id: Optional campaign to limit search to

        Returns:
            The next Job to execute, or None if no jobs available
        """
        jobs: list[Job] = []

        # Get flows to check
        if campaign_id:
            flows = self.repository.get_flows_by_campaign(campaign_id)
        else:
            # Get all flows from all campaigns
            campaigns = self.repository.get_campaigns()
            flows = []
            for campaign in campaigns:
                flows.extend(self.repository.get_flows_by_campaign(campaign.id))

        for flow in flows:
            job = self._get_job_for_flow(flow)
            if job:
                jobs.append(job)

        if not jobs:
            return None

        # Return highest priority job
        jobs.sort()
        return jobs[0]

    def get_all_pending_jobs(self, campaign_id: UUID | None = None) -> list[Job]:
        """
        Get all pending jobs across all flows.

        Args:
            campaign_id: Optional campaign to limit search to

        Returns:
            List of all pending jobs, sorted by priority
        """
        jobs: list[Job] = []

        if campaign_id:
            flows = self.repository.get_flows_by_campaign(campaign_id)
        else:
            campaigns = self.repository.get_campaigns()
            flows = []
            for campaign in campaigns:
                flows.extend(self.repository.get_flows_by_campaign(campaign.id))

        for flow in flows:
            job = self._get_job_for_flow(flow)
            if job:
                jobs.append(job)

        jobs.sort()
        return jobs

    def _get_job_for_flow(self, flow: CampaignFlow) -> Job | None:
        """Determine what job needs to be done for a flow."""
        latest_step = self.repository.get_latest_step(flow.id)

        # No step exists - need to create first step
        if latest_step is None:
            return Job(
                job_type=JobType.CREATE_FIRST_STEP,
                flow_id=flow.id,
                priority=0,
            )

        # Check current state
        if latest_step.state == FlowStepState.GENERATING:
            # Check if generation result exists
            gen_result = self.repository.get_generation_result_by_step(latest_step.id)
            if gen_result is None:
                return Job(
                    job_type=JobType.RUN_GENERATING,
                    flow_id=flow.id,
                    step_id=latest_step.id,
                    priority=1,
                )
            # Generation done but not transitioned - still need to run
            return Job(
                job_type=JobType.RUN_GENERATING,
                flow_id=flow.id,
                step_id=latest_step.id,
                priority=1,
            )

        elif latest_step.state == FlowStepState.COLLECTING_DATA:
            return Job(
                job_type=JobType.RUN_COLLECTING_DATA,
                flow_id=flow.id,
                step_id=latest_step.id,
                priority=2,
            )

        elif latest_step.state == FlowStepState.ANALYZING:
            return Job(
                job_type=JobType.RUN_ANALYZING,
                flow_id=flow.id,
                step_id=latest_step.id,
                priority=3,
            )

        elif latest_step.state == FlowStepState.COMPLETED:
            # Check if more iterations needed
            campaign = flow.campaign
            if campaign and campaign.campaign_spec:
                max_iterations = campaign.campaign_spec.max_iterations
                if latest_step.iteration < max_iterations - 1:
                    return Job(
                        job_type=JobType.CREATE_NEXT_ITERATION,
                        flow_id=flow.id,
                        step_id=latest_step.id,
                        priority=0,
                    )

            # Campaign is complete for this flow
            return None

        return None

    # ---------------------------------------------------------
    # Job Execution
    # ---------------------------------------------------------

    async def execute_job(
        self,
        job: Job,
        assets: list[Asset],
        campaign_spec: CampaignSpec,
    ) -> JobResult:
        """
        Execute a single job.

        Args:
            job: The job to execute
            assets: Available assets for the campaign
            campaign_spec: The campaign specification

        Returns:
            JobResult with success status and next job
        """
        try:
            if job.job_type == JobType.CREATE_FIRST_STEP:
                return await self._execute_create_first_step(job, campaign_spec)

            elif job.job_type == JobType.RUN_GENERATING:
                return await self._execute_generating(job, assets, campaign_spec)

            elif job.job_type == JobType.RUN_COLLECTING_DATA:
                return await self._execute_collecting_data(job)

            elif job.job_type == JobType.RUN_ANALYZING:
                return await self._execute_analyzing(job, campaign_spec)

            elif job.job_type == JobType.CREATE_NEXT_ITERATION:
                return await self._execute_create_next_iteration(job)

            else:
                return JobResult(
                    job=job,
                    success=False,
                    error=f"Unknown job type: {job.job_type}",
                )

        except Exception as e:
            # Rollback transaction on error to prevent cascading failures
            self.session.rollback()
            return JobResult(
                job=job,
                success=False,
                error=str(e),
            )

    async def run_next_job(
        self,
        assets: list[Asset],
        campaign_spec: CampaignSpec,
        campaign_id: UUID | None = None,
    ) -> JobResult | None:
        """
        Find and execute the next available job.

        Convenience method that combines get_next_job and execute_job.

        Args:
            assets: Available assets
            campaign_spec: Campaign specification
            campaign_id: Optional campaign to limit to

        Returns:
            JobResult if a job was executed, None if no jobs available
        """
        job = self.get_next_job(campaign_id)
        if job is None:
            return None

        return await self.execute_job(job, assets, campaign_spec)

    # ---------------------------------------------------------
    # Job Executors
    # ---------------------------------------------------------

    async def _execute_create_first_step(
        self,
        job: Job,
        campaign_spec: CampaignSpec,
    ) -> JobResult:
        """Create the first step for a flow."""
        step = self.service.create_step(
            FlowStepCreate(flow_id=job.flow_id)
        )

        return JobResult(
            job=job,
            success=True,
            next_job=Job(
                job_type=JobType.RUN_GENERATING,
                flow_id=job.flow_id,
                step_id=step.id,
                priority=1,
            ),
            data={"step_id": str(step.id), "iteration": step.iteration},
        )

    async def _execute_generating(
        self,
        job: Job,
        assets: list[Asset],
        campaign_spec: CampaignSpec,
    ) -> JobResult:
        """Execute the GENERATING phase."""
        if job.step_id is None:
            return JobResult(job=job, success=False, error="No step_id provided")

        step = self.service.get_step(job.step_id)
        flow = self.repository.get_flow(job.flow_id)

        # Determine prompt to use
        if step.input_insights:
            prompt = step.input_insights  # Modified prompt from previous analysis
        else:
            prompt = flow.initial_prompt  # Use flow's initial prompt (from campaign spec)

        # Filter assets based on iteration
        current_assets = assets
        if step.input_embedding and step.iteration > 0:
            # Get type-specific embeddings from previous step's winner assets
            type_embeddings: dict[str, list[float]] | None = None

            # Find the previous step to get winner images
            previous_steps = self.repository.get_steps_by_flow(job.flow_id)
            previous_step = None
            for s in previous_steps:
                if s.iteration == step.iteration - 1:
                    previous_step = s
                    break

            if previous_step:
                prev_analysis = self.repository.get_analysis_result_by_step(previous_step.id)
                if prev_analysis and prev_analysis.winner_image_ids:
                    # Collect source assets from winner images
                    winner_assets: list[Asset] = []
                    prev_gen_result = self.repository.get_generation_result_by_step(previous_step.id)
                    if prev_gen_result:
                        prev_images = self.repository.get_images_by_generation_result(prev_gen_result.id)
                        for img in prev_images:
                            if img.id in prev_analysis.winner_image_ids:
                                winner_assets.extend(img.source_assets)

                    if winner_assets:
                        type_embeddings = compute_type_embeddings_from_winners(winner_assets)
                        logger.info(
                            f"Step {step.id}: Computed type embeddings for {len(type_embeddings)} asset types "
                            f"from {len(winner_assets)} winner assets"
                        )

            current_assets = filter_assets_by_iteration(
                target_embedding=step.input_embedding,
                assets=assets,
                iteration=step.iteration,
                type_embeddings=type_embeddings,
            )

            logger.info(
                f"Step {step.id}: Filtered from {len(assets)} to {len(current_assets)} assets "
                f"(iteration {step.iteration}, fraction 1/{step.iteration + 1})"
            )

        # Select asset sets
        logger.info(
            f"Step {step.id}: {len(current_assets)} assets available for selection"
        )
        selection_input = AssetSelectionInput(
            assets=current_assets,
            num_sets=self.config.num_images_per_step,
        )
        selection_output = select_asset_sets(selection_input)

        if not selection_output.asset_sets:
            logger.error(f"Step {step.id}: No asset sets could be created from {len(current_assets)} assets")

        # Collect all selected asset IDs
        all_selected_asset_ids: set[UUID] = set()
        for asset_set in selection_output.asset_sets:
            all_selected_asset_ids.update(asset_set.asset_ids)

        # Check for existing generation result (from a previous failed attempt)
        existing_gen_result = self.repository.get_generation_result_by_step(step.id)
        if existing_gen_result:
            # Delete existing generation result and its images to retry fresh
            logger.info(f"Step {step.id}: Deleting existing generation result to retry")
            self.repository.delete_generation_result(existing_gen_result.id)
            self.session.commit()

        # Create generation result
        gen_result = self.service.create_generation_result(
            GenerationResultCreate(
                step_id=step.id,
                prompt=prompt,
                prompt_notes=step.input_insights,
                selected_asset_ids=list(all_selected_asset_ids),
            )
        )

        generated_image_ids: list[UUID] = []

        logger.info(
            f"Generating images for step {step.id}: "
            f"{len(selection_output.asset_sets)} asset sets selected"
        )

        # Generate images for each asset set
        for i, asset_set in enumerate(selection_output.asset_sets):
            prompt_input = PromptGenerationInput(
                base_prompt=prompt,
                asset_set=asset_set,
            )
            prompt_output = generate_initial_prompt(prompt_input)

            base_asset, reference_assets = get_base_and_reference_assets(asset_set)

            if base_asset is None:
                logger.warning(
                    f"Asset set {i}: No base asset found, skipping. "
                    f"Asset types in set: {list(asset_set.assets.keys())}"
                )
                continue

            logger.info(
                f"Asset set {i}: Generating image with base asset "
                f"{base_asset.id} ({base_asset.file_name})"
            )

            # Async image generation
            image_result = await generate_image_with_flux(
                prompt=prompt_output.prompt,
                base_asset=base_asset,
                reference_assets=reference_assets,
                width=self.config.image_width,
                height=self.config.image_height,
            )

            if image_result.success and image_result.image_url:
                image = self.service.create_generated_image(
                    GeneratedImageCreate(
                        generation_result_id=gen_result.id,
                        file_name=image_result.image_url,
                        metadata_tags=image_result.metadata_tags,
                        model_version=image_result.model_version,
                        source_asset_ids=asset_set.asset_ids,
                    )
                )
                generated_image_ids.append(image.id)
                logger.info(f"Asset set {i}: Image generated successfully: {image.id}")
            else:
                logger.error(
                    f"Asset set {i}: Image generation failed: {image_result.error}"
                )

        # Check if any images were generated
        if not generated_image_ids:
            logger.error(
                f"Step {step.id}: No images were generated, cannot proceed to collecting data"
            )
            return JobResult(
                job=job,
                success=False,
                error="No images were generated",
                data={
                    "step_id": str(step.id),
                    "asset_sets_attempted": len(selection_output.asset_sets),
                },
            )

        # Transition to COLLECTING_DATA
        self.service.transition_to_collecting(step.id)

        return JobResult(
            job=job,
            success=True,
            next_job=Job(
                job_type=JobType.RUN_COLLECTING_DATA,
                flow_id=job.flow_id,
                step_id=step.id,
                priority=2,
            ),
            data={
                "step_id": str(step.id),
                "generated_images": len(generated_image_ids),
                "image_ids": [str(id) for id in generated_image_ids],
            },
        )

    async def _execute_collecting_data(self, job: Job) -> JobResult:
        """Execute the COLLECTING_DATA phase."""
        if job.step_id is None:
            return JobResult(job=job, success=False, error="No step_id provided")

        step = self.service.get_step(job.step_id)
        flow = self.repository.get_flow(job.flow_id)
        target_group = flow.target_group

        gen_result = self.service.get_generation_result(step.id)
        if not gen_result:
            return JobResult(job=job, success=False, error="No generation result found")

        images = self.repository.get_images_by_generation_result(gen_result.id)
        if not images:
            return JobResult(job=job, success=False, error="No images found")

        # Generate descriptions for each image (async)
        image_descriptions: list[tuple[UUID, str]] = []
        for image in images:
            # Use describe_image_from_path for local files, describe_image_from_url for URLs
            file_name = image.file_name
            if file_name.startswith('http://') or file_name.startswith('https://'):
                description_output = await describe_image_from_url(
                    url=file_name,
                    model=self.config.description_model,
                )
            else:
                description_output = await describe_image_from_path(
                    path=file_name,
                    model=self.config.description_model,
                )
            image_descriptions.append((image.id, description_output.description))

            # Store description in metadata
            if image.metadata_tags is None:
                image.metadata_tags = []
            image.metadata_tags.append(f"description:{description_output.description[:500]}")
            self.session.add(image)

        self.session.commit()

        # Generate analytics using OpenAI (async)
        analytics_input = AnalyticsGenerationInput(
            image_descriptions=image_descriptions,
            target_group=target_group,
            model=self.config.analytics_model,
        )
        analytics_output = await generate_analytics_for_images(analytics_input)

        # Store metrics
        for analytics in analytics_output.analytics:
            self.service.create_image_metrics(
                ImageMetricsCreate(
                    image_id=analytics.image_id,
                    impressions=analytics.impressions,
                    clicks=analytics.clicks,
                    conversions=analytics.conversions,
                    cost=analytics.cost,
                )
            )

        # Transition to ANALYZING
        self.service.transition_to_analyzing(step.id)

        return JobResult(
            job=job,
            success=True,
            next_job=Job(
                job_type=JobType.RUN_ANALYZING,
                flow_id=job.flow_id,
                step_id=step.id,
                priority=3,
            ),
            data={
                "step_id": str(step.id),
                "images_processed": len(images),
                "analytics_generated": len(analytics_output.analytics),
            },
        )

    async def _execute_analyzing(
        self,
        job: Job,
        campaign_spec: CampaignSpec,
    ) -> JobResult:
        """Execute the ANALYZING phase."""
        if job.step_id is None:
            return JobResult(job=job, success=False, error="No step_id provided")

        step = self.service.get_step(job.step_id)
        flow = self.repository.get_flow(job.flow_id)
        target_group = flow.target_group

        gen_result = self.service.get_generation_result(step.id)
        if not gen_result:
            return JobResult(job=job, success=False, error="No generation result found")

        images = self.repository.get_images_by_generation_result(gen_result.id)

        # Collect analytics and descriptions
        image_analytics: list[tuple[UUID, dict]] = []
        image_descriptions: dict[UUID, str] = {}

        for image in images:
            metrics = self.repository.get_image_metrics(image.id)
            if metrics:
                image_analytics.append((
                    image.id,
                    {
                        'interaction_rate': metrics.ctr * 1.3,
                        'interactions': metrics.clicks,
                        'conversion_value': metrics.conversions * 40,
                        'conversion_rate': metrics.conversion_rate,
                        'ctr': metrics.ctr,
                    }
                ))

            if image.metadata_tags:
                for tag in image.metadata_tags:
                    if tag.startswith("description:"):
                        image_descriptions[image.id] = tag[12:]
                        break

        # Select winners
        top_ids, bottom_ids = select_top_images_by_score(
            image_analytics,
            top_n=self.config.top_n_winners,
        )

        # Analyze winning images (async)
        winning_descriptions = [
            (img_id, image_descriptions.get(img_id, "No description"))
            for img_id in top_ids
        ]
        losing_descriptions = [
            (img_id, image_descriptions.get(img_id, "No description"))
            for img_id in bottom_ids
        ]

        analysis_input = ImageAnalysisInput(
            winning_image_descriptions=winning_descriptions,
            losing_image_descriptions=losing_descriptions,
            model=self.config.analysis_model,
        )
        analysis_output = await analyze_winning_images(analysis_input)

        # Modify prompt for next iteration (async)
        current_prompt = gen_result.prompt
        modification_input = PromptModificationInput(
            current_prompt=current_prompt,
            winning_image_descriptions=[desc for _, desc in winning_descriptions],
            losing_image_descriptions=[desc for _, desc in losing_descriptions],
            visual_similarities=analysis_output.visual_similarities,
            target_group=target_group,
        )
        modification_output = await modify_prompt_from_analysis(modification_input)

        # Compute mean embedding from winner assets
        winner_embeddings: list[list[float]] = []
        for image in images:
            if image.id in top_ids:
                for asset in image.source_assets:
                    if asset.embedding:
                        winner_embeddings.append(asset.embedding)

        mean_embedding = (
            compute_mean_embedding(winner_embeddings)
            if winner_embeddings
            else [0.0] * 1536
        )

        # Create analysis result (store modified prompt in qualitative_diff for next iteration)
        self.service.create_analysis_result(
            AnalysisResultCreate(
                step_id=step.id,
                winner_image_ids=top_ids,
                output_embedding=mean_embedding,
                qualitative_diff=modification_output.modified_prompt,  # Store modified prompt here
                diff_tags=analysis_output.differentiation_tags,
            )
        )

        # Transition to COMPLETED
        self.service.transition_to_completed(step.id)

        # Determine next job
        max_iterations = campaign_spec.max_iterations
        if step.iteration < max_iterations - 1:
            next_job = Job(
                job_type=JobType.CREATE_NEXT_ITERATION,
                flow_id=job.flow_id,
                step_id=step.id,
                priority=0,
            )
        else:
            next_job = None  # Campaign complete

        return JobResult(
            job=job,
            success=True,
            next_job=next_job,
            data={
                "step_id": str(step.id),
                "winner_ids": [str(id) for id in top_ids],
                "diff_tags": analysis_output.differentiation_tags,
                "campaign_complete": next_job is None,
            },
        )

    async def _execute_create_next_iteration(self, job: Job) -> JobResult:
        """Create the next iteration step."""
        if job.step_id is None:
            return JobResult(job=job, success=False, error="No step_id provided")

        previous_step = self.service.get_step(job.step_id)
        analysis = self.repository.get_analysis_result_by_step(previous_step.id)

        if not analysis:
            return JobResult(job=job, success=False, error="No analysis result found")

        # Create new step with input from previous analysis
        new_step = self.service.create_step(
            FlowStepCreate(
                flow_id=job.flow_id,
                input_embedding=analysis.output_embedding,
                input_insights=analysis.qualitative_diff,  # This contains the modified prompt
            )
        )

        return JobResult(
            job=job,
            success=True,
            next_job=Job(
                job_type=JobType.RUN_GENERATING,
                flow_id=job.flow_id,
                step_id=new_step.id,
                priority=1,
            ),
            data={
                "new_step_id": str(new_step.id),
                "iteration": new_step.iteration,
            },
        )

    # ---------------------------------------------------------
    # Status & Monitoring
    # ---------------------------------------------------------

    def get_campaign_status(self, campaign_id: UUID) -> dict:
        """Get the overall status of a campaign."""
        campaign = self.repository.get_campaign(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}

        flows = self.repository.get_flows_by_campaign(campaign_id)
        flow_statuses = []

        for flow in flows:
            latest_step = self.repository.get_latest_step(flow.id)
            job = self._get_job_for_flow(flow)

            flow_statuses.append({
                "flow_id": str(flow.id),
                "target_group": flow.target_group.name if flow.target_group else None,
                "current_iteration": latest_step.iteration if latest_step else None,
                "current_state": latest_step.state.value if latest_step else None,
                "next_job": job.job_type.value if job else "complete",
            })

        pending_jobs = self.get_all_pending_jobs(campaign_id)

        return {
            "campaign_id": str(campaign_id),
            "total_flows": len(flows),
            "pending_jobs": len(pending_jobs),
            "flows": flow_statuses,
        }

    def get_flow_status(self, flow_id: UUID) -> dict:
        """Get detailed status of a flow."""
        flow = self.repository.get_flow(flow_id)
        if not flow:
            return {"error": "Flow not found"}

        steps = self.repository.get_steps_by_flow(flow_id)
        job = self._get_job_for_flow(flow)

        step_details = []
        for step in steps:
            gen_result = self.repository.get_generation_result_by_step(step.id)
            analysis = self.repository.get_analysis_result_by_step(step.id)

            step_details.append({
                "step_id": str(step.id),
                "iteration": step.iteration,
                "state": step.state.value,
                "has_generation_result": gen_result is not None,
                "has_analysis_result": analysis is not None,
                "image_count": len(gen_result.generated_images) if gen_result else 0,
            })

        return {
            "flow_id": str(flow_id),
            "target_group": flow.target_group.name if flow.target_group else None,
            "next_job": job.job_type.value if job else "complete",
            "steps": step_details,
        }
