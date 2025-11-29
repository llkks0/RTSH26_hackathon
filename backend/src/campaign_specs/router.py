from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from campaign_specs.repository import CampaignSpecRepository
from campaign_specs.service import CampaignSpecNotFoundError, CampaignSpecService
from database import get_session
from models import (
    Asset,
    CampaignSpecCreate,
    CampaignSpecResponse,
    CampaignSpecUpdate,
    TargetGroup,
)

router = APIRouter(prefix='/campaign-specs', tags=['campaign-specs'])


def get_campaign_spec_service(session: Session = Depends(get_session)) -> CampaignSpecService:
    """Dependency injection for CampaignSpecService."""
    repository = CampaignSpecRepository(session)
    return CampaignSpecService(repository)


@router.post('/', response_model=CampaignSpecResponse, status_code=201)
def create_campaign_spec(
    data: CampaignSpecCreate,
    service: CampaignSpecService = Depends(get_campaign_spec_service),
) -> CampaignSpecResponse:
    """Create a new campaign spec."""
    spec = service.create_campaign_spec(data)
    return CampaignSpecResponse.from_campaign_spec(spec)


@router.get('/', response_model=list[CampaignSpecResponse])
def list_campaign_specs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: CampaignSpecService = Depends(get_campaign_spec_service),
) -> list[CampaignSpecResponse]:
    """Get all campaign specs with pagination."""
    specs = service.list_campaign_specs(skip=skip, limit=limit)
    return [CampaignSpecResponse.from_campaign_spec(s) for s in specs]


@router.get('/{campaign_spec_id}', response_model=CampaignSpecResponse)
def get_campaign_spec(
    campaign_spec_id: UUID,
    service: CampaignSpecService = Depends(get_campaign_spec_service),
) -> CampaignSpecResponse:
    """Get a specific campaign spec by ID."""
    try:
        spec = service.get_campaign_spec(campaign_spec_id)
        return CampaignSpecResponse.from_campaign_spec(spec)
    except CampaignSpecNotFoundError:
        raise HTTPException(status_code=404, detail='Campaign spec not found')


@router.patch('/{campaign_spec_id}', response_model=CampaignSpecResponse)
def update_campaign_spec(
    campaign_spec_id: UUID,
    data: CampaignSpecUpdate,
    service: CampaignSpecService = Depends(get_campaign_spec_service),
) -> CampaignSpecResponse:
    """Update a campaign spec."""
    try:
        spec = service.update_campaign_spec(campaign_spec_id, data)
        return CampaignSpecResponse.from_campaign_spec(spec)
    except CampaignSpecNotFoundError:
        raise HTTPException(status_code=404, detail='Campaign spec not found')


@router.delete('/{campaign_spec_id}', status_code=204)
def delete_campaign_spec(
    campaign_spec_id: UUID,
    service: CampaignSpecService = Depends(get_campaign_spec_service),
) -> None:
    """Delete a campaign spec."""
    try:
        service.delete_campaign_spec(campaign_spec_id)
    except CampaignSpecNotFoundError:
        raise HTTPException(status_code=404, detail='Campaign spec not found')


# Asset management endpoints
@router.get('/{campaign_spec_id}/assets', response_model=list[Asset])
def get_campaign_spec_assets(
    campaign_spec_id: UUID,
    service: CampaignSpecService = Depends(get_campaign_spec_service),
) -> list[Asset]:
    """Get all assets for a campaign spec."""
    try:
        return service.get_assets(campaign_spec_id)
    except CampaignSpecNotFoundError:
        raise HTTPException(status_code=404, detail='Campaign spec not found')


@router.post('/{campaign_spec_id}/assets/{asset_id}', status_code=201)
def add_asset_to_campaign_spec(
    campaign_spec_id: UUID,
    asset_id: UUID,
    service: CampaignSpecService = Depends(get_campaign_spec_service),
) -> dict[str, str]:
    """Add an asset to a campaign spec."""
    try:
        service.add_asset(campaign_spec_id, asset_id)
        return {'message': 'Asset added to campaign spec'}
    except CampaignSpecNotFoundError:
        raise HTTPException(status_code=404, detail='Campaign spec not found')


@router.delete('/{campaign_spec_id}/assets/{asset_id}', status_code=204)
def remove_asset_from_campaign_spec(
    campaign_spec_id: UUID,
    asset_id: UUID,
    service: CampaignSpecService = Depends(get_campaign_spec_service),
) -> None:
    """Remove an asset from a campaign spec."""
    try:
        service.remove_asset(campaign_spec_id, asset_id)
    except CampaignSpecNotFoundError:
        raise HTTPException(status_code=404, detail='Campaign spec not found')


# Target group management endpoints
@router.get('/{campaign_spec_id}/target-groups', response_model=list[TargetGroup])
def get_campaign_spec_target_groups(
    campaign_spec_id: UUID,
    service: CampaignSpecService = Depends(get_campaign_spec_service),
) -> list[TargetGroup]:
    """Get all target groups for a campaign spec."""
    try:
        return service.get_target_groups(campaign_spec_id)
    except CampaignSpecNotFoundError:
        raise HTTPException(status_code=404, detail='Campaign spec not found')


@router.post('/{campaign_spec_id}/target-groups/{target_group_id}', status_code=201)
def add_target_group_to_campaign_spec(
    campaign_spec_id: UUID,
    target_group_id: UUID,
    service: CampaignSpecService = Depends(get_campaign_spec_service),
) -> dict[str, str]:
    """Add a target group to a campaign spec."""
    try:
        service.add_target_group(campaign_spec_id, target_group_id)
        return {'message': 'Target group added to campaign spec'}
    except CampaignSpecNotFoundError:
        raise HTTPException(status_code=404, detail='Campaign spec not found')


@router.delete('/{campaign_spec_id}/target-groups/{target_group_id}', status_code=204)
def remove_target_group_from_campaign_spec(
    campaign_spec_id: UUID,
    target_group_id: UUID,
    service: CampaignSpecService = Depends(get_campaign_spec_service),
) -> None:
    """Remove a target group from a campaign spec."""
    try:
        service.remove_target_group(campaign_spec_id, target_group_id)
    except CampaignSpecNotFoundError:
        raise HTTPException(status_code=404, detail='Campaign spec not found')
