from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService


class SearchService:
    """
    Service responsible for semantic search
    over document embeddings stored in Qdrant.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()

    def search(
        self,
        query: str,
        limit: int = 5,
        min_score: float | None = None,
        source: str | None = None,
    ):
        """
        Convert the user query into an embedding
        and retrieve the most similar document chunks.
        """

        # Convert query text into an embedding vector
        query_vector = self.embedding_service.encode_query(query)

        # Search Qdrant for similar document chunks
        results = self.qdrant_service.search(
            query_vector=query_vector,
            limit=limit,
            score_threshold=min_score,
            source=source,
        )

        # Convert Qdrant ScoredPoint objects
        # into simple dictionaries for the API layer
        return [
            {
                "score": result.score,
                "text": result.payload.get("text"),
                "chunk_index": result.payload.get("chunk_index"),
                "page": result.payload.get("page"),
                "source": result.payload.get("source"),
            }
            for result in results
        ]