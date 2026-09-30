from app.schemas.chunk import ChunkData
from app.schemas.document import PageData


class ChunkService:
    """
    Split document pages into smaller overlapping chunks
    while preserving page and source metadata.
    """

    def split(
        self,
        pages: list[PageData],
        source: str | None = None,
        chunk_size: int = 500,
        overlap: int = 100,
    ) -> list[ChunkData]:

        chunks = []

        for page in pages:

            text = page.text
            start = 0

            while start < len(text):

                end = start + chunk_size

                chunk_text = text[start:end]

                chunks.append(
                    ChunkData(
                        id=len(chunks),
                        text=chunk_text,
                        page=page.page,
                        source=source,
                    )
                )

                start += chunk_size - overlap

        return chunks