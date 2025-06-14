from fastapi import APIRouter

from schemas.medicine_recommendation import (
    MedicineRecommendationRequest,
    MedicineRecommendationResponse,
)
from services.diagnosis_medicine_service import DiagnosisMedicineService
from utils.http_response import json, validataion

router = APIRouter()


@router.post(
    "/recommend", response_description="Medicine recommendations based on diagnosis"
)
async def recommend_medicines(recommendation_request: MedicineRecommendationRequest):
    """
    Đề xuất thuốc dựa trên kết quả chẩn đoán từ AI
    """
    try:
        # Validate input
        if not recommendation_request.primary_diagnosis.strip():
            return validataion(
                validation_errors=["Chẩn đoán chính không được để trống"],
                message="Dữ liệu đầu vào không hợp lệ",
            )

        if not recommendation_request.symptoms.strip():
            return validataion(
                validation_errors=["Triệu chứng không được để trống"],
                message="Dữ liệu đầu vào không hợp lệ",
            )

        if recommendation_request.patient_age and (
            recommendation_request.patient_age < 0
            or recommendation_request.patient_age > 150
        ):
            return validataion(
                validation_errors=["Tuổi phải từ 0 đến 150"],
                message="Dữ liệu đầu vào không hợp lệ",
            )

        # Initialize service
        diagnosis_service = DiagnosisMedicineService()

        # Get medicine recommendations from vector database
        vector_results = await diagnosis_service.recommend_medicines_by_diagnosis(
            primary_diagnosis=recommendation_request.primary_diagnosis,
            symptoms=recommendation_request.symptoms,
            alternative_diagnoses=recommendation_request.alternative_diagnoses,
            severity_level=recommendation_request.severity_level,
            patient_age=recommendation_request.patient_age,
            patient_gender=recommendation_request.patient_gender,
            limit=recommendation_request.limit,
        )

        # Format results with MongoDB data
        recommendations = await diagnosis_service.format_medicine_recommendations(
            vector_results=vector_results,
            primary_diagnosis=recommendation_request.primary_diagnosis,
            symptoms=recommendation_request.symptoms,
        )

        # Create search context
        search_query = f"{recommendation_request.primary_diagnosis} - {recommendation_request.symptoms}"
        diagnosis_context = f"Chẩn đoán: {recommendation_request.primary_diagnosis}"
        if recommendation_request.alternative_diagnoses:
            diagnosis_context += f" | Chẩn đoán thay thế: {', '.join(recommendation_request.alternative_diagnoses)}"

        # Create response
        response_data = MedicineRecommendationResponse(
            recommendations=recommendations,
            total_found=len(recommendations),
            search_query=search_query,
            diagnosis_context=diagnosis_context,
        )

        return json(
            data=response_data.dict(),
            message=f"Đề xuất {len(recommendations)} thuốc phù hợp với chẩn đoán",
            status=200,
        )

    except Exception as e:
        print(f"Error recommending medicines: {e}")
        return validataion(
            validation_errors=[f"Lỗi khi đề xuất thuốc: {str(e)}"],
            message="Đã xảy ra lỗi trong quá trình xử lý",
        )


@router.post(
    "/recommend-by-consultation-id/{consultation_id}",
    response_description="Medicine recommendations based on consultation ID",
)
async def recommend_medicines_by_consultation_id(consultation_id: str):
    """
    Đề xuất thuốc dựa trên consultation_id đã có sẵn
    """
    try:
        # Import here to avoid circular imports
        from models.consultation import Consultation

        # Get consultation data
        consultation = await Consultation.get(consultation_id)
        if not consultation:
            return validataion(
                validation_errors=["Không tìm thấy consultation với ID này"],
                message="Consultation không tồn tại",
            )

        # Extract data from consultation
        ai_data = consultation.ai
        human_data = consultation.human

        # Extract string values from DiagnosisData objects
        primary_diagnosis_str = ai_data.primary_diagnosis.diagnosis_name
        alternative_diagnoses_str = [
            diag.diagnosis_name for diag in ai_data.alternative_diagnoses
        ]

        # Create recommendation request from consultation data
        recommendation_request = MedicineRecommendationRequest(
            primary_diagnosis=primary_diagnosis_str,
            alternative_diagnoses=alternative_diagnoses_str,
            symptoms=human_data.symptoms,
            severity_level=ai_data.overall_severity_level,
            patient_age=human_data.patient_age if human_data.patient_age > 0 else None,
            patient_gender=human_data.patient_gender
            if human_data.patient_gender != "không xác định"
            else None,
            limit=10,
        )

        # Initialize service
        diagnosis_service = DiagnosisMedicineService()

        # Get medicine recommendations
        vector_results = await diagnosis_service.recommend_medicines_by_diagnosis(
            primary_diagnosis=recommendation_request.primary_diagnosis,
            symptoms=recommendation_request.symptoms,
            alternative_diagnoses=recommendation_request.alternative_diagnoses,
            severity_level=recommendation_request.severity_level,
            patient_age=recommendation_request.patient_age,
            patient_gender=recommendation_request.patient_gender,
            limit=recommendation_request.limit,
        )

        # Format results
        recommendations = await diagnosis_service.format_medicine_recommendations(
            vector_results=vector_results,
            primary_diagnosis=recommendation_request.primary_diagnosis,
            symptoms=recommendation_request.symptoms,
        )

        # Create response
        search_query = f"{primary_diagnosis_str} - {recommendation_request.symptoms}"
        diagnosis_context = f"Chẩn đoán: {primary_diagnosis_str}"
        if alternative_diagnoses_str:
            diagnosis_context += (
                f" | Chẩn đoán thay thế: {', '.join(alternative_diagnoses_str)}"
            )

        response_data = MedicineRecommendationResponse(
            recommendations=recommendations,
            total_found=len(recommendations),
            search_query=search_query,
            diagnosis_context=diagnosis_context,
        )

        return json(
            data=response_data.dict(),
            message=f"Đề xuất {len(recommendations)} thuốc dựa trên consultation",
            status=200,
        )

    except Exception as e:
        print(f"Error recommending medicines by consultation ID: {e}")
        return validataion(
            validation_errors=[f"Lỗi khi đề xuất thuốc: {str(e)}"],
            message="Đã xảy ra lỗi trong quá trình xử lý",
        )


@router.get("/similar/{medicine_id}", response_description="Get similar medicines")
async def get_similar_medicines(medicine_id: str, limit: int = 5):
    """
    Lấy danh sách thuốc tương tự dựa trên medicine_id
    """
    try:
        # Initialize service
        diagnosis_service = DiagnosisMedicineService()

        # Get similar medicines from vector database
        similar_results = (
            await diagnosis_service.medicine_service.get_similar_medicines(
                medicine_id=medicine_id, limit=limit
            )
        )

        if not similar_results:
            return json(data=[], message="Không tìm thấy thuốc tương tự", status=200)

        # Format results with MongoDB data
        recommendations = await diagnosis_service.format_medicine_recommendations(
            vector_results=similar_results,
            primary_diagnosis="Thuốc tương tự",
            symptoms="Dựa trên thành phần và công dụng",
        )

        response_data = {
            "similar_medicines": [rec.dict() for rec in recommendations],
            "total_found": len(recommendations),
            "reference_medicine_id": medicine_id,
        }

        return json(
            data=response_data,
            message=f"Tìm thấy {len(recommendations)} thuốc tương tự",
            status=200,
        )

    except Exception as e:
        print(f"Error getting similar medicines: {e}")
        return validataion(
            validation_errors=[f"Lỗi khi tìm thuốc tương tự: {str(e)}"],
            message="Đã xảy ra lỗi trong quá trình xử lý",
        )


@router.get("/debug/mongodb", response_description="Debug MongoDB connection and data")
async def debug_mongodb():
    """
    Debug endpoint để kiểm tra kết nối MongoDB và format dữ liệu
    """
    try:
        diagnosis_service = DiagnosisMedicineService()
        debug_info = await diagnosis_service.debug_mongodb_connection()

        return json(data=debug_info, message="Debug thông tin MongoDB", status=200)

    except Exception as e:
        print(f"Error debugging MongoDB: {e}")
        return validataion(
            validation_errors=[f"Lỗi debug MongoDB: {str(e)}"],
            message="Đã xảy ra lỗi trong quá trình debug",
        )
