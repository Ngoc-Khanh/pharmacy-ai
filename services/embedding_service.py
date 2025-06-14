import logging
from typing import Any, Dict, List

import cohere

from config.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.settings = Settings()
        if not self.settings.COHERE_API_KEY:
            raise ValueError("COHERE_API_KEY must be provided")
        self.client = cohere.ClientV2(self.settings.COHERE_API_KEY)
        self.model = self.settings.COHERE_EMBEDDING_MODEL
        self.dimension = self.settings.EMBEDDING_DIMENSION
        logger.info(
            f"Initialized EmbeddingService with model: {self.model} and dimension: {self.dimension}"
        )

    def create_medicine_text_for_embedding(
        self, medicine_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Tạo các text khác nhau cho embedding từ medicine data"""
        try:
            # Primary text - thông tin chính về thuốc
            primary_text = f"""
            Tên thuốc: {medicine_data.get("name", "")}
            Mô tả: {medicine_data.get("description", "")}
            Thành phần chính: {medicine_data.get("details", {}).get("ingredients", "")}
            Công dụng: {", ".join(medicine_data.get("details", {}).get("usage", []))}
            Xuất xứ: {medicine_data.get("details", {}).get("paramaters", {}).get("origin", "")}
            Đóng gói: {medicine_data.get("details", {}).get("paramaters", {}).get("packaging", "")}
            Giá: {medicine_data.get("variants", {}).get("price", 0)} VND
            """.strip()
            # Symptom text - tập trung vào triệu chứng và công dụng
            usage_list = medicine_data.get("details", {}).get("usage", [])
            symptom_text = f"""
            Thuốc điều trị: {", ".join(usage_list)}
            Hoạt chất: {medicine_data.get("details", {}).get("ingredients", "")}
            Tên sản phẩm: {medicine_data.get("name", "")}
            Mô tả công dụng: {medicine_data.get("description", "")}
            """.strip()
            # Usage text - hướng dẫn sử dụng
            dosage = medicine_data.get("usageguide", {}).get("dosage", {})
            directions = medicine_data.get("usageguide", {}).get("directions", [])
            usage_text = f"""
            Hướng dẫn sử dụng thuốc {medicine_data.get("name", "")}:
            Liều dùng người lớn: {dosage.get("adult", "")}
            Liều dùng trẻ em: {dosage.get("child", "")}
            Cách sử dụng: {", ".join(directions)}
            Thành phần: {medicine_data.get("details", {}).get("ingredients", "")}
            """.strip()
            # Safety text - thông tin an toàn
            precautions = medicine_data.get("usageguide", {}).get("precautions", [])
            safety_text = f"""
            Thông tin an toàn cho thuốc {medicine_data.get("name", "")}:
            Lưu ý và cảnh báo: {", ".join(precautions)}
            Thành phần cần chú ý: {medicine_data.get("details", {}).get("ingredients", "")}
            """.strip()
            return {
                "primary": primary_text,
                "symptom": symptom_text,
                "usage": usage_text,
                "safety": safety_text,
            }
        except Exception as e:
            logger.error(f"Error creating medicine text for embedding: {e}")
            # Return default texts if error occurs
            return {
                "primary": medicine_data.get("name", "")
                + " "
                + medicine_data.get("description", ""),
                "symptom": ", ".join(medicine_data.get("details", {}).get("usage", [])),
                "usage": medicine_data.get("name", ""),
                "safety": medicine_data.get("name", ""),
            }

    def embed_texts(self, texts: List[str], input_type: str = "search_document") -> List[List[float]]:
        """
        Tạo embeddings cho danh sách text sử dụng Cohere

        Args:
            texts: List of texts to embed
            input_type: Type of input for Cohere API
        """
        try:
            # Cohere API có giới hạn số lượng text per request
            batch_size = 96  # Cohere limit
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]
                response = self.client.embed(
                    texts=batch_texts,
                    model=self.model,
                    input_type=input_type,
                    embedding_types=["float"],
                )
                batch_embeddings = response.embeddings.float
                all_embeddings.extend(batch_embeddings)
                logger.info(
                    f"Embedded batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}"
                )
            return all_embeddings
        except Exception as e:
            logger.error(f"Error creating embeddings with Cohere: {e}")
            raise

    def embed_single_text(self, text: str, input_type: str = "search_query") -> List[float]:
        """
        Tạo embedding cho một text

        Args:
            text: Text to embed
            input_type: Type of input for Cohere API
        """
        try:
            response = self.client.embed(
                texts=[text],
                model=self.model,
                input_type=input_type,
                embedding_types=["float"],
            )
            return response.embeddings.float[0]
        except Exception as e:
            logger.error(f"Error creating single embedding with Cohere: {e}")
            raise

    def embed_query(self, query: str) -> List[float]:
        """Wrapper method for embedding search queries"""
        return self.embed_single_text(query, input_type="search_query")

    def embed_document(self, document: str) -> List[float]:
        """Wrapper method for embedding documents"""
        return self.embed_single_text(document, input_type="search_document")
