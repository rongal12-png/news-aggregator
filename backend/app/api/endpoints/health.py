from fastapi import APIRouter
from datetime import datetime, timezone

from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc)
    )
