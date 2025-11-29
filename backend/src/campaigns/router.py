from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from campaign_specs.repository import CampaignSpecRepository
from campaigns.models import (
    Campaign,
    CampaignCreate,
    CampaignFlow,
    FlowStep,
    GeneratedImage,
)
from campaigns.repository import CampaignRepository
from campaigns.service import (
    CampaignNotFoundError,
    CampaignService,
    FlowNotFoundError,
    StepNotFoundError,
)
from database import get_session

router = APIRouter(prefix='/campaigns', tags=['campaigns'])


def get_campaign_service(session: Session = Depends(get_session)) -> CampaignService:
    """Dependency injection for CampaignService."""
    repository = CampaignRepository(session)
    return CampaignService(repository)


def get_campaign_spec_repository(
    session: Session = Depends(get_session),
) -> CampaignSpecRepository:
    """Dependency injection for CampaignSpecRepository."""
    return CampaignSpecRepository(session)


# ---------------------------------------------------------
# Campaign Endpoints
# ---------------------------------------------------------


@router.post('/', response_model=Campaign, status_code=201)
def create_campaign(
    data: CampaignCreate,
    service: CampaignService = Depends(get_campaign_service),
    spec_repo: CampaignSpecRepository = Depends(get_campaign_spec_repository),
) -> Campaign:
    """Create a new campaign from a campaign spec."""
    spec = spec_repo.get_by_id(data.campaign_spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail='Campaign spec not found')
    return service.create_campaign(data, spec)


@router.get('/', response_model=list[Campaign])
def list_campaigns(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: CampaignService = Depends(get_campaign_service),
) -> list[Campaign]:
    """Get all campaigns with pagination."""
    return service.list_campaigns(skip=skip, limit=limit)


@router.get('/{campaign_id}', response_model=Campaign)
def get_campaign(
    campaign_id: UUID,
    service: CampaignService = Depends(get_campaign_service),
) -> Campaign:
    """Get a specific campaign by ID."""
    try:
        return service.get_campaign(campaign_id)
    except CampaignNotFoundError:
        raise HTTPException(status_code=404, detail='Campaign not found')


# ---------------------------------------------------------
# Flow Endpoints
# ---------------------------------------------------------


@router.get('/{campaign_id}/flows', response_model=list[CampaignFlow])
def list_flows(
    campaign_id: UUID,
    service: CampaignService = Depends(get_campaign_service),
) -> list[CampaignFlow]:
    """Get all flows for a campaign."""
    try:
        service.get_campaign(campaign_id)  # Verify campaign exists
    except CampaignNotFoundError:
        raise HTTPException(status_code=404, detail='Campaign not found')
    return service.get_flows_by_campaign(campaign_id)


@router.get('/{campaign_id}/flows/{flow_id}', response_model=CampaignFlow)
def get_flow(
    campaign_id: UUID,
    flow_id: UUID,
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignFlow:
    """Get a specific flow by ID."""
    try:
        flow = service.get_flow(flow_id)
        if flow.campaign_id != campaign_id:
            raise HTTPException(status_code=404, detail='Flow not found in this campaign')
        return flow
    except FlowNotFoundError:
        raise HTTPException(status_code=404, detail='Flow not found')


@router.get('/{campaign_id}/flows/{flow_id}/current-step', response_model=FlowStep | None)
def get_current_step(
    campaign_id: UUID,
    flow_id: UUID,
    service: CampaignService = Depends(get_campaign_service),
) -> FlowStep | None:
    """Get the current (latest) step for a flow."""
    try:
        flow = service.get_flow(flow_id)
        if flow.campaign_id != campaign_id:
            raise HTTPException(status_code=404, detail='Flow not found in this campaign')
        return service.get_current_step(flow_id)
    except FlowNotFoundError:
        raise HTTPException(status_code=404, detail='Flow not found')


# ---------------------------------------------------------
# Step Endpoints
# ---------------------------------------------------------


@router.get('/{campaign_id}/flows/{flow_id}/steps', response_model=list[FlowStep])
def list_steps(
    campaign_id: UUID,
    flow_id: UUID,
    service: CampaignService = Depends(get_campaign_service),
) -> list[FlowStep]:
    """Get all steps for a flow."""
    try:
        flow = service.get_flow(flow_id)
        if flow.campaign_id != campaign_id:
            raise HTTPException(status_code=404, detail='Flow not found in this campaign')
        return service.get_steps_by_flow(flow_id)
    except FlowNotFoundError:
        raise HTTPException(status_code=404, detail='Flow not found')


@router.get(
    '/{campaign_id}/flows/{flow_id}/steps/{step_id}',
    response_model=FlowStep,
)
def get_step(
    campaign_id: UUID,
    flow_id: UUID,
    step_id: UUID,
    service: CampaignService = Depends(get_campaign_service),
) -> FlowStep:
    """Get a specific step by ID."""
    try:
        step = service.get_step(step_id)
        if step.flow_id != flow_id:
            raise HTTPException(status_code=404, detail='Step not found in this flow')
        return step
    except StepNotFoundError:
        raise HTTPException(status_code=404, detail='Step not found')


@router.get(
    '/{campaign_id}/flows/{flow_id}/steps/{step_id}/images',
    response_model=list[GeneratedImage],
)
def get_step_images(
    campaign_id: UUID,
    flow_id: UUID,
    step_id: UUID,
    service: CampaignService = Depends(get_campaign_service),
) -> list[GeneratedImage]:
    """Get all generated images for a step."""
    try:
        step = service.get_step(step_id)
        if step.flow_id != flow_id:
            raise HTTPException(status_code=404, detail='Step not found in this flow')
        return service.get_images_by_step(step_id)
    except StepNotFoundError:
        raise HTTPException(status_code=404, detail='Step not found')
