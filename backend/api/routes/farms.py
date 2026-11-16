"""
SmartKhet 2.0 — Farms API Routes
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from models.db_models import Farm
from models.schemas import FarmCreate, FarmResponse
from services.audit_service import audit_service

router = APIRouter()


@router.get("/", response_model=List[FarmResponse])
def list_farms(db: Session = Depends(get_db)):
    """Return all registered farms."""
    return db.query(Farm).all()


@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(farm_id: str, db: Session = Depends(get_db)):
    """Return a single farm by ID."""
    farm = db.query(Farm).filter(Farm.farm_id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail=f"Farm {farm_id} not found")
    return farm


@router.post("/", response_model=FarmResponse, status_code=201)
def create_farm(payload: FarmCreate, db: Session = Depends(get_db)):
    """Register a new farm."""
    existing = db.query(Farm).filter(Farm.farm_id == payload.farm_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Farm {payload.farm_id} already exists")
    farm = Farm(**payload.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    audit_service.log_event(
        db,
        action="farm.create",
        resource_type="Farm",
        resource_id=farm.farm_id,
        details={"district": farm.district, "crop": farm.crop},
    )
    return farm


@router.patch("/{farm_id}", response_model=FarmResponse)
def update_farm(farm_id: str, payload: dict, db: Session = Depends(get_db)):
    """Partial update of a farm's fields."""
    farm = db.query(Farm).filter(Farm.farm_id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail=f"Farm {farm_id} not found")
    for key, value in payload.items():
        if hasattr(farm, key) and key not in ("id", "farm_id", "created_at"):
            setattr(farm, key, value)
    db.commit()
    db.refresh(farm)
    audit_service.log_event(
        db,
        action="farm.update",
        resource_type="Farm",
        resource_id=farm_id,
        details={"updated_fields": list(payload.keys())},
    )
    return farm


@router.delete("/{farm_id}")
def delete_farm(farm_id: str, db: Session = Depends(get_db)):
    """Delete a farm and all associated data."""
    farm = db.query(Farm).filter(Farm.farm_id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail=f"Farm {farm_id} not found")
    db.delete(farm)
    db.commit()
    audit_service.log_event(
        db, action="farm.delete", resource_type="Farm", resource_id=farm_id
    )
    return {"status": "deleted", "farm_id": farm_id}


@router.get("/{farm_id}/data")
def get_farm_data(
    farm_id: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 120,
    db: Session = Depends(get_db),
):
    """Return historical records for a farm formatted for frontend charts."""
    farm = db.query(Farm).filter(Farm.farm_id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail=f"Farm {farm_id} not found")

    from models.db_models import DataRecord
    query = db.query(DataRecord).filter(DataRecord.farm_id == farm_id)
    if start:
        query = query.filter(DataRecord.recorded_at >= start)
    if end:
        query = query.filter(DataRecord.recorded_at <= end)

    records = query.order_by(DataRecord.recorded_at.asc()).limit(limit).all()

    return [
        {
            "id": r.id,
            "farm_id": r.farm_id,
            "date": r.recorded_at.isoformat(),
            "rainfall_mm": float(r.rainfall) if r.rainfall is not None else 0.0,
            "soil_moisture": float(r.soil_moisture) if r.soil_moisture is not None else 0.0,
            "temperature_c": float(r.temperature) if r.temperature is not None else 25.0,
            "humidity_pct": float(r.humidity) if r.humidity is not None else 60.0,
            "source": r.source or "sensor",
            "is_predicted": False,
        }
        for r in records
    ]


@router.get("/{farm_id}/predictions")
def get_farm_predictions(farm_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """Return predictions for a farm."""
    from models.db_models import Prediction
    return (
        db.query(Prediction)
        .filter(Prediction.farm_id == farm_id)
        .order_by(Prediction.predicted_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/{farm_id}/summary")
def get_farm_summary(farm_id: str, db: Session = Depends(get_db)):
    """Return a combined summary of farm, latest readings and prediction counts."""
    farm = db.query(Farm).filter(Farm.farm_id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail=f"Farm {farm_id} not found")

    from models.db_models import DataRecord, Prediction
    record_count = db.query(DataRecord).filter(DataRecord.farm_id == farm_id).count()
    pred_count = db.query(Prediction).filter(Prediction.farm_id == farm_id).count()
    latest = (
        db.query(DataRecord)
        .filter(DataRecord.farm_id == farm_id)
        .order_by(DataRecord.recorded_at.desc())
        .first()
    )

    return {
        "farm": FarmResponse.model_validate(farm),
        "total_records": record_count,
        "total_predictions": pred_count,
        "latest_reading": {
            "recorded_at": latest.recorded_at.isoformat() if latest else None,
            "soil_moisture": latest.soil_moisture if latest else None,
            "temperature": latest.temperature if latest else None,
            "ndvi": latest.ndvi if latest else None,
        },
    }
