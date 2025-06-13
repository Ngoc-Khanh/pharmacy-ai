from fastapi import APIRouter

from .consultation import router as ConsultationRouter

router = APIRouter()

router.include_router(ConsultationRouter, tags=["Consultations"], prefix="/consultation")
