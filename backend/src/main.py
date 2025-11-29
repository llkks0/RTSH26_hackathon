from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from assets.router import router as assets_router
from campaign_specs.router import router as campaign_specs_router
from campaigns.router import router as campaigns_router
from database import create_db_and_tables
from target_groups.router import router as target_groups_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: create database tables
    create_db_and_tables()
    yield
    # Shutdown: cleanup if needed
    pass


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


@app.get('/')
def read_root() -> dict[str, str]:
    return {'message': 'Hello from backend!'}


def main() -> None:
    uvicorn.run(app, host='0.0.0.0', port=8000)


if __name__ == '__main__':
    main()
