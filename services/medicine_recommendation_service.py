import logging
from typing import Any, Dict, List
from datetime import datetime

from beanie import PydanticObjectId
from models.medicine import Medicine
from services.embedding_service import EmbeddingService
from services.milvus_service import MilvusService

logger = logging.getLogger(__name__)


def serialize_medicine_data(medicine_data):
    """
    Custom serializer to handle datetime and other non-JSON serializable objects
    """
    def convert_value(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, PydanticObjectId):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: convert_value(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_value(item) for item in obj]
        else:
            return obj
    
    return convert_value(medicine_data)


class MedicineRecommendationService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.milvus_service = MilvusService()

    async def search_medicines_by_symptoms(
        self, symptoms: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Tìm kiếm thuốc dựa trên triệu chứng"""
        try:
            # Tạo embedding cho triệu chứng
            query_embedding = self.embedding_service.embed_single_text(symptoms)
            # Tìm kiếm trong Milvus
            results = self.milvus_service.search_medicines(
                query_embedding=query_embedding,
                search_type="symptom",
                limit=limit,
                filters="is_active == true and stock_status == 'IN-STOCK'",
            )
            return results
        except Exception as e:
            logger.error(f"Error searching medicines by symptoms: {e}")
            raise

    async def search_medicines_by_ingredient(
        self, ingredient: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Tìm kiếm thuốc dựa trên thành phần"""
        try:
            query_embedding = self.embedding_service.embed_single_text(ingredient)
            results = self.milvus_service.search_medicines(
                query_embedding=query_embedding,
                search_type="primary",
                limit=limit,
                filters="is_active == true",
            )
            return results
        except Exception as e:
            logger.error(f"Error searching medicines by ingredient: {e}")
            raise

    async def get_similar_medicines(
        self, medicine_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Tìm thuốc tương tự dựa trên medicine_id"""
        try:
            # Lấy thông tin thuốc từ MongoDB với multiple strategies
            medicine = None
            
            # Strategy 1: Query by _id directly using get()
            try:
                medicine = await Medicine.get(medicine_id)
                if medicine:
                    logger.info(f"Found medicine using Strategy 1 (get): {medicine_id}")
            except Exception as e:
                logger.debug(f"Strategy 1 failed for {medicine_id}: {e}")
            
            # Strategy 2: Query by id field (not _id)
            if not medicine:
                try:
                    medicine = await Medicine.find_one(Medicine.id == medicine_id)
                    if medicine:
                        logger.info(f"Found medicine using Strategy 2 (id field): {medicine_id}")
                except Exception as e:
                    logger.debug(f"Strategy 2 failed for {medicine_id}: {e}")
            
            # Strategy 3: Query using find with filter
            if not medicine:
                try:
                    medicine = await Medicine.find_one({"$or": [
                        {"_id": medicine_id},
                        {"id": medicine_id}
                    ]})
                    if medicine:
                        logger.info(f"Found medicine using Strategy 3 (filter): {medicine_id}")
                except Exception as e:
                    logger.debug(f"Strategy 3 failed for {medicine_id}: {e}")
            
            if not medicine:
                raise ValueError(f"Medicine not found: {medicine_id}")
            
            # Tạo text và embedding
            try:
                medicine_dict = medicine.model_dump()
            except AttributeError:
                medicine_dict = medicine.dict()
            
            # Serialize datetime and other objects
            medicine_dict = serialize_medicine_data(medicine_dict)
            texts = self.embedding_service.create_medicine_text_for_embedding(
                medicine_dict
            )
            query_embedding = self.embedding_service.embed_single_text(texts["primary"])
            # Tìm kiếm thuốc tương tự
            results = self.milvus_service.search_medicines(
                query_embedding=query_embedding,
                search_type="primary",
                limit=limit + 1,  # +1 để loại bỏ chính nó
                filters=f"medicine_id != '{medicine_id}' and is_active == true",
            )
            return results[:limit]
        except Exception as e:
            logger.error(f"Error getting similar medicines: {e}")
            raise

    async def recommend_by_usage_guide(
        self, usage_query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Đề xuất thuốc dựa trên hướng dẫn sử dụng"""
        try:
            query_embedding = self.embedding_service.embed_single_text(usage_query)
            results = self.milvus_service.search_medicines(
                query_embedding=query_embedding,
                search_type="usage",
                limit=limit,
                filters="is_active == true and stock_status == 'IN-STOCK'",
            )
            return results
        except Exception as e:
            logger.error(f"Error recommending by usage guide: {e}")
            raise
