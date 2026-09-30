from uuid import uuid4
import os

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.schemas.embedding import EmbeddingData


class QdrantService:
    """
    Service responsible for storing and retrieving
    document embeddings using Qdrant.
    """

    COLLECTION_NAME = "documents"
    VECTOR_SIZE = 384

    def __init__(self):
        url = os.getenv(
            "QDRANT_URL",
            "http://localhost:6333"
        )

        print("QdrantService initialized")

        self.client = QdrantClient(url=url)

    def create_collection(self) -> None:
        """
        Create the documents collection if it does not exist.
        """

        if not self.client.collection_exists(
            collection_name=self.COLLECTION_NAME
        ):
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )

    def store_embeddings(
        self,
        embeddings: list[EmbeddingData],
    ) -> None:
        """
        Store document embeddings in Qdrant.
        """

        points = []

        for embedding in embeddings:

            point = PointStruct(
                id=str(uuid4()),

                vector=embedding.embedding,

                payload={
                    "text": embedding.text,
                    "chunk_index": embedding.chunk_index,
                    "page": embedding.page,
                    "source": embedding.source,
                },
            )

            points.append(point)

        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points,
        )

    def store_points(self, point_dicts: list[dict]) -> None:
        """
        Store explicitly constructed document embeddings with metadata in Qdrant.
        """
        points = []
        for p in point_dicts:
            point = PointStruct(
                id=p["id"],
                vector=p["embedding"],
                payload=p["payload"]
            )
            points.append(point)
            
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points,
        )

    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float | None = None,
        source: str | None = None,
    ):
        """
        Search for the most similar document chunks
        using vector similarity and optional metadata filtering.
        """

        # No filter by default
        query_filter = None

        # Filter results by document source if provided
        if source is not None:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source),
                    )
                ]
            )

        # Search Qdrant
        results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
            with_payload=True,
        )

        return results.points