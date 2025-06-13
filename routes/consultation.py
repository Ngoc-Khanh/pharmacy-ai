from fastapi import APIRouter

from schemas.consultation import ConsultationRequest
from utils.http_response import json, validataion
from database.database import create_consultation as db_create_consultation

router = APIRouter()


@router.post("/diagnose", response_description="Consultation created")
async def create_consultation(consultation_request: ConsultationRequest):
    """
    Tạo consultation mới với phân tích AI từ triệu chứng
    """
    try:
        # Validate input
        if not consultation_request.symptoms.strip():
            return validataion(
                validation_errors=["Triệu chứng không được để trống"],
                message="Dữ liệu đầu vào không hợp lệ"
            )
        
        if consultation_request.patient_age and (consultation_request.patient_age < 0 or consultation_request.patient_age > 150):
            return validataion(
                validation_errors=["Tuổi phải từ 0 đến 150"],
                message="Dữ liệu đầu vào không hợp lệ"
            )
        
        consultation = await db_create_consultation(consultation_request)
        
        # Keep database storage format unchanged for internal use
        consultation_dict = {
            "id": str(consultation.id) if consultation.id else None,
            "user_id": consultation.user_id,
            "human": consultation.human.model_dump(),
            "ai": consultation.ai.model_dump(),
            "created_at": consultation.created_at,
            "updated_at": consultation.updated_at
        }
        
        # Create response format matching groq_diagnosis.py structure
        ai_data = consultation.ai.model_dump()
        response_data = {
            "primary_diagnosis": ai_data["primary_diagnosis"],
            "alternative_diagnoses": ai_data["alternative_diagnoses"],
            "general_advice": ai_data["general_advice"],
            "severity_level": ai_data["overall_severity_level"],
            "related_symptoms": ai_data.get("related_symptoms", []),  # Default to empty list if not present
            "recommended_actions": ai_data["recommended_actions"]
        }
        
        return json(
            data=response_data,
            message="Phân tích triệu chứng thành công",
            status=201
        )
    except Exception as e:
        print(f"Error creating consultation: {e}")
        return validataion(
            validation_errors=[f"Lỗi khi tạo consultation: {str(e)}"],
            message="Đã xảy ra lỗi trong quá trình xử lý"
        )
