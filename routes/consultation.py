from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient

from config.config import Settings
from database.database import create_consultation as db_create_consultation
from models.consultation import Consultation
from schemas.consultation import ConsultationRequest
from services.embedding_service import EmbeddingService
from utils.http_response import json, validation

router = APIRouter()


@router.post("/diagnose", response_description="Consultation created")
async def create_consultation(consultation_request: ConsultationRequest):
    """
    Tạo consultation mới với phân tích AI từ triệu chứng
    """
    try:
        # Validate input
        if not consultation_request.symptoms.strip():
            return validation(
                validation_errors=["Triệu chứng không được để trống"],
                message="Dữ liệu đầu vào không hợp lệ",
            )
        if consultation_request.patient_age and (
            consultation_request.patient_age < 0
            or consultation_request.patient_age > 150
        ):
            return validation(
                validation_errors=["Tuổi phải từ 0 đến 150"],
                message="Dữ liệu đầu vào không hợp lệ",
            )
        consultation = await db_create_consultation(consultation_request)
        # Create response format matching groq_diagnosis.py structure
        ai_data = consultation.ai.model_dump()
        response_data = {
            "consultation_id": str(consultation.id),  # Thêm ID của consultation
            "primary_diagnosis": ai_data["primary_diagnosis"],
            "alternative_diagnoses": ai_data["alternative_diagnoses"],
            "general_advice": ai_data["general_advice"],
            "severity_level": ai_data["overall_severity_level"],
            "related_symptoms": ai_data.get(
                "related_symptoms", []
            ),  # Default to empty list if not present
            "recommended_actions": ai_data["recommended_actions"],
        }
        return json(
            data=response_data, message="Phân tích triệu chứng thành công", status=201
        )
    except Exception as e:
        print(f"Error creating consultation: {e}")
        return validation(
            validation_errors=[f"Lỗi khi tạo consultation: {str(e)}"],
            message="Đã xảy ra lỗi trong quá trình xử lý",
        )


@router.get(
    "/recommend-medicines/{consultation_id}",
    response_description="Medicine recommendations based on consultation",
)
async def recommend_medicines_for_consultation(consultation_id: str, limit: int = 10):
    """
    Đề xuất thuốc dựa trên kết quả chẩn đoán từ consultation ID thông qua truy vấn RAG
    """
    try:
        # Lấy thông tin consultation từ database
        consultation = await Consultation.get(consultation_id)
        if not consultation:
            return validation(
                validation_errors=["Không tìm thấy consultation với ID này"],
                message="Consultation không tồn tại",
            )
        # Tạo query text từ thông tin chẩn đoán
        ai_data = consultation.ai
        query_parts = []
        # Thêm chẩn đoán chính
        primary_diagnosis = ai_data.primary_diagnosis
        query_parts.append(f"Điều trị {primary_diagnosis.diagnosis_name}")
        query_parts.append(f"Chữa {primary_diagnosis.diagnosis_name}")
        # Thêm triệu chứng
        query_parts.append(f"Triệu chứng: {consultation.human.symptoms}")
        # Thêm triệu chứng liên quan
        if ai_data.related_symptoms:
            query_parts.append(f"Triệu chứng liên quan: {', '.join(ai_data.related_symptoms)}")
        # Thêm chẩn đoán thay thế
        if ai_data.alternative_diagnoses:
            alt_diagnoses = [diag.diagnosis_name for diag in ai_data.alternative_diagnoses[:2]]  # Chỉ lấy 2 cái đầu
            query_parts.append(f"có thể điều trị {', '.join(alt_diagnoses)}")
        # Tạo query text hoàn chỉnh
        query_text = ". ".join(query_parts)
        # Khởi tạo embedding service và tìm kiếm thuốc
        embedding_service = EmbeddingService()
        rag_results = embedding_service.search_similar_medicines(query_text, limit)
        if not rag_results:
            return json(
                data=[],
                message="Không tìm thấy thuốc phù hợp",
                status=200,
            )
        # Lấy thông tin đầy đủ từ MongoDB
        medicine_ids = [result["medicine_id"] for result in rag_results]
        detailed_medicines = []
        for i, medicine_id in enumerate(medicine_ids):
            try:
                # Sử dụng MongoDB query trực tiếp thay vì Beanie model để tránh validation
                settings = Settings()
                client = AsyncIOMotorClient(settings.DATABASE_URL)
                db = client[settings.DATABASE_NAME]
                collection = db["medicines"]
                # Tìm thuốc bằng raw MongoDB query
                medicine_doc = await collection.find_one({"_id": medicine_id})
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
                    # Thêm thông tin similarity score từ RAG
                    medicine_doc["similarity_score"] = rag_results[i]["similarity_score"]
                    medicine_doc["rag_ranking"] = i + 1
                    detailed_medicines.append(medicine_doc)
            except Exception as e:
                print(f"Error fetching medicine {medicine_id}: {e}")
                continue
        response_data = {
            "consultation_id": consultation_id,
            "consultation_info": {
                "primary_diagnosis": {
                    "name": primary_diagnosis.diagnosis_name,
                    "confidence": primary_diagnosis.confidence_percentage,
                    "description": primary_diagnosis.description,
                },
                "symptoms": consultation.human.symptoms,
                "severity_level": ai_data.overall_severity_level,
            },
            "recommended_medicines": detailed_medicines,
            "total_found": len(detailed_medicines),
            "search_query": query_text,
        }
        return json(
            data=response_data,
            message=f"Tìm thấy {len(detailed_medicines)} thuốc phù hợp với chẩn đoán",
            status=200,
        )
    except Exception as e:
        print(f"Error in recommend_medicines_for_consultation: {e}")
        return validation(
            validation_errors=[f"Lỗi khi đề xuất thuốc: {str(e)}"],
            message="Đã xảy ra lỗi trong quá trình xử lý",
        )
