from fastapi import APIRouter, Depends

from app.dependencies import is_app_healthy
from app.schemas.response import Response

router = APIRouter()

@router.get("/health", response_model=Response)
async def get_health(is_healthy:bool=Depends(is_app_healthy)):
    if not is_healthy:
        return Response(
            status_code=503,
            message='unavailable',
            success=False
        )

    return Response(
        status_code=200,
        message='ok',
        success=True
    )
    