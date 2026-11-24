from functools import lru_cache
from app.config import settings
@lru_cache(maxsize=1)
def encoder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.embedding_model)
def embed(texts: list[str]) -> list[list[float]]:
    if not texts: return []
    return encoder().encode(texts, normalize_embeddings=True).tolist()
