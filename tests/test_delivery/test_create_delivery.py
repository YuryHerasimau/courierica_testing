import allure
import pytest
import json
import random
from data import get_delivery_endpoints
from src.http_methods import MyRequests
from src.assertions import Assertions
from src.validator import Validator
from src.schemas import GetDeliverySchemas
from src.prepare_data.prepare_delivery_data import PrepareDeliveryData
from http import HTTPStatus
from generator.delivery_generator import DeliveryGenerator


@allure.epic("Testing create delivery")
class TestCreateDelivery:
    request = MyRequests()
    url = get_delivery_endpoints()
    assertions = Assertions()
    validator = Validator()
    delivery_data = PrepareDeliveryData()
    delivery_generator = DeliveryGenerator()

    # SAAS

    @allure.title("Create SAAS delivery")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_saas_delivery(self, get_test_name, logistician_saas_auth_headers):
        info = next(self.delivery_generator.generate_delivery(
                company_id="ac6d1196-3488-49b0-b670-8361bca1d8d6", # BSL
                pickup_point_id="9f8896d7-3f85-4d8c-9d6e-e0b9c672cf9a", # ПВ в Минске
                recipient_address="Беларусь, г Минск, ул Брестская, д 68 к 1",
                recipient_point={
                    "latitude": 53.85426,
                    "longitude": 27.51933
                },
            ),
        )
        data = self.delivery_data.prepare_delivery_data(info=info)
        # print(data)

        # Выполнение POST-запроса для создания доставки
        response = self.request.post(url=self.url.create_delivery, data=data, headers=logistician_saas_auth_headers)
        # print(response.json())

        # Проверка статуса ответа
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.CREATED,
            test_name=get_test_name,
        )

        # Получаем ID созданного заказа
        delivery_id = response.json().get("id")

        # Выполнение GET-запроса для проверки созданной доставки
        get_response  = self.request.get(
            url=f"{self.url.list_of_deliveries}/{delivery_id}",
            headers=logistician_saas_auth_headers,
        )
        # print(get_response.json())

        # Проверка статуса ответа от GET-запроса
        self.assertions.assert_status_code(
            response=get_response,
            expected_status_code=HTTPStatus.OK,
            test_name=get_test_name,
        )

        # Проверка данных в ответе от GET-запроса
        self.validator.validate_response(response=get_response, model=GetDeliverySchemas.get_delivery_by_id)
