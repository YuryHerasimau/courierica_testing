from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class IikoDeliveryDataClass:
    organization_id: str
    phone: str
    delivery_point: Dict[str, Any]
    customer: Dict[str, Any]
    items: List[Dict[str, Any]]
    payments: List[Dict[str, Any]]
    delivery_duration: int
    order_type_id: Optional[str] = None
    order_service_type: str = "DeliveryByCourier"
    comment: Optional[str] = None
    external_number: Optional[str] = None
    guests_count: int = 1
    operator_id: Optional[str] = None
    marketing_source_id: Optional[str] = None
    delivery_zone: Optional[str] = None