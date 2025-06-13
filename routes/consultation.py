from fastapi import APIRouter

from database.database import *
from models.consultation import Consultations
from schemas.consultation import Response

router = APIRouter()

@router.get("/", response_description="Consultations retrieved", response_model=Response)
async def get_consultations():
    consultations = await retrieve_consultations()
    return {
        "status_code": 200,
        "response_type": "success",
        "description": "Consultations data retrieved successfully",
        "data": consultations,
    }