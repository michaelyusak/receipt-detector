from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    status_code: int
    message: str
    success: bool
    data: Optional[T] = None