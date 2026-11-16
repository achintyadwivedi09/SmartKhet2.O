"""
SmartKhet 2.0 — Pydantic v2 Schemas
Request / response models for all API endpoints.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Farm Schemas
# ---------------------------------------------------------------------------
class FarmBase(BaseModel):
    farm_id: str
    name: str
    district: str
    crop: str
    latitude: float
    longitude: float
    area_hectares: float
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    soil_moisture_threshold: float = 0.25
    irrigation_trigger_moisture: float = 0.18
    temperature_max_safe: float = 40.0
    temperature_min_safe: float = 15.0
    ndvi_healthy_min: float = 0.45
    fog_node_id: Optional[str] = None


class FarmCreate(FarmBase):
    pass


class FarmResponse(FarmBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# DatasetRegistry Schemas
# ---------------------------------------------------------------------------
class DatasetRegistryBase(BaseModel):
    dataset_name: str
    source: str
    description: Optional[str] = None
    record_count: int = 0
    columns: Optional[List[str]] = None
    file_path: Optional[str] = None
    format: str = "CSV"
    is_active: bool = True


class DatasetRegistryCreate(DatasetRegistryBase):
    pass


class DatasetRegistryResponse(DatasetRegistryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    registered_at: datetime
    last_updated: Optional[datetime] = None


# ---------------------------------------------------------------------------
# DataRecord Schemas
# ---------------------------------------------------------------------------
class DataRecordBase(BaseModel):
    farm_id: str
    dataset_id: Optional[int] = None
    recorded_at: datetime
    source: str = "sensor"
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soil_moisture: Optional[float] = None
    rainfall: Optional[float] = None
    ndvi: Optional[float] = None
    wind_speed: Optional[float] = None
    solar_radiation: Optional[float] = None
    ph: Optional[float] = None
    nitrogen: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None
    crop_stage: Optional[str] = None
    is_demo: bool = False
    notes: Optional[str] = None


class DataRecordCreate(DataRecordBase):
    pass


class DataRecordResponse(DataRecordBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------------------------------------------------------------------------
# MLModel Schemas
# ---------------------------------------------------------------------------
class MLModelBase(BaseModel):
    model_name: str
    model_type: str
    version: str = "1.0.0"
    target_variable: Optional[str] = None
    features: Optional[List[str]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    accuracy: Optional[float] = None
    rmse: Optional[float] = None
    r2_score: Optional[float] = None
    mae: Optional[float] = None
    training_samples: Optional[int] = None
    file_path: Optional[str] = None
    is_active: bool = True


class MLModelCreate(MLModelBase):
    pass


class MLModelResponse(MLModelBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trained_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Prediction Schemas
# ---------------------------------------------------------------------------
class PredictionRequest(BaseModel):
    farm_id: Optional[str] = "TN001"
    temperature: float = Field(28.0, ge=-20, le=60)
    humidity: float = Field(65.0, ge=0, le=100)
    soil_moisture: float = Field(0.25, ge=0, le=1)
    rainfall: float = Field(0.0, ge=0)
    ndvi: Optional[float] = Field(0.5, ge=-1, le=1)
    wind_speed: Optional[float] = Field(2.0, ge=0)
    solar_radiation: Optional[float] = Field(400.0, ge=0)
    ph: Optional[float] = Field(6.5, ge=0, le=14)
    nitrogen: Optional[float] = Field(100.0, ge=0)
    phosphorus: Optional[float] = Field(35.0, ge=0)
    potassium: Optional[float] = Field(80.0, ge=0)


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    farm_id: str
    model_id: Optional[int] = None
    predicted_at: datetime
    input_features: Optional[Dict[str, Any]] = None
    prediction_value: Optional[float] = None
    prediction_label: Optional[str] = None
    confidence: Optional[float] = None
    recommendation: Optional[str] = None
    source: str = "api"


# ---------------------------------------------------------------------------
# FogNode Schemas
# ---------------------------------------------------------------------------
class FogNodeBase(BaseModel):
    node_id: str
    farm_id: str
    location: Optional[str] = None
    is_online: bool = True
    model_loaded: bool = False
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    storage_used_mb: float = 0.0
    buffered_event_count: int = 0


class FogNodeResponse(FogNodeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    last_heartbeat: datetime
    created_at: datetime


class FogInferenceRequest(BaseModel):
    farm_id: str
    temperature: float
    humidity: float
    soil_moisture: float
    rainfall: float
    ndvi: float
    wind_speed: float
    solar_radiation: float
    ph: float
    nitrogen: float
    phosphorus: float
    potassium: float


class FogInferenceResponse(BaseModel):
    farm_id: str
    node_id: str
    prediction_value: float
    prediction_label: str
    confidence: float
    recommendation: str
    source: str = "fog"
    timestamp: datetime


# ---------------------------------------------------------------------------
# FogEvent Schemas
# ---------------------------------------------------------------------------
class FogEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    node_id: str
    event_type: str
    payload: Optional[Dict[str, Any]] = None
    is_synced: bool
    created_at: datetime
    synced_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# AuditLog Schemas
# ---------------------------------------------------------------------------
class AuditLogBase(BaseModel):
    actor: str = "system"
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    status: str = "success"
    ip_address: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogResponse(AuditLogBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    timestamp: datetime


class AuditLogFilter(BaseModel):
    actor: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 50


# ---------------------------------------------------------------------------
# ExperimentRun Schemas
# ---------------------------------------------------------------------------
class ExperimentRunBase(BaseModel):
    experiment_name: str
    description: Optional[str] = None
    model_type: Optional[str] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    dataset_size: Optional[int] = None
    features_used: Optional[List[str]] = None
    notes: Optional[str] = None


class ExperimentRunCreate(ExperimentRunBase):
    pass


class ExperimentRunResponse(ExperimentRunBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    accuracy: Optional[float] = None
    rmse: Optional[float] = None
    r2_score: Optional[float] = None
    mae: Optional[float] = None
    training_time_seconds: Optional[float] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Generic / Utility Schemas
# ---------------------------------------------------------------------------
class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Any]


class StatusResponse(BaseModel):
    status: str
    message: str


class CloudStatsResponse(BaseModel):
    connected: bool
    total_records_synced: int
    total_predictions_synced: int
    last_sync_at: Optional[datetime] = None
    endpoint: str


class PipelineStatsResponse(BaseModel):
    total_records: int
    demo_records: int
    real_records: int
    farms_active: int
    datasets_registered: int
    latest_record_at: Optional[datetime] = None
