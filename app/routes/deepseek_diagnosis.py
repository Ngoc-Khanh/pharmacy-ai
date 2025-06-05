from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from huggingface_hub import InferenceClient
import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deepseek-diagnosis", tags=["deepseek-diagnosis"])

# Configure API with environment variable
API_KEY = os.environ.get("HUGGING_FACE_API_KEY")
if not API_KEY:
  logger.warning("HUGGING_FACE_API_KEY environment variable not set")
  print("Warning: HUGGING_FACE_API_KEY environment variable not set")

# Create InferenceClient instance
client = InferenceClient(provider="novita", api_key=API_KEY)

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
async def analyze_symptoms_deepseek(input_data: SymptomInput = Body(...)):
  """
  Analyze symptoms using DeepSeek LLM and provide possible diagnoses
  """
  logger.info(f"Starting symptom analysis for symptoms: {input_data.symptoms}")
  logger.info(f"Patient info - Age: {input_data.age}, Gender: {input_data.gender}")
  
  if not API_KEY:
    logger.error("HUGGING_FACE_API_KEY not configured")
    raise HTTPException(status_code=500, detail="HUGGING_FACE_API_KEY not configured")
  
  try:
    # Create prompt for DeepSeek
    prompt = f"""
    Bạn là một chuyên gia y tế AI với chuyên môn sâu về chẩn đoán và phân tích triệu chứng. Hãy thực hiện phân tích toàn diện và chi tiết thông tin bệnh nhân sau:

    THÔNG TIN CHI TIẾT BỆNH NHÂN:
    - Các triệu chứng hiện tại: {', '.join(input_data.symptoms)}
    {f"- Độ tuổi: {input_data.age} tuổi" if input_data.age else ""}
    {f"- Giới tính: {input_data.gender}" if input_data.gender else ""}
    {f"- Tiền sử bệnh lý: {input_data.medical_history}" if input_data.medical_history else ""}
    {f"- Thông tin bổ sung và chi tiết khác: {input_data.additional_info}" if input_data.additional_info else ""}

    YÊU CẦU PHÂN TÍCH CHI TIẾT:

    1. TÌNH TRẠNG CÓ THỂ:
    Phân tích và liệt kê tối đa 5 tình trạng bệnh lý có khả năng cao nhất dựa trên các triệu chứng đã cung cấp. 
    Sắp xếp theo thứ tự từ khả năng cao nhất đến thấp nhất.
    Đối với mỗi tình trạng, hãy giải thích ngắn gọn lý do tại sao triệu chứng phù hợp với chẩn đoán này.
    Định dạng: Mỗi tình trạng trên một dòng riêng, bắt đầu bằng dấu gạch ngang (-).

    2. ĐỀ XUẤT VÀ LỜI KHUYÊN CHI TIẾT:
    Cung cấp tối đa 7 lời khuyên thực tế và hữu ích, bao gồm:
    - Các biện pháp chăm sóc tại nhà an toàn và hiệu quả
    - Cách theo dõi và ghi chép sự thay đổi của triệu chứng
    - Những dấu hiệu cảnh báo cần chú ý đặc biệt
    - Thời điểm thích hợp để tìm kiếm sự trợ giúp y tế chuyên nghiệp
    - Các biện pháp phòng ngừa và duy trì sức khỏe
    - Lời khuyên về chế độ ăn uống và sinh hoạt phù hợp
    - Những việc cần tránh để không làm trầm trọng thêm tình trạng
    Định dạng: Mỗi lời khuyên trên một dòng riêng, bắt đầu bằng dấu gạch ngang (-).

    3. MỨC ĐỘ NGHIÊM TRỌNG VÀ ĐÁNH GIÁ:
    Đưa ra đánh giá chi tiết về mức độ nghiêm trọng của tình trạng hiện tại:
    - Nhẹ: Có thể tự chăm sóc tại nhà, theo dõi trong vài ngày
    - Trung bình: Nên tham khảo ý kiến bác sĩ trong 1-2 ngày tới
    - Nghiêm trọng: Cần gặp bác sĩ trong ngày hoặc đến cơ sở y tế
    - Cấp cứu: Cần chăm sóc y tế khẩn cấp ngay lập tức
    Kèm theo giải thích ngắn gọn về lý do đánh giá này.

    ĐỊNH DẠNG PHẢN HỒI BẮT BUỘC:
    Vui lòng trả lời chính xác theo cấu trúc sau để hệ thống có thể xử lý:

    TÌNH TRẠNG CÓ THỂ:
    - [Tên bệnh/tình trạng 1]: [Giải thích ngắn gọn về mối liên hệ với triệu chứng]
    - [Tên bệnh/tình trạng 2]: [Giải thích ngắn gọn về mối liên hệ với triệu chứng]
    - [Tên bệnh/tình trạng 3]: [Giải thích ngắn gọn về mối liên hệ với triệu chứng]
    - [Tên bệnh/tình trạng 4]: [Giải thích ngắn gọn về mối liên hệ với triệu chứng]
    - [Tên bệnh/tình trạng 5]: [Giải thích ngắn gọn về mối liên hệ với triệu chứng]

    ĐỀ XUẤT VÀ LỜI KHUYÊN:
    - [Lời khuyên chi tiết về chăm sóc tại nhà]
    - [Hướng dẫn theo dõi triệu chứng cụ thể]
    - [Các dấu hiệu cảnh báo cần lưu ý]
    - [Thời điểm nên gặp bác sĩ]
    - [Biện pháp phòng ngừa]
    - [Lời khuyên về chế độ sinh hoạt]
    - [Những điều cần tránh]

    MỨC ĐỘ NGHIÊM TRỌNG:
    [Mức độ nghiêm trọng] - [Giải thích chi tiết về lý do đánh giá và khuyến nghị hành động]

    LƯU Ý QUAN TRỌNG:
    - Trả lời hoàn toàn bằng tiếng Việt (TUYỆT ĐỐI KHÔNG ĐƯỢC SỬ DỤNG TIẾNG TRUNG Ở ĐÂY)
    - Tuân thủ chính xác định dạng đã yêu cầu
    - Không thêm bất kỳ thông tin nào khác ngoài cấu trúc đã chỉ định
    - Cung cấp thông tin chi tiết nhưng dễ hiểu với người không chuyên
    - Luôn nhấn mạnh tầm quan trọng của việc tham khảo ý kiến bác sĩ chuyên nghiệp
    """
    
    logger.info("Calling DeepSeek API...")
    logger.debug(f"Prompt length: {len(prompt)} characters")
    
    # Call DeepSeek API
    stream = client.chat.completions.create(
      model="deepseek-ai/DeepSeek-R1-0528",
      messages=[{"role": "user", "content": prompt}],
      temperature=0.7,
      top_p=0.8,
      stream=True,
    )
    
    logger.info("Receiving response from DeepSeek API...")
    
    # Collect response from streaming and capture thinking
    response_text = ""
    thinking_content = ""
    chunk_count = 0
    in_thinking = False
    
    for chunk in stream:
      if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        response_text += content
        
        # Check if we're entering or exiting thinking tags
        if "<think>" in content:
          in_thinking = True
          logger.info("=== MODEL THINKING STARTED ===")
          
        if "</think>" in content:
          in_thinking = False
          logger.info("=== MODEL THINKING ENDED ===")
          # Log the complete thinking content
          if thinking_content.strip():
            logger.info("=== COMPLETE MODEL THINKING PROCESS ===")
            logger.info(f"THINKING: {thinking_content.strip()}")
            logger.info("=== END OF THINKING PROCESS ===")
          
        # Capture thinking content if we're in thinking mode
        if in_thinking:
          # Remove <think> tags from the thinking content
          clean_content = content.replace("<think>", "").replace("</think>", "")
          thinking_content += clean_content
          # Log thinking content in real-time
          if clean_content.strip():
            logger.info(f"THINKING: {clean_content.strip()}")
        
        chunk_count += 1
    
    logger.info(f"Received {chunk_count} chunks from API")
    logger.info(f"Total response length: {len(response_text)} characters")
    
    # Remove thinking tags from the final response
    cleaned_response = response_text
    if "<think>" in cleaned_response and "</think>" in cleaned_response:
      # Extract only the content after </think>
      parts = cleaned_response.split("</think>")
      if len(parts) > 1:
        cleaned_response = parts[-1].strip()
      else:
        # If no content after </think>, remove thinking tags
        import re
        cleaned_response = re.sub(r'<think>.*?</think>', '', cleaned_response, flags=re.DOTALL).strip()
    
    logger.debug(f"Cleaned response (first 500 chars): {cleaned_response[:500]}...")
    
    # Process the response to extract possible conditions and recommendations
    possible_conditions = []
    recommendations = []
    severity = "Không xác định"
    
    logger.info("Parsing response sections...")
    
    # Parse sections based on headers
    if "TÌNH TRẠNG CÓ THỂ:" in cleaned_response:
      logger.info("Found 'TÌNH TRẠNG CÓ THỂ' section")
      conditions_section = cleaned_response.split("TÌNH TRẠNG CÓ THỂ:")[1].split("ĐỀ XUẤT VÀ LỜI KHUYÊN:")[0].strip()
      possible_conditions = [c.strip().lstrip('- ') for c in conditions_section.split('\n') if c.strip() and c.strip().startswith('-')]
      logger.info(f"Parsed {len(possible_conditions)} conditions: {possible_conditions}")
    else:
      logger.warning("'TÌNH TRẠNG CÓ THỂ' section not found in response")
    
    if "ĐỀ XUẤT VÀ LỜI KHUYÊN:" in cleaned_response:
      logger.info("Found 'ĐỀ XUẤT VÀ LỜI KHUYÊN' section")
      if "MỨC ĐỘ NGHIÊM TRỌNG:" in cleaned_response:
        recommendations_section = cleaned_response.split("ĐỀ XUẤT VÀ LỜI KHUYÊN:")[1].split("MỨC ĐỘ NGHIÊM TRỌNG:")[0].strip()
      else:
        recommendations_section = cleaned_response.split("ĐỀ XUẤT VÀ LỜI KHUYÊN:")[1].strip()
      recommendations = [r.strip().lstrip('- ') for r in recommendations_section.split('\n') if r.strip() and r.strip().startswith('-')]
      logger.info(f"Parsed {len(recommendations)} recommendations: {recommendations}")
    else:
      logger.warning("'ĐỀ XUẤT VÀ LỜI KHUYÊN' section not found in response")
    
    if "MỨC ĐỘ NGHIÊM TRỌNG:" in cleaned_response:
      logger.info("Found 'MỨC ĐỘ NGHIÊM TRỌNG' section")
      severity_section = cleaned_response.split("MỨC ĐỘ NGHIÊM TRỌNG:")[1].strip()
      severity_lines = [line for line in severity_section.split('\n') if line.strip()]
      if severity_lines:
        severity = severity_lines[0].strip()
        # Add severity to recommendations
        recommendations.append(f"Mức độ nghiêm trọng: {severity}")
        logger.info(f"Parsed severity: {severity}")
    else:
      logger.warning("'MỨC ĐỘ NGHIÊM TRỌNG' section not found in response")
    
    # If parsing fails, use generic response
    if not possible_conditions:
      logger.warning("No conditions parsed, using fallback")
      possible_conditions = ["Không thể xác định rõ dựa trên triệu chứng đã cung cấp"]
    if not recommendations:
      logger.warning("No recommendations parsed, using fallback")
      recommendations = ["Vui lòng tham khảo ý kiến bác sĩ để được chẩn đoán chính xác"]
      
    disclaimer = "Lưu ý: Đây chỉ là chẩn đoán sơ bộ dựa trên AI và không thay thế cho tư vấn y tế chuyên nghiệp. Vui lòng tham khảo ý kiến bác sĩ."
    
    logger.info("Successfully processed diagnosis request")
    logger.info(f"Final result - Conditions: {len(possible_conditions)}, Recommendations: {len(recommendations)}")
      
    return DiagnosisResponse(
      possible_conditions=possible_conditions,
      recommendations=recommendations,
      disclaimer=disclaimer
    )
    
  except Exception as e:
    logger.error(f"Error processing request: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
