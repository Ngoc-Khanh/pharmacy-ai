import json
import logging
import re
import time
from typing import Dict, Tuple

from groq import Groq

from config.config import Settings

logger = logging.getLogger(__name__)


class GroqService:
    def __init__(self):
        self.settings = Settings()
        self.api_key = self.settings.GROQ_API_KEY
        self.model = self.settings.GROQ_MODEL
        if not self.api_key:
            logger.warning("GROQ_API_KEY không được tìm thấy")
            self.client = None
            return
        try:
            self.client = Groq(api_key=self.api_key)
            logger.info(f"Khởi tạo Groq client thành công với mô hình: {self.model}")
        except Exception as e:
            logger.error(f"Lỗi khi khởi tạo Groq client: {e}")
            self.client = None

    def analyze_symptoms(
        self, symptoms: str, patient_age: int = None, patient_gender: str = None
    ) -> Tuple[Dict, bool]:
        """Phân tích triệu chứng và trả về chẩn đoán"""
        if not self.client:
            return self._get_fallback_response(), True
        try:
            prompt = self._create_diagnosis_prompt(
                symptoms, patient_age, patient_gender
            )
            random_seed = int(time.time() * 1000) % 10000
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""Bạn là chuyên gia y tế AI. Phân tích triệu chứng và trả về JSON tiếng Việt.
                        Tạo phản hồi đa dạng với seed: {random_seed}""",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=5000,
                top_p=0.9,
            )
            
            # Log AI thinking và response
            ai_response = response.choices[0].message.content
            logger.info(f"AI thinking và response: {ai_response}")
            
            result, is_fallback = self._parse_ai_response(ai_response)
            
            # Log kết quả sau khi parse
            logger.info(f"Kết quả sau khi parse: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result, is_fallback
        except Exception as e:
            logger.error(f"Lỗi khi gọi Groq API: {e}")
            return self._get_fallback_response(), True

    def _create_diagnosis_prompt(
        self, symptoms: str, patient_age: int = None, patient_gender: str = None
    ) -> str:
        """Tạo prompt cho AI"""
        patient_info = ""
        if patient_age:
            patient_info += f"Tuổi: {patient_age}. "
        if patient_gender:
            patient_info += f"Giới tính: {patient_gender}. "

        return f"""
        Bạn là bác sĩ chuyên khoa với 20 năm kinh nghiệm. Hãy phân tích triệu chứng một cách chi tiết và toàn diện:
        
        THÔNG TIN BỆNH NHÂN:
        Triệu chứng: {symptoms}
        {patient_info}
        
        YÊU CẦU PHÂN TÍCH:
        1. Nếu thông tin triệu chứng ngắn gọn hoặc mơ hồ, hãy đưa ra phân tích sâu dựa trên kinh nghiệm lâm sàng
        2. Mô tả chi tiết cơ chế bệnh sinh, nguyên nhân có thể
        3. Phân tích mối liên hệ giữa các triệu chứng
        4. Đưa ra lời khuyên cụ thể và thực tế
        5. Mỗi lý do phải dài ít nhất 15-20 từ, giải thích rõ ràng
        6. Mô tả phải chi tiết, không chung chung
        
        Trả về định dạng JSON với nội dung chi tiết:
        {{
            "primary_diagnosis": {{
                "diagnosis_name": "<tên chẩn đoán chính xác và cụ thể>",
                "confidence_percentage": <70-90>,
                "description": "<mô tả chi tiết về bệnh, cơ chế bệnh sinh, diễn biến thường gặp, ít nhất 50-80 từ>",
                "reasons": [
                    "<lý do 1: giải thích chi tiết tại sao triệu chứng phù hợp với chẩn đoán này, ít nhất 15-20 từ>",
                    "<lý do 2: phân tích mối liên hệ giữa triệu chứng và bệnh lý, ít nhất 15-20 từ>",
                    "<lý do 3: so sánh với các bệnh khác và tại sao chẩn đoán này phù hợp nhất, ít nhất 15-20 từ>"
                ]
            }},
            "alternative_diagnoses": [
                {{
                    "diagnosis_name": "<chẩn đoán phụ 1 cụ thể>",
                    "confidence_percentage": <40-70>,
                    "description": "<mô tả chi tiết về bệnh này, tại sao có thể xảy ra, cơ chế, ít nhất 40-60 từ>",
                    "reasons": [
                        "<lý do 1: giải thích chi tiết, ít nhất 15-20 từ>",
                        "<lý do 2: phân tích triệu chứng phù hợp, ít nhất 15-20 từ>",
                        "<lý do 3: so sánh với chẩn đoán chính, ít nhất 15-20 từ>"
                    ]
                }},
                {{
                    "diagnosis_name": "<chẩn đoán phụ 2 cụ thể>",
                    "confidence_percentage": <20-50>,
                    "description": "<mô tả chi tiết, cơ chế bệnh sinh, ít nhất 40-60 từ>",
                    "reasons": [
                        "<lý do 1: giải thích chi tiết tại sao có thể là bệnh này, ít nhất 15-20 từ>",
                        "<lý do 2: phân tích triệu chứng và mối liên hệ, ít nhất 15-20 từ>",
                        "<lý do 3: đánh giá khả năng xảy ra, ít nhất 15-20 từ>"
                    ]
                }}
            ],
            "general_advice": [
                "<lời khuyên 1: chi tiết về chế độ sinh hoạt, dinh dưỡng, nghỉ ngơi, ít nhất 20-30 từ>",
                "<lời khuyên 2: hướng dẫn theo dõi triệu chứng, dấu hiệu cảnh báo, ít nhất 20-30 từ>",
                "<lời khuyên 3: biện pháp phòng ngừa, cải thiện sức khỏe tổng quát, ít nhất 20-30 từ>"
            ],
            "overall_severity_level": "<nhẹ/trung bình/nghiêm trọng>",
            "related_symptoms": [
                "<triệu chứng liên quan 1: mô tả chi tiết tại sao có thể xuất hiện>",
                "<triệu chứng liên quan 2: giải thích mối liên hệ với triệu chứng chính>",
                "<triệu chứng liên quan 3: phân tích cơ chế xuất hiện>"
            ],
            "recommended_actions": [
                "<hành động 1: hướng dẫn cụ thể về thời điểm và cách thức khám bác sĩ, ít nhất 25-35 từ>",
                "<hành động 2: biện pháp tự chăm sóc tại nhà, thuốc không kê đơn an toàn, ít nhất 25-35 từ>",
                "<hành động 3: dấu hiệu cảnh báo cần đi cấp cứu ngay lập tức, ít nhất 25-35 từ>"
            ]
        }}
        
        LƯU Ý QUAN TRỌNG:
        - Mỗi câu trả lời hoàn toàn bằng TIẾNG VIỆT không có tiếng Anh hay tiếng Trung
        - Mỗi mô tả phải chi tiết, không được chung chung
        - Lý do phải giải thích rõ ràng cơ chế, không chỉ liệt kê
        - Lời khuyên phải thực tế, có thể áp dụng được
        - Nếu thông tin ít, hãy dựa vào kinh nghiệm lâm sàng để phân tích sâu
        - Chỉ trả về JSON, không thêm text khác
        """

    def _parse_ai_response(self, response_text: str) -> Tuple[Dict, bool]:
        """Parse response từ AI"""
        try:
            # Làm sạch response
            cleaned_response = response_text.strip()
            # Xử lý think tags
            if "<think>" in cleaned_response and "</think>" in cleaned_response:
                parts = cleaned_response.split("</think>")
                cleaned_response = (
                    parts[-1].strip()
                    if len(parts) > 1
                    else re.sub(
                        r"<think>.*?</think>", "", cleaned_response, flags=re.DOTALL
                    ).strip()
                )
            # Xử lý markdown
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            # Parse JSON
            result = json.loads(cleaned_response)
            # Validate cấu trúc cơ bản
            required_fields = [
                "primary_diagnosis",
                "alternative_diagnoses",
                "general_advice",
                "overall_severity_level",
                "related_symptoms",
                "recommended_actions",
            ]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing field: {field}")
            # Đảm bảo có đủ 2 alternative diagnoses
            if len(result["alternative_diagnoses"]) < 2:
                result["alternative_diagnoses"].extend(
                    [
                        {
                            "diagnosis_name": "Cần thêm thông tin",
                            "confidence_percentage": 30,
                            "description": "Cần thêm triệu chứng để chẩn đoán",
                            "reasons": [
                                "Triệu chứng chưa rõ",
                                "Cần gặp bác sĩ",
                                "Theo dõi thêm",
                            ],
                        }
                    ]
                    * (2 - len(result["alternative_diagnoses"]))
                )
            # Đảm bảo các list có ít nhất 3 items
            self._ensure_min_items(
                result, "general_advice", ["Nghỉ ngơi", "Uống nước", "Theo dõi"]
            )
            self._ensure_min_items(
                result, "related_symptoms", ["Mệt mỏi", "Khó chịu", "Lo lắng"]
            )
            self._ensure_min_items(
                result, "recommended_actions", ["Gặp bác sĩ", "Theo dõi", "Nghỉ ngơi"]
            )
            return result, False
        except Exception as e:
            logger.error(f"Lỗi parse response: {e}")
            return self._get_fallback_response(), True

    def _ensure_min_items(
        self, result: Dict, key: str, defaults: list, min_count: int = 3
    ):
        """Đảm bảo list có đủ số lượng items tối thiểu"""
        if len(result[key]) < min_count:
            result[key].extend(defaults[: min_count - len(result[key])])

    def _get_fallback_response(self) -> Dict:
        """Response mặc định khi có lỗi"""
        return {
            "primary_diagnosis": {
                "diagnosis_name": "Cần thêm thông tin để chẩn đoán",
                "confidence_percentage": 60,
                "description": "Cần thêm thông tin để đưa ra chẩn đoán chính xác",
                "reasons": [
                    "Triệu chứng chưa rõ",
                    "Cần thêm thông tin",
                    "Khuyến khích gặp bác sĩ",
                ],
            },
            "alternative_diagnoses": [
                {
                    "diagnosis_name": "Stress và căng thẳng",
                    "confidence_percentage": 45,
                    "description": "Có thể liên quan đến stress",
                    "reasons": ["Triệu chứng phổ biến", "Do áp lực", "Cần điều chỉnh"],
                },
                {
                    "diagnosis_name": "Mệt mỏi thể chất",
                    "confidence_percentage": 30,
                    "description": "Có thể do thiếu nghỉ ngơi",
                    "reasons": ["Thiếu ngủ", "Hoạt động quá mức", "Cần phục hồi"],
                },
            ],
            "general_advice": [
                "Theo dõi triệu chứng chi tiết",
                "Nghỉ ngơi đầy đủ 7-8 tiếng/ngày",
                "Gặp bác sĩ nếu không cải thiện",
            ],
            "overall_severity_level": "trung bình",
            "related_symptoms": ["Mệt mỏi", "Khó chịu", "Lo lắng"],
            "recommended_actions": [
                "Lập lịch khám bác sĩ",
                "Theo dõi triệu chứng",
                "Nghỉ ngơi và tránh hoạt động nặng",
            ],
        }
