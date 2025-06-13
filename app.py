from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from auth.jwt_bearer import JWTBearer
from config.config import get_database, initiate_database, Settings
from routes import router as api_router
from utils.http_response import fail, json

app = FastAPI()

token_listener = JWTBearer()
settings = Settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def start_database():
    await initiate_database()


@app.get("/", tags=["Root"])
async def read_root():
    return json(
        data={
            "service": "Pharmacy AI Backend",
            "version": "2.0.0",
            "status": "đang chạy",
            "features": [
                "Multiple AI Diagnosis (GroqCloud, Gemini, DeepSeek)",
                "Standardized API Response Format",
                "MongoDB Integration",
                "Multiple Input Formats Support",
            ],
        },
        message="Chào mừng đến với Pharmacy AI Backend v2.0",
    )


@app.get("/health")
async def health_check():
    """Endpoint kiểm tra sức khỏe chi tiết với standardized response"""
    try:
        db = get_database()
        db_status = "connected" if db else "disconnected"

        health_data = {
            "service": "pharmacy-ai-backend",
            "status": "khỏe mạnh",
            "version": "2.0.0",
            "database": db_status,
            "timestamp": "2024-01-01T00:00:00Z",
        }

        return json(data=health_data, message="Hệ thống đang hoạt động bình thường")

    except Exception as e:
        return fail(message="Kiểm tra sức khỏe thất bại", status=500, errors=str(e))


app.include_router(api_router, prefix="/api/v1")
