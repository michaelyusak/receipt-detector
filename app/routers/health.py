from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health():
    return HealthResponse(code=200, message="ok")