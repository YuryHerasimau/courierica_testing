from pydantic import BaseModel, field_validator, AnyUrl
from typing import Optional, List


class Firm(BaseModel):
    id: str
    name: str


class CompanyDetailsSchema(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    logo_id: Optional[str] = None
    is_external: bool
    integration_key: Optional[str] = None
    integration_source: str
    auto_assign_enabled: bool
    eta_enabled: bool
    external_license: bool
    check_courier_slot_enabled: bool
    invoice_customer_ids: Optional[List[str]] = []
    contact_url: Optional[AnyUrl] = None
    firms: Optional[List[Firm]] = []
    created_at: str
    updated_at: Optional[str] = None

    @field_validator("name")
    def check_name(cls, v: str) -> str:
        if len(v) > 50:
            raise ValueError("Name must be less than 50 characters")
        if v is None or v.strip() == "":
            raise ValueError("Name cannot be None or an empty string")
        return v

    @field_validator("address")
    def check_address(cls, v: str) -> str:
        if len(v) > 200:
            raise ValueError("Address must be less than 200 characters")
        return v

    @field_validator("phone")
    def check_phone(cls, v: str) -> str:
        if v is None or v == "":
            return v

        cleaned_v = (
            v.replace("+", "")
            .replace("(", "")
            .replace(")", "")
            .replace(" ", "")
            .replace("-", "")
        )
        length = len(cleaned_v)
        if length < 10 or length > 18:
            raise ValueError("Phone must be between 10 and 18 characters")
        return v

    @field_validator("integration_key")
    def check_integration_key(cls, v: str) -> str:
        if v is not None:
            if len(v) < 8 or len(v) > 50:
                raise ValueError("Integration key must be between 8 and 50 characters long")
        return v

    @field_validator("integration_source")
    def check_integration_source(cls, v: str) -> str:
        if v not in ["iiko", "1c", "rkeeper", "saas"]:
            raise ValueError(
                f'Invalid integration source: {v}. Integration source must be one of ["iiko", "1c", "rkeeper", "saas"]'
            )
        return v


class Pagination(BaseModel):
    page: int
    per_page: int
    total: int


class CompaniesListSchema(BaseModel):
    companies: List[CompanyDetailsSchema]
    pagination: Pagination
