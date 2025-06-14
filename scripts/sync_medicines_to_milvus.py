#!/usr/bin/env python3
"""
Script để đồng bộ dữ liệu Medicine từ MongoDB lên Milvus
Sử dụng: python scripts/sync_medicines_to_milvus.py
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from config.config import Settings
from models.medicine import Medicine
from services.embedding_service import EmbeddingService
from services.milvus_service import MilvusService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("sync_medicines.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class MedicineDataSyncer:
    def __init__(self):
        self.settings = Settings()
        self.embedding_service = EmbeddingService()
        self.milvus_service = MilvusService()
        self.batch_size = 10  # Process medicines in batches

    async def init_database(self):
        """Initialize database connection"""
        try:
            client = AsyncIOMotorClient(self.settings.DATABASE_URL)
            database = client[self.settings.DATABASE_NAME]
            # Initialize beanie with models
            await init_beanie(database=database, document_models=[Medicine])
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def get_all_medicines(self) -> List[Medicine]:
        """Lấy tất cả medicines từ MongoDB"""
        try:
            medicines = await Medicine.find_all().to_list()
            logger.info(f"Found {len(medicines)} medicines in MongoDB")
            return medicines
        except Exception as e:
            logger.error(f"Failed to fetch medicines: {e}")
            raise

    def prepare_medicine_data_for_milvus(self, medicine: Medicine) -> Dict:
        """Chuẩn bị dữ liệu medicine để lưu vào Milvus"""
        try:
            medicine_dict = medicine.model_dump()
            # Prepare data for Milvus
            milvus_data = {
                "id": f"med_{str(medicine.id)}",
                "medicine_id": str(medicine.id),
                "name": medicine.name,
                "slug": medicine.slug,
                "category_id": medicine.category_id,
                "supplier_id": medicine.supplier_id,
                "active_ingredient": medicine.details.ingredients,
                "price": medicine.variants.price,
                "stock_status": medicine.variants.stock_status,
                "is_featured": medicine.variants.is_featured,
                "is_active": medicine.variants.is_active,
                "rating": medicine.ratings.star,
                # Convert complex data to JSON strings
                "therapeutic_uses": json.dumps(
                    medicine.details.usage, ensure_ascii=False
                ),
                "contraindications": json.dumps(
                    medicine.usageguide.precautions, ensure_ascii=False
                ),
                "dosage_info": json.dumps(
                    {
                        "adult": medicine.usageguide.dosage.adult,
                        "child": medicine.usageguide.dosage.child,
                        "directions": medicine.usageguide.directions,
                    },
                    ensure_ascii=False,
                ),
            }
            return milvus_data
        except Exception as e:
            logger.error(f"Failed to prepare medicine data for {medicine.name}: {e}")
            raise

    async def create_embeddings_for_medicine(
        self, medicine: Medicine
    ) -> Dict[str, List[float]]:
        """Tạo embeddings cho một medicine"""
        try:
            medicine_dict = medicine.model_dump()
            # Create different text representations
            texts = self.embedding_service.create_medicine_text_for_embedding(
                medicine_dict
            )
            # Create embeddings for each text type
            embeddings = {}
            for text_type, text_content in texts.items():
                if text_content.strip():  # Only create embedding if text is not empty
                    embedding = self.embedding_service.embed_document(text_content)
                    embeddings[f"{text_type}_embedding"] = embedding
                else:
                    # Create zero embedding if text is empty
                    embeddings[f"{text_type}_embedding"] = [
                        0.0
                    ] * self.embedding_service.dimension
            logger.debug(f"Created embeddings for medicine: {medicine.name}")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to create embeddings for {medicine.name}: {e}")
            raise

    async def sync_medicines_batch(self, medicines: List[Medicine]) -> int:
        """Đồng bộ một batch medicines lên Milvus"""
        try:
            milvus_data_list = []
            for medicine in medicines:
                try:
                    # Prepare basic data
                    milvus_data = self.prepare_medicine_data_for_milvus(medicine)
                    # Create embeddings
                    embeddings = await self.create_embeddings_for_medicine(medicine)
                    # Add embeddings to data
                    milvus_data.update(embeddings)
                    milvus_data_list.append(milvus_data)
                    logger.info(f"Prepared data for medicine: {medicine.name}")
                except Exception as e:
                    logger.error(f"Failed to process medicine {medicine.name}: {e}")
                    continue
            if not milvus_data_list:
                logger.warning("No valid medicine data to insert")
                return 0
            # Insert into Milvus
            self.insert_to_milvus(milvus_data_list)
            return len(milvus_data_list)
        except Exception as e:
            logger.error(f"Failed to sync medicines batch: {e}")
            raise

    def insert_to_milvus(self, data_list: List[Dict]):
        """Insert data vào Milvus collection"""
        try:
            if not self.milvus_service.collection:
                raise ValueError("Milvus collection not initialized")
            # Prepare data for insertion
            entities = []
            for data in data_list:
                entity = [
                    data["id"],
                    data["medicine_id"],
                    data["name"],
                    data["slug"],
                    data["primary_embedding"],
                    data["symptom_embedding"],
                    data["usage_embedding"],
                    data["safety_embedding"],
                    data["category_id"],
                    data["supplier_id"],
                    data["active_ingredient"],
                    data["price"],
                    data["stock_status"],
                    data["is_featured"],
                    data["is_active"],
                    data["rating"],
                    data["therapeutic_uses"],
                    data["contraindications"],
                    data["dosage_info"],
                ]
                entities.append(entity)
            # Transpose entities for Milvus format
            transposed_entities = list(map(list, zip(*entities)))
            # Insert data
            insert_result = self.milvus_service.collection.insert(transposed_entities)
            # Flush to ensure data is written
            self.milvus_service.collection.flush()
            logger.info(f"Successfully inserted {len(data_list)} medicines to Milvus")
            logger.info(f"Insert result: {insert_result}")
        except Exception as e:
            logger.error(f"Failed to insert data to Milvus: {e}")
            raise

    async def sync_all_medicines(self):
        """Đồng bộ tất cả medicines từ MongoDB lên Milvus"""
        try:
            start_time = datetime.now()
            logger.info("Starting medicine synchronization...")
            # Initialize database
            await self.init_database()
            # Create or recreate Milvus collection
            logger.info("Creating Milvus collection...")
            self.milvus_service.create_collection()
            # Get all medicines
            medicines = await self.get_all_medicines()
            if not medicines:
                logger.warning("No medicines found in MongoDB")
                return
            # Process medicines in batches
            total_synced = 0
            total_batches = (len(medicines) + self.batch_size - 1) // self.batch_size
            for i in range(0, len(medicines), self.batch_size):
                batch_num = i // self.batch_size + 1
                batch = medicines[i : i + self.batch_size]
                logger.info(
                    f"Processing batch {batch_num}/{total_batches} ({len(batch)} medicines)"
                )
                try:
                    synced_count = await self.sync_medicines_batch(batch)
                    total_synced += synced_count
                    logger.info(
                        f"Batch {batch_num} completed: {synced_count} medicines synced"
                    )
                except Exception as e:
                    logger.error(f"Failed to process batch {batch_num}: {e}")
                    continue
            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"Synchronization completed!")
            logger.info(f"Total medicines processed: {len(medicines)}")
            logger.info(f"Total medicines synced: {total_synced}")
            logger.info(f"Duration: {duration}")
        except Exception as e:
            logger.error(f"Synchronization failed: {e}")
            raise

    async def verify_sync(self):
        """Kiểm tra kết quả đồng bộ"""
        try:
            if not self.milvus_service.collection:
                logger.error("Milvus collection not initialized")
                return
            # Get collection stats
            stats = self.milvus_service.collection.num_entities
            logger.info(f"Total entities in Milvus collection: {stats}")
            # Test search functionality
            test_query = "thuốc giảm đau"
            test_embedding = self.embedding_service.embed_query(test_query)
            results = self.milvus_service.search_medicines(
                query_embedding=test_embedding, search_type="symptom", limit=5
            )
            logger.info(f"Test search results for '{test_query}':")
            for i, result in enumerate(results, 1):
                logger.info(
                    f"  {i}. {result['name']} (score: {result['similarity_score']:.4f})"
                )
        except Exception as e:
            logger.error(f"Verification failed: {e}")


async def main():
    """Main function"""
    try:
        syncer = MedicineDataSyncer()
        # Sync all medicines
        await syncer.sync_all_medicines()
        # Verify sync
        await syncer.verify_sync()
        logger.info("Script completed successfully!")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
