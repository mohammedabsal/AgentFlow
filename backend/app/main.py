"""
AgentFlow: Production-Grade Autonomous Multi-Agent AI Software Engineering Platform

A Lovable-inspired system that transforms user prompts into fully-functional,
tested, and deployable full-stack applications using a coordinated multi-agent system.

Architecture:
- 11 specialized autonomous agents working in coordinated phases
- LangGraph-inspired orchestration engine
- Real-time WebSocket streaming of execution progress
- Self-healing loops for error recovery
- Docker-based workspace execution
- Comprehensive observability and tracing
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.database.session import bootstrap_database
from app.observability.logging import configure_logging
from app.runtime.workspace_executor import workspace_manager

logger = logging.getLogger(__name__)

# Configure logging and database
configure_logging()
bootstrap_database()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("AgentFlow starting up...")
    yield
    logger.info("AgentFlow shutting down...")


app = FastAPI(
    title="AgentFlow",
    version="0.2.0",
    description="Production-grade orchestration platform for autonomous multi-agent workflows.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(api_router, prefix="/api")


@app.get("/healthz", tags=["health"])
def healthz() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.2.0"}


@app.get("/api/health", tags=["health"])
def api_health() -> dict[str, str]:
    """Detailed health check with system status."""
    return {
        "status": "ok",
        "version": "0.2.0",
        "active_workspaces": len(workspace_manager.active_workspaces),
        "agents_available": "11",
        "feature": "autonomous_multi_agent_system",
    }


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "AgentFlow",
        "version": "0.2.0",
        "description": "Autonomous Multi-Agent AI Software Engineering Platform",
        "docs": "/docs",
        "api": "/api",
        "health": "/healthz",
    }
