from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Generates vector embeddings for code chunks."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str], batch_size: int = 50) -> list[list[float]]:
        """Encode a list of texts into embedding vectors.

        Args:
            texts: Strings to embed.
            batch_size: Number of texts processed at once.

        Returns:
            List of embedding vectors (each a list of floats).
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Embed a single search query."""
        return self.model.encode(query).tolist()

    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()
