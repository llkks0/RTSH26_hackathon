from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from assets.repository import AssetRepository
from assets.service import AssetNotFoundError, AssetService
from database import get_session
from models import Asset, AssetCreate, AssetType, AssetUpdate

router = APIRouter(prefix='/assets', tags=['assets'])

ASSET_FILES_DIR = Path(__file__).parent.parent.parent / 'asset-files'
ASSET_FILES_DIR.mkdir(exist_ok=True)


def get_asset_service(session: Session = Depends(get_session)) -> AssetService:
    """Dependency injection for AssetService."""
    repository = AssetRepository(session)
    return AssetService(repository)


@router.post('/', response_model=Asset, status_code=201)
def create_asset(
    data: AssetCreate,
    service: AssetService = Depends(get_asset_service),
) -> Asset:
    """Create a new asset (metadata only, no file upload)."""
    return service.create_asset(data)


@router.post('/upload', response_model=Asset, status_code=201)
async def upload_asset(
    file: UploadFile = File(...),
    name: str = Form(...),
    asset_type: AssetType = Form(...),
    caption: str = Form(...),
    tags: str = Form(default=''),  # comma-separated tags
    service: AssetService = Depends(get_asset_service),
) -> Asset:
    """Upload a file and create an asset."""
    # Generate unique filename
    file_ext = Path(file.filename or '').suffix
    unique_filename = f'{uuid4()}{file_ext}'
    file_path = ASSET_FILES_DIR / unique_filename

    # Save file
    content = await file.read()
    file_path.write_bytes(content)

    # Parse tags
    tag_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else []

    # Create asset record
    asset_data = AssetCreate(
        name=name,
        file_name=unique_filename,
        asset_type=asset_type,
        caption=caption,
        tags=tag_list,
    )
    return service.create_asset(asset_data)


@router.get('/files/{filename}')
def get_asset_file(filename: str) -> FileResponse:
    """Serve an asset file."""
    file_path = ASSET_FILES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='File not found')
    return FileResponse(file_path)


@router.get('/', response_model=list[Asset])
def list_assets(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    asset_type: AssetType | None = Query(default=None),
    service: AssetService = Depends(get_asset_service),
) -> list[Asset]:
    """Get all assets with optional filtering and pagination."""
    return service.list_assets(skip=skip, limit=limit, asset_type=asset_type)


@router.get('/{asset_id}', response_model=Asset)
def get_asset(
    asset_id: UUID,
    service: AssetService = Depends(get_asset_service),
) -> Asset:
    """Get a specific asset by ID."""
    try:
        return service.get_asset(asset_id)
    except AssetNotFoundError:
        raise HTTPException(status_code=404, detail='Asset not found')


@router.patch('/{asset_id}', response_model=Asset)
def update_asset(
    asset_id: UUID,
    data: AssetUpdate,
    service: AssetService = Depends(get_asset_service),
) -> Asset:
    """Update an asset."""
    try:
        return service.update_asset(asset_id, data)
    except AssetNotFoundError:
        raise HTTPException(status_code=404, detail='Asset not found')


@router.delete('/{asset_id}', status_code=204)
def delete_asset(
    asset_id: UUID,
    service: AssetService = Depends(get_asset_service),
) -> None:
    """Delete an asset."""
    try:
        service.delete_asset(asset_id)
    except AssetNotFoundError:
        raise HTTPException(status_code=404, detail='Asset not found')