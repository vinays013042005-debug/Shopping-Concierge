import logging
import hashlib
from typing import List, Union
import numpy as np
from app.config import EMBEDDING_MODEL_NAME

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self._fallback_dim = 384  # Matches all-MiniLM-L6-v2 dimension

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer '{self.model_name}': {e}. Using deterministic fallback.")
                self._model = "FALLBACK"
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        mdl = self.model
        if mdl != "FALLBACK":
            try:
                embeddings = mdl.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return embeddings.tolist()
            except Exception as e:
                logger.error(f"Error during model encoding: {e}. Falling back to pseudo-embeddings.")

        # Deterministic hashing fallback for offline/test environments
        return [self._pseudo_embedding(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        results = self.embed_texts([query])
        return results[0] if results else [0.0] * self._fallback_dim

    def _pseudo_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic 384-dimensional unit vector from text hashing.
        Allows testing and vector search logic even without GPU/PyTorch weights.
        """
        words = text.lower().split()
        vec = np.zeros(self._fallback_dim, dtype=np.float32)
        for w in words:
            # Hash word into seed
            h = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16)
            idx = h % self._fallback_dim
            sign = 1.0 if ((h >> 8) % 2 == 0) else -1.0
            vec[idx] += sign

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0
        return vec.tolist()

embedding_service = EmbeddingService()
