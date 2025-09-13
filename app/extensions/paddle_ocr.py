from paddleocr import PaddleOCR

import cv2
import numpy as np

from app.app_exception import BadRequestException, InternalErrorException
from app.helpers.price import parse_price
from app.helpers.keyword import find_summary_keyword

from app.schemas.response import Response

class PaddleOcrEngine:
    __text_det_box_thresh = 0.6
    __text_det_unclip_ratio = 1.5

    __min_word_confidence = 0.7

    __angle_tolerance = 5.0
    __dist_tolerance = 20.0

    def __init__(self,
                 version: str='PP-OCRv3',
                 use_textline_orientation: bool=True,
                 use_doc_orientation_classify: bool=False,
                 use_doc_unwarping: bool=False,
                 text_det_box_thresh: float = 0.6,
                 text_det_unclip_ratio: float = 1.5,
                 min_word_confidence: float = 0.7,
                 angle_tolerance: float = 5.0,
                 dist_tolerance: float = 20.0):
        self.__text_det_box_thresh = text_det_box_thresh
        self.__text_det_unclip_ratio = text_det_unclip_ratio

        self.__min_word_confidence = min_word_confidence

        self.__angle_tolerance = angle_tolerance
        self.__dist_tolerance = dist_tolerance
        
        self.ocr = PaddleOCR(
            ocr_version=version,
            use_textline_orientation=use_textline_orientation,
            use_doc_orientation_classify=use_doc_orientation_classify,
            use_doc_unwarping=use_doc_unwarping,
            lang='en'
        )

    def __is_box_horizontal(self, box, tolerance=0.7):
        """
        box: list of 4 points [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        Returns True if box is mostly horizontal (width >> height).
        """

        dx = ((box[1][0] - box[0][0]) + (box[2][0] - box[3][0])) / 2
        dy = ((box[3][1] - box[0][1]) + (box[2][1] - box[1][1])) / 2

        dx, dy = abs(dx), abs(dy)

        # check orientation
        return dx >= dy * tolerance

    def __ocr(self, img: np.ndarray) -> list:
        return self.ocr.predict(img, 
                                text_det_box_thresh=self.__text_det_box_thresh,
                                text_det_unclip_ratio=self.__text_det_unclip_ratio)
    
    def __group_items(self, res: list):
        items = []
        for page in res:  # in case of multipage
            polys = page["dt_polys"]       # list of quadrilaterals
            texts = page["rec_texts"]      # recognized text
            scores = page["rec_scores"]    # confidence scores

            for box, text, conf in zip(polys, texts, scores):
                if conf < self.__min_word_confidence:
                    continue

                if not self.__is_box_horizontal(box):
                    continue

                if not text.strip():
                    continue
                y_mean = np.mean([p[1] for p in box])  # average y
                x_mean = np.mean([p[0] for p in box])  # average x

                y_min = min(y for _, y in box)
                y_max = max(y for _, y in box)

                x_min = min(x for x, _ in box)
                x_max = max(x for x, _ in box)

                items.append((box, y_mean, x_mean, x_min, x_max, text, conf, y_min, y_max))

        return items
    
    def __box_baseline(self, box):
        """Return (x_mid, y_mid) of bottom edge and slope (angle in radians)."""
        x1, y1 = box[3]  # bottom-left
        x2, y2 = box[2]  # bottom-right
        dx, dy = x2 - x1, y2 - y1
        angle = np.arctan2(dy, dx)
        x_mid = (x1 + x2) / 2
        y_mid = (y1 + y2) / 2
        return x_mid, y_mid, angle
    
    def __lines_from_items(self, items):
        """items: [(box, text, conf, ...)] returns list of [texts per line]."""
        lines = []

        for item in items:
            box, *rest = item
            x_mid, y_mid, angle = self.__box_baseline(box)
            added = False

            for line in lines:
                # use first baseline as reference
                x0, y0, angle0 = line['ref']
                angle_diff = abs(np.degrees(angle - angle0))
                dy = abs(y_mid - y0)
                if angle_diff < self.__angle_tolerance and dy < self.__dist_tolerance:
                    line['items'].append(item)
                    added = True
                    break

            if not added:
                lines.append({'ref': (x_mid, y_mid, angle), 'items': [item]})

        # Convert lines to list of texts sorted left-to-right
        final_lines = []
        for line in lines:
            if len(line['items']) <= 1:   # skip if only one box, since it less likely to be a summary or items details
                continue

            texts = [it[5] for it in sorted(line['items'], key=lambda it: np.mean([p[0] for p in it[0]]))]
            final_lines.append(texts)

        return final_lines
    
    def __convert_res_to_lines(self, res: list):
        grouped_items = self.__group_items(res)
        return self.__lines_from_items(items=grouped_items)
    
    def __classify_details(self, details: list = []):
        processed = []

        for i in details:
            if i['qty'] > 0:
                detail = {
                    'category': 'item',
                    'info': i
                }

                processed.append(detail)

                continue

            summary_keyword = find_summary_keyword(word=i['item'])
            if summary_keyword:
                if summary_keyword != i['item']:
                    i['item'] = summary_keyword

                del i['qty']
                detail = {
                    'category': 'summary',
                    'info': i
                }

                processed.append(detail)
            else:
                i['qty'] = 1

                detail = {
                    'category': 'item',
                    'info': i
                }

                processed.append(detail)

        return processed
    
    def __extract_details_from_lines(self, lines:list):
        details = []

        for line in lines:
            qty = 0
            item = ''
            price = {'currency': None, 'numeric': 0}

            for word in line:
                if word.isdigit():
                    qty = int(word)
                    continue

                parsed_price = parse_price(word)
                if parsed_price:
                    price = parsed_price  
                    continue

                item = word

            if item:
                details.append({'item': item, 'qty': qty, 'price': price})

        return self.__classify_details(details=details) 

    def detect(self, contents: bytes):
        if len(contents) == 0:
            raise BadRequestException('File is empty')

        np_img: np.ndarray = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
        if np_img is None:
            raise BadRequestException('Uploaded file is not a valid image')
        
        try:
            res = self.__ocr(img=np_img)
        except Exception as e:
            raise InternalErrorException(f'[extensions][paddle_ocr][detect][self.__ocr] Failed to perform OCR: {str(e)}')
        
        if res is None or len(res) == 0:
            raise InternalErrorException(f'[extensions][paddle_ocr][detect] Empty response from Paddle')
        
        lines = self.__convert_res_to_lines(res)

        details = self.__extract_details_from_lines(lines)

        return Response[list](
            status_code=200,
            message='ok',
            success=True,
            data=details
        )
