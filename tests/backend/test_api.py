"""
SmartKhet 2.0 — FastAPI API Endpoint Tests
"""
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.database import init_db, SessionLocal
from app.main import health_check
from api.routes import farms, datasets, ml, fog, cloud, audit, analytics
from models.schemas import PredictionRequest, FogInferenceRequest


@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()


def test_health_check():
    res = health_check()
    assert res["status"] == "healthy"
    assert res["app"] == "SmartKhet 2.0"
    assert res["farms_configured"] == 3
    assert res["fog_nodes_active"] == 3


def test_list_farms(db_session):
    res = farms.list_farms(db=db_session)
    assert len(res) >= 3
    farm_ids = [f.farm_id for f in res]
    assert "TN001" in farm_ids
    assert "TN002" in farm_ids
    assert "TN003" in farm_ids


def test_get_single_farm(db_session):
    res = farms.get_farm("TN001", db=db_session)
    assert res.farm_id == "TN001"
    assert res.district == "Thanjavur"
    assert res.crop == "Rice"


def test_list_datasets(db_session):
    res = datasets.list_datasets(db=db_session)
    assert isinstance(res, list)


def test_get_ml_model_info(db_session):
    res = ml.get_model_info(db=db_session)
    assert res is not None
    assert "Random Forest" in res.get("model_name", "") or "rf" in str(res).lower()


def test_ml_predict(db_session):
    req = PredictionRequest(
        farm_id="TN001",
        soil_moisture=0.22,
        rainfall=0.0,
        temperature=31.0,
        humidity=65.0
    )
    res = ml.predict(req, db=db_session)
    assert "predicted_moisture" in res or "prediction_value" in res
    assert "recommendation" in res


def test_list_fog_nodes(db_session):
    res = fog.list_nodes(db=db_session)
    assert len(res) == 3
    node_ids = [n["node_id"] for n in res]
    assert "FOG-TN001" in node_ids


def test_cloud_status(db_session):
    res = cloud.cloud_status(db=db_session)
    assert "connected" in res
    assert "stored_records" in res


def test_analytics_overview(db_session):
    res = analytics.overview(db=db_session)
    assert "total_records" in res
    assert "farms_active" in res
    assert res["farms_active"] == 3
