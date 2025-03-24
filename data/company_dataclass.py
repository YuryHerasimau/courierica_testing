from dataclasses import dataclass


@dataclass
class CompanyDataClass:
    name: str
    address: str
    phone: str
    logo_id: str
    integration_key: str
    integration_source: str
    external_license: bool
    invoice_customer_ids: list[str]  # str
    contact_url: str
    firms: dict