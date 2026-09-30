from pathlib import Path

from paddleocr import PaddleOCR

from app.schemas.document import DocumentData, PageData
from app.services.text_cleaner import TextCleaner


class OCRService:
    """
    Service responsible for extracting text from scanned documents
    using PaddleOCR.
    """

    def __init__(self):

        self.ocr = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            lang="en"
        )

    def extract_text(self, file_path: Path) -> DocumentData:
        """
        Run OCR on an image or scanned PDF and return
        extracted text while preserving page boundaries.
        """

        print(f"Running OCR on: {file_path}")

        result = self.ocr.predict(str(file_path))

        page_data = self._extract_pages(result)

        text = "\n".join(
            page.text
            for page in page_data
        )

        return DocumentData(
            text=text,
            characters=len(text),
            is_empty=len(text.strip()) == 0,
            pages=len(page_data),
            source=file_path.name,
            page_data=page_data,
        )

    def _extract_pages(self, result) -> list[PageData]:
        """
        Convert PaddleOCR output into page-level text.
        """

        pages = []

        for page_number, page in enumerate(result, start=1):

            if isinstance(page, dict):

                page_text = "\n".join(
                    page.get("rec_texts", [])
                )

                pages.append(
                    PageData(
                        page=page_number,
                        text=page_text,
                    )
                )

        return pages