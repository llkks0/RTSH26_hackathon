from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from database import get_session
from models import TargetGroup, TargetGroupCreate, TargetGroupUpdate
from target_groups.repository import TargetGroupRepository
from target_groups.service import TargetGroupNotFoundError, TargetGroupService

router = APIRouter(prefix='/target-groups', tags=['target-groups'])


def get_target_group_service(session: Session = Depends(get_session)) -> TargetGroupService:
    """Dependency injection for TargetGroupService."""
    repository = TargetGroupRepository(session)
    return TargetGroupService(repository)


@router.post('/', response_model=TargetGroup, status_code=201)
def create_target_group(
    data: TargetGroupCreate,
    service: TargetGroupService = Depends(get_target_group_service),
) -> TargetGroup:
    """Create a new target group."""
    return service.create_target_group(data)


@router.get('/', response_model=list[TargetGroup])
def list_target_groups(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: TargetGroupService = Depends(get_target_group_service),
) -> list[TargetGroup]:
    """Get all target groups with pagination."""
    return service.list_target_groups(skip=skip, limit=limit)


@router.get('/{target_group_id}', response_model=TargetGroup)
def get_target_group(
    target_group_id: UUID,
    service: TargetGroupService = Depends(get_target_group_service),
) -> TargetGroup:
    """Get a specific target group by ID."""
    try:
        return service.get_target_group(target_group_id)
    except TargetGroupNotFoundError:
        raise HTTPException(status_code=404, detail='Target group not found')


@router.patch('/{target_group_id}', response_model=TargetGroup)
def update_target_group(
    target_group_id: UUID,
    data: TargetGroupUpdate,
    service: TargetGroupService = Depends(get_target_group_service),
) -> TargetGroup:
    """Update a target group."""
    try:
        return service.update_target_group(target_group_id, data)
    except TargetGroupNotFoundError:
        raise HTTPException(status_code=404, detail='Target group not found')


@router.delete('/{target_group_id}', status_code=204)
def delete_target_group(
    target_group_id: UUID,
    service: TargetGroupService = Depends(get_target_group_service),
) -> None:
    """Delete a target group."""
    try:
        service.delete_target_group(target_group_id)
    except TargetGroupNotFoundError:
        raise HTTPException(status_code=404, detail='Target group not found')
