from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import os
import logging
from app.routes import router as api_router
from app.database import connect_to_mongo, close_mongo_connection
from app.utils.response import create_success_response, create_error_response, create_validation_error_response
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pharmacy AI Backend",
    description="Backend đơn giản sử dụng FastAPI cho ứng dụng AI dược phẩm với standardized response format",
    version="2.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler với standardized response"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message="Có lỗi HTTP xảy ra",
            status=exc.status_code,
            errors=str(exc.detail)
        )
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Global validation exception handler với standardized response"""
    logger.error(f"Validation Error: {exc.errors()}")
    validation_errors = [f"{error['loc'][-1]}: {error['msg']}" for error in exc.errors()]
    return JSONResponse(
        status_code=422,
        content=create_validation_error_response(
            validation_errors=validation_errors,
            message="Dữ liệu đầu vào không hợp lệ"
        )
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global general exception handler với standardized response"""
    logger.error(f"Unexpected Error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            message="Có lỗi không mong muốn xảy ra",
            status=500,
            errors=str(exc)
        )
    )

# Database connection events
@app.on_event("startup")
async def startup_event():
    """Sự kiện khởi động - kết nối MongoDB"""
    try:
        await connect_to_mongo()
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Sự kiện tắt - đóng kết nối MongoDB"""
    try:
        await close_mongo_connection()
        logger.info("Database connection closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Endpoint kiểm tra sức khỏe với standardized response"""
    return create_success_response(
        data={
            "service": "Pharmacy AI Backend",
            "version": "2.0.0",
            "status": "đang chạy",
            "features": [
                "Multiple AI Diagnosis (GroqCloud, Gemini, DeepSeek)",
                "Standardized API Response Format", 
                "MongoDB Integration",
                "Multiple Input Formats Support"
            ]
        },
        message="Chào mừng đến với Pharmacy AI Backend v2.0"
    )

@app.get("/health")
async def health_check():
    """Endpoint kiểm tra sức khỏe chi tiết với standardized response"""
    try:
        # Check database connection
        from app.database import get_database
        db = get_database()
        db_status = "connected" if db else "disconnected"
        
        health_data = {
            "service": "pharmacy-ai-backend",
            "status": "khỏe mạnh",
            "version": "2.0.0",
            "database": db_status,
            "endpoints": {
                "groq_diagnosis": "/api/v1/groq/diagnose",
                "gemini_diagnosis": "/api/v1/diagnosis/analyze", 
                "deepseek_diagnosis": "/api/v1/deepseek-diagnosis/analyze"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        return create_success_response(
            data=health_data,
            message="Hệ thống đang hoạt động bình thường"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return create_error_response(
            message="Kiểm tra sức khỏe thất bại",
            status=500,
            errors=str(e)
        )

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Pharmacy AI Backend on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
