"""BGE-M3 encoder compatible with the published movie embeddings."""

import numpy as np

from ..errors import ConfigurationError, ModelUnavailable


class BGEM3QueryEmbedder:
    def __init__(self, model_name: str = "BAAI/bge-m3", *, model: object | None = None):
        if model is None:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_name)
        self.model = model
        if self.model.get_embedding_dimension() != 1024:
            raise ConfigurationError("The query encoder must produce 1024 dimensions.")

    def embed_query(self, text: str) -> list[float]:
        try:
            vector = self.model.encode(text, normalize_embeddings=True)
            array = np.asarray(vector, dtype=np.float32)
        except Exception as exc:
            raise ModelUnavailable("The query encoder failed.") from exc
        if array.shape != (1024,) or not np.isfinite(array).all() or not np.any(array):
            raise ModelUnavailable("The query encoder returned an invalid vector.")
        return array.tolist()
