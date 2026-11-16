"""
SmartKhet 2.0 — Fog Computing Service
Simulates three fog nodes (one per farm) with local ML inference,
event buffering, and cloud synchronisation.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import FARMS
from models.db_models import FogEvent, FogNode as FogNodeDB, Prediction
from services.ml_service import ml_service, FEATURE_COLS


@dataclass
class FogNodeState:
    """In-memory state of a single fog node."""
    node_id: str
    farm_id: str
    is_online: bool = True
    model_loaded: bool = False
    cloud_connected: bool = True
    event_queue: List[Dict[str, Any]] = field(default_factory=list)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    storage_used_mb: float = 0.0
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "farm_id": self.farm_id,
            "is_online": self.is_online,
            "model_loaded": self.model_loaded,
            "cloud_connected": self.cloud_connected,
            "buffered_event_count": len(self.event_queue),
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "storage_used_mb": self.storage_used_mb,
            "last_heartbeat": self.last_heartbeat.isoformat(),
        }


class FogService:
    """
    Manages in-process fog node simulation for SmartKhet 2.0.
    Each FogNodeState mirrors a farm's edge device that runs local
    ML inference and buffers events when the cloud link is down.
    """

    def __init__(self):
        self._rng = random.Random(99)
        self._nodes: Dict[str, FogNodeState] = {}
        for farm_id, cfg in FARMS.items():
            self._nodes[farm_id] = FogNodeState(
                node_id=cfg.fog_node_id,
                farm_id=farm_id,
            )

    # ------------------------------------------------------------------
    # Node Accessors
    # ------------------------------------------------------------------
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        self._refresh_metrics()
        return [n.to_dict() for n in self._nodes.values()]

    def get_node(self, farm_id: str) -> Optional[FogNodeState]:
        return self._nodes.get(farm_id)

    def _refresh_metrics(self):
        """Simulate fluctuating resource usage on each node."""
        for node in self._nodes.values():
            if node.is_online:
                node.cpu_usage = round(self._rng.uniform(10.0, 65.0), 2)
                node.memory_usage = round(self._rng.uniform(20.0, 70.0), 2)
                node.storage_used_mb = round(
                    120.0 + len(node.event_queue) * 0.5, 2
                )
                node.last_heartbeat = datetime.utcnow()

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def run_inference(
        self,
        farm_id: str,
        features: Dict[str, float],
        db: Session,
    ) -> Dict[str, Any]:
        """
        Run local ML inference on a fog node. If the model is loaded,
        return a prediction; otherwise return a rule-based fallback.
        Persist the result as a Prediction row and a FogEvent.
        """
        node = self._nodes.get(farm_id)
        if node is None:
            raise ValueError(f"No fog node for farm_id={farm_id}")
        if not node.is_online:
            raise RuntimeError(f"Fog node {node.node_id} is offline")

        # Ensure model loaded
        if not node.model_loaded:
            loaded = ml_service.load_model()
            node.model_loaded = loaded

        if node.model_loaded:
            result = ml_service.predict(features, farm_id)
        else:
            # Rule-based fallback when model is unavailable
            sm = features.get("soil_moisture", 0.25)
            ndvi = features.get("ndvi", 0.5)
            proxy = sm * 4.0 + ndvi * 3.0
            result = {
                "prediction_value": round(proxy, 4),
                "prediction_label": "Medium Yield" if proxy >= 3 else "Low Yield",
                "confidence": 0.55,
                "recommendation": "Rule-based fallback: check soil moisture and NDVI.",
            }

        # Persist prediction
        ml_model_info = ml_service.get_model_info(db)
        pred = Prediction(
            farm_id=farm_id,
            model_id=ml_model_info["id"] if ml_model_info else None,
            predicted_at=datetime.utcnow(),
            input_features=features,
            prediction_value=result["prediction_value"],
            prediction_label=result["prediction_label"],
            confidence=result["confidence"],
            recommendation=result["recommendation"],
            source="fog",
        )
        db.add(pred)
        db.commit()
        db.refresh(pred)

        event_payload = {
            "prediction_id": pred.id,
            **result,
        }
        self.buffer_event(node, "inference", event_payload, db)

        return {
            "farm_id": farm_id,
            "node_id": node.node_id,
            "timestamp": datetime.utcnow().isoformat(),
            **result,
            "source": "fog",
        }

    # ------------------------------------------------------------------
    # Event Buffering
    # ------------------------------------------------------------------
    def buffer_event(
        self,
        node: FogNodeState,
        event_type: str,
        payload: Dict[str, Any],
        db: Optional[Session] = None,
    ) -> None:
        """Buffer an event on the node and persist it in the DB."""
        event = {
            "node_id": node.node_id,
            "event_type": event_type,
            "payload": payload,
            "created_at": datetime.utcnow().isoformat(),
        }
        node.event_queue.append(event)

        if db is not None:
            db_event = FogEvent(
                node_id=node.node_id,
                event_type=event_type,
                payload=payload,
                is_synced=False,
            )
            db.add(db_event)
            db.commit()

    # ------------------------------------------------------------------
    # Cloud Sync / Connectivity
    # ------------------------------------------------------------------
    def sync_to_cloud(self, farm_id: str, db: Session) -> Dict[str, Any]:
        """Mark all buffered events for a node as synced."""
        node = self._nodes.get(farm_id)
        if node is None:
            raise ValueError(f"No fog node for farm_id={farm_id}")

        synced_count = len(node.event_queue)
        node.event_queue.clear()

        # Update DB rows
        now = datetime.utcnow()
        updated = (
            db.query(FogEvent)
            .filter(
                FogEvent.node_id == node.node_id,
                FogEvent.is_synced == False,
            )
            .all()
        )
        for ev in updated:
            ev.is_synced = True
            ev.synced_at = now
        db.commit()

        # Update FogNode DB row
        db_node = db.query(FogNodeDB).filter(FogNodeDB.node_id == node.node_id).first()
        if db_node:
            db_node.buffered_event_count = 0
            db.commit()

        return {
            "node_id": node.node_id,
            "farm_id": farm_id,
            "synced_events": synced_count,
            "status": "success",
            "synced_at": now.isoformat(),
        }

    def disconnect_cloud(self, farm_id: str) -> Dict[str, Any]:
        """Simulate cloud link disconnection for a fog node."""
        node = self._nodes.get(farm_id)
        if node is None:
            raise ValueError(f"No fog node for farm_id={farm_id}")
        node.cloud_connected = False
        return {"node_id": node.node_id, "cloud_connected": False}

    def reconnect_cloud(self, farm_id: str) -> Dict[str, Any]:
        """Simulate cloud link reconnection for a fog node."""
        node = self._nodes.get(farm_id)
        if node is None:
            raise ValueError(f"No fog node for farm_id={farm_id}")
        node.cloud_connected = True
        return {"node_id": node.node_id, "cloud_connected": True}

    def set_offline(self, farm_id: str) -> Dict[str, Any]:
        node = self._nodes.get(farm_id)
        if node:
            node.is_online = False
        return {"node_id": node.node_id if node else farm_id, "is_online": False}

    def set_online(self, farm_id: str) -> Dict[str, Any]:
        node = self._nodes.get(farm_id)
        if node:
            node.is_online = True
        return {"node_id": node.node_id if node else farm_id, "is_online": True}

    # ------------------------------------------------------------------
    # DB Persistence Init
    # ------------------------------------------------------------------
    def init_db_nodes(self, db: Session) -> None:
        """Create FogNode DB rows if they don't already exist."""
        for farm_id, state in self._nodes.items():
            existing = (
                db.query(FogNodeDB).filter(FogNodeDB.node_id == state.node_id).first()
            )
            if not existing:
                cfg = FARMS[farm_id]
                db_node = FogNodeDB(
                    node_id=state.node_id,
                    farm_id=farm_id,
                    location=f"{cfg.district}, Tamil Nadu",
                    is_online=True,
                    model_loaded=False,
                    cpu_usage=0.0,
                    memory_usage=0.0,
                    storage_used_mb=0.0,
                    buffered_event_count=0,
                )
                db.add(db_node)
        db.commit()

    def get_buffered_events(self, farm_id: str) -> List[Dict[str, Any]]:
        node = self._nodes.get(farm_id)
        return node.event_queue.copy() if node else []


# Module-level singleton
fog_service = FogService()
