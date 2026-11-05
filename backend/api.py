
import asyncio
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)

from telemetry_store import (
    get_all_telemetry,
    get_device_telemetry,
    get_device_count,
)

from mqtt_service import mqtt_service
from websocket_manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Register FastAPI's event loop with the MQTT service.
    mqtt_service.set_event_loop(asyncio.get_running_loop())

    print("[API] Event loop registered with MQTT service")

    # Start MQTT service.
    mqtt_service.start()

    yield

    # Stop MQTT service during application shutdown.
    mqtt_service.stop()

    print("[API] Application shutdown complete")


app = FastAPI(
    title="Telecom Digital Twin API",
    description="Backend API for the Virtual Telecommunications and Cyber-Physical Systems Engineering Laboratory",
    version="0.3.0",
    lifespan=lifespan
)


@app.get("/")
async def root():

    return {
        "application": "Telecom Digital Twin API",
        "status": "running",
        "phase": "Phase 4 - Backend Development"
    }


@app.get("/health")
async def health_check():

    return {
        "status": "healthy",
        "service": "telecom-digital-twin-backend",
        "mqtt_connected": mqtt_service.is_connected()
    }


@app.get("/api/telemetry")
async def all_telemetry():

    return {
        "site_id": "TELECOM-SITE-001",
        "device_count": get_device_count(),
        "devices": get_all_telemetry()
    }


@app.get("/api/telemetry/{device_id}")
async def device_telemetry(device_id: str):

    event = get_device_telemetry(device_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail=f"No telemetry found for device: {device_id}"
        )

    return event


@app.websocket("/ws/telemetry")
async def telemetry_websocket(websocket: WebSocket):

    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception as error:
        print(f"[WEBSOCKET] Connection error: {error}")
        manager.disconnect(websocket)
