from uuid import UUID
from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient

from config.config import Settings
from services.embedding_service import EmbeddingService
from utils.http_response import json, validation

router = APIRouter()

@router.get("/{medicine_id}/embedding-status", response_description="Check embedding status")
async def get_embedding_status(medicine_id: str):
    """
    Kiểm tra trạng thái embedding của thuốc trong vector database
    """
    try:
        # Validate UUID format
        try:
            from uuid import UUID
            UUID(medicine_id)
        except ValueError:
            return validation(
                validation_errors=["ID thuốc không đúng định dạng UUID"],
                message="Dữ liệu đầu vào không hợp lệ",
            )
        # Kiểm tra trong vector database
        embedding_service = EmbeddingService()
        check_result = embedding_service.check_medicine_embedding_exists(medicine_id)
        if "error" in check_result:
            return validation(
                validation_errors=[f"Lỗi khi kiểm tra: {check_result['error']}"],
                message="Không thể kiểm tra trạng thái embedding",
            )
        response_data = {
            "medicine_id": medicine_id,
            "embedding_exists": check_result.get("exists", False),
            "medicine_info": {
                "name": check_result.get("name", ""),
                "description": check_result.get("description", ""),
                "vector_id": check_result.get("vector_id", "")
            } if check_result.get("exists", False) else None,
            "status": "embedded" if check_result.get("exists") else "not_embedded"
        }
        return json(
            data=response_data,
            message="Kiểm tra trạng thái embedding thành công",
            status=200
        )
    except Exception as e:
        print(f"Error checking embedding status for {medicine_id}: {e}")
        return validation(
            validation_errors=[f"Lỗi khi kiểm tra trạng thái: {str(e)}"],
            message="Đã xảy ra lỗi trong quá trình xử lý",
        )

@router.post("/{medicine_id}/embed-medicine", response_description="Medicine embedded to vector database")
async def embed_medicine_by_id(medicine_id: str):
    """
    Nhận ID thuốc từ Laravel, lấy dữ liệu từ MongoDB và embedding lên vector database
    """
    try:
        # Validate UUID format
        try:
            UUID(medicine_id)
        except ValueError:
            return validation(
                validation_errors=["ID thuốc không không đúng định dạng UUID"],
                message="Dữ liệu đầu vào không hợp lệ",
            )
        # Kết nối MongoDB và lấy thông tin thuốc
        settings = Settings()
        client = AsyncIOMotorClient(settings.DATABASE_URL)
        db = client[settings.DATABASE_NAME]
        collection = db["medicines"]
        # Tìm thuốc bằng ID
        medicine_doc = await collection.find_one({"_id": medicine_id})
        if not medicine_doc:
            return validation(
                validation_errors=["Không tìm thấy ID thuốc trong cơ sở dữ liệu"],
                message="Thuốc không tồn tại",
            )
        # Chuyển đổi _id thành string để embedding service xử lý
        medicine_doc["_id"] = str(medicine_doc["_id"])
        # Khởi tạo embedding service
        embedding_service = EmbeddingService()
        # Kiểm tra xem thuốc đã được embedding chưa
        existing_results = embedding_service.search_similar_medicines(
            medicine_doc.get("name", ""), limit=1
        )
        # Nếu đã tồn tại (similarity score rất cao), cập nhập
        should_update = False
        if existing_results:
            for result in existing_results:
                if (
                    result["medicine_id"] == medicine_id
                    and result["similarity_score"] > 0.99
                ):
                    should_update = True
                    break
        # Thực hiện embedding
        success = embedding_service.insert_medicine_embedding(medicine_doc)
        if success:
            action = "Cập nhật" if should_update else "Thêm mới"
            response_data = {
                "medicine_id": medicine_id,
                "medicine_name": medicine_doc.get("name", ""),
                "action": action,
                "embedding_status": "success",
                "message": f"{action} embedding thành công",
            }
            return json(
                data=response_data,
                message=f"{action} embedding thuốc thành công",
                status=201 if not should_update else 200,
            )
        else:
            return validation(
                validation_errors=["Không thể thực hiện embedding thuốc"],
                message="Lỗi khi embedding thuốc vào vector database",
            )
    except Exception as e:
        print(f"Error embedding medicine {medicine_id}: {e}")
        return validation(
            validation_errors=[f"Lỗi khi embedding thuốc: {str(e)}"],
            message="Đã xảy ra lỗi trong quá trình xử lý",
        )

@router.delete("/{medicine_id}/delete-medicine", response_description="Delete medicine from vector database")
async def delete_medicine_embedding(medicine_id: str):
    """
    Xóa embedding của thuốc khỏi vector database
    """
    try:
        # Validate UUID format
        try:
            UUID(medicine_id)
        except ValueError:
            return validation(
                validation_errors=["ID thuốc không đúng định dạng UUID"],
                message="Dữ liệu đầu vào không hợp lệ",
            )
        # Khởi tạo embedding service
        embedding_service = EmbeddingService()
        # Kiểm tra xem embedding có tồn tại không
        check_result = embedding_service.check_medicine_embedding_exists(medicine_id)
        if not check_result.get("exists", False):
            return validation(
                validation_errors=["Không tìm thấy embedding cho thuốc này"],
                message="Embedding không tồn tại trong vector database",
            )
        # Thực hiện xóa embedding
        success = embedding_service.delete_medicine_embedding(medicine_id)
        if success:
            response_data = {
                "medicine_id": medicine_id,
                "medicine_name": check_result.get("name", ""),
                "action": "deleted",
                "status": "success"
            }
            return json(
                data=response_data,
                message="Xóa embedding thuốc thành công",
                status=200
            )
        else:
            return validation(
                validation_errors=["Không thể xóa embedding"],
                message="Lỗi khi xóa embedding khỏi vector database",
            )
    except Exception as e:
        print(f"Error deleting medicine embedding {medicine_id}: {e}")
        return validation(
            validation_errors=[f"Lỗi khi xóa embedding: {str(e)}"],
            message="Đã xảy ra lỗi trong quá trình xử lý",
        )