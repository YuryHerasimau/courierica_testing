from dataclasses import dataclass


@dataclass
class DeliveryDataClass:
    company_id: str
    pickup_point_id: str
    # external_number: str
    # external_id: str
    recipient_address: str
    # recipient_address_comment: str
    recipient_point: str
    recipient_phone: str
    recipient_name: str
    # recipient_comment: str
    # cost: float
    # to_pay_card: float
    # to_pay_cash: float
    # change: float
    payment_method: str
    paid: bool
    # ready_to_ship: bool
    time_from: str
    time_till: str
    # timezone: str
    # back_link: str
    # specification: str
    # currency: str
    # ship_cost: int