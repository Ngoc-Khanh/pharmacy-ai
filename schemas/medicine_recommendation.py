from typing import Any, Dict, List

from pydantic import BaseModel

class ConsultationInfo(BaseModel):
    name: str
    confidence: float
    description: str

class MedicineRecommendationResponse(BaseModel):
    consultation_id: str
    consultation_info: Dict[str, Any]
    recommended_medicines: List[Dict[str, Any]]
    total_found: int
    search_query: str

class MedicineRecommendation(BaseModel):
    primary_diagnosis: str