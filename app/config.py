from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "change-me"
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    qdrant_url: str = "http://localhost:6333"
    redis_url: str = "redis://localhost:6379/0"
    grobid_url: str = "http://localhost:8070"
    mineru_url: str = ""  # external adapter: see README
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    objects_dir: str = "/data/objects"
    max_upload_mb: int = 80
    allow_fallback_pdf: bool = True
    enable_visual: bool = False
    visual_model: str = "vidore/colqwen2-v1.0"
    visual_dim: int = 128
    retrieval_limit: int = 12
settings = Settings()
