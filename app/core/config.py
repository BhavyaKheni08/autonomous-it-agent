import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Auto-IT-Support"
    # Default to localhost postgres if not set
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auto_it_support"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    CHROMA_DB_PATH: str = "./data/chroma_db"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
