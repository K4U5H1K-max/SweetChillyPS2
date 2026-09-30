from pydantic import BaseModel, Field

class DocumentData(BaseModel):


    """
    represents a processed document.

    Stores the extracted text along with metadata such as character count,
    page count, extraction source, and generated text chunks for downstream
    Ai processing
    """
    text: str
    characters: int
    is_empty: bool

    pages: int | None = None
    source: str | None = None

    chunks: list[str] = Field(default_factory=list)