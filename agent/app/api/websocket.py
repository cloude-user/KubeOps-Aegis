import asyncio
import json
import random
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("aegis.ws")

router = APIRouter()


class TelemetryConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to WS client: {e}")


manager = TelemetryConnectionManager()


@router.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Stream live simulated K8s cluster telemetry every 2 seconds
            cpu_usage = round(random.uniform(35.0, 78.0), 1)
            mem_usage = round(random.uniform(50.0, 85.0), 1)
            pod_count = 42

            telemetry_event = {
                "type": "METRIC_UPDATE",
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                "data": {
                    "cluster_name": "aks-kubeops-aegis-prd",
                    "cpu_utilization": cpu_usage,
                    "memory_utilization": mem_usage,
                    "active_pods": pod_count,
                    "cluster_status": "HEALTHY" if cpu_usage < 85 else "HIGH_LOAD"
                }
            }
            await websocket.send_json(telemetry_event)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
