import logging
import json
import re
import time
import random
from typing import Dict, Tuple

from groq import Groq
from config.config import Settings

logger = logging.getLogger(__name__)


class GroqService:
    def __init__(self):
        self.settings = Settings()
        self.api_key = self.settings.GROQ_API_KEY
        if not self.api_key:
            logger.warning(
                "GROQ_API_KEY không được tìm thấy hoặc chưa được cấu hình trong environment variables"
            )
            self.client = None
            self.model = self.settings.GROQ_MODEL
            logger.warning(f"Sử dụng mô hình mặc định: {self.model}")
            return
        try:
            self.client = Groq(api_key=self.api_key)
            self.model = self.settings.GROQ_MODEL
            logger.info(f"Khởi tạo Groq client thành công với mô hình: {self.model}")
        except Exception as e:
            logger.error(f"Lỗi khi khởi tạo Groq client: {e}")
            logger.warning(
                "GROQ_API_KEY không hợp lệ hoặc không thể kết nối đến Groq API"
            )
            self.client = None
            self.model = self.settings.GROQ_MODEL

    async def analyze_symptoms(
        self, symptoms: str, patient_age: int = None, patient_gender: str = None
    ) -> Tuple[Dict, bool]:
        """
        Phân tích triệu chứng và trả về chẩn đoán với độ tin cậy, lời khuyên và triệu chứng liên quan
        Returns: (result_dict, is_fallback)
        """
        if not self.client:
            logger.warning("Groq client không khả dụng, sử dụng fallback response")
            return self._get_fallback_response(), True
        try:
            # Prompt cho Groq API
            prompt = self._create_diagnosis_prompt(
                symptoms, patient_age, patient_gender
            )
            # Tạo seed ngẫu nhiên để đảm bảo phản hồi mới mỗi lần
            random_seed = int(time.time() * 1000) % 10000
            logger.info(f"Using random seed: {random_seed}")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""Bạn là một chuyên gia y tế AI. Hãy phân tích triệu chứng và trả về kết quả bằng tiếng Việt theo định dạng JSON chính xác như yêu cầu. 
                        Luôn trả về JSON hợp lệ và không thêm bất kỳ text nào khác ngoài JSON.
                        
                        QUAN TRỌNG: Mỗi lần phân tích cần có góc nhìn mới và phản hồi khác biệt. Hãy xem xét nhiều khả năng và đưa ra phân tích sáng tạo.
                        Random seed: {random_seed} (sử dụng để tạo phản hồi đa dạng)""",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,  # Tăng temperature để tạo phản hồi đa dạng hơn
                max_tokens=5000,  # Tăng max_tokens để có phản hồi chi tiết hơn
                top_p=0.9,  # Tăng top_p để cho phép nhiều lựa chọn từ ngữ hơn
            )
            logger.info("Đã nhận phản hồi từ Groq API")
            result, is_fallback = self._parse_ai_response(
                response.choices[0].message.content
            )
            return result, is_fallback
        except Exception as e:
            logger.error(f"Lỗi khi gọi Groq API: {e}")
            return self._get_fallback_response(), True

    def _create_diagnosis_prompt(
        self, symptoms: str, patient_age: int = None, patient_gender: str = None
    ) -> str:
        """Tạo prompt nâng cao cho AI để tạo 3 phiên bản chẩn đoán"""
        patient_info = ""
        if patient_age:
            patient_info += f"Tuổi: {patient_age} tuổi. "
        if patient_gender:
            patient_info += f"Giới tính: {patient_gender}. "

        # Thêm yếu tố thời gian để tạo prompt đa dạng
        timestamp = int(time.time())
        random_factor = random.randint(1, 1000)

        prompt = f"""
            Bạn là một chuyên gia y tế AI với kinh nghiệm sâu rộng. Hãy phân tích triệu chứng sau đây và đưa ra 3 phiên bản chẩn đoán khác nhau theo thứ tự ưu tiên:

            THÔNG TIN BỆNH NHÂN:
            Triệu chứng: {symptoms}
            {patient_info}
            
            PHÂN TÍCH ID: {timestamp}-{random_factor} (đảm bảo phân tích mới và độc đáo)

            YÊU CẦU PHÂN TÍCH ĐA DẠNG:
            1. Đưa ra 1 chẩn đoán CHÍNH (khả năng cao nhất: 70-90%)
            2. Đưa ra 2 chẩn đoán THẾ THỂ (khả năng trung bình: 40-70% và 20-50%)
            3. Mỗi chẩn đoán phải có lý do cụ thể dựa trên triệu chứng
            4. Đưa ra lời khuyên chung và hành động cụ thể
            5. **QUAN TRỌNG**: Mỗi lần phân tích phải có góc nhìn và cách tiếp cận khác nhau, không lặp lại phản hồi cũ

            Hãy trả về kết quả theo định dạng JSON chính xác như sau (KHÔNG thêm markdown):

            {{
                "primary_diagnosis": {{
                    "diagnosis_name": "<tên chẩn đoán chính>",
                    "confidence_percentage": <số từ 70-90>,
                    "description": "<mô tả chi tiết về tình trạng này>",
                    "reasons": [
                        "<lý do 1 dựa trên triệu chứng>",
                        "<lý do 2 dựa trên triệu chứng>",
                        "<lý do 3 dựa trên triệu chứng>"
                    ]
                }},
                "alternative_diagnoses": [
                    {{
                        "diagnosis_name": "<tên chẩn đoán thay thế 1>",
                        "confidence_percentage": <số từ 40-70>,
                        "description": "<mô tả chi tiết về tình trạng này>",
                        "reasons": [
                            "<lý do 1>",
                            "<lý do 2>",
                            "<lý do 3>"
                        ]
                    }},
                    {{
                        "diagnosis_name": "<tên chẩn đoán thay thế 2>",
                        "confidence_percentage": <số từ 20-50>,
                        "description": "<mô tả chi tiết về tình trạng này>",
                        "reasons": [
                            "<lý do 1>",
                            "<lý do 2>",
                            "<lý do 3>"
                        ]
                    }}
                ],
                "general_advice": [
                    "<lời khuyên chung 1>",
                    "<lời khuyên chung 2>",
                    "<lời khuyên chung 3>",
                    "<lời khuyên chung 4>",
                    "<lời khuyên chung 5>"
                ],
                "overall_severity_level": "<nhẹ/trung bình/nghiêm trọng/rất nghiêm trọng>",
                "related_symptoms": [
                    "<triệu chứng liên quan 1>",
                    "<triệu chứng liên quan 2>",
                    "<triệu chứng liên quan 3>",
                    "<triệu chứng liên quan 4>",
                    "<triệu chứng liên quan 5>"
                ],
                "recommended_actions": [
                    "<hành động cụ thể 1>",
                    "<hành động cụ thể 2>",
                    "<hành động cụ thể 3>",
                    "<hành động cụ thể 4>"
                ]
            }}

            HƯỚNG DẪN CHI TIẾT:
            - Chẩn đoán chính: Khả năng cao nhất dựa trên triệu chứng rõ ràng
            - Chẩn đoán thay thế: Các khả năng khác cần xem xét
            - Lý do: Giải thích tại sao triệu chứng phù hợp với chẩn đoán
            - Lời khuyên chung: Áp dụng cho tất cả các trường hợp
            - Hành động cụ thể: Các bước cần thực hiện ngay
            - Mức độ nghiêm trọng: Đánh giá tổng thể tình trạng
            - Luôn khuyến khích gặp bác sĩ nếu nghiêm trọng

            **LƯU Ý QUAN TRỌNG VỀ TÍNH ĐA DẠNG**:
            - Mỗi lần phân tích hãy xem xét từ góc độ khác nhau
            - Thay đổi cách diễn đạt và từ ngữ sử dụng
            - Đưa ra các chẩn đoán thay thế đa dạng
            - Lời khuyên và hành động nên phù hợp với từng trường hợp cụ thể
            - Tránh sử dụng cùng một template phản hồi

            Trả lời HOÀN TOÀN bằng tiếng Việt và tuân thủ chính xác định dạng JSON.
            """
        return prompt

    def _parse_ai_response(self, response_text: str) -> Tuple[Dict, bool]:
        """Parse response từ AI và trả về dict với cấu trúc mới"""
        try:
            logger.info("=== RAW GROQ RESPONSE ===")
            logger.info(f"Response text (first 500 chars): {response_text[:500]}...")
            logger.info(f"Response length: {len(response_text)} characters")

            # Làm sạch response - xử lý think tags
            cleaned_response = response_text.strip()

            # Xử lý think tags nếu có
            if "<think>" in cleaned_response and "</think>" in cleaned_response:
                # Lấy phần sau </think>
                parts = cleaned_response.split("</think>")
                if len(parts) > 1:
                    cleaned_response = parts[-1].strip()
                    logger.info("✅ Removed <think> tags from response")
                else:
                    # Nếu không có content sau </think>, xóa toàn bộ think block
                    cleaned_response = re.sub(
                        r"<think>.*?</think>", "", cleaned_response, flags=re.DOTALL
                    ).strip()
                    logger.info("✅ Removed complete <think> block")

            # Xử lý markdown nếu có
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            logger.info(
                f"Cleaned response (first 300 chars): {cleaned_response[:300]}..."
            )

            # Parse JSON
            result = json.loads(cleaned_response)
            logger.info("✅ JSON parsing successful")

            # Validate structure
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
                    logger.error(f"❌ Missing required field: {field}")
                    raise ValueError(f"Missing required field: {field}")

            logger.info("✅ All required fields present")

            # Validate primary diagnosis
            primary = result["primary_diagnosis"]
            if not all(
                key in primary
                for key in [
                    "diagnosis_name",
                    "confidence_percentage",
                    "description",
                    "reasons",
                ]
            ):
                logger.error("❌ Invalid primary_diagnosis structure")
                raise ValueError("Invalid primary_diagnosis structure")

            logger.info(f"✅ Primary diagnosis: {primary['diagnosis_name']}")

            # Validate alternative diagnoses
            alternatives = result["alternative_diagnoses"]
            if len(alternatives) != 2:
                logger.warning(
                    f"Expected 2 alternative diagnoses, got {len(alternatives)}"
                )
                # Pad or truncate to ensure exactly 2
                if len(alternatives) < 2:
                    alternatives.extend(
                        [
                            {
                                "diagnosis_name": "Cần thêm thông tin để chẩn đoán",
                                "confidence_percentage": 30,
                                "description": "Cần thêm triệu chứng để đưa ra chẩn đoán chính xác hơn",
                                "reasons": [
                                    "Triệu chứng chưa rõ ràng",
                                    "Cần thêm thông tin",
                                    "Khuyến khích gặp bác sĩ",
                                ],
                            }
                        ]
                        * (2 - len(alternatives))
                    )
                else:
                    alternatives = alternatives[:2]
                result["alternative_diagnoses"] = alternatives

            # Ensure all lists have minimum required items
            if len(result["general_advice"]) < 3:
                result["general_advice"].extend(
                    ["Nghỉ ngơi đầy đủ", "Uống nhiều nước", "Theo dõi triệu chứng"][
                        : 3 - len(result["general_advice"])
                    ]
                )

            if len(result["related_symptoms"]) < 3:
                result["related_symptoms"].extend(
                    ["Mệt mỏi", "Khó chịu", "Lo lắng"][
                        : 3 - len(result["related_symptoms"])
                    ]
                )

            if len(result["recommended_actions"]) < 3:
                result["recommended_actions"].extend(
                    ["Tham khảo ý kiến bác sĩ", "Theo dõi triệu chứng", "Nghỉ ngơi"][
                        : 3 - len(result["recommended_actions"])
                    ]
                )

            logger.info(
                "✅ Response validation successful - returning REAL AI response"
            )
            return result, False  # False = not fallback

        except json.JSONDecodeError as e:
            logger.error(f"❌ Lỗi parse JSON: {e}")
            logger.error(f"Raw response text: {response_text}")
            logger.error("Returning fallback response due to JSON parse error")
            return self._get_fallback_response(), True  # True = fallback
        except Exception as e:
            logger.error(f"❌ Lỗi parse response: {e}")
            logger.error(f"Raw response text: {response_text}")
            logger.error("Returning fallback response due to validation error")
            return self._get_fallback_response(), True  # True = fallback

    def _get_fallback_response(self) -> Dict:
        """Trả về response mặc định với cấu trúc mới khi có lỗi"""
        return {
            "primary_diagnosis": {
                "diagnosis_name": "Cần thêm thông tin để chẩn đoán chính xác",
                "confidence_percentage": 60,
                "description": "Dựa trên triệu chứng hiện tại, cần thêm thông tin để đưa ra chẩn đoán chính xác",
                "reasons": [
                    "Triệu chứng chưa đủ rõ ràng",
                    "Cần thêm thông tin về thời gian xuất hiện",
                    "Khuyến khích thăm khám bác sĩ",
                ],
            },
            "alternative_diagnoses": [
                {
                    "diagnosis_name": "Stress và căng thẳng",
                    "confidence_percentage": 45,
                    "description": "Các triệu chứng có thể liên quan đến stress và áp lực cuộc sống",
                    "reasons": [
                        "Triệu chứng phổ biến khi stress",
                        "Có thể do áp lực công việc",
                        "Cần điều chỉnh lối sống",
                    ],
                },
                {
                    "diagnosis_name": "Mệt mỏi thể chất",
                    "confidence_percentage": 30,
                    "description": "Có thể do thiếu nghỉ ngơi hoặc hoạt động quá mức",
                    "reasons": [
                        "Có thể do thiếu ngủ",
                        "Hoạt động thể chất quá mức",
                        "Cần thời gian phục hồi",
                    ],
                },
            ],
            "general_advice": [
                "Theo dõi triệu chứng và ghi chép lại chi tiết",
                "Nghỉ ngơi đầy đủ và duy trì giấc ngủ 7-8 tiếng/ngày",
                "Uống nhiều nước và duy trì chế độ ăn cân bằng",
                "Tránh stress và áp lực không cần thiết",
                "Đến gặp bác sĩ nếu triệu chứng không cải thiện sau 2-3 ngày",
            ],
            "overall_severity_level": "trung bình",
            "related_symptoms": [
                "Mệt mỏi",
                "Khó chịu",
                "Lo lắng",
                "Căng thẳng",
                "Mất ngủ",
            ],
            "recommended_actions": [
                "Lập lịch khám bác sĩ trong 1-2 ngày tới",
                "Theo dõi và ghi chép các triệu chứng mới",
                "Nghỉ ngơi và tránh hoạt động nặng",
                "Liên hệ cơ sở y tế nếu triệu chứng trầm trọng hơn",
            ],
        }
