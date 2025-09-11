import os
from pydantic import BaseModel
import json
from typing import Any

class AppConfig(BaseModel):
    port: int

def init_config() -> AppConfig:
    config_path = os.getenv('RECEIPT_DETECTOR_CONFIG_PATH')
    if not config_path:
        raise RuntimeError("[configs][init_config] Environment variable RECEIPT_DETECTOR_CONFIG_PATH is not set")
    
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"[configs][init_config] Config file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config_data: dict[str, Any] = json.load(f)

    return AppConfig(**config_data)