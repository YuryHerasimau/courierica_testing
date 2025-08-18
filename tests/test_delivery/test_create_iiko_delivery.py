import random
import time
import allure
from http import HTTPStatus

from data import get_delivery_endpoints
from services.iiko_delivery_service import IikoDeliveryService
from src.http_methods import MyRequests
from src.assertions import Assertions
from src.validator import Validator
from src.schemas import GetDeliverySchemas
from settings import settings


@allure.epic("Testing iiko integration")
class TestCreateIikoDelivery:
    delivery_service = IikoDeliveryService()
    request = MyRequests()
    saas_url = get_delivery_endpoints()
    assertions = Assertions()
    validator = Validator()

    @allure.title("Test create random iiko delivery")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_random_iiko_delivery(self, get_test_name, iiko_headers, logistician_iiko_auth_headers):
        # Генерация случайного адреса и времени
        address_key, _ = random.choice(list(self.delivery_service.address_data.items()))
        delivery_duration = random.randint(60, 1 * 24 * 60)  # от 1 часа до 1 суток

        order_id, delivery_point = self.delivery_service.create_order(
            address_key=address_key,
            duration=delivery_duration,
            iiko_headers=iiko_headers,
        )

        # Поиск IIKO заказа в Курьерике
        iiko_delivery = self.delivery_service.find_delivery_by_external_id(
            external_id=order_id,
            delivery_point=delivery_point,
            auth_headers=logistician_iiko_auth_headers
        )
        assert iiko_delivery["external_id"] == order_id
        assert iiko_delivery["pickup_point"]["id"] == settings.COURIERICA_PICKUP_POINT_ID
        assert iiko_delivery["company"]["integration_source"] == "iiko"

        get_response  = self.request.get(
            url=f"{self.saas_url.list_of_deliveries}/{iiko_delivery['id']}",
            headers=logistician_iiko_auth_headers,
        )
        self.assertions.assert_status_code(get_response, HTTPStatus.OK, get_test_name)
        self.validator.validate_response(get_response, GetDeliverySchemas.get_delivery_by_id)

    @allure.title("Test create given number of random iiko deliveries")
    @allure.severity(allure.severity_level.MINOR)
    def test_create_given_number_of_random_iiko_deliveries(self, iiko_headers, logistician_iiko_auth_headers, number_of_deliveries=5):
        delivery_ids = []
        
        for i in range(number_of_deliveries):
            print(f"Creating delivery #{i+1}...")
            # Генерация случайного адреса и времени
            address_key, _ = random.choice(list(self.delivery_service.address_data.items()))
            delivery_duration = random.randint(60, 1 * 24 * 60)  # от 1 часа до 1 суток
            order_id, delivery_point = self.delivery_service.create_order(
                address_key=address_key,
                duration=delivery_duration,
                iiko_headers=iiko_headers,
            )

            # Поиск IIKO заказа в Курьерике
            iiko_delivery = self.delivery_service.find_delivery_by_external_id(
                external_id=order_id,
                delivery_point=delivery_point,
                auth_headers=logistician_iiko_auth_headers
            )
            assert iiko_delivery["external_id"] == order_id
            delivery_ids.append(iiko_delivery["id"])
            time.sleep(0.5)

        print(delivery_ids)
