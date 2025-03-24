from data.delivery_dataclass import DeliveryDataClass
from src.prepare_data.prepare_basic_data import BaseTestData
from src.schemas.delivery_request_schema import DeliveryRequestSchema


class PrepareDeliveryData(BaseTestData):
    """
    Класс для подготовки данных доставки в формате, подходящем для HTTP-запросов.
    """

    def prepare_delivery_data(self, info: DeliveryDataClass) -> str:
        """
        Подготавливает данные доставки в формате JSON.

        :param info: Данные доставки в виде объекта DeliveryDataClass.
        :return: JSON-строка с данными доставки.
        """
        data = DeliveryRequestSchema(
            company_id=info.company_id,
            pickup_point_id=info.pickup_point_id,
            recipient_address=info.recipient_address,
            recipient_point=info.recipient_point,
            recipient_phone=info.recipient_phone,
            recipient_name=info.recipient_name,
            payment_method=info.payment_method,
            paid=info.paid,
            time_from=info.time_from,
            time_till=info.time_till,
        )
        # Передаем данные как словарь для прикрепления
        # `__dict__` позволяет получить словарь с атрибутами, который можно правильно отформатировать
        self.attach_request(request=data.model_dump())
        return data.model_dump_json()