# Pharmacy AI Backend

Backend đơn giản sử dụng FastAPI cho ứng dụng AI dược phẩm với khả năng triển khai Heroku.

## Tính năng

- Framework web FastAPI
- CORS được kích hoạt để tích hợp frontend
- Các endpoint kiểm tra sức khỏe
- Sẵn sàng triển khai Heroku

## Phát triển cục bộ

1. Cài đặt các dependencies:
```bash
pip install -r requirements.txt
```

2. Chạy ứng dụng:
```bash
python main.py
```

API sẽ có sẵn tại `http://localhost:8000`

## API Endpoints

- `GET /` - Thông điệp chào mừng
- `GET /health` - Kiểm tra sức khỏe

## Tài liệu API tương tác

Khi đã chạy, truy cập:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Triển khai Heroku

1. Cài đặt Heroku CLI
2. Đăng nhập Heroku: `heroku login`
3. Tạo ứng dụng: `heroku create ten-ung-dung-cua-ban`
4. Triển khai: `git push heroku main`

## Biến môi trường

- `PORT` - Cổng server (tự động được thiết lập bởi Heroku)

## Cấu trúc dự án

```
pharmacy-ai/
├── main.py           # Ứng dụng FastAPI
├── requirements.txt  # Dependencies Python
├── Procfile         # File quy trình Heroku
├── runtime.txt      # Phiên bản Python cho Heroku
└── README.md        # File này
```
