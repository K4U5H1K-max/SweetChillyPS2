"""
Request Models
Response Models
Internal Data Models
"""

from pydantic import BaseModel, Field


class PageData(BaseModel):
    """
    Represents the extracted text and metadata of a single document page.
    """

    page: int
    text: str


class DocumentData(BaseModel):
    """
    Represents the data extracted from a document.
    """

    text: str
    characters: int
    is_empty: bool

    pages: int | None = None
    source: str | None = None

    page_data: list[PageData] = Field(default_factory=list)