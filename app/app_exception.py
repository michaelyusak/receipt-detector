class AppException(Exception):
    def __init__(self, message: str, code: int, detail=None):
        self.status_code = code
        self.message = message
        self.detail = detail

class BadRequestException(AppException):
    def __init__(self, message: str, code: int = 400):
        super().__init__(message, code)

class InternalErrorException(AppException):
    def __init__(self, detail: str, code: int = 500):
        super().__init__('internal server error', code, detail)