import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Form, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.groq_service import GroqService
from app.models import SymptomRequest, DiagnosisResponse, HumanInput, AIResponse, consultation, SingleDiagnosis
from app.database import get_database
from app.utils.response import create_success_response, create_error_response, create_validation_error_response
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/groq", tags=["Groq Diagnosis"])

def get_groq_service():
    """Dependency để inject GroqService"""
    return GroqService()

async def get_db() -> AsyncIOMotorDatabase:
    """Dependency để lấy database connection"""
    return get_database()

async def _process_diagnosis(
    user_id: str,
    symptoms: str,
    patient_age: Optional[int],
    patient_gender: Optional[str],
    groq_service: GroqService,
    db: AsyncIOMotorDatabase
) -> DiagnosisResponse:
    """
    Xử lý chẩn đoán triệu chứng và lưu vào database với multiple diagnosis
    """
    try:
        logger.info(f"Processing multiple diagnosis for user {user_id}")
        
        # Gọi service để phân tích triệu chứng
        analysis_result, is_fallback = await groq_service.analyze_symptoms(
            symptoms=symptoms,
            patient_age=patient_age,
            patient_gender=patient_gender
        )
        
        if is_fallback:
            logger.warning("Received fallback response from Groq - not saving to database")
            # Vẫn trả về response nhưng không lưu vào database
        else:
            logger.info("Received real AI response from Groq - will save to database")
        
        # Tạo SingleDiagnosis objects
        primary_diagnosis = SingleDiagnosis(
            diagnosis_name=analysis_result["primary_diagnosis"]["diagnosis_name"],
            confidence_percentage=analysis_result["primary_diagnosis"]["confidence_percentage"],
            description=analysis_result["primary_diagnosis"]["description"],
            reasons=analysis_result["primary_diagnosis"]["reasons"]
        )
        
        alternative_diagnoses = [
            SingleDiagnosis(
                diagnosis_name=alt["diagnosis_name"],
                confidence_percentage=alt["confidence_percentage"],
                description=alt["description"],
                reasons=alt["reasons"]
            ) for alt in analysis_result["alternative_diagnoses"]
        ]
        
        # Tạo response object với cấu trúc mới
        diagnosis_response = DiagnosisResponse(
            primary_diagnosis=primary_diagnosis,
            alternative_diagnoses=alternative_diagnoses,
            general_advice=analysis_result["general_advice"],
            severity_level=analysis_result["overall_severity_level"],
            related_symptoms=analysis_result["related_symptoms"],
            recommended_actions=analysis_result["recommended_actions"]
        )
        
        # Chỉ lưu vào database nếu KHÔNG phải fallback response
        if not is_fallback:
            # Chuẩn bị dữ liệu để lưu vào database
            human_input = HumanInput(
                symptoms=symptoms,
                patient_age=patient_age,
                patient_gender=patient_gender
            )
            
            ai_response = AIResponse(
                primary_diagnosis=primary_diagnosis,
                alternative_diagnoses=alternative_diagnoses,
                general_advice=analysis_result["general_advice"],
                related_symptoms=analysis_result["related_symptoms"],
                overall_severity_level=analysis_result["overall_severity_level"],
                recommended_actions=analysis_result["recommended_actions"]
            )
            
            # Tạo consultation record
            consultation_record = consultation(
                user_id=user_id,
                human=human_input,
                ai=ai_response,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Lưu vào database
            try:
                consultation_collection = db.get_collection("consultation")
                result = await consultation_collection.insert_one(consultation_record.model_dump(by_alias=True))
                logger.info(f"Saved consultation to database with ID: {result.inserted_id}")
            except Exception as db_error:
                logger.error(f"Error saving to database: {db_error}")
                # Không raise error, chỉ log để response vẫn trả về
        else:
            logger.info("Skipping database save for fallback response")
        
        return diagnosis_response
        
    except Exception as e:
        logger.error(f"Error in _process_diagnosis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi trong quá trình chẩn đoán: {str(e)}"
        )

@router.post("/diagnose")
async def diagnose_symptoms(
    request: SymptomRequest,
    groq_service: GroqService = Depends(get_groq_service),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """
    API chẩn đoán triệu chứng sử dụng GroqCloud với Qwen (JSON payload)
    Trả về response theo định dạng chuẩn
    """
    try:
        # Validate input
        if not request.symptoms.strip():
            return create_validation_error_response(
                validation_errors=["Triệu chứng không được để trống"],
                message="Dữ liệu đầu vào không hợp lệ"
            )
        
        result = await _process_diagnosis(
            user_id=request.user_id,
            symptoms=request.symptoms,
            patient_age=request.patient_age,
            patient_gender=request.patient_gender,
            groq_service=groq_service,
            db=db
        )
        
        return create_success_response(
            data=result.model_dump(),
            message="Chẩn đoán triệu chứng thành công",
            status=200
        )
        
    except HTTPException as he:
        logger.error(f"HTTP Exception in diagnose_symptoms: {he.detail}")
        return create_error_response(
            message="Lỗi xử lý chẩn đoán",
            status=he.status_code,
            errors=str(he.detail)
        )
    except Exception as e:
        logger.error(f"Unexpected error in diagnose_symptoms: {e}")
        return create_error_response(
            message="Có lỗi không mong muốn xảy ra",
            status=500,
            errors=str(e)
        )

@router.post("/diagnose-form")
async def diagnose_symptoms_form(
    user_id: str = Form(..., description="ID của người dùng"),
    symptoms: str = Form(..., description="Triệu chứng người dùng nhập vào"),
    patient_age: Optional[int] = Form(None, description="Tuổi của bệnh nhân"),
    patient_gender: Optional[str] = Form(None, description="Giới tính của bệnh nhân"),
    groq_service: GroqService = Depends(get_groq_service),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """
    API chẩn đoán triệu chứng sử dụng GroqCloud với Qwen (Form data)
    Trả về response theo định dạng chuẩn
    """
    try:
        # Validate input
        if not symptoms.strip():
            return create_validation_error_response(
                validation_errors=["Triệu chứng không được để trống"],
                message="Dữ liệu đầu vào không hợp lệ"
            )
        
        result = await _process_diagnosis(
            user_id=user_id,
            symptoms=symptoms,
            patient_age=patient_age,
            patient_gender=patient_gender,
            groq_service=groq_service,
            db=db
        )
        
        return create_success_response(
            data=result.model_dump(),
            message="Chẩn đoán triệu chứng thành công (Form data)",
            status=200
        )
        
    except HTTPException as he:
        logger.error(f"HTTP Exception in diagnose_symptoms_form: {he.detail}")
        return create_error_response(
            message="Lỗi xử lý chẩn đoán",
            status=he.status_code,
            errors=str(he.detail)
        )
    except Exception as e:
        logger.error(f"Unexpected error in diagnose_symptoms_form: {e}")
        return create_error_response(
            message="Có lỗi không mong muốn xảy ra",
            status=500,
            errors=str(e)
        )

@router.post("/diagnose-universal")
async def diagnose_symptoms_universal(
    request: Request,
    user_id: Optional[str] = Form(None),
    symptoms: Optional[str] = Form(None),
    patient_age: Optional[int] = Form(None),
    patient_gender: Optional[str] = Form(None),
    groq_service: GroqService = Depends(get_groq_service),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """
    API chẩn đoán triệu chứng universal - tự động detect JSON hoặc Form data
    Trả về response theo định dạng chuẩn
    """
    try:
        content_type = request.headers.get("content-type", "").lower()
        
        # Nếu là JSON
        if "application/json" in content_type:
            try:
                json_data = await request.json()
                symptom_request = SymptomRequest(**json_data)
                
                if not symptom_request.symptoms.strip():
                    return create_validation_error_response(
                        validation_errors=["Triệu chứng không được để trống"],
                        message="Dữ liệu JSON không hợp lệ"
                    )
                
                result = await _process_diagnosis(
                    user_id=symptom_request.user_id,
                    symptoms=symptom_request.symptoms,
                    patient_age=symptom_request.patient_age,
                    patient_gender=symptom_request.patient_gender,
                    groq_service=groq_service,
                    db=db
                )
                
                return create_success_response(
                    data=result.model_dump(),
                    message="Chẩn đoán triệu chứng thành công (JSON)",
                    status=200
                )
                
            except Exception as json_error:
                logger.error(f"Error parsing JSON: {json_error}")
                return create_error_response(
                    message="Định dạng JSON không hợp lệ",
                    status=400,
                    errors=str(json_error)
                )
        
        # Nếu là form data
        elif any(ct in content_type for ct in ["application/x-www-form-urlencoded", "multipart/form-data"]):
            # Validate required fields
            if not user_id or not symptoms:
                return create_validation_error_response(
                    validation_errors=["user_id và symptoms là bắt buộc"],
                    message="Dữ liệu form không hợp lệ"
                )
            
            if not symptoms.strip():
                return create_validation_error_response(
                    validation_errors=["Triệu chứng không được để trống"],
                    message="Dữ liệu form không hợp lệ"
                )
            
            result = await _process_diagnosis(
                user_id=user_id,
                symptoms=symptoms,
                patient_age=patient_age,
                patient_gender=patient_gender,
                groq_service=groq_service,
                db=db
            )
            
            return create_success_response(
                data=result.model_dump(),
                message="Chẩn đoán triệu chứng thành công (Form data)",
                status=200
            )
        
        else:
            return create_error_response(
                message="Content-Type không được hỗ trợ",
                status=400,
                errors="Sử dụng application/json, application/x-www-form-urlencoded, hoặc multipart/form-data"
            )
            
    except HTTPException as he:
        logger.error(f"HTTP Exception in diagnose_symptoms_universal: {he.detail}")
        return create_error_response(
            message="Lỗi xử lý chẩn đoán",
            status=he.status_code,
            errors=str(he.detail)
        )
    except Exception as e:
        logger.error(f"Unexpected error in diagnose_symptoms_universal: {e}")
        return create_error_response(
            message="Có lỗi không mong muốn xảy ra",
            status=500,
            errors=str(e)
        )

@router.post("/diagnose-demo")
async def diagnose_symptoms_demo(
    request: SymptomRequest,
    groq_service: GroqService = Depends(get_groq_service),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """
    API chẩn đoán DEMO với 3 phiên bản chẩn đoán khác nhau
    Trả về response theo định dạng chuẩn với logging chi tiết
    """
    try:
        logger.info(f"Demo diagnosis request for user: {request.user_id}")
        logger.info(f"Symptoms: {request.symptoms}")
        
        # Validate input
        if not request.symptoms.strip():
            return create_validation_error_response(
                validation_errors=["Triệu chứng không được để trống"],
                message="Dữ liệu demo không hợp lệ"
            )
        
        result = await _process_diagnosis(
            user_id=request.user_id,
            symptoms=request.symptoms,
            patient_age=request.patient_age,
            patient_gender=request.patient_gender,
            groq_service=groq_service,
            db=db
        )
        
        # Log kết quả để demo
        logger.info("=== MULTIPLE DIAGNOSIS RESULTS ===")
        logger.info(f"Primary Diagnosis: {result.primary_diagnosis.diagnosis_name} ({result.primary_diagnosis.confidence_percentage}%)")
        for i, alt in enumerate(result.alternative_diagnoses, 1):
            logger.info(f"Alternative {i}: {alt.diagnosis_name} ({alt.confidence_percentage}%)")
        logger.info(f"Overall Severity: {result.severity_level}")
        logger.info(f"General Advice Count: {len(result.general_advice)}")
        logger.info(f"Recommended Actions Count: {len(result.recommended_actions)}")
        logger.info("=== END RESULTS ===")
        
        return create_success_response(
            data=result.model_dump(),
            message="Demo chẩn đoán multiple diagnosis thành công",
            status=200
        )
        
    except HTTPException as he:
        logger.error(f"HTTP Exception in diagnose_symptoms_demo: {he.detail}")
        return create_error_response(
            message="Lỗi demo chẩn đoán",
            status=he.status_code,
            errors=str(he.detail)
        )
    except Exception as e:
        logger.error(f"Unexpected error in diagnose_symptoms_demo: {e}")
        return create_error_response(
            message="Có lỗi không mong muốn trong demo",
            status=500,
            errors=str(e)
        )