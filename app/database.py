import logging
import traceback

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# ---------------------------------------------------------------------------
# Fix 1: Auto-convert "postgres://" → "postgresql://" (SQLAlchemy requirement)
# ---------------------------------------------------------------------------
_db_url = settings.DATABASE_URL
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    logger.warning("DATABASE_URL scheme corrected: postgres:// → postgresql://")

# ---------------------------------------------------------------------------
# Fix 2: Ensure SSL for Neon – add sslmode=require if not already present
# ---------------------------------------------------------------------------
if "sslmode" not in _db_url:
    separator = "&" if "?" in _db_url else "?"
    _db_url = f"{_db_url}{separator}sslmode=require"
    logger.warning("sslmode=require appended to DATABASE_URL for Neon compatibility.")

# ---------------------------------------------------------------------------
# Engine — pool_pre_ping reconnects automatically after idle drops
# ---------------------------------------------------------------------------
engine = create_engine(
    _db_url,
    pool_pre_ping=True,      # Detect stale/dropped connections before use
    pool_size=5,
    max_overflow=10,
    echo=True,               # ← Prints every SQL query to console for debugging
                             #   Set to False in production
    connect_args={
        "connect_timeout": 10,   # Fail fast instead of hanging
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ---------------------------------------------------------------------------
# Fix 3: get_db with rollback-on-error so bad commits don't leave dirty state
# ---------------------------------------------------------------------------
def get_db():
    """
    FastAPI Dependency – yields a database session.
    • Commits are handled explicitly in each route.
    • Rolls back automatically if an unhandled exception occurs.
    • Always closes the session (releases connection to pool).
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        logger.error("Database session error – rolling back:\n%s", traceback.format_exc())
        db.rollback()
        raise
    finally:
        db.close()


def verify_connection() -> bool:
    """Utility: test the DB connection at startup."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection verified successfully.")
        return True
    except Exception as exc:
        logger.error("❌ Database connection FAILED: %s", exc)
        return False

