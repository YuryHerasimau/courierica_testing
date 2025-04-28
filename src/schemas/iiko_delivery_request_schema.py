from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

class IikoDeliveryRequestSchema(BaseModel):
    organizationId: str
    order: Dict[str, Any]