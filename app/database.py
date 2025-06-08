import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

db = Database()

async def connect_to_mongo():
    try:
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        database_name = os.getenv("DATABASE_NAME", "pharmacy_ai")
        db.client = AsyncIOMotorClient(mongodb_url)
        await db.client.admin.command('ping')
        db.database = db.client[database_name]
    except ConnectionFailure as e:
        logger.error(f"Lỗi kết nối MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Lỗi không xác định khi kết nối MongoDB: {e}")
        raise

async def close_mongo_connection():
    if db.client:
        db.client.close()
        logger.info("Đã đóng kết nối MongoDB")

def get_database():
    return db.database 