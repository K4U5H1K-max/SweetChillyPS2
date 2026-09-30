from app.schemas.document import DocumentData


class DocumentClassifier:
    """
    Responsible for deciding the next processing step.
    """

    def classify(self, document: DocumentData) -> str:

        if document.is_empty:
            return "ocr"

        return "text"