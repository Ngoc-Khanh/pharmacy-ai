from fastapi import APIRouter
from app.routes.diagnosis import router as diagnosis_router

router = APIRouter()
router.include_router(diagnosis_router) 