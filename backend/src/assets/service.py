from uuid import UUID

from assets.repository import AssetRepository
from models import Asset, AssetCreate, AssetType, AssetUpdate


class AssetNotFoundError(Exception):
    """Raised when an asset is not found."""

    def __init__(self, asset_id: UUID) -> None:
        self.asset_id = asset_id
        super().__init__(f'Asset with id {asset_id} not found')


class AssetService:
    """Business logic layer for Asset operations."""

    def __init__(self, repository: AssetRepository) -> None:
        self.repository = repository

    def create_asset(self, data: AssetCreate) -> Asset:
        """Create a new asset."""
        asset = Asset.model_validate(data)
        return self.repository.create(asset)

    def get_asset(self, asset_id: UUID) -> Asset:
        """Get an asset by ID. Raises AssetNotFoundError if not found."""
        asset = self.repository.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundError(asset_id)
        return asset

    def list_assets(
        self,
        skip: int = 0,
        limit: int = 100,
        asset_type: AssetType | None = None,
    ) -> list[Asset]:
        """List all assets with optional filtering and pagination."""
        return self.repository.get_all(skip=skip, limit=limit, asset_type=asset_type)

    def update_asset(self, asset_id: UUID, data: AssetUpdate) -> Asset:
        """Update an asset. Raises AssetNotFoundError if not found."""
        asset = self.repository.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundError(asset_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(asset, key, value)

        return self.repository.update(asset)

    def delete_asset(self, asset_id: UUID) -> None:
        """Delete an asset. Raises AssetNotFoundError if not found."""
        asset = self.repository.get_by_id(asset_id)
        if not asset:
            raise AssetNotFoundError(asset_id)
        self.repository.delete(asset)
