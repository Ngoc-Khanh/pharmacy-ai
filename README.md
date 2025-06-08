# Pharmacy AI Backend

Backend đơn giản sử dụng FastAPI cho ứng dụng AI dược phẩm với khả năng triển khai Heroku.

## Tính năng

- Framework web FastAPI
- CORS được kích hoạt để tích hợp frontend
- Các endpoint kiểm tra sức khỏe
- AI chẩn đoán triệu chứng sử dụng GroqCloud với Qwen
- Lưu trữ MongoDB cho lịch sử tư vấn
- Sẵn sàng triển khai Heroku

## Phát triển cục bộ

1. Cài đặt các dependencies:
```bash
pip install -r requirements.txt
```

2. Thiết lập biến môi trường:
Tạo file `.env` trong thư mục gốc với nội dung:
```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=pharmacy_ai

# Groq API Configuration (Bắt buộc cho AI chẩn đoán)
GROQ_API_KEY=your_groq_api_key_here

# Other API Keys (tuỳ chọn)
GOOGLE_API_KEY=your_google_api_key_here
```

**Lưu ý**: Để sử dụng tính năng AI chẩn đoán, bạn cần:
- Đăng ký tài khoản tại [GroqCloud](https://console.groq.com)
- Tạo API key và thêm vào file `.env`

3. Chạy ứng dụng:
```bash
python main.py
```

API sẽ có sẵn tại `http://localhost:8000`

## API Endpoints

### Endpoints cơ bản
- `GET /` - Thông điệp chào mừng
- `GET /health` - Kiểm tra sức khỏe

### AI Chẩn đoán (GroqCloud + Qwen)
- `POST /api/groq/diagnose` - Chẩn đoán triệu chứng
- `GET /api/groq/history/{user_id}` - Lịch sử tư vấn của user
- `GET /api/groq/history` - Tất cả lịch sử tư vấn
- `GET /api/groq/stats` - Thống kê tư vấn
- `DELETE /api/groq/history/{user_id}` - Xóa lịch sử user

### Ví dụ sử dụng API chẩn đoán:

**Request:**
```json
POST /api/groq/diagnose
{
  "user_id": "user123",
  "symptoms": "đau đầu, sốt, mệt mỏi",
  "patient_age": 25,
  "patient_gender": "nam"
}
```

**Response:**
```json
{
  "confidence_percentage": 85,
  "advice": [
    "Nghỉ ngơi đầy đủ và uống nhiều nước",
    "Sử dụng thuốc hạ sốt nếu cần thiết", 
    "Đến gặp bác sĩ nếu triệu chứng kéo dài quá 3 ngày"
  ],
  "severity_level": "trung bình",
  "related_symptoms": [
    "buồn nôn", "chóng mặt", "ăn không ngon", "khô họng", "đau cơ"
  ],
  "diagnosis": "Nhiễm virus cảm lạnh thông thường"
}
```

## Tài liệu API tương tác

Khi đã chạy, truy cập:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Triển khai Heroku

1. Cài đặt Heroku CLI
2. Đăng nhập Heroku: `heroku login`
3. Tạo ứng dụng: `heroku create ten-ung-dung-cua-ban`
4. Thiết lập biến môi trường trên Heroku:
```bash
heroku config:set GROQ_API_KEY=your_groq_api_key_here
heroku config:set MONGODB_URL=your_mongodb_connection_string
```
5. Triển khai: `git push heroku main`

## Biến môi trường

- `PORT` - Cổng server (tự động được thiết lập bởi Heroku)
- `GROQ_API_KEY` - API key cho GroqCloud (bắt buộc cho AI chẩn đoán)
- `MONGODB_URL` - Connection string MongoDB
- `DATABASE_NAME` - Tên database MongoDB
- `GOOGLE_API_KEY` - API key Google (tuỳ chọn)

## Cấu trúc dự án

```
pharmacy-ai/
├── main.py                 # Ứng dụng FastAPI chính
├── requirements.txt        # Dependencies Python
├── Procfile               # File quy trình Heroku
├── runtime.txt            # Phiên bản Python cho Heroku
├── app/
│   ├── models.py          # Pydantic models
│   ├── database.py        # MongoDB connection
│   ├── routes/            # API routes
│   │   ├── groq_diagnosis.py  # AI chẩn đoán endpoints
│   │   └── ...
│   └── services/          # Business logic
│       └── groq_service.py    # GroqCloud integration
└── README.md              # File này
```

## Cấu trúc Database MongoDB

Collection `Consultation`:
```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "human": {
    "symptoms": "string",
    "patient_age": "number",
    "patient_gender": "string"
  },
  "ai": [
    {
      "confidence_percentage": "number",
      "advice": ["string"],
      "related_symptoms": ["string"],
      "diagnosis": "string",
      "severity_level": "string"
    }
  ],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```
