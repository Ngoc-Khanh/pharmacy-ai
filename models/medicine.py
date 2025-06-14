from typing import List, Optional, Union
from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, validator


class Thumbnail(BaseModel):
    public_id: str
    url: str
    alt: str


class Variants(BaseModel):
    price: int
    quantity: Optional[int] = None
    limit_quantity: int
    stock_status: str
    original_price: int
    discount_percent: int
    is_featured: bool
    is_active: bool


class Ratings(BaseModel):
    star: float
    liked: int
    review_count: int


class Parameters(BaseModel):
    origin: str
    packaging: str


class Details(BaseModel):
    ingredients: str
    usage: List[str]
    paramaters: Parameters


class Dosage(BaseModel):
    adult: str
    child: str


class Usageguide(BaseModel):
    dosage: Dosage
    directions: List[str]
    precautions: List[str]


class Medicine(Document):
    id: Optional[Union[PydanticObjectId, str]] = Field(default=None, alias="_id")
    category_id: str
    supplier_id: str
    name: str
    slug: str
    thumbnail: Thumbnail
    description: str
    variants: Variants
    ratings: Ratings
    details: Details
    usageguide: Usageguide
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None

    @validator('id', pre=True)
    def validate_id(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # If it's a string UUID, keep it as string
            return v
        return v

    @validator('created_at', 'updated_at', pre=True)
    def validate_datetime(cls, v):
        if v is None:
            return v
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return v
        return str(v)

    class Settings:
        name = "medicines"
