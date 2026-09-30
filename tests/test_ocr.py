import pytest
from pathlib import Path
from app.services.ocr_service import OCRService

@pytest.mark.skip(reason="Needs local file")
def test_ocr_extraction():
    ocr = OCRService()
    result = ocr.extract_text(Path("data/uploads/t.png"))
    print(result)