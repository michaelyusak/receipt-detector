import time
import sys

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from app.configs.config import init_config
from app.logger import setup_logger

from app.extensions.paddle_ocr import PaddleOcrEngine
from app.services.receipt import Receipt

from app.routers.health import router as health_router
from app.routers.receipt import router as receipt_router

from app.app_exception import AppException, InternalErrorException

from app.schemas.response import Response

# Load Config
try:
    config = init_config()
except RuntimeError as e:
    print(f'Failed to initialize config: {str(e)}')
    sys.exit(1)

# Setup Logger
logger = setup_logger(log_level=config.log_level)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---

    # Setup OCR Engine
    paddle_ocr_engine = PaddleOcrEngine(
        version=config.paddle_ocr.version,
        use_textline_orientation=config.paddle_ocr.use_textline_orientation,
        use_doc_orientation_classify=config.paddle_ocr.use_doc_orientation_classify,
        use_doc_unwarping=config.paddle_ocr.use_doc_unwarping,
        text_det_box_thresh=config.paddle_ocr.text_det_box_thresh,
        text_det_unclip_ratio=config.paddle_ocr.text_det_unclip_ratio,
        min_word_confidence=config.paddle_ocr.min_word_confidence,
        angle_tolerance=config.paddle_ocr.angle_tolerance,
        dist_tolerance=config.paddle_ocr.dist_tolerance
    )

    # Setup Receipt Service
    app.state.receipt_service = Receipt(ocr_engine=paddle_ocr_engine)

    app.state.is_app_healthy = True

    yield  # <<< FastAPI runs here (while app is serving)

    # --- Shutdown ---
    logger.info(f"Shutting down in {config.graceful_period_seconds}s...")

    app.state.is_app_healthy = False

    time.sleep(config.graceful_period_seconds)

app = FastAPI(lifespan=lifespan)

app.include_router(health_router)
app.include_router(receipt_router)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, AppException):
        if isinstance(exc, InternalErrorException):
            logger.exception(f'Internal error occurred: {exc.detail} [path: {request.url.path}][status_code: {exc.status_code}]', exc_info=exc)

        return JSONResponse(
            status_code=exc.status_code,
            content=Response(
                status_code=exc.status_code,
                message=exc.message,
                success=False
            )
        )
    
    logger.exception(f'Unexpected error', exc_info=exc)
    
    return JSONResponse(
        status_code=500,
        content=Response(
            status_code=500, 
            message='internal server error',
            success=False
        )
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=False)