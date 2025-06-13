from pydantic import BaseModel
from typing import Optional


class ConsultationRequest(BaseModel):
    user_id: str
    symptoms: str
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "112398",
                "symptoms": "Sốt và ho",
                "patient_age": 30,
                "patient_gender": "nam",
            }
        }
