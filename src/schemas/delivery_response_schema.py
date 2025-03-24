from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class Point(BaseModel):
    latitude: float
    longitude: float

class Company(BaseModel):
    id: str
    name: str
    integration_source: str

class PickupPoint(BaseModel):
    id: str
    name: str
    address: str
    hide_recipient_address: bool
    point: Point
    enabled: bool

class Author(BaseModel):
    id: str
    external_id: Optional[str]
    name: str
    last_name: Optional[str]

class Event(BaseModel):
    id: str
    type: str
    name: str
    author: Author
    point: Optional[Point]
    comment: Optional[str]
    created_at: datetime

class Specification(BaseModel):
    items: Optional[List]
    delivered_partially: bool

class DeliveryDetailsSchema(BaseModel):
    id: str
    number: str
    company_id: str
    company: Company
    pickup_point: PickupPoint
    courier: Optional[str]
    external_id: Optional[str]
    external_number: str
    recipient_name: str
    recipient_phone: str
    recipient_address: str
    recipient_address_comment: Optional[str]
    recipient_point: Point
    recipient_comment: Optional[str]
    payment_method: Optional[str] = None # См. вопрос №2 в TO DO
    cost: float
    to_pay: float
    to_pay_card: float
    to_pay_cash: float
    change: float
    paid: bool
    ship_cost: float
    status: str
    ready_to_ship: bool
    is_on_way: bool
    specification: Optional[Specification]
    events: List[Event]
    tpl_lock: bool
    time_from: datetime
    time_till: datetime
    timezone: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    decision_3pl: Optional[str]
    time_deadline_3pl: Optional[str]
    time_deadline_auto_assign: Optional[str]
    autoassign_deadline_processed: bool
    when_ready_to: Optional[str]
    time_to_assigns: Dict = Field(default_factory=Dict)
    last_minute: Dict = Field(default_factory=Dict)
    back_link: Optional[str]
    currency: str
    route_step_points_fact: List[Point] = Field(default_factory=List)
    route_step_points_plan: List[Point] = Field(default_factory=List)