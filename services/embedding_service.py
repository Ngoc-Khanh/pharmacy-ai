import logging
from typing import Any, Dict, List, Optional

import cohere
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from config.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.settings = Settings()
        self.cohere_client = None
        self.milvus_collection = None
        if self.settings.COHERE_API_KEY:
            try:
                self.cohere_client = cohere.ClientV2(self.settings.COHERE_API_KEY)
                logger.info("Khởi tạo Cohere client thành công")
            except Exception as e:
                logger.error(f"Lỗi khi khởi tạo Cohere client: {e}")
        else:
            logger.warning("Không tìm thấy COHERE_API_KEY trong config")
        self._init_milvus_connection()

    def _init_milvus_connection(self):
        """Khởi tạo kết nối Milvus/Zilliz Cloud"""
        try:
            if self.settings.MILVUS_URI and self.settings.MILVUS_TOKEN:
                connections.connect(
                    alias="default",
                    uri=self.settings.MILVUS_URI,
                    token=self.settings.MILVUS_TOKEN,
                )
                logger.info("Kết nối Milvus thành công")
                self._create_collection_if_not_exists()
            else:
                logger.warning("MILVUS_URI hoặc MILVUS_TOKEN không được cấu hình")
        except Exception as e:
            logger.error(f"Lỗi khi kết nối Zilliz Cloud: {e}")

    def _create_collection_if_not_exists(self):
        """Tạo collection nếu chưa tồn tại"""
        try:
            collection_name = self.settings.MILVUS_COLLECTION_NAME
            if utility.has_collection(collection_name):
                self.milvus_collection = Collection(collection_name)
                logger.info(f"Collection {collection_name} đã tồn tại")
                return
            # Định nghĩa schema
            fields = [
                FieldSchema(
                    name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True
                ),
                FieldSchema(name="medicine_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="category_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="supplier_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(
                    name="description", dtype=DataType.VARCHAR, max_length=2000
                ),
                FieldSchema(
                    name="ingredients", dtype=DataType.VARCHAR, max_length=1000
                ),
                FieldSchema(name="usage", dtype=DataType.VARCHAR, max_length=1000),
                FieldSchema(name="origin", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="packaging", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="price", dtype=DataType.FLOAT),
                FieldSchema(name="stock_status", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="is_featured", dtype=DataType.BOOL),
                FieldSchema(name="is_active", dtype=DataType.BOOL),
                FieldSchema(name="rating_star", dtype=DataType.FLOAT),
                FieldSchema(
                    name="embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.settings.EMBEDDING_DIMENSION,
                ),
            ]
            schema = CollectionSchema(
                fields, f"Tạo embedding vector cho bảng {collection_name}"
            )
            # Tạo collection
            self.milvus_collection = Collection(collection_name, schema)
            # Tạo index
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024},
            }
            self.milvus_collection.create_index(
                field_name="embedding", index_params=index_params
            )
            logger.info(f"Tạo collection {collection_name} thành công!")
        except Exception as e:
            logger.error(f"Lỗi khi tạo collection: {e}")

    def create_medicine_embedding_text(self, medicine_data: Dict[str, Any]) -> str:
        """Tạo text để embedding từ dữ liệu thuốc"""
        try:
            text_parts = []  # Tạo danh sách để lưu các phần của text
            # Thông tin cơ bản
            text_parts.append(f"Tên thuốc: {medicine_data.get('name', '')}")
            text_parts.append(f"Mô tả: {medicine_data.get('description', '')}")
            # Thành phần và công dụng
            if "details" in medicine_data:
                details = medicine_data["details"]
                if "ingredients" in details:
                    text_parts.append(f"Thành phần: {details['ingredients']}")
                if "usage" in details and isinstance(details["usage"], list):
                    text_parts.append(f"Công dụng: {', '.join(details['usage'])}")
                if "paramaters" in details:  # Note: typo in original data
                    params = details["paramaters"]
                    if "origin" in params:
                        text_parts.append(f"Xuất xứ: {params['origin']}")
                    if "packaging" in params:
                        text_parts.append(f"Đóng gói: {params['packaging']}")
            # Hướng dẫn sử dụng
            if "usageguide" in medicine_data:
                guide = medicine_data["usageguide"]
                if "dosage" in guide:
                    dosage = guide["dosage"]
                    if "adult" in dosage:
                        text_parts.append(f"Liều dùng người lớn: {dosage['adult']}")
                    if "child" in dosage:
                        text_parts.append(f"Liều dùng trẻ em: {dosage['child']}")
                if "directions" in guide and isinstance(guide["directions"], list):
                    text_parts.append(f"Cách dùng: {', '.join(guide['directions'])}")
                if "precautions" in guide and isinstance(guide["precautions"], list):
                    text_parts.append(f"Lưu ý: {', '.join(guide['precautions'])}")
            # Thông tin giá và tình trạng
            if "variants" in medicine_data:
                variants = medicine_data["variants"]
                text_parts.append(f"Giá: {variants.get('price', 0)} VND")
                text_parts.append(f"Tình trạng: {variants.get('stock_status', '')}")
            return ". ".join(text_parts)
        except Exception as e:
            logger.error(f"Lỗi khi tạo embedding text: {e}")
            return (
                medicine_data.get("name", "")
                + ". "
                + medicine_data.get("description", "")
            )

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Tạo embedding từ text sử dụng Cohere"""
        try:
            if not self.cohere_client:
                logger.error("Cohere client chưa được khởi tạo")
                return None
            response = self.cohere_client.embed(
                texts=[text],
                model=self.settings.COHERE_EMBEDDING_MODEL,
                input_type="search_document",
                embedding_types=["float"],
                output_dimension=self.settings.EMBEDDING_DIMENSION,
            )
            return response.embeddings.float[0]
        except Exception as e:
            logger.error(f"Lỗi khi tạo embedding: {e}")
            return None

    def insert_medicine_embedding(self, medicine_data: Dict[str, Any]) -> bool:
        """Thêm embedding vào Milvus"""
        try:
            if not self.milvus_collection:
                logger.error("Collection Milvus chưa được khởi tạo")
                return False
            # Tạo text để embedding
            embedding_text = self.create_medicine_embedding_text(medicine_data)
            # Tạo embedding
            embedding = self.generate_embedding(embedding_text)
            if not embedding:
                logger.error("Không thể tạo embedding")
                return False
            # Chuẩn bị dữ liệu để chèn
            medicine_id = medicine_data.get("_id", "")
            if isinstance(medicine_id, dict) and "$oid" in medicine_id:
                medicine_id = medicine_id["$oid"]
            # Trích xuất dữ liệu với các mặc định an toàn
            variants = medicine_data.get("variants", {})
            details = medicine_data.get("details", {})
            params = details.get("paramaters", {})  # Note: typo in original
            ratings = medicine_data.get("ratings", {})
            # Chuẩn bị sử dụng như chuỗi
            usage_list = details.get("usage", [])
            usage_str = (
                ", ".join(usage_list)
                if isinstance(usage_list, list)
                else str(usage_list)
            )
            
            # Sửa lỗi: Chuẩn bị dữ liệu theo format mà Milvus mong đợi
            # Milvus mong đợi dữ liệu theo format: [field1_values, field2_values, ...]
            data = [
                [str(medicine_id)],  # id (primary key)
                [str(medicine_id)],  # medicine_id
                [medicine_data.get("name", "")],
                [medicine_data.get("category_id", "")],
                [medicine_data.get("supplier_id", "")],
                [medicine_data.get("description", "")],
                [details.get("ingredients", "")],
                [usage_str],
                [params.get("origin", "")],
                [params.get("packaging", "")],
                [float(variants.get("price", 0))],
                [variants.get("stock_status", "")],
                [bool(variants.get("is_featured", False))],
                [bool(variants.get("is_active", True))],
                [float(ratings.get("star", 0))],
                [embedding],
            ]
            # Thêm dữ liệu vào Milvus
            self.milvus_collection.insert(data)
            self.milvus_collection.flush()
            logger.info(f"Đã chèn embedding cho thuốc: {medicine_data.get('name', '')}")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi chèn embedding: {e}")
            return False

    def search_similar_medicines(self, query_text: str, limit: int = 10) -> List[Dict]:
        """Tìm kiếm thuốc tương tự dựa trên embedding"""
        try:
            if not self.milvus_collection:
                logger.error("Collection Milvus chưa được khởi tạo")
                return []
            # Load collection
            self.milvus_collection.load()
            # Tạo embedding cho query
            query_embedding = self.generate_embedding(query_text)
            if not query_embedding:
                return []
            # Search parameters
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10},
            }
            results = self.milvus_collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                output_fields=[
                    "medicine_id",
                    "name",
                    "description",
                    "price",
                    "rating_star",
                    "stock_status",
                ],
            )
            # Format results
            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append(
                        {
                            "medicine_id": hit.entity.get("medicine_id"),
                            "name": hit.entity.get("name"),
                            "description": hit.entity.get("description"),
                            "price": hit.entity.get("price"),
                            "rating_star": hit.entity.get("rating_star"),
                            "stock_status": hit.entity.get("stock_status"),
                            "similarity_score": hit.score,
                        }
                    )

            return formatted_results
        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm: {e}")
            return []

    def batch_insert_medicines(
        self, medicines_data: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Chèn nhiều thuốc cùng lúc"""
        success_count = 0
        error_count = 0
        for medicine in medicines_data:
            if self.insert_medicine_embedding(medicine):
                success_count += 1
            else:
                error_count += 1
        logger.info(
            f"Batch insert hoàn thành: {success_count} thành công, {error_count} lỗi"
        )
        return {"success": success_count, "error": error_count}
