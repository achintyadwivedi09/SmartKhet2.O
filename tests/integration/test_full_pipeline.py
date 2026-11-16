"""
SmartKhet 2.0 — End-to-End Pipeline & Audit Integration Test
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.database import init_db, SessionLocal
from services.data_service import data_service
from services.fog_service import fog_service
from services.ml_service import ml_service
from services.audit_service import audit_service
from models.db_models import AuditLog


def test_full_operational_cycle():
    init_db()
    db = SessionLocal()
    try:
        # 1. Seed demo data
        data_res = data_service.seed_demo_data(db)
        assert data_res["inserted_demo_records"] >= 0

        # 2. Verify model loaded
        assert ml_service.is_loaded

        # 3. Execute Fog decision
        features = {"soil_moisture": 0.20, "rainfall": 0.0, "temperature": 33.0, "humidity": 55.0}
        pred_res = fog_service.run_inference("TN001", features, db)
        assert pred_res is not None

        # 4. Check audit log written
        logs = db.query(AuditLog).all()
        assert len(logs) > 0

        # 5. Export CSV audit log
        audit_service.export_csv(db)
        csv_file = PROJECT_ROOT / "docs" / "SMARTKHET_PROJECT_AUDIT_LOG.csv"
        assert csv_file.exists(), "CSV audit log must be exported successfully"
    finally:
        db.close()

