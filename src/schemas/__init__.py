from src.schemas import company_response_schema, delivery_response_schema


class GetCompanySchemas:
    """Класс для хранения схем получения информации о компаниях."""

    create_company = company_response_schema.CompanyDetailsSchema
    get_company_by_id = company_response_schema.CompanyDetailsSchema
    get_companies = company_response_schema.CompaniesListSchema

class GetDeliverySchemas:
    """Класс для хранения схем получения информации о доставках."""

    create_delivery = delivery_response_schema.DeliveryDetailsSchema
    get_delivery_by_id = delivery_response_schema.DeliveryDetailsSchema
    get_deliveries = delivery_response_schema.DeliveriesListSchema