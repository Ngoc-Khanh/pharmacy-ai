from fastapi import APIRouter
from app.routes.database import router as database
from app.routes.groq_diagnosis import router as groq_diagnosis_router

router = APIRouter()

router.include_router(database)
router.include_router(groq_diagnosis_router)
