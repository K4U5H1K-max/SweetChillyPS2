from sentence_transformers import SentenceTransformer

from app.schemas.chunk import ChunkData
from app.schemas.embedding import EmbeddingData


class EmbeddingService:
    """
    Service responsible for converting text into vector embeddings.
    """

    _model = None

    def __init__(self):
        if EmbeddingService._model is None:
            print("Loading embedding model...")
            EmbeddingService._model = SentenceTransformer(
                "BAAI/bge-small-en-v1.5"
            )

        self.model = EmbeddingService._model

    def encode(
        self,
        chunks: list[ChunkData],
    ) -> list[EmbeddingData]:

        texts = [chunk.text for chunk in chunks]

        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
        )

        embeddings = []

        for chunk, vector in zip(chunks, vectors):

            embeddings.append(
                EmbeddingData(
                    text=chunk.text,
                    embedding=vector.tolist(),
                    chunk_index=chunk.id,
                    page=chunk.page,
                    source=chunk.source,
                )
            )

        return embeddings

    def encode_query(
        self,
        query: str,
    ) -> list[float]:

        vector = self.model.encode(
            query,
            normalize_embeddings=True,
        )

        return vector.tolist()