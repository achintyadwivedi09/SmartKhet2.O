"""
SmartKhet 2.0 — WebSocket Manager + Endpoint
Broadcasts real-time sensor updates and fog events to connected clients.
"""
from __future__ import annotations
import asyncio
import json
import random
from datetime import datetime
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Maintains the pool of active WebSocket connections."""

    def __init__(self):
        self._connections: List[WebSocket] = []
        self._rng = random.Random(7)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        """Send a JSON message to every connected client."""
        payload = json.dumps(message, default=str)
        dead: List[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_personal(self, websocket: WebSocket, message: dict) -> None:
        await websocket.send_text(json.dumps(message, default=str))

    @property
    def connection_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()


def _build_live_reading(farm_id: str, rng: random.Random) -> dict:
    """Simulate a live sensor reading for demonstration."""
    return {
        "type": "sensor_update",
        "farm_id": farm_id,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "temperature": round(rng.uniform(24, 38), 2),
            "humidity": round(rng.uniform(45, 85), 2),
            "soil_moisture": round(rng.uniform(0.15, 0.45), 3),
            "rainfall": round(max(0.0, rng.gauss(2.0, 3.0)), 2),
            "ndvi": round(rng.uniform(0.30, 0.80), 3),
        },
        "is_demo": True,
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint at /ws.
    On connection, pushes a live-feed of simulated sensor readings every 3 s.
    Clients can send JSON {action: "ping"} and receive {action: "pong"}.
    """
    await manager.connect(websocket)
    farm_ids = ["TN001", "TN002", "TN003"]
    rng = random.Random()

    await manager.send_personal(websocket, {
        "type": "connected",
        "message": "Welcome to SmartKhet 2.0 live feed",
        "connection_count": manager.connection_count,
    })

    try:
        while True:
            # Try to receive a client message (non-blocking, 3 s timeout)
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=3.0)
                msg = json.loads(raw)
                if msg.get("action") == "ping":
                    await manager.send_personal(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            except asyncio.TimeoutError:
                pass  # Normal — just push a reading

            # Push a demo sensor reading for a rotating farm
            farm_id = rng.choice(farm_ids)
            reading = _build_live_reading(farm_id, rng)
            await manager.broadcast(reading)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
