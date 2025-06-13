from datetime import datetime

from models.consultation import AIData, Consultation, HumanData
from schemas.consultation import ConsultationRequest
from services.groq_service import GroqService

consultation_collection = Consultation


async def create_consultation(consultation_data: ConsultationRequest) -> Consultation:
    """Tạo consultation mới với phân tích AI"""
    groq_service = GroqService()
    ai_result, is_fallback = groq_service.analyze_symptoms(
        symptoms=consultation_data.symptoms,
        patient_age=consultation_data.patient_age,
        patient_gender=consultation_data.patient_gender,
    )
    human_data = HumanData(
        symptoms=consultation_data.symptoms,
        patient_age=consultation_data.patient_age or 0,
        patient_gender=consultation_data.patient_gender or "không xác định",
    )
    ai_data = AIData(**ai_result)
    consultation = Consultation(
        user_id=consultation_data.user_id,  # Sửa: Không cần PydanticObjectId
        human=human_data,  # Sửa: field name trong model
        ai=ai_data,  # Sửa: field name trong model
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    await consultation.create()
    return consultation