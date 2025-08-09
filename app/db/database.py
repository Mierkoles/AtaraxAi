"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base_class import Base

# Create database engine
if settings.effective_database_url.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        settings.effective_database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # Azure SQL configuration
    engine = create_engine(
        settings.effective_database_url,
        echo=settings.DEBUG,
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency to get database session.
    Use this as a dependency in FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
