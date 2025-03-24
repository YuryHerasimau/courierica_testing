from pydantic import BaseModel
from typing import Optional, List


class Firm(BaseModel):
    id: str
    name: str


class CompanyRequestSchema(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    logo_id: Optional[str] = None
    integration_key: Optional[str] = None
    integration_source: Optional[str] = None
    external_license: bool
    invoice_customer_ids: Optional[List[str]] = []
    contact_url: Optional[str] = None
    firms: Optional[List[Firm]] = []
