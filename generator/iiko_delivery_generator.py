import random
from typing import Iterator, Dict, List, Optional
from datetime import datetime, timedelta
from generator.base_generator import BaseGenerator
from data.iiko_delivery_dataclass import IikoDeliveryDataClass

class IikoDeliveryGenerator(BaseGenerator):
    def __init__(self):
        self.default_product_id = "29a32e2b-e3c7-4e7a-9750-a1f10c45e0fa"
        self.default_payment_type_id = "09322f46-578a-d210-add7-eec222a08871"
        self.default_operator_id = "b910f793-971e-4db5-a230-f8e9a8f86167"
    """
    Генератор данных для заказов iiko.
    """
    
    def generate_iiko_order(
        self,
        organizationId: str,
        delivery_duration: int = 60,
        delivery_point: dict = None,
        **kwargs
    ) -> Iterator[IikoDeliveryDataClass]:
        base_data = {
            "organization_id": organizationId,
            "phone": "+7" + "".join([str(random.randint(0, 9)) for _ in range(10)]),
            "delivery_point": delivery_point or {
                "coordinates": {
                    "latitude": round(55.75 + random.uniform(-0.05, 0.05), 6),
                    "longitude": round(37.6 + random.uniform(-0.1, 0.1), 6)
                },
                "address": {
                    "type": "city",
                    "line1": "Москва, тестовая улица, д. " + str(random.randint(1, 100))
                },
                "externalCartographyId": None,
                "comment": None
            },
            "customer": kwargs.get("customer", {
                "type": "one-time",
                "name": f"Тестовый Клиент {random.randint(1, 1000)}"
            }),
            "items": kwargs.get("items", [{
                "type": "Product",
                "amount": 1,
                "productId": self.default_product_id,
                "price": 200,
                "comment": None
            }]),
            "payments": kwargs.get("payments", [{
                "paymentTypeKind": "Cash",
                "sum": 200,
                "paymentTypeId": self.default_payment_type_id,
                "isProcessedExternally": True,
                "paymentAdditionalData": None,
                "isFiscalizedExternally": False,
                "isPrepay": True
            }]),
            "delivery_duration": delivery_duration,
            "operator_id": kwargs.get("operator_id", self.default_operator_id)
        }
        
        # Объединяем с переданными параметрами
        final_data = {**base_data, **kwargs}
        yield IikoDeliveryDataClass(**final_data)
    
    def _generate_delivery_point(self, point_data) -> Dict:
        if point_data is None:
            return {
                "coordinates": {
                    "latitude": float(self.faker.latitude()), # 55.793728
                    "longitude": float(self.faker.longitude()) # 37.614428
                },
                "address": {
                    "type": "city",
                    "line1": self.get_address(address=None) # "Москва, улица Сущёвский Вал, 55"
                },
                "externalCartographyId": None,
                "comment": None
            }
        return point_data
    
    def _generate_customer(self, customer_data) -> Dict:
        if customer_data is None:
            return {
                "type": "one-time",
                "name": self.faker.name(),
            }
        return customer_data
    
    def _generate_items(self, items_data) -> List[Dict]:
        if items_data is None:
            return [{
                "type": "Product",
                "amount": 1,
                "productId": self.default_product_id,
                "comment": None,
                "price": 200
            } for _ in range(random.randint(1, 5))]
        return items_data
    
    def _generate_payments(self, payments_data):
        if payments_data is None:
            return [{
                "paymentTypeKind": "Cash",
                "sum": 200,
                "paymentTypeId": self.default_payment_type_id,
                "isProcessedExternally": True,
                "paymentAdditionalData": None,
                "isFiscalizedExternally": False,
                "isPrepay": True
            }]
        return payments_data
    
    def _generate_order_type(self, order_type_data):
        if order_type_data is None:
            return {
                "id": None,
                "name": "Доставка курьером",
                "orderServiceType": "DeliveryByCourier"
            }
        return order_type_data
    
    def _get_default_complete_before(self):
        return (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S.000")