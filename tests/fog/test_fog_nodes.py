"""
SmartKhet 2.0 — Fog Computing Edge Autonomy Tests
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from services.fog_service import fog_service
from services.ml_service import ml_service
from app.database import init_db, SessionLocal


def test_fog_nodes_initialized():
    nodes = fog_service.get_all_nodes()
    assert len(nodes) == 3, f"Expected 3 fog nodes, found {len(nodes)}"
    node_ids = {n["node_id"] for n in nodes}
    assert "FOG-TN001" in node_ids
    assert "FOG-TN002" in node_ids
    assert "FOG-TN003" in node_ids


def test_fog_local_inference_and_offline_buffering():
    init_db()
    db = SessionLocal()
    try:
        # 1. Sever cloud link for TN001
        fog_service.disconnect_cloud("TN001")
        node = fog_service.get_node("TN001")
        assert node.cloud_connected is False

        # 2. Run local edge inference
        features = {
            "soil_moisture": 0.22,
            "rainfall": 0.0,
            "temperature": 32.0,
            "humidity": 60.0
        }
        res = fog_service.run_inference("TN001", features, db)
        assert "predicted_moisture" in res or "prediction_value" in res
        assert res["source"] == "fog"

        # 3. Check event was queued in local buffer
        assert len(node.event_queue) > 0, "Event must be buffered locally while cloud is disconnected"

        # 4. Reconnect and sync
        fog_service.reconnect_cloud("TN001")
        assert node.cloud_connected is True
        sync_res = fog_service.sync_to_cloud("TN001", db)
        assert sync_res["status"] == "success"
        assert len(node.event_queue) == 0, "Buffer queue should be empty after sync"
    finally:
        db.close()

