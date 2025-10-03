from data.iiko_delivery_dataclass import IikoDeliveryDataClass
from generator.iiko_delivery_generator import IikoDeliveryGenerator
from src.prepare_data.prepare_basic_data import BaseTestData
from src.schemas.iiko_delivery_request_schema import IikoDeliveryRequestSchema

class PrepareIikoDeliveryData(BaseTestData):
    """
    Класс для подготовки данных заказов iiko в формате, подходящем для HTTP-запросов.
    """
    def __init__(self, generator: IikoDeliveryGenerator):
        self.generator = generator
    
    def prepare_iiko_delivery_data(self, info: IikoDeliveryDataClass) -> str:
        """
        Подготавливает данные заказа iiko в формате JSON.

        :param info: Данные заказа iiko в виде объекта IikoDeliveryDataClass.
        :return: JSON-строка с данными заказа iiko.
        """
        data = IikoDeliveryRequestSchema(
            organizationId=info.organization_id,
            order={
                "menuId": None,
                "id": None,
                "externalNumber": info.external_number,
                "phone": info.phone,
                "phoneExtension": info.phone_extension,
                "orderTypeId": info.order_type_id,
                "orderServiceType": info.order_service_type,
                "deliveryPoint": info.delivery_point,
                "comment": info.comment,
                "customer": info.customer,
                "guests": {
                    "count": info.guests_count,
                    "splitBetweenPersons": False
                },
                "marketingSourceId": info.marketing_source_id,
                "operatorId": info.operator_id,
                "deliveryDuration": info.delivery_duration,
                "deliveryZone": info.delivery_zone,
                "items": info.items,
                "payments": info.payments,
                "tips": None,
                "sourceKey": None,
                "discountsInfo": None,
                "loyaltyInfo": {
                    "coupon": None,
                    "applicableManualConditions": None
                },
                "chequeAdditionalInfo": None,
                "externalData": None
            }
        )
        self.attach_request(request=data.model_dump())
        return data.model_dump_json()