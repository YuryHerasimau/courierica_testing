import json
import time
import allure
from datetime import datetime
from http import HTTPStatus

from settings import settings
from functions import load_json, retry
from src.http_methods import MyRequests
from src.assertions import Assertions
from src.validator import Validator
from generator.iiko_delivery_generator import IikoDeliveryGenerator
from src.prepare_data.prepare_iiko_delivery_data import PrepareIikoDeliveryData
from data import get_delivery_endpoints, get_iiko_endpoints


class IikoDeliveryService:
    def __init__(self):
        self.iiko_url = get_iiko_endpoints()
        self.saas_url = get_delivery_endpoints()
        self.request = MyRequests()
        self.assertions = Assertions()
        self.validator = Validator()
        self.iiko_delivery_generator = IikoDeliveryGenerator()
        self.iiko_delivery_data = PrepareIikoDeliveryData(generator=self.iiko_delivery_generator)
        self.address_data = load_json("tests/e2e/config/iiko_address_data.json")

    @allure.step("Создание заказа в IIKO с заданным адресом и duration")
    def create_order(self, address_key, duration, iiko_headers):
        if address_key not in self.address_data:
            raise ValueError(f"Address '{address_key}' not found in address config")

        address_info = self.address_data[address_key]
        info = next(self.iiko_delivery_generator.generate_iiko_order(
            organizationId=settings.IIKO_ORGANIZATION_ID,
            delivery_duration=duration,
            delivery_point={
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
        data = self.iiko_delivery_data.prepare_iiko_delivery_data(info=info)
        response = self.request.post(url=self.iiko_url.create_order, data=data, headers=iiko_headers)
        self.assertions.assert_status_code(response, HTTPStatus.OK)

        correlation_id = response.json()["correlationId"]
        order_id = response.json()["orderInfo"]["id"]

        self.wait_for_order_status(iiko_headers, settings.IIKO_ORGANIZATION_ID, correlation_id)
        print(f"Created order: {order_id} ({address_key}), duration={(duration / 60):.2f} hours")
        return order_id, info.delivery_point
    
    @allure.step("Ожидание успешного статуса заказа IIKO")
    def wait_for_order_status(self, headers, organization_id, correlation_id, timeout=60):
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
                break
            time.sleep(3)
        return False

    @allure.step("Поиск заказа в Курьерике по external_id")
    @retry(max_attempts=3, delay=10)
    def find_delivery_by_external_id(self, external_id, delivery_point, auth_headers, status="new"):
        today = datetime.now().strftime("%Y-%m-%d")
        search_address = delivery_point["address"]["line1"]
        print(search_address)

        response = self.request.get(
            url=f"{self.saas_url.list_of_deliveries}"
                f"?pickup_point_id={settings.COURIERICA_PICKUP_POINT_ID}"
                f"&created_at_from={today}"
                f"&statuses={status}"
                f"&search={search_address}"
                f"&page=1&per_page=10",
            headers=auth_headers,
        )
        self.assertions.assert_status_code(response, HTTPStatus.OK)

        deliveries = response.json().get("deliveries") or []
        for delivery in deliveries:
            if delivery.get("external_id") == external_id:
                print("Delivery found:", delivery.get("external_number"))
                return delivery

        raise AssertionError(f"Delivery with external_id {external_id} not found. "
                             f"Searched address: {search_address}")
    
    @allure.step("Отмена заказа в IIKO")
    def cancel_order(self, order_id, iiko_headers, test_name=None):
        cancel_response = self.request.post(
            url=self.iiko_url.cancel_order,
            data=json.dumps({
                "organizationId": settings.IIKO_ORGANIZATION_ID,
                "orderId": order_id
            }),
            headers=iiko_headers    
        )
        correlation_id = cancel_response.json()["correlationId"]
        self.assertions.assert_status_code(cancel_response, HTTPStatus.OK, test_name)
        self.wait_for_order_status(iiko_headers, settings.IIKO_ORGANIZATION_ID, correlation_id)

    @allure.step("Доставка заказа в IIKO")
    def deliver_order(self, order_id, iiko_headers, test_name=None):
        deliver_response = self.request.post(
            url=self.iiko_url.deliver_order,
            data=json.dumps({
                "organizationId": settings.IIKO_ORGANIZATION_ID,
                "orderId": order_id,
                "deliveryStatus": "Delivered"
            }),
            headers=iiko_headers    
        )
        correlation_id = deliver_response.json()["correlationId"]
        self.assertions.assert_status_code(deliver_response, HTTPStatus.OK, test_name)
        self.wait_for_order_status(iiko_headers, settings.IIKO_ORGANIZATION_ID, correlation_id)

    @allure.step("Закрытие заказа в IIKO")
    def close_order(self, order_id, iiko_headers, test_name=None):
        close_response = self.request.post(
            url=self.iiko_url.close_order,
            data=json.dumps({
                "organizationId": settings.IIKO_ORGANIZATION_ID,
                "orderId": order_id
            }),
            headers=iiko_headers
        )
        correlation_id = close_response.json()["correlationId"]
        self.assertions.assert_status_code(close_response, HTTPStatus.OK, test_name)
        self.wait_for_order_status(iiko_headers, settings.IIKO_ORGANIZATION_ID, correlation_id)

    @allure.step("Отмена и закрытие всех заказов в IIKO")
    def cancel_and_close_all_orders(self, iiko_headers, test_name=None):
        status_cancel = [
            "Unconfirmed",
            "WaitCooking",
            "ReadyForCooking",
            "CookingStarted",
            "CookingCompleted",
            "Waiting"
            ]
        status_delivered = 'OnWay'
        status_closed = 'Delivered'

        # Получаем все заказы за текущий день
        current_date = datetime.now().date()
        response = self.request.post(
            url=self.iiko_url.list_of_orders_by_statuses_and_dates,
            data=json.dumps({
                "organizationIds": [settings.IIKO_ORGANIZATION_ID],
                "deliveryDateFrom": f"{current_date}T00:00:00",
                "status": []
            }),
            headers=iiko_headers
        )
        self.assertions.assert_status_code(response, HTTPStatus.OK, test_name)

        data = response.json()
        if not data.get('ordersByOrganizations'):
            print('Нет заказов для отмены или закрытия')
            return
        
        data_order_cancel = []
        data_order_deliv = []
        data_order_closed = []

        for order in data['ordersByOrganizations'][0]['orders']:
            if order['creationStatus'] == 'Success':
                if order['order']['status'] in status_cancel:
                    data_order_cancel.append(order['id'])
                elif order['order']['status'] == status_delivered:
                    data_order_deliv.append(order['id'])
                elif order['order']['status'] == status_closed:
                    data_order_closed.append(order['id'])

        print(f'Заказы для отмены [{len(data_order_cancel)}]: {data_order_cancel}')
        print(f'Заказы для доставки [{len(data_order_deliv)}]: {data_order_deliv}')
        print(f'Заказы для закрытия [{len(data_order_closed)}]: {data_order_closed}')

        # Обрабатываем заказы для отмены
        if data_order_cancel:
            for order_id in data_order_cancel:
                try:
                    self.cancel_order(order_id, iiko_headers, test_name)
                    print(f'Заказ - {order_id} - успешно отменен')
                except Exception as e:
                    print(f'Ошибка отмены заказа {order_id}: {str(e)}')
        else:
            print('Нет заказов для отмены')

        # Обрабатываем заказы для доставки
        if data_order_deliv:
            for order_id in data_order_deliv:
                try:
                    self.deliver_order(order_id, iiko_headers, test_name)
                    data_order_closed.append(order_id)
                    print(f'Статус заказа - {order_id} - успешно изменен на Delivered')
                except Exception as e:
                    print(f'Ошибка изменения статуса заказа {order_id}: {str(e)}')
        else:
            print('Нет заказов для изменения статуса')

        # Обрабатываем заказы для закрытия
        if data_order_closed:
            for order_id in data_order_closed:
                try:
                    self.close_order(order_id, iiko_headers, test_name)
                    print(f'Заказ - {order_id} - успешно закрыт')
                except Exception as e:
                    print(f'Ошибка закрытия заказа {order_id}: {str(e)}')
        else:
            print('Нет заказов для закрытия')