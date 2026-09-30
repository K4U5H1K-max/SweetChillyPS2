from fastapi import APIRouter

from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResult,
)

from app.services.search_service import SearchService


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


search_service = SearchService()


@router.post(
    "",
    response_model=SearchResponse,
)
async def search(request: SearchRequest):

    results = search_service.search(
        query=request.query,
        limit=request.limit,
        min_score=request.min_score,
        source=request.source,
    )

    search_results = [
        SearchResult(
            score=result["score"],
            text=result["text"],
            chunk_index=result["chunk_index"],
            page=result["page"],
            source=result["source"],
        )
        for result in results
    ]

    return SearchResponse(
        query=request.query,
        min_score=request.min_score,
        results=search_results,
    )


