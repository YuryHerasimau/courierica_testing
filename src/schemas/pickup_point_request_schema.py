from pydantic import BaseModel
from typing import Optional

class Point(BaseModel):
    latitude: float
    longitude: float
class PickupPointRequestSchema(BaseModel):
    company_id: str
    name: str
    address: str
    point: Point
    external_id: Optional[str] = None
    phone: Optional[str] = None
    currency: Optional[str] = "RUB"
    firm_id: Optional[str] = None
