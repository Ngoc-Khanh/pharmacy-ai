from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Generic, TypeVar, Union
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema

# Generic type for data
T = TypeVar('T')

# Standard API Response wrapper
class APIResponse(BaseModel, Generic[T]):
    data: Optional[Union[T, List[T]]] = Field(None, description="Dữ liệu response")
    message: str = Field(..., description="Thông điệp mô tả kết quả")
    status: int = Field(..., description="Mã trạng thái HTTP")
    locale: str = Field(default="vi", description="Ngôn ngữ response")
    errors: Optional[str] = Field(None, description="Thông tin lỗi nếu có")

# Success response helper
class SuccessResponse(APIResponse[T], Generic[T]):
    status: int = Field(default=200, description="Mã trạng thái thành công")
    errors: Optional[str] = Field(default=None, description="Không có lỗi")

# Error response helper  
class ErrorResponse(APIResponse[None]):
    data: Optional[None] = Field(default=None, description="Không có dữ liệu khi lỗi")
    status: int = Field(..., description="Mã trạng thái lỗi")
    errors: str = Field(..., description="Chi tiết lỗi")

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type, handler
    ):
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

class MongoBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

# Request model cho triệu chứng đầu vào
class SymptomRequest(BaseModel):
    user_id: str = Field(..., description="ID của người dùng")
    symptoms: str = Field(..., description="Triệu chứng người dùng nhập vào")
    patient_age: Optional[int] = Field(None, description="Tuổi của bệnh nhân")
    patient_gender: Optional[str] = Field(None, description="Giới tính của bệnh nhân")

# Model cho một chẩn đoán đơn lẻ
class SingleDiagnosis(BaseModel):
    diagnosis_name: str = Field(..., description="Tên chẩn đoán")
    confidence_percentage: int = Field(..., description="Độ tin cậy (phần trăm)")
    description: str = Field(..., description="Mô tả chi tiết về chẩn đoán")
    reasons: List[str] = Field(..., description="Lý do dẫn đến chẩn đoán này")

# Model cho phần human trong consultation
class HumanInput(BaseModel):
    symptoms: str = Field(..., description="Triệu chứng")
    patient_age: Optional[int] = Field(None, description="Tuổi bệnh nhân")
    patient_gender: Optional[str] = Field(None, description="Giới tính bệnh nhân")

class AIResponse(BaseModel):
    primary_diagnosis: SingleDiagnosis = Field(..., description="Chẩn đoán chính (khả năng cao nhất)")
    alternative_diagnoses: List[SingleDiagnosis] = Field(..., description="2 chẩn đoán thay thế")
    general_advice: List[str] = Field(..., description="Lời khuyên chung")
    related_symptoms: List[str] = Field(..., description="Triệu chứng liên quan")
    overall_severity_level: str = Field(..., description="Mức độ nghiêm trọng tổng thể")
    recommended_actions: List[str] = Field(..., description="Hành động được khuyến nghị")

# Response model cho API - tương thích ngược
class DiagnosisResponse(BaseModel):
    primary_diagnosis: SingleDiagnosis = Field(..., description="Chẩn đoán chính")
    alternative_diagnoses: List[SingleDiagnosis] = Field(..., description="2 chẩn đoán thay thế")
    general_advice: List[str] = Field(..., description="Lời khuyên chung")
    severity_level: str = Field(..., description="Mức độ nghiêm trọng")
    related_symptoms: List[str] = Field(..., description="Triệu chứng liên quan")
    recommended_actions: List[str] = Field(..., description="Hành động được khuyến nghị")
    
    # Backward compatibility properties
    @property
    def confidence_percentage(self) -> int:
        return self.primary_diagnosis.confidence_percentage
    
    @property
    def diagnosis(self) -> str:
        return self.primary_diagnosis.diagnosis_name
    
    @property
    def advice(self) -> List[str]:
        return self.general_advice[:3]  # Trả về 3 lời khuyên đầu

# Model chính lưu vào MongoDB collection "Consultation"
class consultation(MongoBaseModel):
    user_id: str = Field(..., description="ID của người dùng")
    human: HumanInput = Field(..., description="Input từ người dùng")
    ai: AIResponse = Field(..., description="Response từ AI")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)