from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import google.generativeai as genai
import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])

# Configure Gemini API with environment variable
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("Warning: GEMINI_API_KEY environment variable not set")

# Configure the Gemini API
genai.configure(api_key=API_KEY)

# Define models
class SymptomInput(BaseModel):
    symptoms: List[str]
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_history: Optional[str] = None
    additional_info: Optional[str] = None

class DiagnosisResponse(BaseModel):
    possible_conditions: List[str]
    recommendations: List[str]
    disclaimer: str

@router.post("/analyze", response_model=DiagnosisResponse)
async def analyze_symptoms(input_data: SymptomInput = Body(...)):
    """
    Analyze symptoms using Gemini LLM and provide possible diagnoses
    """
    if not API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    
    try:
        # Create prompt for Gemini
        prompt = f"""
        Bạn là một trợ lý y tế AI hỗ trợ phân tích triệu chứng ban đầu. Hãy phân tích thông tin sau:

        THÔNG TIN BỆNH NHÂN:
        - Triệu chứng: {', '.join(input_data.symptoms)}
        {f"- Tuổi: {input_data.age}" if input_data.age else ""}
        {f"- Giới tính: {input_data.gender}" if input_data.gender else ""}
        {f"- Tiền sử bệnh: {input_data.medical_history}" if input_data.medical_history else ""}
        {f"- Thông tin bổ sung: {input_data.additional_info}" if input_data.additional_info else ""}

        YÊU CẦU PHÂN TÍCH:
        1. TÌNH TRẠNG CÓ THỂ:
        Liệt kê tối đa 5 tình trạng y tế có thể liên quan đến các triệu chứng trên, xếp theo khả năng từ cao đến thấp.
        Mỗi tình trạng trình bày trên một dòng mới, bắt đầu bằng dấu gạch đầu dòng (-).

        2. ĐỀ XUẤT VÀ LỜI KHUYÊN:
        Cung cấp tối đa 5 đề xuất hữu ích cho bệnh nhân, bao gồm các lời khuyên về chăm sóc, theo dõi triệu chứng, và khi nào nên gặp bác sĩ.
        Mỗi đề xuất trình bày trên một dòng mới, bắt đầu bằng dấu gạch đầu dòng (-).

        3. MỨC ĐỘ NGHIÊM TRỌNG:
        Đánh giá mức độ nghiêm trọng của các triệu chứng theo thang điểm: Nhẹ, Trung bình, Nghiêm trọng, hoặc Cần chăm sóc y tế khẩn cấp.

        ĐỊNH DẠNG PHẢN HỒI:
        Trả lời chính xác theo cấu trúc sau để dễ xử lý:

        TÌNH TRẠNG CÓ THỂ:
        - [tình trạng 1]
        - [tình trạng 2]
        ...

        ĐỀ XUẤT VÀ LỜI KHUYÊN:
        - [đề xuất 1]
        - [đề xuất 2]
        ...

        MỨC ĐỘ NGHIÊM TRỌNG:
        [mức độ]

        Trả lời bằng tiếng Việt và KHÔNG thêm thông tin nào khác ngoài định dạng đã yêu cầu.
        """
        
        # Call Gemini API
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        response = model.generate_content(prompt)
        
        # Process the response to extract possible conditions and recommendations
        response_text = response.text
        
        # More robust parsing logic
        possible_conditions = []
        recommendations = []
        severity = "Không xác định"
        
        # Parse sections based on headers
        if "TÌNH TRẠNG CÓ THỂ:" in response_text:
            conditions_section = response_text.split("TÌNH TRẠNG CÓ THỂ:")[1].split("ĐỀ XUẤT VÀ LỜI KHUYÊN:")[0].strip()
            possible_conditions = [c.strip().lstrip('- ') for c in conditions_section.split('\n') if c.strip() and c.strip().startswith('-')]
        
        if "ĐỀ XUẤT VÀ LỜI KHUYÊN:" in response_text:
            if "MỨC ĐỘ NGHIÊM TRỌNG:" in response_text:
                recommendations_section = response_text.split("ĐỀ XUẤT VÀ LỜI KHUYÊN:")[1].split("MỨC ĐỘ NGHIÊM TRỌNG:")[0].strip()
            else:
                recommendations_section = response_text.split("ĐỀ XUẤT VÀ LỜI KHUYÊN:")[1].strip()
            recommendations = [r.strip().lstrip('- ') for r in recommendations_section.split('\n') if r.strip() and r.strip().startswith('-')]
        
        if "MỨC ĐỘ NGHIÊM TRỌNG:" in response_text:
            severity_section = response_text.split("MỨC ĐỘ NGHIÊM TRỌNG:")[1].strip()
            severity_lines = [line for line in severity_section.split('\n') if line.strip()]
            if severity_lines:
                severity = severity_lines[0].strip()
                # Add severity to recommendations
                recommendations.append(f"Mức độ nghiêm trọng: {severity}")
        
        # If parsing fails, use generic response
        if not possible_conditions:
            possible_conditions = ["Không thể xác định rõ dựa trên triệu chứng đã cung cấp"]
        if not recommendations:
            recommendations = ["Vui lòng tham khảo ý kiến bác sĩ để được chẩn đoán chính xác"]
            
        disclaimer = "Lưu ý: Đây chỉ là chẩn đoán sơ bộ dựa trên AI và không thay thế cho tư vấn y tế chuyên nghiệp. Vui lòng tham khảo ý kiến bác sĩ."
            
        return DiagnosisResponse(
            possible_conditions=possible_conditions,
            recommendations=recommendations,
            disclaimer=disclaimer
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}") 