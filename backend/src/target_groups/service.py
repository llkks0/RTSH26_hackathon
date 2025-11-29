from uuid import UUID

from models import TargetGroup, TargetGroupCreate, TargetGroupUpdate
from target_groups.repository import TargetGroupRepository


class TargetGroupNotFoundError(Exception):
    """Raised when a target group is not found."""

    def __init__(self, target_group_id: UUID) -> None:
        self.target_group_id = target_group_id
        super().__init__(f'TargetGroup with id {target_group_id} not found')


class TargetGroupService:
    """Business logic layer for TargetGroup operations."""

    def __init__(self, repository: TargetGroupRepository) -> None:
        self.repository = repository

    def create_target_group(self, data: TargetGroupCreate) -> TargetGroup:
        """Create a new target group."""
        target_group = TargetGroup.model_validate(data)
        return self.repository.create(target_group)

    def get_target_group(self, target_group_id: UUID) -> TargetGroup:
        """Get a target group by ID. Raises TargetGroupNotFoundError if not found."""
        target_group = self.repository.get_by_id(target_group_id)
        if not target_group:
            raise TargetGroupNotFoundError(target_group_id)
        return target_group

    def list_target_groups(self, skip: int = 0, limit: int = 100) -> list[TargetGroup]:
        """List all target groups with pagination."""
        return self.repository.get_all(skip=skip, limit=limit)

    def update_target_group(self, target_group_id: UUID, data: TargetGroupUpdate) -> TargetGroup:
        """Update a target group. Raises TargetGroupNotFoundError if not found."""
        target_group = self.repository.get_by_id(target_group_id)
        if not target_group:
            raise TargetGroupNotFoundError(target_group_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(target_group, key, value)

        return self.repository.update(target_group)

    def delete_target_group(self, target_group_id: UUID) -> None:
        """Delete a target group. Raises TargetGroupNotFoundError if not found."""
        target_group = self.repository.get_by_id(target_group_id)
        if not target_group:
            raise TargetGroupNotFoundError(target_group_id)
        self.repository.delete(target_group)
