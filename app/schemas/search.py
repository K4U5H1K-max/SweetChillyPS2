""""SearchRequest ↓ الـ input SearchResult ↓ نتيجة واحدة SearchResponse ↓ الـ response بالكامل"""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """
    Represents a semantic search request.
    """

    query: str

    # Number of results to return
    limit: int = Field(
        default=5,
        gt=0,
    )

    # Minimum similarity score required for a result
    min_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    # optional document source filter
    source:str | None = None

class SearchResult(BaseModel):
    """
    Represents a single semantic search result.
    """

    score: float
    text: str
    chunk_index: int | None = None
    page: int | None = None
    source: str | None = None


class SearchResponse(BaseModel):
    """
    Represents the semantic search response.
    """

    query: str
    results: list[SearchResult]

    # Minimum score threshold used for the search
    min_score: float | None = None