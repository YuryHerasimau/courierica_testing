import json
from src.http_methods import MyRequests
from src.assertions import Assertions
from http import HTTPStatus
from data import get_delivery_endpoints


class DeliveryService:
    def __init__(self):
        self.request = MyRequests()
        self.delivery_url = get_delivery_endpoints()
        self.assertions = Assertions()

    def create_delivery(self, get_test_name, data, headers):
        """Создание заказа"""
        response = self.request.post(url=self.delivery_url.create_delivery, data=data, headers=headers)
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.CREATED, test_name=get_test_name)
        delivery_id = response.json().get("id")
        print(f"Order with ID {delivery_id} created.")
        return delivery_id

    def assign_delivery(self, get_test_name, delivery_id, courier_id, headers):
        """Назначение курьера на заказ"""
        response = self.request.patch(
            url=f"{self.delivery_url.list_of_deliveries}/{delivery_id}/courier/{courier_id}",
            headers=headers
        )
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.NO_CONTENT, test_name=get_test_name)
        print(f"Courier {courier_id} is assigned to order {delivery_id}")
        return response

    def complete_delivery(self, get_test_name, delivery_id, status, headers):
        """Завершение доставки заказа"""
        response = self.request.patch(
            url=f"{self.delivery_url.list_of_deliveries}/{delivery_id}/status/{status}",
            headers=headers
        )
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.NO_CONTENT, test_name=get_test_name)
        print(f"Completion of delivery. Status: {status}, Order ID: {delivery_id}")
        return response

    def complete_delivery_with_reason(self, get_test_name, delivery_id, status, reason, headers):
        """Завершение доставки заказа с указанием причины (только для 'delivered' в режиме 'reason')."""

        # Если статус НЕ 'delivered', отправляем запрос без данных (как обычное завершение доставки)
        if status != "delivered":
            return self.complete_delivery(get_test_name, delivery_id, status, headers)

        if not reason:
            raise ValueError("It is necessary to indicate the reason for the completion of delivery outside the address.")

        # Подготовка данных для 'delivered'
        request_payload = {
            "delivered": {
                "reason": reason.get("reason"),  # Добавить значение по умолчанию - 6?
                "comment": reason.get("comment")  # Добавить значение по умолчанию - autotest?
            }
        }

        # Завершаем доставку со статусом 'delivered' и передаем payload
        response = self.request.patch(
            url=f"{self.delivery_url.list_of_deliveries}/{delivery_id}/status/{status}",
            headers=headers,
            data=json.dumps(request_payload)
        )
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.NO_CONTENT, test_name=get_test_name)
        print(f"Completion of delivery. Payload: {request_payload}, Status: {status}, Order ID: {delivery_id}")
        
        # Получаем данные о завершенной доставке
        # response_order = self.request.get(url=f"{self.delivery_url.list_of_deliveries}/{delivery_id}", headers=headers)
        # print(f"Причина завершения доставки: {response_order.json().get('events')[0].get('comment')}")
            
        return response
