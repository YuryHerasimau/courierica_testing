from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Point(BaseModel):
    latitude: float
    longitude: float

class PickupPointDetailsSchema(BaseModel):
    id: str
    company_id: str
    name: str
    address: str
    phone: Optional[str] = None
    point: Point
    zone: Optional[List[Point]] = Field(default_factory=list)
    currency: Optional[str] = "RUB"
    firm_id: Optional[str] = None
    created_at: str
    updated_at: Optional[datetime] = None

class Pagination(BaseModel):
    page: int
    per_page: int
    total: int

class PickupPointsListSchema(BaseModel):
    pickup_points: List[PickupPointDetailsSchema]
    pagination: Pagination