from fastapi import APIRouter, UploadFile, File, Depends

from app.dependencies import get_receipt_service
from app.services.receipt import Receipt
from app.schemas.response import Response

router = APIRouter()

@router.post("/receipt/detect", response_model=Response)
async def detect(file: UploadFile = File(), receipt_service: Receipt=Depends(get_receipt_service)):
    contents = await file.read()
    return receipt_service.detect(contents)