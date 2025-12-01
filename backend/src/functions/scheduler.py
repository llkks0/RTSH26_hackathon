"""
Job Scheduler - Background worker for processing campaign jobs.

This scheduler can be run as a background task to continuously
process pending jobs across all campaigns.

All processing methods are async for non-blocking operation.
"""

import asyncio
import logging
from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session, select

from database import engine
from models import CampaignSpec

from .orchestrator import (
    FlowOrchestrator,
    Job,
    JobResult,
    JobType,
    OrchestrationConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """Configuration for the job scheduler."""

    poll_interval_seconds: float = 5.0  # How often to check for jobs
    max_jobs_per_run: int = 10  # Max jobs to process per poll
    orchestration_config: OrchestrationConfig | None = None


class JobScheduler:
    """
    Background job scheduler for campaign processing.

    All job processing methods are async for non-blocking operation.

    Usage:
        scheduler = JobScheduler()

        # Run once (process available jobs)
        results = await scheduler.run_once()

        # Integrate with FastAPI lifespan
        async def lifespan(app):
            task = asyncio.create_task(run_scheduler_loop(scheduler))
            yield
            task.cancel()
    """

    def __init__(self, config: SchedulerConfig | None = None) -> None:
        self.config = config or SchedulerConfig()

    async def run_once(self) -> list[JobResult]:
        """
        Process all available jobs once.

        Returns:
            List of job results
        """
        results: list[JobResult] = []

        with Session(engine) as session:
            try:
                # Ensure clean transaction state at start
                session.rollback()

                orchestrator = FlowOrchestrator(
                    session,
                    self.config.orchestration_config,
                )

                # First, ensure all flows have their first step created
                await self._ensure_first_steps_created(orchestrator)

                jobs_processed = 0
                while jobs_processed < self.config.max_jobs_per_run:
                    try:
                        job = orchestrator.get_next_job()
                        if job is None:
                            logger.debug("No more jobs to process")
                            break

                        logger.info(f"Processing job: {job.job_type.value} for flow {job.flow_id}")

                        # Get the assets and campaign spec for this job
                        flow = orchestrator.repository.get_flow(job.flow_id)
                        if not flow:
                            logger.error(f"Flow not found for job: {job.flow_id}")
                            continue

                        if not flow.campaign:
                            logger.error(f"Campaign not loaded for flow: {job.flow_id}")
                            continue

                        campaign_spec = self._get_campaign_spec(session, flow.campaign.campaign_spec_id)
                        if not campaign_spec:
                            logger.error(f"Campaign spec not found: {flow.campaign.campaign_spec_id}")
                            continue

                        assets = list(campaign_spec.base_assets) if campaign_spec.base_assets else []
                        logger.info(f"Job has {len(assets)} assets available from campaign spec {campaign_spec.id}")

                        result = await orchestrator.execute_job(job, assets, campaign_spec)
                        results.append(result)
                        jobs_processed += 1

                        if result.success:
                            logger.info(f"Job completed successfully: {result.data}")
                        else:
                            logger.error(f"Job failed: {result.error}")

                    except Exception as e:
                        logger.error(f"Error processing job: {e}")
                        session.rollback()
                        break  # Exit loop on error to avoid cascading failures

            except Exception as e:
                logger.error(f"Scheduler session error: {e}")
            finally:
                # Always rollback to ensure connection is clean before returning to pool
                session.rollback()

        if results:
            logger.info(f"Processed {len(results)} jobs")
        return results

    async def _ensure_first_steps_created(self, orchestrator: FlowOrchestrator) -> None:
        """
        Ensure all flows have their first step created.

        This is a safety check to make sure CREATE_FIRST_STEP jobs
        are executed even if there were previous issues.
        """
        try:
            campaigns = orchestrator.repository.get_campaigns()
            for campaign in campaigns:
                flows = orchestrator.repository.get_flows_by_campaign(campaign.id)
                for flow in flows:
                    try:
                        latest_step = orchestrator.repository.get_latest_step(flow.id)
                        if latest_step is None:
                            logger.info(f"Creating first step for flow {flow.id}")
                            # Get campaign spec for the flow
                            campaign_spec = self._get_campaign_spec(
                                orchestrator.session,
                                campaign.campaign_spec_id,
                            )
                            if campaign_spec:
                                job = Job(
                                    job_type=JobType.CREATE_FIRST_STEP,
                                    flow_id=flow.id,
                                    priority=0,
                                )
                                result = await orchestrator.execute_job(job, [], campaign_spec)
                                if result.success:
                                    logger.info(f"Created first step for flow {flow.id}: {result.data}")
                                else:
                                    logger.error(f"Failed to create first step: {result.error}")
                    except Exception as e:
                        logger.error(f"Error processing flow {flow.id}: {e}")
                        # Rollback any failed transaction
                        orchestrator.session.rollback()
        except Exception as e:
            logger.error(f"Error ensuring first steps: {e}")
            orchestrator.session.rollback()

    async def tick(self) -> list[JobResult]:
        """
        Single tick of the scheduler - process available jobs.

        Returns:
            List of job results from this tick
        """
        return await self.run_once()

    def get_pending_jobs_summary(self) -> dict:
        """
        Get a summary of all pending jobs.

        Returns:
            Summary dict with job counts by type
        """
        with Session(engine) as session:
            orchestrator = FlowOrchestrator(
                session,
                self.config.orchestration_config,
            )

            jobs = orchestrator.get_all_pending_jobs()

            summary = {
                "total_pending": len(jobs),
                "by_type": {},
                "jobs": [],
            }

            for job in jobs:
                job_type = job.job_type.value
                summary["by_type"][job_type] = summary["by_type"].get(job_type, 0) + 1
                summary["jobs"].append({
                    "type": job_type,
                    "flow_id": str(job.flow_id),
                    "step_id": str(job.step_id) if job.step_id else None,
                    "priority": job.priority,
                })

            return summary

    def _get_campaign_spec(self, session: Session, spec_id: UUID) -> CampaignSpec | None:
        """Get campaign spec with relationships loaded."""
        from sqlalchemy.orm import selectinload

        statement = (
            select(CampaignSpec)
            .where(CampaignSpec.id == spec_id)
            .options(
                selectinload(CampaignSpec.target_groups),
                selectinload(CampaignSpec.base_assets),
            )
        )
        return session.exec(statement).first()


async def run_scheduler_loop(
    scheduler: JobScheduler,
    interval_seconds: float | None = None,
) -> None:
    """
    Run the scheduler continuously as an async loop.

    This can be used as a background task in FastAPI's lifespan.

    Args:
        scheduler: The JobScheduler instance
        interval_seconds: Override the poll interval (uses scheduler config if None)
    """
    interval = interval_seconds or scheduler.config.poll_interval_seconds
    logger.info(f"Starting async scheduler loop (polling every {interval}s)")

    try:
        while True:
            results = await scheduler.tick()
            if not results:
                logger.debug(f"No jobs, sleeping for {interval}s")
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info("Scheduler loop cancelled")
        raise


async def run_scheduler_cli() -> None:
    """Entry point for running the scheduler from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    scheduler = JobScheduler()
    await run_scheduler_loop(scheduler)


if __name__ == "__main__":
    asyncio.run(run_scheduler_cli())
