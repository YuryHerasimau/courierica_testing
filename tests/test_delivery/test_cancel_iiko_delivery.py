import allure
import pytest
import random
from http import HTTPStatus

from data import get_delivery_endpoints
from src.http_methods import MyRequests
from src.assertions import Assertions
from src.validator import Validator
from services.iiko_delivery_service import IikoDeliveryService


@allure.epic("Testing iiko integration")
class TestCancelIikoDelivery:
    delivery_service = IikoDeliveryService()
    request = MyRequests()
    saas_url = get_delivery_endpoints()
    assertions = Assertions()
    validator = Validator()

    @allure.title("Test cancel iiko delivery")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_cancel_iiko_order(self, get_test_name, iiko_headers, logistician_iiko_auth_headers):
        with allure.step("Создаём новый заказ через iiko API"):
            address_key, _ = random.choice(list(self.delivery_service.address_data.items()))
            order_id, delivery_point = self.delivery_service.create_order(
                address_key=address_key,
                duration=60,
                iiko_headers=iiko_headers,
            )

        with allure.step(f"Отменяем заказ {order_id}"):
            self.delivery_service.cancel_order(order_id, iiko_headers, test_name=get_test_name)

        with allure.step("Проверяем, что заказ в Курьерике перешёл в статус 'cancelled'"):
            delivery = self.delivery_service.find_delivery_by_external_id(
                external_id=order_id,
                delivery_point=delivery_point,
                auth_headers=logistician_iiko_auth_headers,
                status="canceled",
            )
            assert delivery["status"] in ["cancelled", "canceled", "отменён"], (
                f"Ожидался статус 'cancelled', но получен {delivery['status']}"
            )

        with allure.step("Запрашиваем заказ через API и проверяем, что он корректен"):
            get_response = self.request.get(
                url=f"{self.saas_url.list_of_deliveries}/{delivery['id']}",
                headers=logistician_iiko_auth_headers,
            )
            self.assertions.assert_status_code(get_response, HTTPStatus.OK, get_test_name)


    @allure.title("[Очистка] Отмена и закрытие всех заказов IIKO за сегодняшний день")
    @pytest.mark.extended
    def test_cancel_and_close_all_orders(self, get_test_name, iiko_headers):
        self.delivery_service.cancel_and_close_all_orders(iiko_headers, get_test_name)