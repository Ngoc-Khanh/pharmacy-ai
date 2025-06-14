from typing import List, Optional
from pydantic import BaseModel, Field


class MedicineRecommendationRequest(BaseModel):
    """Request schema cho đề xuất thuốc"""
    primary_diagnosis: str = Field(..., description="Chẩn đoán chính")
    alternative_diagnoses: Optional[List[str]] = Field(default=[], description="Các chẩn đoán thay thế")
    symptoms: str = Field(..., description="Triệu chứng của bệnh nhân")
    severity_level: Optional[str] = Field(default="medium", description="Mức độ nghiêm trọng")
    patient_age: Optional[int] = Field(default=None, description="Tuổi bệnh nhân")
    patient_gender: Optional[str] = Field(default=None, description="Giới tính bệnh nhân")
    limit: Optional[int] = Field(default=10, ge=1, le=50, description="Số lượng thuốc đề xuất tối đa")


class MedicineInfo(BaseModel):
    """Thông tin thuốc từ MongoDB"""
    id: str
    name: str
    slug: str
    description: str
    thumbnail: dict
    price: int
    original_price: int
    discount_percent: int
    stock_status: str
    rating: float
    review_count: int
    ingredients: str
    usage: List[str]
    dosage: dict
    directions: List[str]
    precautions: List[str]
    origin: str
    packaging: str
    is_active: bool
    is_featured: bool


class MedicineRecommendation(BaseModel):
    """Thông tin đề xuất thuốc với điểm số"""
    medicine: MedicineInfo
    similarity_score: float = Field(..., description="Điểm tương đồng (0-1)")
    recommendation_reason: str = Field(..., description="Lý do đề xuất")


class MedicineRecommendationResponse(BaseModel):
    """Response schema cho đề xuất thuốc"""
    recommendations: List[MedicineRecommendation]
    total_found: int
    search_query: str
    diagnosis_context: str 