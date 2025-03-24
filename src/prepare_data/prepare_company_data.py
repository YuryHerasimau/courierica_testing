from data.company_dataclass import CompanyDataClass
from src.prepare_data.prepare_basic_data import BaseTestData
from src.schemas.company_request_schema import CompanyRequestSchema


class PrepareCompanyData(BaseTestData):
    """
    Класс для подготовки данных компании в формате, подходящем для HTTP-запросов.
    """

    def prepare_company_json(self, info: CompanyDataClass) -> str:
        """
        Подготавливает данные компании в формате JSON.

        :param info: Данные компании в виде объекта CompanyDataClass.
        :return: JSON-строка с данными компании.
        """
        data = CompanyRequestSchema(
            name=info.name,
            address=info.address,
            phone=info.phone,
            logo_id=info.logo_id,
            integration_key=info.integration_key,
            integration_source=info.integration_source,
            external_license=info.external_license,
            invoice_customer_ids=info.invoice_customer_ids,
            contact_url=info.contact_url,
            # firms=info.firms,
            firms=[firm for firm in info.firms],
        )
        self.attach_request(request=data.model_dump())  # Вместо __dict__
        return data.model_dump_json()