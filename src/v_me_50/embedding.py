"""BGE-M3 query encoder matching the published movie vectors."""

import numpy as np


class BGEM3QueryEmbedder:
    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        if self.model.get_embedding_dimension() != 1024:
            raise ValueError("BGE-M3 model must produce 1024 dimensions.")

    def embed_query(self, text: str) -> list[float]:
        vector = self.model.encode(text, normalize_embeddings=True)
        array = np.asarray(vector, dtype=np.float32)
        if array.shape != (1024,) or not np.isfinite(array).all():
            raise ValueError("Query encoder returned an invalid vector.")
        return array.tolist()
