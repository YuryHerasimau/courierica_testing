from src.http_methods import MyRequests
from src.assertions import Assertions
from http import HTTPStatus
from data import get_pickup_point_endpoints


class PickupPointService:
    def __init__(self):
        self.request = MyRequests()
        self.pickup_point_url = get_pickup_point_endpoints() 
        self.assertions = Assertions()

    def turn_on_delivery_mode_allow(self, get_test_name, pickup_point_id, headers):
        """Включение режима доставки курьером 'Без ограничений'"""
        response = self.request.patch(
            url=f"{self.pickup_point_url.list_of_pickup_points}/{pickup_point_id}/courier_delivered_mode/allow",
            headers=headers
        )
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.NO_CONTENT, test_name=get_test_name)
        return response

    def get_courier_delivery_mode(self, get_test_name, pickup_point_id, headers):
        """Получение настройки на пункте выдачи - Ограничение на кнопку 'Передал' в приложении курьера"""
        response = self.request.get(
            url=f"{self.pickup_point_url.list_of_pickup_points}/{pickup_point_id}",
            headers=headers
        )
        courier_delivered_mode = response.json().get("courier_delivered_mode")
        courier_delivered_mode_distance = response.json().get("courier_delivered_mode_distance")
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.OK, test_name=get_test_name)
        print(f"Courier delivery mode at pickup point {pickup_point_id}: {courier_delivered_mode}, {courier_delivered_mode_distance}")
        return courier_delivered_mode, courier_delivered_mode_distance