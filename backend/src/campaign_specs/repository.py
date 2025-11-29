from uuid import UUID

from sqlmodel import Session, select

from models import (
    Asset,
    CampaignSpec,
    CampaignSpecAsset,
    CampaignSpecTargetGroup,
    TargetGroup,
)


class CampaignSpecRepository:
    """Data access layer for CampaignSpec entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, campaign_spec: CampaignSpec) -> CampaignSpec:
        """Persist a new campaign spec to the database."""
        self.session.add(campaign_spec)
        self.session.commit()
        self.session.refresh(campaign_spec)
        return campaign_spec

    def get_by_id(self, campaign_spec_id: UUID) -> CampaignSpec | None:
        """Get a campaign spec by its ID."""
        return self.session.get(CampaignSpec, campaign_spec_id)

    def get_all(self, skip: int = 0, limit: int = 100) -> list[CampaignSpec]:
        """Get all campaign specs with pagination."""
        statement = select(CampaignSpec).offset(skip).limit(limit)
        return list(self.session.exec(statement).all())

    def update(self, campaign_spec: CampaignSpec) -> CampaignSpec:
        """Update an existing campaign spec."""
        self.session.add(campaign_spec)
        self.session.commit()
        self.session.refresh(campaign_spec)
        return campaign_spec

    def delete(self, campaign_spec: CampaignSpec) -> None:
        """Delete a campaign spec from the database."""
        self.session.delete(campaign_spec)
        self.session.commit()

    # Asset link management
    def add_asset(self, campaign_spec_id: UUID, asset_id: UUID) -> None:
        """Link an asset to a campaign spec."""
        link = CampaignSpecAsset(campaign_spec_id=campaign_spec_id, asset_id=asset_id)
        self.session.add(link)
        self.session.commit()

    def remove_asset(self, campaign_spec_id: UUID, asset_id: UUID) -> bool:
        """Remove an asset link from a campaign spec."""
        statement = select(CampaignSpecAsset).where(
            CampaignSpecAsset.campaign_spec_id == campaign_spec_id,
            CampaignSpecAsset.asset_id == asset_id,
        )
        link = self.session.exec(statement).first()
        if link:
            self.session.delete(link)
            self.session.commit()
            return True
        return False

    def get_assets(self, campaign_spec_id: UUID) -> list[Asset]:
        """Get all assets linked to a campaign spec."""
        statement = (
            select(Asset)
            .join(CampaignSpecAsset)
            .where(CampaignSpecAsset.campaign_spec_id == campaign_spec_id)
        )
        return list(self.session.exec(statement).all())

    # Target group link management
    def add_target_group(self, campaign_spec_id: UUID, target_group_id: UUID) -> None:
        """Link a target group to a campaign spec."""
        link = CampaignSpecTargetGroup(
            campaign_spec_id=campaign_spec_id, target_group_id=target_group_id
        )
        self.session.add(link)
        self.session.commit()

    def remove_target_group(self, campaign_spec_id: UUID, target_group_id: UUID) -> bool:
        """Remove a target group link from a campaign spec."""
        statement = select(CampaignSpecTargetGroup).where(
            CampaignSpecTargetGroup.campaign_spec_id == campaign_spec_id,
            CampaignSpecTargetGroup.target_group_id == target_group_id,
        )
        link = self.session.exec(statement).first()
        if link:
            self.session.delete(link)
            self.session.commit()
            return True
        return False

    def get_target_groups(self, campaign_spec_id: UUID) -> list[TargetGroup]:
        """Get all target groups linked to a campaign spec."""
        statement = (
            select(TargetGroup)
            .join(CampaignSpecTargetGroup)
            .where(CampaignSpecTargetGroup.campaign_spec_id == campaign_spec_id)
        )
        return list(self.session.exec(statement).all())
