from fastapi import APIRouter, HTTPException
from typing import List, Dict
from app.services.database_service import db_service
from pydantic import BaseModel

router = APIRouter()

# === DATABASE STATUS ===
@router.get("/status")
async def database_status():
    """Kiểm tra trạng thái kết nối database"""
    try:
        from app.database import get_database
        db = get_database()
        if db is None:
            raise HTTPException(status_code=503, detail="Chưa kết nối database")
        
        # Test connection bằng cách đếm collections
        collections = await db.list_collection_names()
        return {
            "status": "connected",
            "message": "Kết nối MongoDB thành công",
            "collections": collections
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Lỗi kết nối database: {str(e)}") 