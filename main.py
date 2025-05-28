from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Pharmacy AI Backend",
    description="Backend đơn giản sử dụng FastAPI cho ứng dụng AI dược phẩm",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Endpoint kiểm tra sức khỏe"""
    return {"message": "Chào mừng đến với Pharmacy AI Backend", "status": "đang chạy"}


@app.get("/health")
async def health_check():
    """Endpoint kiểm tra sức khỏe"""
    return {"status": "khỏe mạnh", "service": "pharmacy-ai-backend"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
