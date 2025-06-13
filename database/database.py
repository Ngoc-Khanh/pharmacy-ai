from typing import List, Union

from beanie import PydanticObjectId

from models.consultation import Consultations

consultation_collection = Consultations

async def retrieve_consultations() -> List[Consultations]:
    consultation = await consultation_collection.all().to_list()
    return consultation