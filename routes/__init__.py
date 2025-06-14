from fastapi import APIRouter

from .consultation import router as ConsultationRouter
from .medicine_recommendation import router as MedicineRecommendationRouter

router = APIRouter()

router.include_router(ConsultationRouter, tags=["Consultations"], prefix="/consultation")
router.include_router(MedicineRecommendationRouter, tags=["Medicine Recommendations"], prefix="/medicine-recommendation")
