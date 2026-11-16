"""
SmartKhet 2.0 — Data Service
Manages dataset registry, sensor records, and demo data seeding.
All seeded records are explicitly labelled is_demo=True.
"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import FARMS
from models.db_models import DataRecord, DatasetRegistry, Farm
from models.schemas import DataRecordResponse, DatasetRegistryResponse, PipelineStatsResponse

# Deterministic seed for reproducibility of demo data
_RNG = random.Random(42)

# Crop-stage progression (approximate days after sowing)
CROP_STAGES = {
    "Rice": ["Nursery", "Transplanting", "Tillering", "Panicle Initiation", "Heading", "Ripening"],
    "Cotton": ["Germination", "Seedling", "Squaring", "Flowering", "Boll Development", "Maturity"],
    "Groundnut": ["Germination", "Vegetative", "Flowering", "Pegging", "Pod Development", "Maturity"],
}


def _stage_for_day(crop: str, day: int) -> str:
    stages = CROP_STAGES.get(crop, ["Unknown"])
    idx = min(int(day / 20), len(stages) - 1)
    return stages[idx]


def _make_demo_records(farm_id: str, dataset_id: int, days: int = 90) -> List[Dict[str, Any]]:
    """Generate realistic-looking DEMONSTRATION sensor records for a farm.

    Values follow agronomic ranges for each crop but are synthetically generated
    and are clearly tagged is_demo=True. They should NOT be treated as real measurements.
    """
    cfg = FARMS[farm_id]
    base_date = datetime.utcnow() - timedelta(days=days)
    records = []

    for day in range(days):
        ts = base_date + timedelta(days=day, hours=_RNG.randint(6, 18))
        stage = _stage_for_day(cfg.crop, day)

        # Base environmental values with seasonal drift
        season_factor = abs((day % 90) - 45) / 45.0  # 0–1 oscillation
        temperature = round(_RNG.uniform(24.0, 36.0) + season_factor * 4.0, 2)
        humidity = round(_RNG.uniform(45.0, 85.0) - season_factor * 10.0, 2)
        soil_moisture = round(
            cfg.soil_moisture_threshold + _RNG.uniform(-0.08, 0.08), 3
        )
        rainfall = round(max(0.0, _RNG.gauss(3.0, 4.0)), 2)
        ndvi = round(
            cfg.ndvi_healthy_min + _RNG.uniform(-0.1, 0.15) + (day / days) * 0.1, 3
        )
        wind_speed = round(_RNG.uniform(0.5, 5.5), 2)
        solar_radiation = round(_RNG.uniform(150.0, 650.0), 2)
        ph = round(_RNG.uniform(5.8, 7.5), 2)
        nitrogen = round(_RNG.uniform(80.0, 160.0), 2)
        phosphorus = round(_RNG.uniform(20.0, 60.0), 2)
        potassium = round(_RNG.uniform(60.0, 140.0), 2)

        records.append(
            {
                "farm_id": farm_id,
                "dataset_id": dataset_id,
                "recorded_at": ts,
                "source": "demo",
                "temperature": temperature,
                "humidity": humidity,
                "soil_moisture": max(0.0, min(1.0, soil_moisture)),
                "rainfall": rainfall,
                "ndvi": max(-1.0, min(1.0, ndvi)),
                "wind_speed": wind_speed,
                "solar_radiation": solar_radiation,
                "ph": ph,
                "nitrogen": nitrogen,
                "phosphorus": phosphorus,
                "potassium": potassium,
                "crop_stage": stage,
                "is_demo": True,
                "notes": "DEMONSTRATION DATA — synthetically generated for SmartKhet 2.0 testing",
            }
        )
    return records


class DataService:
    """Provides access to datasets, records, and pipeline statistics."""

    # ------------------------------------------------------------------
    # Dataset Registry
    # ------------------------------------------------------------------
    def get_dataset_registry(self, db: Session) -> List[DatasetRegistryResponse]:
        rows = db.query(DatasetRegistry).all()
        return [DatasetRegistryResponse.model_validate(r) for r in rows]

    def register_dataset(
        self, db: Session, **kwargs: Any
    ) -> DatasetRegistry:
        ds = DatasetRegistry(**kwargs)
        db.add(ds)
        db.commit()
        db.refresh(ds)
        return ds

    # ------------------------------------------------------------------
    # Data Records
    # ------------------------------------------------------------------
    def get_data_records(
        self,
        db: Session,
        farm_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 500,
        offset: int = 0,
    ) -> List[DataRecordResponse]:
        query = db.query(DataRecord)
        if farm_id:
            query = query.filter(DataRecord.farm_id == farm_id)
        if start_date:
            query = query.filter(DataRecord.recorded_at >= start_date)
        if end_date:
            query = query.filter(DataRecord.recorded_at <= end_date)
        rows = (
            query.order_by(DataRecord.recorded_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [DataRecordResponse.model_validate(r) for r in rows]

    def get_latest_record(self, db: Session, farm_id: str) -> Optional[DataRecord]:
        return (
            db.query(DataRecord)
            .filter(DataRecord.farm_id == farm_id)
            .order_by(DataRecord.recorded_at.desc())
            .first()
        )

    # ------------------------------------------------------------------
    # Pipeline Statistics
    # ------------------------------------------------------------------
    def get_pipeline_stats(self, db: Session) -> PipelineStatsResponse:
        total = db.query(DataRecord).count()
        demo = db.query(DataRecord).filter(DataRecord.is_demo == True).count()
        real = total - demo
        farms_active = db.query(Farm).count()
        datasets = db.query(DatasetRegistry).filter(DatasetRegistry.is_active == True).count()
        latest = (
            db.query(DataRecord)
            .order_by(DataRecord.recorded_at.desc())
            .first()
        )
        return PipelineStatsResponse(
            total_records=total,
            demo_records=demo,
            real_records=real,
            farms_active=farms_active,
            datasets_registered=datasets,
            latest_record_at=latest.recorded_at if latest else None,
        )

    # ------------------------------------------------------------------
    # Demo Data Seeding
    # ------------------------------------------------------------------
    def seed_demo_data(self, db: Session) -> Dict[str, Any]:
        """
        Seed the database with farms and demonstration sensor records.
        Idempotent: skips farms/datasets that already exist.
        Returns a summary of what was inserted.
        """
        inserted_farms = 0
        inserted_records = 0

        for farm_id, cfg in FARMS.items():
            # Upsert Farm
            existing_farm = db.query(Farm).filter(Farm.farm_id == farm_id).first()
            if not existing_farm:
                farm = Farm(
                    farm_id=cfg.farm_id,
                    name=cfg.name,
                    district=cfg.district,
                    crop=cfg.crop,
                    latitude=cfg.latitude,
                    longitude=cfg.longitude,
                    area_hectares=cfg.area_hectares,
                    soil_type=cfg.soil_type,
                    irrigation_type=cfg.irrigation_type,
                    soil_moisture_threshold=cfg.soil_moisture_threshold,
                    irrigation_trigger_moisture=cfg.irrigation_trigger_moisture,
                    temperature_max_safe=cfg.temperature_max_safe,
                    temperature_min_safe=cfg.temperature_min_safe,
                    ndvi_healthy_min=cfg.ndvi_healthy_min,
                    fog_node_id=cfg.fog_node_id,
                )
                db.add(farm)
                db.commit()
                db.refresh(farm)
                inserted_farms += 1

            # Upsert DatasetRegistry entry
            ds_name = f"Demo Sensor Dataset — {cfg.name} ({farm_id})"
            existing_ds = (
                db.query(DatasetRegistry)
                .filter(DatasetRegistry.dataset_name == ds_name)
                .first()
            )
            if not existing_ds:
                ds = DatasetRegistry(
                    dataset_name=ds_name,
                    source="Synthetic Demo Generator",
                    description=(
                        f"Demonstration sensor data for {cfg.crop} farm in {cfg.district}. "
                        "All records are synthetically generated and labelled is_demo=True."
                    ),
                    columns=[
                        "farm_id", "recorded_at", "source", "temperature", "humidity",
                        "soil_moisture", "rainfall", "ndvi", "wind_speed", "solar_radiation",
                        "ph", "nitrogen", "phosphorus", "potassium", "crop_stage",
                    ],
                    format="DB",
                    is_active=True,
                )
                db.add(ds)
                db.commit()
                db.refresh(ds)
                existing_ds = ds

            # Only seed records if none exist for this farm
            existing_count = (
                db.query(DataRecord).filter(DataRecord.farm_id == farm_id).count()
            )
            if existing_count == 0:
                records = _make_demo_records(farm_id, existing_ds.id, days=90)
                db.bulk_insert_mappings(DataRecord, records)
                db.commit()
                inserted_records += len(records)

                # Update dataset record count
                existing_ds.record_count = (
                    db.query(DataRecord).filter(DataRecord.farm_id == farm_id).count()
                )
                db.commit()

        return {
            "inserted_farms": inserted_farms,
            "inserted_demo_records": inserted_records,
            "message": (
                "Demo seeding complete. All inserted records are labelled is_demo=True "
                "and must NOT be treated as real sensor measurements."
            ),
        }


# Module-level singleton
data_service = DataService()
