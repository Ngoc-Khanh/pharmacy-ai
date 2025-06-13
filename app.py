from fastapi import FastAPI, Depends

from auth.jwt_bearer import JWTBearer
from config.config import initiate_database
from routes.consultation import router as ConsultationRouter

app = FastAPI()

token_listener = JWTBearer()

@app.on_event("startup")
async def start_database():
    await initiate_database()


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "API AI Service for Pharmacy Store"}

app.include_router(ConsultationRouter, tags=["Consultations"], prefix="/v1/consultation")