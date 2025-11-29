import os
from collections.abc import Generator

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, SQLModel

# Import models to register them with SQLModel
from models import *  # noqa: F403
from campaigns.models import *  # noqa: F403

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/project_database',
)


def ensure_database_exists() -> None:
    """Create the database if it doesn't exist."""
    # Parse the database URL to get connection details
    # Format: postgresql://user:password@host:port/database
    if 'postgresql://' not in DATABASE_URL:
        return  # Not PostgreSQL, skip

    try:
        # Extract database name from URL
        db_name = DATABASE_URL.split('/')[-1].split('?')[0]
        # Create URL to connect to default 'postgres' database
        base_url = '/'.join(DATABASE_URL.split('/')[:-1]) + '/postgres'

        # Connect to postgres database to create the target database
        temp_engine = create_engine(base_url, isolation_level='AUTOCOMMIT')
        with temp_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text(
                    "SELECT 1 FROM pg_database WHERE datname = :db_name"
                ),
                {'db_name': db_name}
            )
            exists = result.fetchone() is not None

            if not exists:
                # Create the database
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
        temp_engine.dispose()
    except OperationalError:
        # Database might already exist or connection failed
        # Let SQLModel handle the error when trying to create tables
        pass


# Create engine
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables() -> None:
    """Create database and tables from SQLModel models."""
    ensure_database_exists()
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    """Dependency to get database session."""
    with Session(engine) as session:
        yield session
