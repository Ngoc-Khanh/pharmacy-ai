from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import google.generativeai as genai
import os
from typing import List, Optional

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
        Hãy phân tích các triệu chứng sau đây và đưa ra chẩn đoán y tế sơ bộ:
        
        Triệu chứng: {', '.join(input_data.symptoms)}
        
        {f"Tuổi: {input_data.age}" if input_data.age else ""}
        {f"Giới tính: {input_data.gender}" if input_data.gender else ""}
        {f"Tiền sử bệnh: {input_data.medical_history}" if input_data.medical_history else ""}
        {f"Thông tin bổ sung: {input_data.additional_info}" if input_data.additional_info else ""}
        
        Hãy đưa ra:
        1. Danh sách các tình trạng có thể xảy ra
        2. Đề xuất và lời khuyên sơ bộ
        
        Trả lời bằng tiếng Việt.
        """
        
        # Call Gemini API
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        response = model.generate_content(prompt)
        
        # Process the response to extract possible conditions and recommendations
        response_text = response.text
        
        # Simple parsing logic - this can be made more sophisticated
        possible_conditions = []
        recommendations = []
        
        # Very basic parsing - in production you would use more robust methods
        if "tình trạng có thể" in response_text.lower():
            sections = response_text.split("\n\n")
            for i, section in enumerate(sections):
                if "tình trạng có thể" in section.lower() and i+1 < len(sections):
                    condition_text = sections[i+1]
                    possible_conditions = [c.strip() for c in condition_text.split("\n") if c.strip()]
                if "đề xuất" in section.lower() or "lời khuyên" in section.lower() and i+1 < len(sections):
                    rec_text = sections[i+1]
                    recommendations = [r.strip() for r in rec_text.split("\n") if r.strip()]
        
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