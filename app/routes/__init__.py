from fastapi import APIRouter
from app.routes.diagnosis import router as diagnosis_router
from app.routes.deepseek_diagnosis import router as deepseek_diagnosis_router


router = APIRouter()
router.include_router(diagnosis_router)
router.include_router(deepseek_diagnosis_router)
