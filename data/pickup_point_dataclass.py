from dataclasses import dataclass


@dataclass
class PickupPointDataClass:
    company_id: str
    name: str
    address: str
    point: dict
    external_id: str = None
    phone: str = None
    currency: str = "RUB"
    firm_id: str = None
