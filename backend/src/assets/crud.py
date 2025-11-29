from uuid import UUID

from sqlmodel import Session, select

from models import Asset, AssetType


def create_asset(session: Session, asset: Asset) -> Asset:
    """Create a new asset."""
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def get_asset(session: Session, asset_id: UUID) -> Asset | None:
    """Get an asset by ID."""
    return session.get(Asset, asset_id)


def get_assets(
    session: Session,
    skip: int = 0,
    limit: int = 100,
    asset_type: AssetType | None = None,
) -> list[Asset]:
    """Get all assets with optional filtering and pagination."""
    statement = select(Asset)
    if asset_type:
        statement = statement.where(Asset.asset_type == asset_type)
    statement = statement.offset(skip).limit(limit)
    return list(session.exec(statement).all())


def update_asset(session: Session, asset_id: UUID, asset_update: dict) -> Asset | None:
    """Update an asset."""
    asset = session.get(Asset, asset_id)
    if not asset:
        return None
    for key, value in asset_update.items():
        setattr(asset, key, value)
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def delete_asset(session: Session, asset_id: UUID) -> bool:
    """Delete an asset."""
    asset = session.get(Asset, asset_id)
    if not asset:
        return False
    session.delete(asset)
    session.commit()
    return True
