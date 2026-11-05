from fastapi import FastAPI

app = FastAPI(
    title="Telecom Digital Twin API",
    description="Backend API for the Virtual Telecommunications Engineering Laboratory",
    version="0.1.0"
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