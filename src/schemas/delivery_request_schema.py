from pydantic import BaseModel
from typing import Optional, List, Dict


class DeliveryRequestSchema(BaseModel):
    company_id: str
    pickup_point_id: str
    # external_number: Optional[str] = None
    # external_id: Optional[str] = None
    recipient_address: str
    # recipient_address_comment: Optional[str] = None
    recipient_point: Dict
    recipient_phone: str
    recipient_name: str
    # recipient_comment: Optional[str] = None
    # cost: float
    # to_pay_card: float
    # to_pay_cash: float
    # change: float
    # payment_method: str
    paid: bool
    # ready_to_ship: bool
    time_from: str
    time_till: str
    # timezone: Optional[str] = None
    # back_link: Optional[str] = None
    # specification: Optional[str] = None
    # currency: Optional[str] = None
    # ship_cost: Optional[int] = None