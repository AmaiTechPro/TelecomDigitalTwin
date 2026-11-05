from fastapi import FastAPI, HTTPException

from telemetry_store import (
    get_all_telemetry,
    get_device_telemetry,
    get_device_count,
)


app = FastAPI(
    title="Telecom Digital Twin API",
    description="Backend API for the Virtual Telecommunications and Cyber-Physical Systems Engineering Laboratory",
    version="0.2.0"
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
        "service": "telecom-digital-twin-backend"
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