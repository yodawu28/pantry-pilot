from fastapi import APIRouter

from app.routers.response.health_check import HealthCheckResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(response_model=HealthCheckResponse):
    """Health check endpoint"""
    return HealthCheckResponse(status="ok", service="pantry-pilot-api", version="1.0.0")
