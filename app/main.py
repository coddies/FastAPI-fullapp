"""
main.py – FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import engine
from app.models import Base
from app.routers import tasks, users


# ---------------------------------------------------------------------------
# Lifespan: create tables on startup (Alembic handles migrations in prod)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables that don't exist yet – safe to call multiple times
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic here if needed (e.g. close connection pools)


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
# CORS middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Add prod domains
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
    return JSONResponse({"status": "healthy"})
