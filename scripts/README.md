# Scripts Đồng Bộ Dữ Liệu Medicine

Thư mục này chứa các script để đồng bộ dữ liệu Medicine từ MongoDB lên Milvus vector database.

## Các File

- `sync_medicines_to_milvus.py`: Script chính để đồng bộ dữ liệu
- `run_sync.py`: Script đơn giản để chạy với các tùy chọn
- `README.md`: File hướng dẫn này

## Yêu Cầu

### 1. Cấu Hình Environment Variables

Tạo file `.env` trong thư mục gốc với các biến sau:

```env
# MongoDB
DATABASE_URL=mongodb://localhost:27017
DATABASE_NAME=pharmacy

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

### 2. Cài Đặt Dependencies

```bash
pip install -r requirements.txt
```

## Cách Sử Dụng

### 1. Đồng Bộ Toàn Bộ Dữ Liệu

```bash
# Chạy script chính
python scripts/sync_medicines_to_milvus.py

# Hoặc sử dụng script đơn giản
python scripts/run_sync.py
```

### 2. Các Tùy Chọn Nâng Cao

```bash
# Chỉ kiểm tra kết quả đồng bộ (không sync)
python scripts/run_sync.py --verify-only

# Đồng bộ với batch size tùy chỉnh
python scripts/run_sync.py --batch-size 20

# Tạo lại collection Milvus (xóa dữ liệu cũ)
python scripts/run_sync.py --recreate-collection

# Kết hợp các tùy chọn
python scripts/run_sync.py --batch-size 15 --recreate-collection
```

## Quy Trình Hoạt Động

1. **Kết nối Database**: Script kết nối với MongoDB và Milvus
2. **Tạo Collection**: Tạo collection trong Milvus với schema phù hợp
3. **Lấy Dữ Liệu**: Lấy tất cả medicines từ MongoDB
4. **Tạo Embeddings**: Tạo 4 loại embeddings cho mỗi medicine:
   - `primary_embedding`: Thông tin tổng quan
   - `symptom_embedding`: Triệu chứng và công dụng
   - `usage_embedding`: Hướng dẫn sử dụng
   - `safety_embedding`: Thông tin an toàn
5. **Lưu Dữ Liệu**: Lưu dữ liệu và embeddings vào Milvus
6. **Kiểm Tra**: Kiểm tra kết quả và test tìm kiếm

## Cấu Trúc Dữ Liệu trong Milvus

```python
{
    "id": "med_<medicine_id>",
    "medicine_id": "<original_mongodb_id>",
    "name": "Tên thuốc",
    "slug": "ten-thuoc",
    "primary_embedding": [1024 dimensions],
    "symptom_embedding": [1024 dimensions], 
    "usage_embedding": [1024 dimensions],
    "safety_embedding": [1024 dimensions],
    "category_id": "category_id",
    "supplier_id": "supplier_id",
    "active_ingredient": "Hoạt chất",
    "price": 50000,
    "stock_status": "in_stock",
    "is_featured": true,
    "is_active": true,
    "rating": 4.5,
    "therapeutic_uses": "[\"Giảm đau\", \"Hạ sốt\"]",
    "contraindications": "[\"Không dùng cho trẻ dưới 12 tuổi\"]",
    "dosage_info": "{\"adult\": \"1-2 viên/lần\", \"child\": \"0.5-1 viên/lần\"}"
}
```

## Logs

Script sẽ tạo file log `sync_medicines.log` để theo dõi quá trình đồng bộ.

## Xử Lý Lỗi

- Script sẽ tiếp tục xử lý ngay cả khi một số medicine gặp lỗi
- Tất cả lỗi được ghi log chi tiết
- Batch processing giúp tránh mất toàn bộ dữ liệu khi có lỗi

## Kiểm Tra Kết Quả

Sau khi đồng bộ, script sẽ:
- Hiển thị số lượng entities trong Milvus
- Thực hiện test search với query "thuốc giảm đau"
- Hiển thị top 5 kết quả tìm kiếm

## Lưu Ý

1. **API Limits**: Cohere API có giới hạn request, script đã xử lý batch processing
2. **Memory Usage**: Với dataset lớn, có thể cần điều chỉnh batch size
3. **Network**: Đảm bảo kết nối ổn định với Milvus Cloud
4. **Backup**: Nên backup dữ liệu trước khi chạy với `--recreate-collection`

## Troubleshooting

### Lỗi Kết Nối Milvus
```
Failed to connect to Milvus: <error>
```
- Kiểm tra MILVUS_URI và MILVUS_TOKEN
- Đảm bảo Milvus Cloud service đang hoạt động

### Lỗi Cohere API
```
Error creating embeddings with Cohere: <error>
```
- Kiểm tra COHERE_API_KEY
- Kiểm tra quota API còn lại

### Lỗi MongoDB
```
Failed to fetch medicines: <error>
```
- Kiểm tra DATABASE_URL
- Đảm bảo MongoDB đang chạy và có dữ liệu 