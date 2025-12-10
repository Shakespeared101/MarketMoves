"""
Configuration settings for MarketMoves API
Uses pydantic-settings for environment variable management
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union
import os
from pathlib import Path


# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application settings
    APP_NAME: str = "MarketMoves"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # CORS settings - can be comma-separated string or list
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    # Database settings
    SQLITE_DB_PATH: str = str(DATA_DIR / "marketmoves.db")
    DUCKDB_PATH: str = str(DATA_DIR / "analytics.duckdb")

    # Neo4j settings
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "marketmoves"
    NEO4J_DATABASE: str = "neo4j"

    # Ollama/LLM settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"  # or "mistral"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048

    # RAG settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DB_PATH: str = str(DATA_DIR / "vector_store")
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    RAPTOR_LEVELS: int = 3
    TOP_K_RETRIEVAL: int = 5

    # Data source API keys (optional - many sources are free)
    SEC_EDGAR_USER_AGENT: str = "shakthi3203@gmail.com"
    NEWSAPI_KEY: str = "c01db65867dd4b31b8476f2e7fc6532e"  # Get free key from newsapi.org
    ALPHA_VANTAGE_KEY: str = "FGWYIAF1HGILFPV4"  # Optional - for additional financial data

    # Data ingestion settings
    MAX_COMPANIES_TO_TRACK: int = 50
    DATA_UPDATE_INTERVAL_HOURS: int = 24
    HISTORICAL_DATA_YEARS: int = 5

    # Risk scoring weights
    RISK_WEIGHT_VOLATILITY: float = 0.3
    RISK_WEIGHT_LITIGATION: float = 0.25
    RISK_WEIGHT_SENTIMENT: float = 0.2
    RISK_WEIGHT_FINANCIAL_ANOMALY: float = 0.15
    RISK_WEIGHT_REGULATORY: float = 0.1

    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600  # 1 hour

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = str(PROJECT_ROOT / "logs" / "marketmoves.log")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Create settings instance
settings = Settings()

# Ensure data directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
os.makedirs(Path(settings.LOG_FILE).parent, exist_ok=True)
