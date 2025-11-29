from uuid import UUID

from campaign_specs.repository import CampaignSpecRepository
from models import Asset, CampaignSpec, CampaignSpecCreate, CampaignSpecUpdate, TargetGroup


class CampaignSpecNotFoundError(Exception):
    """Raised when a campaign spec is not found."""

    def __init__(self, campaign_spec_id: UUID) -> None:
        self.campaign_spec_id = campaign_spec_id
        super().__init__(f'CampaignSpec with id {campaign_spec_id} not found')


class CampaignSpecService:
    """Business logic layer for CampaignSpec operations."""

    def __init__(self, repository: CampaignSpecRepository) -> None:
        self.repository = repository

    def create_campaign_spec(self, data: CampaignSpecCreate) -> CampaignSpec:
        """Create a new campaign spec."""
        # Extract target_group_ids before creating the campaign spec
        target_group_ids = data.target_group_ids
        campaign_data = data.model_dump(exclude={'target_group_ids'})
        campaign_spec = CampaignSpec.model_validate(campaign_data)
        campaign_spec = self.repository.create(campaign_spec)

        # Add target groups if provided
        for target_group_id in target_group_ids:
            self.repository.add_target_group(campaign_spec.id, target_group_id)

        # Refresh to get the relationships loaded
        return self.repository.get_by_id(campaign_spec.id)  # type: ignore

    def get_campaign_spec(self, campaign_spec_id: UUID) -> CampaignSpec:
        """Get a campaign spec by ID. Raises CampaignSpecNotFoundError if not found."""
        campaign_spec = self.repository.get_by_id(campaign_spec_id)
        if not campaign_spec:
            raise CampaignSpecNotFoundError(campaign_spec_id)
        return campaign_spec

    def list_campaign_specs(self, skip: int = 0, limit: int = 100) -> list[CampaignSpec]:
        """List all campaign specs with pagination."""
        return self.repository.get_all(skip=skip, limit=limit)

    def update_campaign_spec(
        self, campaign_spec_id: UUID, data: CampaignSpecUpdate
    ) -> CampaignSpec:
        """Update a campaign spec. Raises CampaignSpecNotFoundError if not found."""
        campaign_spec = self.repository.get_by_id(campaign_spec_id)
        if not campaign_spec:
            raise CampaignSpecNotFoundError(campaign_spec_id)

        update_data = data.model_dump(exclude_unset=True)
        target_group_ids = update_data.pop('target_group_ids', None)

        # Update basic fields
        for key, value in update_data.items():
            setattr(campaign_spec, key, value)

        campaign_spec = self.repository.update(campaign_spec)

        # Update target groups if provided
        if target_group_ids is not None:
            # Remove all existing target groups
            current_target_groups = self.repository.get_target_groups(campaign_spec_id)
            for tg in current_target_groups:
                self.repository.remove_target_group(campaign_spec_id, tg.id)

            # Add new target groups
            for target_group_id in target_group_ids:
                self.repository.add_target_group(campaign_spec_id, target_group_id)

            # Refresh to get updated relationships
            campaign_spec = self.repository.get_by_id(campaign_spec_id)  # type: ignore

        return campaign_spec

    def delete_campaign_spec(self, campaign_spec_id: UUID) -> None:
        """Delete a campaign spec. Raises CampaignSpecNotFoundError if not found."""
        campaign_spec = self.repository.get_by_id(campaign_spec_id)
        if not campaign_spec:
            raise CampaignSpecNotFoundError(campaign_spec_id)
        self.repository.delete(campaign_spec)

    # Asset management
    def add_asset(self, campaign_spec_id: UUID, asset_id: UUID) -> None:
        """Add an asset to a campaign spec."""
        if not self.repository.get_by_id(campaign_spec_id):
            raise CampaignSpecNotFoundError(campaign_spec_id)
        self.repository.add_asset(campaign_spec_id, asset_id)

    def remove_asset(self, campaign_spec_id: UUID, asset_id: UUID) -> None:
        """Remove an asset from a campaign spec."""
        if not self.repository.get_by_id(campaign_spec_id):
            raise CampaignSpecNotFoundError(campaign_spec_id)
        self.repository.remove_asset(campaign_spec_id, asset_id)

    def get_assets(self, campaign_spec_id: UUID) -> list[Asset]:
        """Get all assets for a campaign spec."""
        if not self.repository.get_by_id(campaign_spec_id):
            raise CampaignSpecNotFoundError(campaign_spec_id)
        return self.repository.get_assets(campaign_spec_id)

    # Target group management
    def add_target_group(self, campaign_spec_id: UUID, target_group_id: UUID) -> None:
        """Add a target group to a campaign spec."""
        if not self.repository.get_by_id(campaign_spec_id):
            raise CampaignSpecNotFoundError(campaign_spec_id)
        self.repository.add_target_group(campaign_spec_id, target_group_id)

    def remove_target_group(self, campaign_spec_id: UUID, target_group_id: UUID) -> None:
        """Remove a target group from a campaign spec."""
        if not self.repository.get_by_id(campaign_spec_id):
            raise CampaignSpecNotFoundError(campaign_spec_id)
        self.repository.remove_target_group(campaign_spec_id, target_group_id)

    def get_target_groups(self, campaign_spec_id: UUID) -> list[TargetGroup]:
        """Get all target groups for a campaign spec."""
        if not self.repository.get_by_id(campaign_spec_id):
            raise CampaignSpecNotFoundError(campaign_spec_id)
        return self.repository.get_target_groups(campaign_spec_id)
