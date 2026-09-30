import fitz
from pathlib import Path

from app.schemas.document import DocumentData, PageData


def extract_text_from_pdf(file_path: Path) -> DocumentData:
    """
    Extract text from a PDF document while preserving page boundaries.
    """

    document = fitz.open(file_path)

    page_data = []
    all_text = ""

    for page_number, page in enumerate(document, start=1):

        page_text = page.get_text()

        page_data.append(
            PageData(
                page=page_number,
                text=page_text,
            )
        )

        all_text += page_text

    document.close()

    return DocumentData(
        text=all_text,
        characters=len(all_text),
        is_empty=len(all_text.strip()) == 0,
        pages=len(page_data),
        source=file_path.name,
        page_data=page_data,
    )