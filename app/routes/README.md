# API Chẩn đoán bệnh với Gemini

API này sử dụng mô hình Gemini của Google để phân tích các triệu chứng và đưa ra chẩn đoán sơ bộ.

## Cài đặt

1. Cài đặt các gói phụ thuộc:
```bash
pip install -r requirements.txt
```

2. Thiết lập API key cho Gemini:
```bash
# Windows
set GEMINI_API_KEY=your_api_key_here

# Linux/macOS
export GEMINI_API_KEY=your_api_key_here
```

## Sử dụng API

### Endpoint

```
POST /api/diagnosis/analyze
```

### Tham số đầu vào

```json
{
  "symptoms": ["đau đầu", "sốt", "mệt mỏi"],
  "age": 35,
  "gender": "nam",
  "medical_history": "Không có tiền sử bệnh nào đáng kể",
  "additional_info": "Triệu chứng xuất hiện sau khi đi du lịch"
}
```

| Tham số | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|----------|-------|
| symptoms | array | Có | Danh sách các triệu chứng |
| age | integer | Không | Tuổi của bệnh nhân |
| gender | string | Không | Giới tính của bệnh nhân |
| medical_history | string | Không | Tiền sử bệnh của bệnh nhân |
| additional_info | string | Không | Thông tin bổ sung |

### Kết quả trả về

```json
{
  "possible_conditions": [
    "Cảm cúm",
    "COVID-19",
    "Sốt xuất huyết"
  ],
  "recommendations": [
    "Nghỉ ngơi và uống nhiều nước",
    "Xem xét thực hiện xét nghiệm COVID-19",
    "Tham khảo ý kiến bác sĩ nếu các triệu chứng nghiêm trọng hơn"
  ],
  "disclaimer": "Lưu ý: Đây chỉ là chẩn đoán sơ bộ dựa trên AI và không thay thế cho tư vấn y tế chuyên nghiệp. Vui lòng tham khảo ý kiến bác sĩ."
}
```

## Ví dụ

Xem file `examples/diagnosis_example.py` để biết cách sử dụng API này từ Python.

## Lưu ý

- API này chỉ cung cấp chẩn đoán sơ bộ và không thay thế cho tư vấn y tế chuyên nghiệp.
- Độ chính xác của chẩn đoán phụ thuộc vào mô hình Gemini và thông tin đầu vào được cung cấp.
- Luôn tham khảo ý kiến bác sĩ cho các vấn đề sức khỏe. 