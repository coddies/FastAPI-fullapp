from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

# Neon PostgreSQL requires SSL – psycopg2 respects the sslmode in the URL
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,          # Detect stale connections before use
    pool_size=5,
    max_overflow=10,
    echo=False,                  # Set True to log SQL statements for debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def get_db():
    """
    FastAPI Dependency – yields a database session and ensures
    it is always closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
