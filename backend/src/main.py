from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Session

from assets.crud import (
    create_asset,
    delete_asset,
    get_asset,
    get_assets,
    update_asset,
)
from database import create_db_and_tables, get_session
from models import Asset, AssetCreate, AssetType, AssetUpdate


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: create database tables
    create_db_and_tables()
    yield
    # Shutdown: cleanup if needed
    pass


app = FastAPI(lifespan=lifespan)


@app.get('/')
def read_root() -> dict[str, str]:
    return {'message': 'Hello from backend!'}


# Asset CRUD endpoints
@app.post('/assets/', response_model=Asset, status_code=201)
def create_asset_endpoint(asset_data: AssetCreate, session: Session = Depends(get_session)) -> Asset:
    """Create a new asset."""
    asset = Asset(**asset_data.model_dump())
    return create_asset(session, asset)


@app.get('/assets/', response_model=list[Asset])
def read_assets(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    asset_type: AssetType | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[Asset]:
    """Get all assets with optional filtering and pagination."""
    return get_assets(session, skip=skip, limit=limit, asset_type=asset_type)


@app.get('/assets/{asset_id}', response_model=Asset)
def read_asset(asset_id: UUID, session: Session = Depends(get_session)) -> Asset:
    """Get a specific asset by ID."""
    asset = get_asset(session, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail='Asset not found')
    return asset


@app.put('/assets/{asset_id}', response_model=Asset)
def update_asset_endpoint(
    asset_id: UUID,
    asset_update: AssetUpdate,
    session: Session = Depends(get_session),
) -> Asset:
    """Update an asset."""
    # Filter out None values from the update
    update_data = {k: v for k, v in asset_update.model_dump().items() if v is not None}
    asset = update_asset(session, asset_id, update_data)
    if not asset:
        raise HTTPException(status_code=404, detail='Asset not found')
    return asset


@app.delete('/assets/{asset_id}', status_code=204)
def delete_asset_endpoint(asset_id: UUID, session: Session = Depends(get_session)) -> None:
    """Delete an asset."""
    success = delete_asset(session, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail='Asset not found')


def main() -> None:
    uvicorn.run(app, host='0.0.0.0', port=8000)


if __name__ == '__main__':
    main()
