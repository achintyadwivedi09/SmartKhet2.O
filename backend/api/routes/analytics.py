"""
SmartKhet 2.0 — Analytics API Routes
Provides aggregated analytics for the dashboard.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import FARMS
from models.db_models import DataRecord, Prediction, AuditLog

router = APIRouter()


@router.get("/overview")
def overview(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """High-level platform overview for the dashboard header."""
    total_records = db.query(DataRecord).count()
    total_predictions = db.query(Prediction).count()
    total_audit = db.query(AuditLog).count()
    farms = list(FARMS.keys())

    # Average soil moisture per farm from last 7 days
    since = datetime.utcnow() - timedelta(days=7)
    farm_moisture = {}
    for fid in farms:
        avg = (
            db.query(func.avg(DataRecord.soil_moisture))
            .filter(DataRecord.farm_id == fid, DataRecord.recorded_at >= since)
            .scalar()
        )
        farm_moisture[fid] = round(avg, 3) if avg else None

    return {
        "total_records": total_records,
        "total_predictions": total_predictions,
        "total_audit_events": total_audit,
        "farms_active": len(farms),
        "average_soil_moisture_7d": farm_moisture,
    }


@router.get("/timeseries")
def timeseries(
    farm_id: str = Query(...),
    metric: str = Query("soil_moisture", description="temperature|humidity|soil_moisture|ndvi|rainfall"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return a time series of a chosen metric for a farm."""
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(DataRecord)
        .filter(DataRecord.farm_id == farm_id, DataRecord.recorded_at >= since)
        .order_by(DataRecord.recorded_at.asc())
        .all()
    )

    allowed = {"temperature", "humidity", "soil_moisture", "ndvi", "rainfall",
               "wind_speed", "solar_radiation", "ph", "nitrogen", "phosphorus", "potassium"}
    if metric not in allowed:
        metric = "soil_moisture"

    return [
        {
            "timestamp": r.recorded_at.isoformat(),
            "value": getattr(r, metric),
            "is_demo": r.is_demo,
        }
        for r in rows
        if getattr(r, metric) is not None
    ]


@router.get("/crop-health")
def crop_health(
    farm_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Summarise crop health indicators for a farm from recent data."""
    since = datetime.utcnow() - timedelta(days=7)
    rows = (
        db.query(DataRecord)
        .filter(DataRecord.farm_id == farm_id, DataRecord.recorded_at >= since)
        .all()
    )

    cfg = FARMS.get(farm_id)
    if not rows:
        return {"farm_id": farm_id, "status": "no data", "records_checked": 0}

    avg_ndvi = sum(r.ndvi for r in rows if r.ndvi is not None) / max(
        len([r for r in rows if r.ndvi is not None]), 1
    )
    avg_sm = sum(r.soil_moisture for r in rows if r.soil_moisture is not None) / max(
        len([r for r in rows if r.soil_moisture is not None]), 1
    )
    avg_temp = sum(r.temperature for r in rows if r.temperature is not None) / max(
        len([r for r in rows if r.temperature is not None]), 1
    )

    ndvi_ok = avg_ndvi >= (cfg.ndvi_healthy_min if cfg else 0.45)
    sm_ok = avg_sm >= (cfg.irrigation_trigger_moisture if cfg else 0.18)
    temp_ok = (cfg.temperature_min_safe if cfg else 15) <= avg_temp <= (cfg.temperature_max_safe if cfg else 42)

    alerts = []
    if not ndvi_ok:
        alerts.append("Low NDVI — possible crop stress")
    if not sm_ok:
        alerts.append("Low soil moisture — irrigation recommended")
    if not temp_ok:
        alerts.append("Temperature outside safe range")

    health_score = round((ndvi_ok + sm_ok + temp_ok) / 3.0 * 100, 1)

    return {
        "farm_id": farm_id,
        "records_checked": len(rows),
        "avg_ndvi_7d": round(avg_ndvi, 3),
        "avg_soil_moisture_7d": round(avg_sm, 3),
        "avg_temperature_7d": round(avg_temp, 2),
        "health_score_pct": health_score,
        "alerts": alerts,
        "status": "healthy" if not alerts else "attention_required",
    }


@router.get("/predictions-summary")
def predictions_summary(
    farm_id: Optional[str] = Query(None),
    days: int = Query(7),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return a summary of predictions grouped by label."""
    since = datetime.utcnow() - timedelta(days=days)
    query = db.query(Prediction).filter(Prediction.predicted_at >= since)
    if farm_id:
        query = query.filter(Prediction.farm_id == farm_id)
    rows = query.all()

    label_counts: Dict[str, int] = {}
    for r in rows:
        label = r.prediction_label or "Unknown"
        label_counts[label] = label_counts.get(label, 0) + 1

    avg_confidence = (
        sum(r.confidence for r in rows if r.confidence) / max(len(rows), 1)
    )

    return {
        "total_predictions": len(rows),
        "label_distribution": label_counts,
        "average_confidence": round(avg_confidence, 4),
        "period_days": days,
        "farm_id": farm_id,
    }
