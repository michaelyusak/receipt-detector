import sys

from fastapi import FastAPI
import uvicorn

from app.configs.config import init_config
from app.routers.health import router as health_router

try:
    config = init_config()
except RuntimeError as e:
    print(f"Config initialisation failed: {e}")
    sys.exit(1)

app = FastAPI()

app.include_router(health_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=False)