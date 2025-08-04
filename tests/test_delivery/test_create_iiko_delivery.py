import random
import time
import allure
import pytest
import json
from datetime import datetime
from http import HTTPStatus

from data import get_iiko_endpoints, get_delivery_endpoints
from src.http_methods import MyRequests
from src.assertions import Assertions
from src.validator import Validator
from src.schemas import GetDeliverySchemas
from src.prepare_data.prepare_iiko_delivery_data import PrepareIikoDeliveryData
from generator.iiko_delivery_generator import IikoDeliveryGenerator
from settings import settings
from functions import load_json


@allure.epic("Testing iiko integration")
class TestCreateIikoDelivery:
    request = MyRequests()
    iiko_url = get_iiko_endpoints()
    saas_url = get_delivery_endpoints()
    assertions = Assertions()
    validator = Validator()
    iiko_delivery_generator = IikoDeliveryGenerator()
    iiko_delivery_data = PrepareIikoDeliveryData(generator=iiko_delivery_generator)
    
    def _wait_for_order_status(self, headers, organization_id, correlation_id, timeout=60):
        """Ожидание успешного статуса заказа с таймаутом"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            status_response = self.request.post(
                url=self.iiko_url.check_status,
                data=json.dumps({
                    "organizationId": organization_id,
                    "correlationId": correlation_id
                }),
                headers=headers
            )
            print(status_response.json())

            status = status_response.json().get("state")
            if status == "Success":
                return True
            elif status == "Error":
                raise AssertionError("Order creation failed")
            
            time.sleep(3)
        
        raise AssertionError(f"Order status check timeout. Last status: {status}")
    
    def _find_delivery_by_external_id(self, external_id, delivery_point, auth_headers):
        """Поиск заказа в Курьерике по external_id"""
        today = datetime.now().strftime("%Y-%m-%d")
        search_address = delivery_point["address"]["line1"]
        
        response = self.request.get(
            url=f"{self.saas_url.list_of_deliveries}" \
                f"?pickup_point_id={settings.COURIERICA_PICKUP_POINT_ID}" \
                f"&created_at_from={today}" \
                f"&statuses=new" \
                f"&search={search_address}" \
                f"&page=1&per_page=10",
            headers=auth_headers,
        )
        
        self.assertions.assert_status_code(response, HTTPStatus.OK)
        
        deliveries = response.json().get("deliveries", [])
        for delivery in deliveries:
            if delivery.get("external_id") == external_id:
                print("delivery found is", delivery.get("external_number"))
                return delivery
        
        raise AssertionError(f"Delivery with external_id {external_id} not found. Searched address: {search_address}")

    @allure.title("Test create iiko delivery order")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_create_iiko_delivery(self, get_test_name, iiko_headers, logistician_iiko_auth_headers):
        address_data = load_json("tests/e2e/config/iiko_address_data.json")

        # Генерация случайного адреса и времени
        _, address_info = random.choice(list(address_data.items()))
        delivery_duration = random.randint(60, 3 * 24 * 60)  # от 1 часа до 3 суток

        # Генерация данных
        info = next(self.iiko_delivery_generator.generate_iiko_order(
            organizationId=settings.IIKO_ORGANIZATION_ID,
            delivery_duration=delivery_duration,
            delivery_point= {
                "coordinates": {
                    "latitude": address_info["latitude"],
                    "longitude": address_info["longitude"]
                },
                "address": {
                    "type": "city",
                    "line1": address_info["line1"]
                }
            }
        ))

        # Подготовка и отправка запроса для создания заказа в IIKO
        data = self.iiko_delivery_data.prepare_iiko_delivery_data(info=info)
        response = self.request.post(url=self.iiko_url.create_order, data=data, headers=iiko_headers)

        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.OK,
            test_name=get_test_name,
        )

        order_id = response.json()["orderInfo"]["id"]
        correlation_id = response.json()["correlationId"]
        
        # Ожидание успешного создания заказа
        self._wait_for_order_status(
            headers=iiko_headers,
            organization_id=settings.IIKO_ORGANIZATION_ID,
            correlation_id=correlation_id
        )

        # Поиск IIKO заказа в Курьерике
        iiko_delivery = self._find_delivery_by_external_id(
            external_id=order_id,
            delivery_point=info.delivery_point,
            auth_headers=logistician_iiko_auth_headers
        )

        assert iiko_delivery["external_id"] == order_id
        assert iiko_delivery["pickup_point"]["id"] == settings.COURIERICA_PICKUP_POINT_ID
        assert iiko_delivery["company"]["integration_source"] == "iiko"

        get_response  = self.request.get(
            url=f"{self.saas_url.list_of_deliveries}/{iiko_delivery['id']}",
            headers=logistician_iiko_auth_headers,
        )
        self.assertions.assert_status_code(
            response=get_response,
            expected_status_code=HTTPStatus.OK,
            test_name=get_test_name,
        )
        self.validator.validate_response(response=get_response, model=GetDeliverySchemas.get_delivery_by_id)
