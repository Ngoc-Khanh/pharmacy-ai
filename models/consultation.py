from typing import List, Optional

from beanie import Document
from pydantic import BaseModel


class HumanData(BaseModel):
    symptoms: str
    patient_age: int
    patient_gender: str

class DiagnosisData(BaseModel):
    diagnosis_name: str
    confidence_percentage: float
    description: str
    reasons: List[str]

class AIData(BaseModel):
    primary_diagnosis: DiagnosisData
    alternative_diagnoses: List[DiagnosisData]
    general_advice: List[str]
    related_symptoms: List[str]
    overall_severity_level: str
    recommended_actions: List[str]

class Consultation(Document):
    user_id: str
    human: HumanData
    ai: AIData
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "68431c3cc1f7e38b780d0dc6",
                "human": {
                    "symptoms": "tôi bị điên",
                    "patient_age": 25.5,
                    "patient_gender": "nam"
                },
                "ai": {
                    "primary_diagnosis": {
                        "diagnosis_name": "Rối loạn tâm thần phân liệt",
                        "confidence_percentage": 80.0,
                        "description": "Tình trạng rối loạn nhận thức, cảm xúc và hành vi với các triệu chứng như ảo giác, hoang tưởng, mất liên hệ với thực tế.",
                        "reasons": [
                            "Triệu chứng 'bị điên' thường liên quan đến mất kiểm soát nhận thức",
                            "Tuổi 25 là thời điểm phổ biến khởi phát bệnh tâm thần phân liệt"
                        ]
                    },
                    "alternative_diagnoses": [],
                    "general_advice": ["Liên hệ ngay với chuyên gia tâm thần để được đánh giá đầy đủ"],
                    "related_symptoms": ["Nghe tiếng nói ảo giác", "Có ý nghĩ kỳ lạ không logic"],
                    "overall_severity_level": "nghiêm trọng",
                    "recommended_actions": ["Khám chuyên khoa tâm thần cấp cứu nếu có ý định tự hại"]
                }
            }
        }

    class Settings:
        name = "consultations"