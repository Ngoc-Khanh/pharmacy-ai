from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)
from typing import List, Dict, Optional
import json
import logging
from config.config import Settings

logger = logging.getLogger(__name__)


class MilvusService:
    def __init__(self):
        self.settings = Settings()
        self.collection_name = self.settings.MILVUS_COLLECTION_NAME
        self.dimension = self.settings.EMBEDDING_DIMENSION
        self.collection = None
        self.connect()

    def connect(self):
        """Kết nối tới Milvus Cloud"""
        try:
            if not self.settings.MILVUS_URI or not self.settings.MILVUS_TOKEN:
                raise ValueError("Milvus URI and TOKEN must be provided")
            connections.connect(
                alias="default",
                uri=self.settings.MILVUS_URI,
                token=self.settings.MILVUS_TOKEN,
            )
            logger.info("Connected to Milvus Cloud successfully!")
            # Initialize collection if exists
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                self.collection.load()
                logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def create_collection(self) -> Collection:
        """Tạo collection cho medicine embeddings"""
        try:
            # Define schema
            fields = [
                FieldSchema(
                    name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True
                ),
                FieldSchema(name="medicine_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="slug", dtype=DataType.VARCHAR, max_length=200),
                # Embeddings
                FieldSchema(
                    name="primary_embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.dimension,
                ),
                FieldSchema(
                    name="symptom_embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.dimension,
                ),
                FieldSchema(
                    name="usage_embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.dimension,
                ),
                FieldSchema(
                    name="safety_embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.dimension,
                ),
                # Metadata for filtering
                FieldSchema(name="category_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="supplier_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(
                    name="active_ingredient", dtype=DataType.VARCHAR, max_length=500
                ),
                FieldSchema(name="price", dtype=DataType.INT64),
                FieldSchema(name="stock_status", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="is_featured", dtype=DataType.BOOL),
                FieldSchema(name="is_active", dtype=DataType.BOOL),
                FieldSchema(name="rating", dtype=DataType.FLOAT),
                # JSON fields for complex data
                FieldSchema(
                    name="therapeutic_uses", dtype=DataType.VARCHAR, max_length=2000
                ),
                FieldSchema(
                    name="contraindications", dtype=DataType.VARCHAR, max_length=2000
                ),
                FieldSchema(
                    name="dosage_info", dtype=DataType.VARCHAR, max_length=1000
                ),
            ]

            schema = CollectionSchema(fields, "Medicine embeddings collection for RAG")

            # Drop existing collection if exists
            if utility.has_collection(self.collection_name):
                utility.drop_collection(self.collection_name)
                logger.info(f"Dropped existing collection: {self.collection_name}")

            # Create collection
            collection = Collection(self.collection_name, schema)
            logger.info(f"Created collection: {self.collection_name}")

            # Create indexes
            self._create_indexes(collection)

            self.collection = collection
            return collection

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    def _create_indexes(self, collection: Collection):
        """Tạo indexes cho vector search"""
        try:
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
            }

            # Index cho các embedding vectors
            collection.create_index("primary_embedding", index_params)
            collection.create_index("symptom_embedding", index_params)
            collection.create_index("usage_embedding", index_params)
            collection.create_index("safety_embedding", index_params)

            logger.info("Created vector indexes")

            # Load collection vào memory
            collection.load()
            logger.info("Collection loaded into memory")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise

    def search_medicines(
        self,
        query_embedding: List[float],
        search_type: str = "primary",
        limit: int = 10,
        filters: Optional[str] = None,
    ) -> List[Dict]:
        """Tìm kiếm thuốc dựa trên embedding"""
        try:
            if not self.collection:
                raise ValueError("Collection not initialized")

            # Chọn field embedding phù hợp
            embedding_field = f"{search_type}_embedding"

            # Search parameters
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

            # Output fields
            output_fields = [
                "medicine_id",
                "name",
                "slug",
                "active_ingredient",
                "price",
                "rating",
                "stock_status",
                "is_active",
                "therapeutic_uses",
                "contraindications",
                "dosage_info",
            ]

            # Thực hiện search
            results = self.collection.search(
                data=[query_embedding],
                anns_field=embedding_field,
                param=search_params,
                limit=limit,
                output_fields=output_fields,
                expr=filters,  # Filter expression
            )

            # Format results
            formatted_results = []
            for hit in results[0]:
                # Helper function to safely parse JSON
                def safe_json_parse(data, default):
                    try:
                        if isinstance(data, str):
                            return json.loads(data)
                        return data if data is not None else default
                    except (json.JSONDecodeError, TypeError):
                        return default
                
                result_data = {
                    "medicine_id": hit.entity.medicine_id,
                    "name": hit.entity.name,
                    "slug": hit.entity.slug,
                    "active_ingredient": hit.entity.active_ingredient,
                    "price": hit.entity.price,
                    "rating": hit.entity.rating,
                    "stock_status": hit.entity.stock_status,
                    "is_active": hit.entity.is_active,
                    "therapeutic_uses": safe_json_parse(hit.entity.therapeutic_uses, []),
                    "contraindications": safe_json_parse(hit.entity.contraindications, []),
                    "dosage_info": safe_json_parse(hit.entity.dosage_info, {}),
                    "similarity_score": hit.score,
                }
                formatted_results.append(result_data)

            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
