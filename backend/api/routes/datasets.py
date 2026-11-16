"""
SmartKhet 2.0 — Datasets API Routes
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from models.db_models import DataRecord, DatasetRegistry
from models.schemas import DataRecordResponse, DatasetRegistryResponse, PipelineStatsResponse
from services.data_service import data_service
from services.audit_service import audit_service

router = APIRouter()


@router.get("/registry", response_model=List[DatasetRegistryResponse])
def list_datasets(db: Session = Depends(get_db)):
    """Return all registered datasets."""
    return data_service.get_dataset_registry(db)


@router.get("/registry/{dataset_id}", response_model=DatasetRegistryResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    ds = db.query(DatasetRegistry).filter(DatasetRegistry.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds


@router.get("/records", response_model=List[DataRecordResponse])
def list_records(
    farm_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Return sensor/field data records with optional filtering."""
    return data_service.get_data_records(
        db,
        farm_id=farm_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )


@router.get("/pipeline/stats", response_model=PipelineStatsResponse)
def pipeline_stats(db: Session = Depends(get_db)):
    """Return high-level data pipeline statistics."""
    return data_service.get_pipeline_stats(db)


@router.post("/seed")
def seed_demo(db: Session = Depends(get_db)):
    """
    Seed the database with demonstration data.
    All seeded records are labelled is_demo=True.
    Safe to call multiple times (idempotent).
    """
    result = data_service.seed_demo_data(db)
    audit_service.log_event(
        db,
        action="data.seed",
        resource_type="DataRecord",
        details=result,
    )
    return result


@router.get("/records/{record_id}", response_model=DataRecordResponse)
def get_record(record_id: int, db: Session = Depends(get_db)):
    rec = db.query(DataRecord).filter(DataRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")
    return rec
