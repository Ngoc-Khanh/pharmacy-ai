from fastapi import APIRouter

from .consultation import router as ConsultationRouter
from .embed import router as EmbedRouter
from .medicine import router as MedicineRouter

router = APIRouter()

router.include_router(ConsultationRouter, tags=["Consultations"], prefix="/consultation")
router.include_router(EmbedRouter, tags=["Embeds"], prefix="/embed")
router.include_router(MedicineRouter, tags=["Medicines"], prefix="/medicine")