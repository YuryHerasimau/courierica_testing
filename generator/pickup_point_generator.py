from generator.base_generator import BaseGenerator
from data.pickup_point_dataclass import PickupPointDataClass
from typing import Iterator


class PickupPointGenerator(BaseGenerator):
    """
    Генератор данных для пункта выдачи.
    """
    def generate_pickup_point(
        self,
        company_id: str,
        name=None,
        address=None,
        point=None,
        external_id=None,
        phone=None,
        currency="RUB",
        firm_id=None,
    ) -> Iterator[PickupPointDataClass]:
        yield PickupPointDataClass(
            company_id=company_id,
            external_id=self.get_id(external_id),
            name=self.get_name(name=name),
            address=self.get_address(address=address),
            phone=self.get_phone(phone=phone),
            point=self.get_point(point),
            currency=currency,
            firm_id=self.get_id(firm_id) if firm_id else None,
        )
