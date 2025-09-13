import os
from pydantic import BaseModel
import json
from typing import Any

class PaddleOcr(BaseModel):
    version: str = "PP-OCRv3"
    use_textline_orientation: bool = True
    use_doc_orientation_classify: bool = False
    use_doc_unwarping: bool = False
    text_det_box_thresh: float = 0.6
    text_det_unclip_ratio: float = 1.5
    min_word_confidence: float = 0.7
    angle_tolerance: float = 5.0
    dist_tolerance: float = 20.0

class AppConfig(BaseModel):
    port: int
    log_level: str
    graceful_period_seconds: int
    paddle_ocr: PaddleOcr

def init_config() -> AppConfig:
    config_path = os.getenv('RECEIPT_DETECTOR_CONFIG_PATH')
    if not config_path:
        raise RuntimeError("[configs][init_config] Environment variable RECEIPT_DETECTOR_CONFIG_PATH is not set")
    
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"[configs][init_config] Config file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config_data: dict[str, Any] = json.load(f)

    return AppConfig(**config_data)