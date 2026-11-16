"""
SmartKhet 2.0 — Configuration
Farm definitions, sensor thresholds, and application settings.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Farm Definitions (Tamil Nadu, India)
# ---------------------------------------------------------------------------

@dataclass
class FarmConfig:
    farm_id: str
    name: str
    district: str
    crop: str
    latitude: float
    longitude: float
    area_hectares: float
    soil_type: str
    irrigation_type: str
    soil_moisture_threshold: float          # volumetric water content (m³/m³)
    irrigation_trigger_moisture: float      # trigger irrigation below this
    temperature_max_safe: float             # °C
    temperature_min_safe: float             # °C
    ndvi_healthy_min: float                 # minimum healthy NDVI
    fog_node_id: str

FARMS: Dict[str, FarmConfig] = {
    "TN001": FarmConfig(
        farm_id="TN001",
        name="Cauvery Delta Farm",
        district="Thanjavur",
        crop="Rice",
        latitude=10.787,
        longitude=79.139,
        area_hectares=4.2,
        soil_type="Clay loam",
        irrigation_type="Flood / Canal",
        soil_moisture_threshold=0.35,
        irrigation_trigger_moisture=0.28,
        temperature_max_safe=38.0,
        temperature_min_safe=18.0,
        ndvi_healthy_min=0.55,
        fog_node_id="FOG-TN001",
    ),
    "TN002": FarmConfig(
        farm_id="TN002",
        name="Kongu Upland Farm",
        district="Coimbatore",
        crop="Cotton",
        latitude=11.0168,
        longitude=76.9558,
        area_hectares=6.0,
        soil_type="Red sandy loam",
        irrigation_type="Drip",
        soil_moisture_threshold=0.25,
        irrigation_trigger_moisture=0.18,
        temperature_max_safe=40.0,
        temperature_min_safe=15.0,
        ndvi_healthy_min=0.45,
        fog_node_id="FOG-TN002",
    ),
    "TN003": FarmConfig(
        farm_id="TN003",
        name="Madurai Drylands Farm",
        district="Madurai",
        crop="Groundnut",
        latitude=9.9252,
        longitude=78.1198,
        area_hectares=3.5,
        soil_type="Red loamy",
        irrigation_type="Sprinkler",
        soil_moisture_threshold=0.20,
        irrigation_trigger_moisture=0.14,
        temperature_max_safe=42.0,
        temperature_min_safe=16.0,
        ndvi_healthy_min=0.40,
        fog_node_id="FOG-TN003",
    ),
}

# Convenience list
FARM_IDS: List[str] = list(FARMS.keys())

# ---------------------------------------------------------------------------
# Soil Moisture Thresholds (quick lookup by crop name)
# ---------------------------------------------------------------------------
SOIL_MOISTURE_THRESHOLDS: Dict[str, float] = {
    "Rice": 0.35,
    "Cotton": 0.25,
    "Groundnut": 0.20,
}

# ---------------------------------------------------------------------------
# Directories & Paths
# ---------------------------------------------------------------------------
BACKEND_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT: str = os.path.dirname(BACKEND_DIR)
DATA_DIR: str = os.path.join(PROJECT_ROOT, "data")
MODEL_DIR: str = os.path.join(DATA_DIR, "models")
DOCS_DIR: str = os.path.join(PROJECT_ROOT, "docs")

RF_MODEL_PATH: str = os.path.join(MODEL_DIR, "rf_model.joblib")
XGB_MODEL_PATH: str = os.path.join(MODEL_DIR, "xgb_model.joblib")
SCALER_PATH: str = os.path.join(MODEL_DIR, "scaler.joblib")
MODEL_METADATA_PATH: str = os.path.join(MODEL_DIR, "model_metadata.json")
FEATURE_LIST_PATH: str = os.path.join(DATA_DIR, "metadata", "feature_list.json")
AUDIT_LOG_PATH: str = os.path.join(DOCS_DIR, "SMARTKHET_PROJECT_AUDIT_LOG.csv")

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BACKEND_DIR, 'smartkhet2.db')}"
)

# ---------------------------------------------------------------------------
# Cloud / Fog Settings
# ---------------------------------------------------------------------------
FOG_SYNC_INTERVAL_SECONDS: int = int(os.getenv("FOG_SYNC_INTERVAL", "30"))
CLOUD_ENDPOINT: str = os.getenv("CLOUD_ENDPOINT", "http://localhost:8001")

# ---------------------------------------------------------------------------
# App Settings
# ---------------------------------------------------------------------------
APP_NAME: str = "SmartKhet 2.0"
APP_VERSION: str = "2.0.0"
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
CORS_ORIGINS: List[str] = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")
