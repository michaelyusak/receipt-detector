from app.extensions.paddle_ocr import PaddleOcrEngine

class Receipt:
    __ocr_engine: PaddleOcrEngine = None

    def __init__(self, ocr_engine):
        self.__ocr_engine = ocr_engine

    def detect(self, contents: bytes):
        if not self.__ocr_engine:
            return RuntimeError('OCR engine not provided')
        
        return self.__ocr_engine.detect(contents)
