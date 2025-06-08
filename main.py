from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.routes import router as api_router
from app.database import connect_to_mongo, close_mongo_connection
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# Database connection events
@app.on_event("startup")
async def startup_event():
    """Sự kiện khởi động - kết nối MongoDB"""
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    """Sự kiện tắt - đóng kết nối MongoDB"""
    await close_mongo_connection()

# Include API routes
app.include_router(api_router, prefix="/api")


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
