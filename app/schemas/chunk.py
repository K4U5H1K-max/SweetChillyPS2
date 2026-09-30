from pydantic import BaseModel

class ChunkData(BaseModel):
    """
    Represents a single text chunk ready for embedding
    and storage inside the vector database.
    """
    id: int
    text: str
    page: int | None = None
    source: str | None = None