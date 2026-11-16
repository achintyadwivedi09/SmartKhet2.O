"""
SmartKhet 2.0 — FastAPI Application Entrypoint
===============================================
Main server integrating Big Data analytics, ML inference,
Fog node processing, Cloud sync, and real-time WebSocket feeds.
"""

from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import APP_NAME, APP_VERSION, CORS_ORIGINS
from app.database import init_db, SessionLocal
from services.data_service import data_service
from services.fog_service import fog_service
from services.ml_service import ml_service
from services.audit_service import audit_service

from api.routes import (
    farms,
    datasets,
    ml,
    fog,
    cloud,
    audit,
    analytics,
    experiments,
)
from api import websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smartkhet")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("Initializing SmartKhet 2.0 Database...")
    init_db()

    db = SessionLocal()
    try:
        logger.info("Seeding demonstration farm datasets...")
        data_service.seed_demo_data(db)

        logger.info("Initializing Fog Computing nodes...")
        fog_service.init_db_nodes(db)

        logger.info("Syncing trained ML model metadata...")
        ml_service.sync_to_db(db)

        audit_service.log(
            action="SYSTEM_STARTUP",
            resource_type="system",
            resource_id="smartkhet-2.0",
            details={"version": APP_VERSION, "status": "online"},
            db=db,
        )
    except Exception as e:
        logger.error(f"Error during startup seeding: {e}")
    finally:
        db.close()

    yield

    # Shutdown sequence
    logger.info("Shutting down SmartKhet 2.0 server.")


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Big Data-Powered Fog-Based Intelligent Rural Irrigation System",
    lifespan=lifespan,
)

# CORS middleware for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": APP_NAME,
        "version": APP_VERSION,
        "model_loaded": ml_service.is_loaded,
        "farms_configured": 3,
        "fog_nodes_active": 3,
    }


# Include WebSocket endpoint
app.include_router(websocket.router, tags=["WebSocket"])

# Include Route Modules (both with and without /api prefix for proxy resilience)
route_modules = [
    (farms.router, "/farms", ["Farms"]),
    (datasets.router, "/datasets", ["Datasets"]),
    (ml.router, "/ml", ["Machine Learning"]),
    (fog.router, "/fog", ["Fog Computing"]),
    (cloud.router, "/cloud", ["Cloud Synchronization"]),
    (audit.router, "/audit", ["Audit & Provenance"]),
    (analytics.router, "/analytics", ["Analytics"]),
    (experiments.router, "/experiments", ["Experiments"]),
]

for router, prefix, tags in route_modules:
    app.include_router(router, prefix=prefix, tags=tags)
    app.include_router(router, prefix=f"/api{prefix}", tags=tags)

