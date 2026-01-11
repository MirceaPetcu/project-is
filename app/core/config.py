from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    PROJECT_NAME: str = "OSINT Intelligence Platform"
    VERSION: str = "1.0.0"
    
    # LLM Configuration
    LLM_PROVIDER: str = "ollama"  # "ollama" or "openai"

    # OpenAI Configuration (used when LLM_PROVIDER="openai")
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Ollama Configuration (used when LLM_PROVIDER="ollama")
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b-instruct-q8_0"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text:latest"
    OLLAMA_EMBEDDING_DIM: int = 768
    OLLAMA_TIMEOUT: int = 300
    OLLAMA_NUM_CTX: int = 8192
    
    # Storage Configuration
    WORKING_DIR: str = "./osint_data"
    GRAPH_STORAGE: str = "neo4j"
    CACHE_STORAGE: str = "redis"
    
    # Neo4j Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URI: Optional[str] = None
    
    # Milvus Configuration
    MILVUS_URI: str = "http://localhost:19530"
    MILVUS_DB_NAME: str = "default"
    # MongoDB Configuration
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "osint_platform"
    
    # Source Credibility
    MIN_CREDIBILITY_SCORE: float = 0.3
    DEFAULT_SOURCE_CREDIBILITY: float = 0.5
    
    # Analysis Configuration
    MISINFORMATION_THRESHOLD: float = 0.7
    NARRATIVE_DETECTION_WINDOW_DAYS: int = 7
    TEMPORAL_RESOLUTION_HOURS: int = 1
    GEOGRAPHIC_CLUSTER_RADIUS_KM: float = 50.0
    
    # Alert Configuration
    PREDICTIVE_ALERT_THRESHOLD: float = 0.8
    ALERT_CHECK_INTERVAL_MINUTES: int = 15
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure working directory exists
os.makedirs(settings.WORKING_DIR, exist_ok=True)

# Export required environment variables for LightRAG storage backends
os.environ.setdefault("MILVUS_URI", settings.MILVUS_URI)
os.environ.setdefault("MILVUS_DB_NAME", settings.MILVUS_DB_NAME)
os.environ.setdefault("NEO4J_URI", settings.NEO4J_URI)
os.environ.setdefault("NEO4J_USERNAME", settings.NEO4J_USERNAME)
os.environ.setdefault("NEO4J_PASSWORD", settings.NEO4J_PASSWORD)
os.environ.setdefault("REDIS_URI", settings.REDIS_URI or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}")
os.environ.setdefault("MONGO_URI", settings.MONGO_URI)
os.environ.setdefault("MONGO_DATABASE", settings.MONGO_DB)
