"""
SmartKhet 2.0 — Cloud Service
Tracks the application's simulated cloud connectivity and sync statistics.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from models.db_models import DataRecord, Prediction


class CloudService:
    """Manages simulated cloud connectivity and sync statistics."""

    def __init__(self):
        self.connected: bool = True
        self._last_sync_at: Optional[datetime] = None
        self._endpoint: str = "http://localhost:8001"

    def connect(self) -> Dict[str, Any]:
        self.connected = True
        return {"connected": True, "message": "Cloud connection established."}

    def disconnect(self) -> Dict[str, Any]:
        self.connected = False
        return {"connected": False, "message": "Cloud connection terminated."}

    def set_endpoint(self, endpoint: str) -> None:
        self._endpoint = endpoint

    def get_stats(self, db: Session) -> Dict[str, Any]:
        """Return cloud sync statistics derived from the database."""
        total_records = db.query(DataRecord).count()
        total_predictions = db.query(Prediction).count()

        return {
            "connected": self.connected,
            "stored_records": total_records,
            "total_records_synced": total_records,
            "total_predictions_synced": total_predictions,
            "last_sync_at": self._last_sync_at.isoformat() if self._last_sync_at else None,
            "endpoint": self._endpoint,
        }

    def mark_sync(self) -> None:
        """Record that a sync just completed."""
        self._last_sync_at = datetime.utcnow()


# Module-level singleton
cloud_service = CloudService()
