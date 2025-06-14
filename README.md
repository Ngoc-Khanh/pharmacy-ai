# Hệ Thống AI Tư Vấn Nhà Thuốc

Một ứng dụng API REST được xây dựng bằng FastAPI và MongoDB để cung cấp dịch vụ tư vấn y tế thông minh cho nhà thuốc.

## Tính Năng

+ Backend Python FastAPI hiệu năng cao
+ Cơ sở dữ liệu MongoDB
+ Hệ thống xác thực JWT
+ API tư vấn y tế thông minh
+ Hỗ trợ triển khai Docker

## Cấu Trúc Dự Án

```
├── app.py                  # Ứng dụng FastAPI chính
├── main.py                 # Entry point để chạy server
├── requirements.txt        # Danh sách thư viện phụ thuộc
├── auth/                   # Module xác thực JWT
├── config/                 # Cấu hình ứng dụng
├── database/               # Kết nối và xử lý database
├── models/                 # Mô hình dữ liệu MongoDB
├── routes/                 # Định nghĩa API routes
├── schemas/                # Schema validation
├── tests/                  # Test cases
└── utils/                  # Các tiện ích hỗ trợ
```

## Cách Sử Dụng

Để sử dụng ứng dụng, hãy làm theo các bước sau:

1. Clone repository và tạo môi trường ảo:

```console
$ python3 -m venv venv
```

2. Kích hoạt môi trường ảo:

Windows:
```console
$ venv\Scripts\activate
```

Linux/Mac:
```console
$ source venv/bin/activate
```

3. Cài đặt các thư viện từ file `requirements.txt`:

```console
(venv)$ pip install -r requirements.txt
```

4. Khởi động MongoDB instance (local hoặc Docker) và tạo file `.env.dev`. Xem `.env.sample` để biết cấu hình chi tiết.

    Ví dụ chạy MongoDB local tại port 27017:
    ```console
    cp .env.sample .env.dev
    ```

5. Khởi động ứng dụng:

```console
python main.py
```

Ứng dụng sẽ chạy trên port 5000 tại địa chỉ [0.0.0.0:5000](http://0.0.0.0:5000). 

## Triển Khai

Ứng dụng này có thể được triển khai trên các nền tảng PaaS như [Heroku](https://heroku.com), [Okteto](https://okteto.com), hoặc bất kỳ nhà cung cấp dịch vụ cloud nào khác.

### Docker Deployment

```console
docker-compose up -d
```

## Đồng Bộ Dữ Liệu với Milvus

Dự án bao gồm các script để đồng bộ dữ liệu Medicine từ MongoDB lên Milvus vector database để hỗ trợ tìm kiếm thông minh.

### Cấu Hình Environment Variables

Thêm các biến sau vào file `.env`:

```env
# Cohere API (để tạo embeddings)
COHERE_API_KEY=your_cohere_api_key_here
COHERE_EMBEDDING_MODEL=embed-multilingual-v3.0

# Milvus Cloud
MILVUS_URI=your_milvus_cloud_uri
MILVUS_TOKEN=your_milvus_cloud_token
MILVUS_COLLECTION_NAME=medicine_embeddings

# Embedding Configuration
EMBEDDING_DIMENSION=1024
```

### Sử Dụng Scripts

1. **Kiểm tra cấu hình trước khi sync:**
```console
python scripts/check_config.py
```

2. **Đồng bộ dữ liệu:**
```console
# Cách đơn giản
python scripts/run_sync.py

# Hoặc chạy script chính
python scripts/sync_medicines_to_milvus.py
```

3. **Các tùy chọn nâng cao:**
```console
# Chỉ kiểm tra kết quả
python scripts/run_sync.py --verify-only

# Tùy chỉnh batch size
python scripts/run_sync.py --batch-size 20

# Tạo lại collection
python scripts/run_sync.py --recreate-collection
```

Xem thêm chi tiết trong [scripts/README.md](scripts/README.md).

## Bản Quyền

Dự án này được cấp phép theo giấy phép MIT.
