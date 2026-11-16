"""
SmartKhet 2.0 — Cloud API Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from services.cloud_service import cloud_service
from services.audit_service import audit_service

router = APIRouter()


@router.get("/status")
def cloud_status(db: Session = Depends(get_db)):
    """Return cloud connection status and sync statistics."""
    return cloud_service.get_stats(db)


@router.get("/sync-history")
def get_sync_history(limit: int = 20, db: Session = Depends(get_db)):
    """Return simulated/actual cloud sync history events."""
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    events = []
    for i in range(min(limit, 10)):
        events.append({
            "id": i + 1,
            "node_id": f"FOG-00{(i % 3) + 1}",
            "farm_id": f"TN00{(i % 3) + 1}",
            "records_synced": 90 - (i * 5),
            "status": "success",
            "timestamp": (now - timedelta(minutes=(i * 15) + 3)).isoformat(),
            "bytes_transferred": 14200 - (i * 600),
            "latency_ms": round(12.4 + (i * 0.8), 1),
        })
    return events


@router.post("/connect")
def connect(db: Session = Depends(get_db)):
    """Connect to the cloud endpoint."""
    result = cloud_service.connect()
    audit_service.log_event(db, action="cloud.connect", details=result)
    return result


@router.post("/disconnect")
def disconnect(db: Session = Depends(get_db)):
    """Disconnect from the cloud endpoint."""
    result = cloud_service.disconnect()
    audit_service.log_event(db, action="cloud.disconnect", details=result)
    return result


@router.post("/sync")
def sync(db: Session = Depends(get_db)):
    """Simulate a full data sync to the cloud."""
    if not cloud_service.connected:
        return {"status": "error", "message": "Cloud is not connected"}
    cloud_service.mark_sync()
    stats = cloud_service.get_stats(db)
    audit_service.log_event(db, action="cloud.sync", details={"records": stats["total_records_synced"]})
    return {"status": "synced", **stats}
