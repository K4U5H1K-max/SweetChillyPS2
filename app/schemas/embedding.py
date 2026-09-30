from pydantic import BaseModel

class EmbeddingData(BaseModel):
    """
    represent a text chunk together with it's embedding vector
    """

    text:str
    embedding:list[float]

    chunk_index: int | None = None
    page: int | None = None
    source: str | None = None