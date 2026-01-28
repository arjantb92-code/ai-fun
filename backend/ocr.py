import easyocr
import os
import re
import ssl

class OCRService:
    def __init__(self):
        ssl._create_default_https_context = ssl._create_unverified_context
        self.reader = easyocr.Reader(['nl', 'en'])

    def process_receipt(self, image_path):

        results = self.reader.readtext(image_path)

        full_text = " ".join([res[1] for res in results])

        total = 0.0
        amounts = []

        potential_amounts = re.findall(r"\d+[.,]\d{2}", full_text)
        for val in potential_amounts:
            try:
                cleaned_val = val.replace(",", ".")
                amounts.append(float(cleaned_val))
            except ValueError:
                continue

        if amounts:
            total = max(amounts)

        return {
            "raw_text": full_text,
            "extracted_data": {
                "total": total,
                "date": self._extract_date(full_text),
                "merchant": self._extract_merchant(full_text),
            },
        }

    def _extract_date(self, text):
        date_match = re.search(r"\d{2}[-/]\d{2}[-/]\d{4}", text)
        if date_match:
            return date_match.group(0)
        return None

    def _extract_merchant(self, text):
        common_merchants = [
            "Albert Heijn",
            "Jumbo",
            "Lidl",
            "Aldi",
            "TrainMore",
            "Shell",
        ]
        for merchant in common_merchants:
            if merchant.lower() in text.lower():
                return merchant
        return "Unknown Merchant"


ocr_service = None


def get_ocr_service():
    global ocr_service
    if ocr_service is None:
        ocr_service = OCRService()
    return ocr_service
