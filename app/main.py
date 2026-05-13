"""
main.py – FastAPI application entry point.
"""
import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import engine, verify_connection
from app.models import Base
from app.routers import tasks, users

# ---------------------------------------------------------------------------
# Logging – shows SQL queries, errors, and startup info in the terminal
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: verify DB connection + create any missing tables on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Task Manager API...")

    # Verify Neon DB is reachable before accepting requests
    if verify_connection():
        logger.info("✅ Neon PostgreSQL connection OK")
    else:
        logger.error("❌ Could not connect to Neon PostgreSQL – check DATABASE_URL in .env")

    # Create tables that don't exist yet (safe to call multiple times)
    # Alembic handles schema migrations; this is a safety net for new tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables verified / created.")
    except Exception as exc:
        logger.error("❌ Failed to create tables: %s", exc)

    yield

    logger.info("🛑 Task Manager API shutting down.")


# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Task Manager API",
    description=(
        "A production-ready REST API built with FastAPI, SQLAlchemy, "
        "Neon PostgreSQL, JWT authentication, and secure HTTP-only cookies."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Global exception handler – logs the real traceback and returns it in detail
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error(
        "Unhandled exception on %s %s\n%s",
        request.method, request.url, tb
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error.",
            "error": str(exc),
            # Remove 'traceback' in production for security
            "traceback": tb,
        },
    )


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,   # Required for cookie-based auth
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(users.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Root / health endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def root():
    return {"message": "Task Manager API is running 🚀", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health_check():
    ok = verify_connection()
    return JSONResponse({
        "status": "healthy" if ok else "unhealthy",
        "database": "connected" if ok else "unreachable",
    }, status_code=200 if ok else 503)

