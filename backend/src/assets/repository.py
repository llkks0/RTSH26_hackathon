from uuid import UUID

from sqlmodel import Session, select

from models import Asset, AssetType


class AssetRepository:
    """Data access layer for Asset entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, asset: Asset) -> Asset:
        """Persist a new asset to the database."""
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def get_by_id(self, asset_id: UUID) -> Asset | None:
        """Get an asset by its ID."""
        return self.session.get(Asset, asset_id)

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        asset_type: AssetType | None = None,
    ) -> list[Asset]:
        """Get all assets with optional filtering and pagination."""
        statement = select(Asset)
        if asset_type:
            statement = statement.where(Asset.asset_type == asset_type)
        statement = statement.offset(skip).limit(limit)
        return list(self.session.exec(statement).all())

    def update(self, asset: Asset) -> Asset:
        """Update an existing asset."""
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def delete(self, asset: Asset) -> None:
        """Delete an asset from the database."""
        self.session.delete(asset)
        self.session.commit()
