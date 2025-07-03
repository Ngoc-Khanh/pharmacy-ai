from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient

from config.config import Settings
from services.embedding_service import EmbeddingService
from utils.http_response import json, validation

router = APIRouter()

@router.get("/{medicine_id}/simmilar-medicines", response_description="Get similar medicines based on medicine ID")
async def get_simmilar_medicines(medicine_id: str, limit: int = 4):
    """
    Lấy top sản phẩm tương tự dựa trên ID sản phẩm
    """
    try:
        # Lấy thông tin chi tiết thuốc gốc từ MongoDB
        settings = Settings()
        client = AsyncIOMotorClient(settings.DATABASE_URL)
        db = client[settings.DATABASE_NAME]
        collection = db["medicines"]
        # Tìm thuốc gốc
        original_medicine = await collection.find_one({"_id": medicine_id})
        if not original_medicine:
            return validation(
                validation_errors=["Không tìm thấy thuốc với ID này"],
                message="Thuốc không tồn tại",
            )
        # Khởi tạo embedding service
        embedding_service = EmbeddingService()
        # Tạo query text từ thông tin thuốc gốc để tìm sản phẩm tương tự
        query_parts = []
        # Thêm tên thuốc (để tìm thuốc cùng loại)
        query_parts.append(f"Thuốc: {original_medicine.get('name', '')}")
        # Thêm mô tả
        query_parts.append(f"Mô tả: {original_medicine.get('description', '')}")
        # Thêm thông tin chi tiết nếu có
        if "details" in original_medicine:
            details = original_medicine["details"]
            if "ingredients" in details:
                query_parts.append(f"Thành phần: {details['ingredients']}")
            if "usage" in details and isinstance(details["usage"], list):
                usage_text = ', '.join(details['usage'])
                query_parts.append(f"Công dụng: {usage_text}")
                query_parts.append(f"Điều trị: {usage_text}")
        # Thêm danh mục để tìm thuốc cùng danh mục
        if "category_id" in original_medicine:
            query_parts.append(f"Danh mục: {original_medicine['category_id']}")
        # Tạo query text hoàn chỉnh
        query_text = ". ".join(query_parts)
        # Tìm kiếm thuốc tương tự (lấy nhiều hơn để có thể lọc)
        similar_results = embedding_service.search_similar_medicines(query_text, limit + 5)
        if not similar_results:
            return json(
                data={
                    "original_medicine": {
                        "id": str(original_medicine["_id"]),
                        "name": original_medicine.get("name", ""),
                        "description": original_medicine.get("description", "")
                    },
                    "similar_medicines": [],
                    "total_found": 0
                },
                message="Không tìm thấy thuốc tương tự",
                status=200,
            )
        # Lọc bỏ thuốc gốc khỏi kết quả và lấy thông tin chi tiết
        filtered_results = []
        for result in similar_results:
            # Bỏ qua thuốc gốc
            if result["medicine_id"] == medicine_id:
                continue
            # Lấy thông tin đầy đủ từ MongoDB
            try:
                medicine_doc = await collection.find_one({"_id": result["medicine_id"]})
                if medicine_doc:
                    # Xử lý UUID serialization
                    if "_id" in medicine_doc:
                        medicine_doc["id"] = str(medicine_doc["_id"])
                        del medicine_doc["_id"]
                    # Xử lý các UUID fields khác
                    for field, value in medicine_doc.items():
                        if hasattr(value, "hex"):  # Check if it's a UUID
                            medicine_doc[field] = str(value)
                    # Xử lý datetime fields
                    if "created_at" in medicine_doc and hasattr(medicine_doc["created_at"], "isoformat"):
                        medicine_doc["created_at"] = medicine_doc["created_at"].isoformat()
                    if "updated_at" in medicine_doc and hasattr(medicine_doc["updated_at"], "isoformat"):
                        medicine_doc["updated_at"] = medicine_doc["updated_at"].isoformat()
                    # Thêm thông tin similarity score
                    medicine_doc["similarity_score"] = result["similarity_score"]
                    medicine_doc["similarity_ranking"] = len(filtered_results) + 1
                    filtered_results.append(medicine_doc)
                    # Đủ số lượng yêu cầu thì dừng
                    if len(filtered_results) >= limit:
                        break
            except Exception as e:
                print(f"Error fetching similar medicine {result['medicine_id']}: {e}")
                continue
        # Chuẩn bị thông tin thuốc gốc
        original_medicine_info = {
            "id": str(original_medicine["_id"]),
            "name": original_medicine.get("name", ""),
            "description": original_medicine.get("description", ""),
            "category_id": original_medicine.get("category_id", ""),
            "thumbnail": original_medicine.get("thumbnail", {}),
            "variants": original_medicine.get("variants", {})
        }
        response_data = {
            "original_medicine": original_medicine_info,
            "similar_medicines": filtered_results,
            "total_found": len(filtered_results),
            "search_strategy": "embedding_similarity",
            "query_used": query_text
        }
        return json(
            data=response_data,
            message=f"Tìm thấy {len(filtered_results)} sản phẩm tương tự",
            status=200,
        )
    except Exception as e:
        print(f"Error in get_similar_medicines: {e}")
        return validation(
            validation_errors=[f"Lỗi khi tìm sản phẩm tương tự: {str(e)}"],
            message="Đã xảy ra lỗi trong quá trình xử lý",
        )