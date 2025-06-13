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

    class Config:
        env_file = ".env"
        from_attributes = True

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