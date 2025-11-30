import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import dotenv

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

from sqlmodel import Session, select

from assets.router import router as assets_router, process_asset_description_and_embedding
from campaign_specs.router import router as campaign_specs_router
from campaigns.router import router as campaigns_router
from database import create_db_and_tables, engine
from functions.router import router as jobs_router
from functions.scheduler import JobScheduler, SchedulerConfig, run_scheduler_loop
from models import Asset
from target_groups.router import router as target_groups_router

# Background scheduler task
scheduler_task: asyncio.Task | None = None


async def backfill_asset_embeddings() -> None:
    """
    Backfill descriptions and embeddings for assets that don't have them.

    This runs on startup to ensure all existing assets have embeddings.
    """
    logger.info("Starting asset embedding backfill...")

    with Session(engine) as session:
        # Find assets without embeddings
        statement = select(Asset).where(Asset.embedding == None)  # noqa: E711
        assets_without_embeddings = list(session.exec(statement).all())

        if not assets_without_embeddings:
            logger.info("No assets need embedding backfill")
            return

        logger.info(f"Found {len(assets_without_embeddings)} assets to process")

        for i, asset in enumerate(assets_without_embeddings):
            logger.info(f"Processing asset {i + 1}/{len(assets_without_embeddings)}: {asset.id} ({asset.name})")
            await process_asset_description_and_embedding(asset, session)

    logger.info("Asset embedding backfill complete")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global scheduler_task

    # Startup: create database tables
    create_db_and_tables()

    # Backfill asset embeddings for existing assets
    await backfill_asset_embeddings()

    # Start background scheduler with async processing
    scheduler = JobScheduler(SchedulerConfig(
        poll_interval_seconds=10.0,
        max_jobs_per_run=5,
    ))
    scheduler_task = asyncio.create_task(run_scheduler_loop(scheduler))
    logger.info("Background job scheduler started")

    yield

    # Shutdown: cancel scheduler
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        logger.info("Background job scheduler stopped")


app = FastAPI(lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Register routers
app.include_router(assets_router)
app.include_router(target_groups_router)
app.include_router(campaign_specs_router)
app.include_router(campaigns_router)
app.include_router(jobs_router)


@app.get('/')
def read_root() -> dict[str, str]:
    return {'message': 'Hello from backend!'}


def main() -> None:
    uvicorn.run(app, host='0.0.0.0', port=8000)


if __name__ == '__main__':
    main()
