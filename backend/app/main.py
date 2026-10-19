"""Afterlight API — main application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, vault, assets, dead_mans_switch, legacy_messages, executor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup
    engine.dispose()


app = FastAPI(
    title="Afterlight API",
    description="Digital Estate Planning & Legacy Infrastructure",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(vault.router)
app.include_router(assets.router)
app.include_router(dead_mans_switch.router)
app.include_router(legacy_messages.router)
app.include_router(executor.router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "afterlight-api", "version": "0.1.0"}


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "Afterlight API",
        "description": "Digital Estate Planning & Legacy Infrastructure",
        "version": "0.1.0",
        "docs": "/docs",
    }
