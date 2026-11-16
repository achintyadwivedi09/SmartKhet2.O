"""
SmartKhet 2.0 — Fog Computing API Routes
"""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from models.db_models import FogEvent, FogNode as FogNodeDB
from models.schemas import FogInferenceRequest, FogNodeResponse
from services.fog_service import fog_service
from services.audit_service import audit_service

router = APIRouter()


@router.get("/nodes", response_model=List[Dict[str, Any]])
def list_nodes(db: Session = Depends(get_db)):
    """Return status of all fog nodes."""
    return fog_service.get_all_nodes()


@router.get("/nodes/{farm_id}")
def get_node(farm_id: str):
    """Return state of a specific fog node."""
    node = fog_service.get_node(farm_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"No fog node for farm {farm_id}")
    return node.to_dict()


@router.post("/nodes/{farm_id}/infer")
def fog_infer(
    farm_id: str,
    payload: FogInferenceRequest,
    db: Session = Depends(get_db),
):
    """Run ML inference on the fog node for the given farm."""
    features = payload.model_dump(exclude={"farm_id"})
    try:
        result = fog_service.run_inference(farm_id, features, db)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    audit_service.log_event(
        db,
        action="fog.inference",
        resource_type="FogNode",
        resource_id=farm_id,
        details={"label": result.get("prediction_label")},
    )
    return result


@router.post("/nodes/{farm_id}/sync")
def sync_node(farm_id: str, db: Session = Depends(get_db)):
    """Push buffered events from a fog node to the cloud."""
    try:
        result = fog_service.sync_to_cloud(farm_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    audit_service.log_event(
        db,
        action="fog.sync",
        resource_type="FogNode",
        resource_id=farm_id,
        details=result,
    )
    return result


@router.post("/nodes/{farm_id}/disconnect")
def disconnect_cloud(farm_id: str):
    """Simulate cloud link disconnection."""
    try:
        return fog_service.disconnect_cloud(farm_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/nodes/{farm_id}/reconnect")
def reconnect_cloud(farm_id: str):
    """Simulate cloud link reconnection."""
    try:
        return fog_service.reconnect_cloud(farm_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/nodes/{farm_id}/offline")
def set_offline(farm_id: str):
    """Take a fog node offline."""
    return fog_service.set_offline(farm_id)


@router.post("/nodes/{farm_id}/online")
def set_online(farm_id: str):
    """Bring a fog node back online."""
    return fog_service.set_online(farm_id)


@router.get("/nodes/{farm_id}/events")
def get_buffered_events(farm_id: str):
    """Return in-memory buffered events for a fog node."""
    return fog_service.get_buffered_events(farm_id)


@router.get("/events", response_model=List[Dict[str, Any]])
def list_fog_events(
    node_id: str = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Return persisted fog events from the database."""
    query = db.query(FogEvent)
    if node_id:
        query = query.filter(FogEvent.node_id == node_id)
    rows = query.order_by(FogEvent.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "node_id": r.node_id,
            "event_type": r.event_type,
            "payload": r.payload,
            "is_synced": r.is_synced,
            "created_at": r.created_at.isoformat(),
            "synced_at": r.synced_at.isoformat() if r.synced_at else None,
        }
        for r in rows
    ]
