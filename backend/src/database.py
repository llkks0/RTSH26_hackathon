import os
from collections.abc import Generator

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from sqlmodel import Session, SQLModel, create_engine

# Import models to register them with SQLModel
from models import *  # noqa: F403

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/project_database',
)

# Create engine
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables() -> None:
    """Create database tables from SQLModel models."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    """Dependency to get database session."""
    with Session(engine) as session:
        yield session
