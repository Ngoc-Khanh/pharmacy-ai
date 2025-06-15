from typing import Optional

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings
import models as models


class Settings(BaseSettings):
    # database configurations
    DATABASE_URL: Optional[str] = "mongodb://localhost:27017"
    DATABASE_NAME: str = "pharmacy"

    # JWT
    SECRET_KEY: str = "secret"
    ALGORITHM: str = "HS256"

    # LLM API KEY
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "qwen-qwq-32b"
    COHERE_API_KEY: Optional[str] = None
    COHERE_EMBEDDING_MODEL: str = "embed-multilingual-v3.0"

    # Milvus configurations
    MILVUS_URI: Optional[str] = None
    MILVUS_TOKEN: Optional[str] = None
    MILVUS_COLLECTION_NAME: str = "medicine_embeddings"

    # Embedding configurations
    EMBEDDING_DIMENSION: int = 1024

    # CORS Configuration
    ENVIRONMENT: str = "development"  # development, production
    CORS_ORIGINS: str = "*"  # Comma-separated list for production

    class Config:
        env_file = ".env"
        from_attributes = True

    def get_cors_origins(self) -> list:
        """Get CORS origins based on environment"""
        if self.ENVIRONMENT == "production":
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return ["*"]  # Allow all origins in development


async def initiate_database():
    settings = Settings()
    client = AsyncIOMotorClient(settings.DATABASE_URL)
    try:
        await client.admin.command("ping")
        print("MongoDB connection successful")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return
    await init_beanie(
        database=client[settings.DATABASE_NAME], document_models=models.__all__
    )


def get_database():
    settings = Settings()
    client = AsyncIOMotorClient(settings.DATABASE_URL)
    return client[settings.DATABASE_NAME]
