from typing import List, Optional, Union
from uuid import UUID, uuid4
from datetime import datetime

from beanie import Document
from pydantic import BaseModel, Field


class Thumbnail(BaseModel):
    public_id: str
    url: str
    alt: str


class Variants(BaseModel):
    price: int
    quantity: int
    limit_quantity: int
    stock_status: str
    original_price: float
    discount_percent: int
    is_featured: bool
    is_active: bool


class Ratings(BaseModel):
    star: float
    liked: int
    review_count: int


class Paramaters(BaseModel):
    origin: str
    packaging: str


class Details(BaseModel):
    ingredients: str
    usage: List[str]
    paramaters: Paramaters


class Dosage(BaseModel):
    adult: str
    child: str


class UsageGuide(BaseModel):
    dosage: Dosage
    directions: List[str]
    precautions: List[str]


class Medicine(Document):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    category_id: str
    supplier_id: str
    name: str
    slug: str
    thumbnail: Thumbnail
    description: str
    variants: Variants
    ratings: Ratings
    details: Details
    usageguide: UsageGuide
    created_at: Optional[Union[str, datetime]] = None
    updated_at: Optional[Union[str, datetime]] = None

    class Settings:
        name = "medicines"