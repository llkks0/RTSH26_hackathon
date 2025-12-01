"""
API endpoints for the job scheduler and orchestrator.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from database import get_session

from .orchestrator import FlowOrchestrator
from .scheduler import JobScheduler, SchedulerConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/jobs', tags=['jobs'])


@router.get('/pending')
def get_pending_jobs() -> dict:
    """Get a summary of all pending jobs across all campaigns."""
    scheduler = JobScheduler()
    return scheduler.get_pending_jobs_summary()


@router.post('/run')
async def run_pending_jobs(max_jobs: int = 10) -> dict:
    """
    Run pending jobs.

    Args:
        max_jobs: Maximum number of jobs to process (default 10)
    """
    config = SchedulerConfig(max_jobs_per_run=max_jobs)
    scheduler = JobScheduler(config)

    results = await scheduler.run_once()

    return {
        "jobs_processed": len(results),
        "results": [
            {
                "job_type": r.job.job_type.value,
                "flow_id": str(r.job.flow_id),
                "success": r.success,
                "error": r.error,
                "data": r.data,
            }
            for r in results
        ],
    }


@router.get('/campaigns/{campaign_id}/status')
def get_campaign_status(
    campaign_id: UUID,
    session: Session = Depends(get_session),
) -> dict:
    """Get the status of a specific campaign including pending jobs."""
    orchestrator = FlowOrchestrator(session)
    return orchestrator.get_campaign_status(campaign_id)


@router.get('/flows/{flow_id}/status')
def get_flow_status(
    flow_id: UUID,
    session: Session = Depends(get_session),
) -> dict:
    """Get detailed status of a specific flow."""
    orchestrator = FlowOrchestrator(session)
    return orchestrator.get_flow_status(flow_id)


@router.post('/campaigns/{campaign_id}/run')
async def run_campaign_jobs(
    campaign_id: UUID,
    max_jobs: int = 10,
    session: Session = Depends(get_session),
) -> dict:
    """
    Run pending jobs for a specific campaign.

    Args:
        campaign_id: The campaign to process jobs for
        max_jobs: Maximum number of jobs to process
    """
    from sqlalchemy.orm import selectinload
    from sqlmodel import select

    from campaigns.repository import CampaignRepository
    from models import CampaignSpec

    orchestrator = FlowOrchestrator(session)
    repository = CampaignRepository(session)

    # Get campaign
    campaign = repository.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get campaign spec with relationships
    statement = (
        select(CampaignSpec)
        .where(CampaignSpec.id == campaign.campaign_spec_id)
        .options(
            selectinload(CampaignSpec.target_groups),
            selectinload(CampaignSpec.base_assets),
        )
    )
    campaign_spec = session.exec(statement).first()
    if not campaign_spec:
        raise HTTPException(status_code=404, detail="Campaign spec not found")

    assets = list(campaign_spec.base_assets) if campaign_spec.base_assets else []

    results = []
    jobs_processed = 0

    while jobs_processed < max_jobs:
        job = orchestrator.get_next_job(campaign_id)
        if job is None:
            break

        logger.info(f"Processing job: {job.job_type.value} for flow {job.flow_id}")
        result = await orchestrator.execute_job(job, assets, campaign_spec)
        results.append(result)
        jobs_processed += 1

        if not result.success:
            logger.error(f"Job failed: {result.error}")
            break  # Stop on error

    return {
        "campaign_id": str(campaign_id),
        "jobs_processed": len(results),
        "results": [
            {
                "job_type": r.job.job_type.value,
                "flow_id": str(r.job.flow_id),
                "step_id": str(r.job.step_id) if r.job.step_id else None,
                "success": r.success,
                "error": r.error,
                "data": r.data,
            }
            for r in results
        ],
    }
