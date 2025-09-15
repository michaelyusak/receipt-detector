from fastapi import Request

from app.services.receipt import Receipt

def get_receipt_service(request: Request) -> Receipt:
    return request.app.state.receipt_service

def is_app_healthy(request: Request) -> bool:
    return getattr(request.app.state, "is_app_healthy", False)