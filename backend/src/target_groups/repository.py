from uuid import UUID

from sqlmodel import Session, select

from models import TargetGroup


class TargetGroupRepository:
    """Data access layer for TargetGroup entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, target_group: TargetGroup) -> TargetGroup:
        """Persist a new target group to the database."""
        self.session.add(target_group)
        self.session.commit()
        self.session.refresh(target_group)
        return target_group

    def get_by_id(self, target_group_id: UUID) -> TargetGroup | None:
        """Get a target group by its ID."""
        return self.session.get(TargetGroup, target_group_id)

    def get_all(self, skip: int = 0, limit: int = 100) -> list[TargetGroup]:
        """Get all target groups with pagination."""
        statement = select(TargetGroup).offset(skip).limit(limit)
        return list(self.session.exec(statement).all())

    def update(self, target_group: TargetGroup) -> TargetGroup:
        """Update an existing target group."""
        self.session.add(target_group)
        self.session.commit()
        self.session.refresh(target_group)
        return target_group

    def delete(self, target_group: TargetGroup) -> None:
        """Delete a target group from the database."""
        self.session.delete(target_group)
        self.session.commit()
