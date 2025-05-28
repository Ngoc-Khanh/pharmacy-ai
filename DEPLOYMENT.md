# Pharmacy AI Backend - FastAPI

Một backend đơn giản sử dụng FastAPI cho ứng dụng Pharmacy AI.

## Cài đặt và chạy local

### 1. Tạo và kích hoạt virtual environment:
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# hoặc
.\venv\Scripts\activate.bat  # Windows CMD
```

### 2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

### 3. Chạy server development:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Hoặc sử dụng script có sẵn:
```bash
.\start_dev.bat
```

Server sẽ chạy tại: http://127.0.0.1:8000

## API Endpoints

- `GET /` - Kiểm tra sức khỏe và thông điệp chào mừng
- `GET /health` - Endpoint kiểm tra sức khỏe

### Ví dụ sử dụng API:

```bash
# Kiểm tra sức khỏe và thông điệp chào mừng
curl http://127.0.0.1:8000/

# Endpoint kiểm tra sức khỏe
curl http://127.0.0.1:8000/health
```

## Deploy lên Heroku

### 1. Cài đặt Heroku CLI
Tải và cài đặt từ: https://devcenter.heroku.com/articles/heroku-cli

### 2. Login vào Heroku:
```bash
heroku login
```

### 3. Tạo ứng dụng Heroku:
```bash
heroku create ten-ung-dung-cua-ban
```

### 4. Set buildpack Python:
```bash
heroku buildpacks:set heroku/python
```

### 5. Deploy:
```bash
git add .
git commit -m "Initial commit"
git push heroku main
```

### 6. Mở ứng dụng:
```bash
heroku open
```

### 7. Xem logs:
```bash
heroku logs --tail
```

## Files quan trọng cho Heroku

- `Procfile` - Định nghĩa cách Heroku chạy ứng dụng
- `requirements.txt` - Danh sách Python dependencies
- `runtime.txt` - Chỉ định phiên bản Python

## Environment Variables

Để thêm environment variables trên Heroku:
```bash
heroku config:set TEN_BIEN=gia_tri
```

## Cấu trúc dự án

```
pharmacy-ai/
├── main.py              # Ứng dụng FastAPI
├── requirements.txt     # Dependencies Python
├── Procfile            # File quy trình Heroku
├── runtime.txt         # Phiên bản Python
├── start_dev.bat       # Script server phát triển
├── test_server.py      # Script kiểm tra server
├── .gitignore          # File git ignore
└── README.md           # Tài liệu này
```

## Phát triển

Để thêm tính năng mới:

1. Thêm routes mới trong `main.py`
2. Cập nhật dependencies trong `requirements.txt` nếu cần
3. Test local bằng `uvicorn main:app --reload`
4. Commit và push lên Heroku

## Troubleshooting

### Lỗi thường gặp:

1. **Import Error**: Đảm bảo virtual environment được kích hoạt
2. **Port Error**: Đảm bảo port 8000 không bị sử dụng
3. **Heroku Deploy Error**: Kiểm tra logs bằng `heroku logs --tail`

### Kiểm tra sức khỏe:
```bash
curl https://ten-ung-dung-cua-ban.herokuapp.com/health
```
