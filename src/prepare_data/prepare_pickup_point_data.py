from data.pickup_point_dataclass import PickupPointDataClass
from src.prepare_data.prepare_basic_data import BaseTestData
from src.schemas.pickup_point_request_schema import PickupPointRequestSchema, Point


class PreparePickupPointData(BaseTestData):
    """
    Класс для подготовки данных пункта выдачи в формате, подходящем для HTTP-запросов.
    """
    def prepare_pickup_point_json(self, info: PickupPointDataClass) -> str:
        data = PickupPointRequestSchema(
            company_id=info.company_id,
            name=info.name,
            address=info.address,
            phone=info.phone,
            external_id=info.external_id,
            point=Point(**info.point),
            currency=info.currency,
            firm_id=info.firm_id,
        )
        self.attach_request(request=data.model_dump())
        return data.model_dump_json()
