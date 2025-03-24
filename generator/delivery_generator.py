from generator.base_generator import BaseGenerator
from data.delivery_dataclass import DeliveryDataClass
from typing import Iterator


class DeliveryGenerator(BaseGenerator):
    """
    Генератор данных для доставки.
    """

    def generate_delivery(
        self,
        company_id=None,
        pickup_point_id=None,
        recipient_address=None,
        recipient_point=None,
        recipient_phone=None,
        recipient_name=None,
        payment_method=None,
        paid=None,
        time_from=None,
        time_till=None,
    ) -> Iterator[DeliveryDataClass]:
        yield DeliveryDataClass(
            company_id=self.get_id(uid=company_id),
            pickup_point_id=self.get_id(uid=pickup_point_id),
            recipient_address=self.get_address(address=recipient_address),
            recipient_point=self.get_point(point=recipient_point),
            recipient_phone=self.get_phone(phone=recipient_phone),
            recipient_name=self.get_name(name=recipient_name),
            payment_method=self.get_payment_method(payment_method=payment_method),
            paid=self.get_paid(paid=paid),
            time_from=self.get_time_from(time_from=time_from),
            time_till=self.get_time_till(time_till=time_till),
        )