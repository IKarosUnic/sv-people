"""FastAPI Application Server for the Saltbor Visual Simulation Platform.

Hosts the REST APIs, Server-Sent Events (SSE) telemetry stream, and mounts
the static Single-Page Simulation Application for 100% offline interactive observability.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from saltbor.visualization.api import router as api_router, set_controller
from saltbor.visualization.controller import SimulationController

logger = logging.getLogger(__name__)

WEB_DIR = Path(__file__).parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage simulation background worker lifecycle."""
    controller = getattr(app.state, "controller", None)
    if controller:
        controller.start_worker()
        logger.info("Simulation controller started in lifespan.")
    yield
    if controller:
        controller.stop_worker()
        logger.info("Simulation controller stopped in lifespan.")


def create_app(
    controller: Optional[SimulationController] = None,
    seed: Optional[int] = 42,
    db_path: str = "saltbor.db",
) -> FastAPI:
    """Create and configure the FastAPI simulation application."""
    app = FastAPI(
        title="SALTBOR — Interactive Visual Simulation Platform",
        description="Digital Society Observability, Real Territorial World Explorer & Cognitive Architecture Workbench",
        version="1.3.0-V",
        lifespan=lifespan,
    )

    # Allow CORS for flexible local development and embedded webviews
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize or bind controller
    if controller is None:
        controller = SimulationController(seed=seed, db_path=db_path)

    app.state.controller = controller
    set_controller(controller)

    # Mount API endpoints
    app.include_router(api_router)

    # Mount web application static assets
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

    return app


def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    seed: Optional[int] = 42,
    db_path: str = "saltbor.db",
) -> None:
    """Launch the simulation visualization server via Uvicorn."""
    import uvicorn

    app = create_app(seed=seed, db_path=db_path)
    print(f"\n" + "=" * 80)
    print("  SALTBOR — PHASE 1.3-V VISUAL SIMULATION PLATFORM")
    print(f"  * Local Web Interface : http://{host}:{port}/")
    print(f"  * Interactive API Docs: http://{host}:{port}/docs")
    print(f"  * Simulation Database : {db_path}")
    print(f"  * Master Random Seed  : {seed}")
    print("=" * 80 + "\n")
    uvicorn.run(app, host=host, port=port, log_level="info")
