from generator.base_generator import BaseGenerator
from data.company_dataclass import CompanyDataClass
from typing import Iterator


class CompanyGenerator(BaseGenerator):
    """
    Генератор данных для компании.
    """

    def generate_company(
        self,
        name=None,
        address=None,
        phone=None,
        logo_id=None,
        integration_key_length=None,
        integration_source=None,
        external_license=None,
        invoice_customer_ids_count=0,
        contact_url=None,
        firms_count=0,
    ) -> Iterator[CompanyDataClass]:
        yield CompanyDataClass(
            name=self.get_name(name=name),
            address=self.get_address(address=address),
            phone=self.get_phone(phone=phone),
            logo_id=self.get_logo_id(logo_id=logo_id),
            integration_key=self.get_integration_key(integration_key_length=integration_key_length),
            integration_source=self.get_integration_source(integration_source=integration_source),
            external_license=self.get_external_license(external_license=external_license),
            invoice_customer_ids=self.get_invoice_customer_ids(invoice_customer_ids_count=invoice_customer_ids_count),
            contact_url=self.get_contact_url(contact_url=contact_url),
            firms=self.get_firms(firms_count=firms_count),
        )