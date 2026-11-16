"""
SmartKhet 2.0 — SQLAlchemy ORM Models
All database table definitions live here.
"""
from __future__ import annotations
import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


# ---------------------------------------------------------------------------
# Farm
# ---------------------------------------------------------------------------
class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    district = Column(String(80), nullable=False)
    crop = Column(String(60), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    area_hectares = Column(Float, nullable=False)
    soil_type = Column(String(80))
    irrigation_type = Column(String(80))
    soil_moisture_threshold = Column(Float, default=0.25)
    irrigation_trigger_moisture = Column(Float, default=0.18)
    temperature_max_safe = Column(Float, default=40.0)
    temperature_min_safe = Column(Float, default=15.0)
    ndvi_healthy_min = Column(Float, default=0.45)
    fog_node_id = Column(String(40))
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    data_records = relationship("DataRecord", back_populates="farm", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="farm", cascade="all, delete-orphan")
    fog_node = relationship("FogNode", back_populates="farm", uselist=False)


# ---------------------------------------------------------------------------
# DatasetRegistry
# ---------------------------------------------------------------------------
class DatasetRegistry(Base):
    __tablename__ = "dataset_registry"

    id = Column(Integer, primary_key=True, index=True)
    dataset_name = Column(String(120), nullable=False)
    source = Column(String(120), nullable=False)
    description = Column(Text)
    record_count = Column(Integer, default=0)
    columns = Column(JSON)                      # list of column names
    file_path = Column(String(255))
    format = Column(String(20), default="CSV")
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=_now)
    last_updated = Column(DateTime, default=_now, onupdate=_now)

    data_records = relationship("DataRecord", back_populates="dataset")


# ---------------------------------------------------------------------------
# DataRecord  (individual sensor / field observation)
# ---------------------------------------------------------------------------
class DataRecord(Base):
    __tablename__ = "data_records"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(String(20), ForeignKey("farms.farm_id"), nullable=False, index=True)
    dataset_id = Column(Integer, ForeignKey("dataset_registry.id"), nullable=True)
    recorded_at = Column(DateTime, nullable=False, index=True)
    source = Column(String(60), default="sensor")          # sensor | satellite | manual | demo
    temperature = Column(Float)                             # °C
    humidity = Column(Float)                                # %
    soil_moisture = Column(Float)                           # m³/m³
    rainfall = Column(Float)                                # mm
    ndvi = Column(Float)                                    # -1 to +1
    wind_speed = Column(Float)                              # m/s
    solar_radiation = Column(Float)                         # W/m²
    ph = Column(Float)                                      # soil pH
    nitrogen = Column(Float)                                # kg/ha
    phosphorus = Column(Float)                              # kg/ha
    potassium = Column(Float)                               # kg/ha
    crop_stage = Column(String(40))
    is_demo = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=_now)

    farm = relationship("Farm", back_populates="data_records")
    dataset = relationship("DatasetRegistry", back_populates="data_records")


# ---------------------------------------------------------------------------
# MLModel
# ---------------------------------------------------------------------------
class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(80), nullable=False)
    model_type = Column(String(60), nullable=False)         # RandomForest | XGBoost | …
    version = Column(String(20), default="1.0.0")
    target_variable = Column(String(60))
    features = Column(JSON)                                  # list of feature names
    hyperparameters = Column(JSON)
    accuracy = Column(Float)
    rmse = Column(Float)
    r2_score = Column(Float)
    mae = Column(Float)
    training_samples = Column(Integer)
    file_path = Column(String(255))
    is_active = Column(Boolean, default=True)
    trained_at = Column(DateTime, default=_now)
    created_at = Column(DateTime, default=_now)

    predictions = relationship("Prediction", back_populates="model")


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(String(20), ForeignKey("farms.farm_id"), nullable=False, index=True)
    model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=True)
    predicted_at = Column(DateTime, default=_now, index=True)
    input_features = Column(JSON)
    prediction_value = Column(Float)
    prediction_label = Column(String(80))
    confidence = Column(Float)
    recommendation = Column(Text)
    source = Column(String(40), default="fog")              # fog | cloud | api
    is_acted_upon = Column(Boolean, default=False)

    farm = relationship("Farm", back_populates="predictions")
    model = relationship("MLModel", back_populates="predictions")


# ---------------------------------------------------------------------------
# FogNode
# ---------------------------------------------------------------------------
class FogNode(Base):
    __tablename__ = "fog_nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(40), unique=True, nullable=False, index=True)
    farm_id = Column(String(20), ForeignKey("farms.farm_id"), unique=True, nullable=False)
    location = Column(String(120))
    is_online = Column(Boolean, default=True)
    model_loaded = Column(Boolean, default=False)
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    storage_used_mb = Column(Float, default=0.0)
    last_heartbeat = Column(DateTime, default=_now)
    buffered_event_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now)

    farm = relationship("Farm", back_populates="fog_node")
    events = relationship("FogEvent", back_populates="node", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# FogEvent
# ---------------------------------------------------------------------------
class FogEvent(Base):
    __tablename__ = "fog_events"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(40), ForeignKey("fog_nodes.node_id"), nullable=False, index=True)
    event_type = Column(String(60), nullable=False)         # inference | alert | sync | heartbeat
    payload = Column(JSON)
    is_synced = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_now, index=True)
    synced_at = Column(DateTime, nullable=True)

    node = relationship("FogNode", back_populates="events")


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=_now, index=True)
    actor = Column(String(80), default="system")
    action = Column(String(120), nullable=False)
    resource_type = Column(String(60))
    resource_id = Column(String(80))
    details = Column(JSON)
    status = Column(String(20), default="success")          # success | warning | error
    ip_address = Column(String(45))


# ---------------------------------------------------------------------------
# ExperimentRun
# ---------------------------------------------------------------------------
class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id = Column(Integer, primary_key=True, index=True)
    experiment_name = Column(String(120), nullable=False)
    description = Column(Text)
    model_type = Column(String(60))
    hyperparameters = Column(JSON)
    dataset_size = Column(Integer)
    features_used = Column(JSON)
    accuracy = Column(Float)
    rmse = Column(Float)
    r2_score = Column(Float)
    mae = Column(Float)
    training_time_seconds = Column(Float)
    notes = Column(Text)
    status = Column(String(20), default="running")          # running | completed | failed
    started_at = Column(DateTime, default=_now)
    completed_at = Column(DateTime, nullable=True)
