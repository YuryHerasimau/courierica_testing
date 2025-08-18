import allure
import time
import random
from datetime import datetime

from tests.e2e.config.order_data import generate_hardcoded_orders, generate_random_orders
from services.auth_service import AuthService
from services.delivery_service import DeliveryService
from services.courier_service import CourierService
from services.pickup_point_service import PickupPointService
from services.route_service import RouteService
from src.prepare_data.prepare_delivery_data import PrepareDeliveryData
from generator.delivery_generator import DeliveryGenerator
from functions import load_json
from settings import settings


@allure.epic(
    "Testing delivery creation, delivery assignment and delivery completion by courier for SAAS company"
)
class TestDeliveryCourierFlow:
    auth_service = AuthService()
    delivery_service = DeliveryService()
    courier_service = CourierService()
    delivery_data = PrepareDeliveryData()
    delivery_generator = DeliveryGenerator()
    pickup_point_service = PickupPointService()
    route_service = RouteService()

    @staticmethod
    def perform_delivery_completion(
        test_name, delivery_id, headers, statuses, complete_func, reason=None
    ):
        """Выполнение завершения доставки с учетом статусов."""
        for status in statuses:
            # Если передана причина, используем функцию с причиной
            if reason and complete_func.__name__ == "complete_delivery_with_reason":
                complete_func(test_name, delivery_id, status, reason, headers)
            # Иначе используем стандартную функцию завершения
            else:
                complete_func(test_name, delivery_id, status, headers)
            time.sleep(5)

    @allure.title("End-to-End Test: Single Order Delivery Flow")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_any_order_delivery(self, get_test_name, logistician_saas_auth_headers, courier_saas_auth_headers):
        """
        Проверка полного цикла выполнения доставки заданного количество заказов:
        - Создание доставки на рандомный адрес.
        - Включение смены курьера.
        - Назначение курьера на доставку.
        - Выполнение всех этапов доставки ("pickup_arrived", "pickuped", "delivered").
        - Завершение доставки с учетом ограничения на кнопку 'Передал' в приложении курьера.
        """
        company_id = settings.COURIER_COMPANY_ID
        pickup_point_id = settings.COURIER_PICKUP_POINT_ID
        courier_id = self.auth_service.get_courier_id(courier_saas_auth_headers)

        # Шаг 1: Создание заказа
        orders = generate_random_orders(count=random.randint(1, 5))

        delivery_ids = []
        for order in orders:
            info = next(
                self.delivery_generator.generate_delivery(
                    company_id=company_id,
                    pickup_point_id=pickup_point_id,
                    recipient_address=order.address,
                    recipient_point={"latitude": order.latitude, "longitude": order.longitude},
                    time_from=order.time_from,
                    time_till=order.time_till,
                )
            )
            data = self.delivery_data.prepare_delivery_data(info=info)
            delivery_id = self.delivery_service.create_delivery(
                get_test_name, data, logistician_saas_auth_headers
            )
            delivery_ids.append(delivery_id)
            time.sleep(5)

        # Шаг 2: Включение смены для курьера
        self.courier_service.turn_on_shift(
            get_test_name, courier_id, pickup_point_id, logistician_saas_auth_headers
        )

        # Шаг 3: Назначение курьера на заказ
        for delivery_id in delivery_ids:
            self.delivery_service.assign_delivery(
                get_test_name, delivery_id, courier_id, logistician_saas_auth_headers
            )
            time.sleep(5)

        # Шаг 4: Завершение заказа по разным статусам
        statuses = ["pickup_arrived", "pickuped", "delivered"]
        courier_delivered_mode, _ = self.pickup_point_service.get_courier_delivery_mode(
            get_test_name, pickup_point_id, logistician_saas_auth_headers
        )
        self.complete_orders_by_courier_delivered_mode(
            get_test_name,
            delivery_ids, # [delivery_id],
            statuses,
            courier_delivered_mode,
            courier_saas_auth_headers,
            logistician_saas_auth_headers,
        )


    @allure.title("End-to-End Test: Multi-Order Routing and Delivery Flow")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_multiple_deliveries_routing_flow(self, get_test_name, logistician_saas_auth_headers, courier_saas_auth_headers):
        """
        Проверка полного цикла маршрутизации и выполнения нескольких доставок:
        - Создание нескольких заказов.
        - Включение смены курьера.
        - Назначение курьера на все заказы.
        - Выполнение доставки для каждого заказа.
        - Проверка маршрута курьера на корректность данных и финальный статус.
        """
        company_id = settings.COURIER_COMPANY_ID
        pickup_point_id = settings.COURIER_PICKUP_POINT_ID
        courier_id = self.auth_service.get_courier_id(courier_saas_auth_headers)
        date = datetime.now().strftime("%Y-%m-%d")

        # Генерация списка заказов
        orders = generate_hardcoded_orders()

        # Загрузка маршрутов из файла
        geo_updates_data = load_json("tests/e2e/config/geo_updates.json")

        # Преобразование данных в список маршрутов для удобного доступа
        geo_updates = [
            geo_updates_data["first_order"],
            geo_updates_data["second_order"],
            geo_updates_data["third_order"],
        ]

        # Шаг 1: Создание заказов
        order_ids = self.create_deliveries(
            get_test_name,
            company_id,
            pickup_point_id,
            orders,
            logistician_saas_auth_headers,
        )

        # Шаг 2: Включение смены для курьера
        self.courier_service.turn_on_shift(
            get_test_name, courier_id, pickup_point_id, logistician_saas_auth_headers
        )

        # Шаг 3: Назначение курьера на заказы
        self.assign_deliveries(
            get_test_name, order_ids, courier_id, logistician_saas_auth_headers
        )

        # Шаг 4: Обновление геопозиции курьера и выполнение заказов
        for idx, order_id in enumerate(order_ids):
            # geo_updates[idx] - список координат для текущего заказа
            self.complete_order(
                get_test_name,
                courier_id,
                courier_saas_auth_headers,
                order_id,
                geo_updates[idx],
            )

        # Шаг 5: Проверяем статус маршрута
        # Ждем 10 секунд перед началом проверки
        time.sleep(10)

        # Пытаемся проверить статус маршрута до 3 раз
        max_attempts = 3
        for attempt in range(max_attempts):
            print(f"Checking route status. Attempt {attempt + 1}/{max_attempts}.")
            try:
                self.route_service.get_route_status(
                    get_test_name,
                    company_id,
                    courier_id,
                    pickup_point_id,
                    date,
                    logistician_saas_auth_headers,
                )
                print(f"Route status checked successfully on attempt {attempt + 1}.")
                break  # Если статус успешно проверен, выходим из цикла
            except AssertionError as e:
                # Если это не последняя попытка, ждем перед следующей проверкой
                if attempt < max_attempts - 1:
                    print(
                        f"Attempt {attempt + 1}/{max_attempts} to check route status failed. Error: {e}. "
                        f"Retrying in 5 seconds..."
                    )
                    time.sleep(5)
                else:
                    print(f"All {max_attempts} attempts to check route status failed. Error: {e}.")
                    raise e

    def create_deliveries(
        self, test_name, company_id, pickup_point_id, orders, headers
    ):
        """Создает заказы и возвращает их ID."""
        order_ids = []
        for order in orders:
            info = next(
                self.delivery_generator.generate_delivery(
                    company_id=company_id,
                    pickup_point_id=pickup_point_id,
                    recipient_address=order.address,
                    recipient_point={
                        "latitude": order.latitude,
                        "longitude": order.longitude,
                    },
                    time_till=order.time_till,
                )
            )
            data = self.delivery_data.prepare_delivery_data(info=info)
            delivery_id = self.delivery_service.create_delivery(
                test_name, data, headers
            )
            order_ids.append(delivery_id)
            time.sleep(10)

        return order_ids

    def assign_deliveries(self, test_name, order_ids, courier_id, headers):
        """Назначает курьера на заказы."""
        for order_id in order_ids:
            self.delivery_service.assign_delivery(
                test_name, order_id, courier_id, headers
            )
            time.sleep(10)

    def complete_order(
        self, test_name, courier_id, courier_saas_auth_headers, order_id, geo_updates
    ):
        """Выполняет этапы доставки заказа: pickup_arrived, pickuped, delivered."""

        # Статус "pickup_arrived"
        self.update_geo_and_complete(
            test_name,
            courier_id,
            order_id,
            "pickup_arrived",
            geo_updates[0],
            courier_saas_auth_headers,
        )

        # Статус "pickuped"
        self.update_geo_and_complete(
            test_name,
            courier_id,
            order_id,
            "pickuped",
            geo_updates[1],
            courier_saas_auth_headers,
        )

        # Статус "delivered"
        for geo_point in geo_updates[2:]:
            self.courier_service.update_courier_geo(
                test_name,
                courier_id,
                geo_point["latitude"],
                geo_point["longitude"],
                courier_saas_auth_headers,
            )
            time.sleep(10)

            # помогает избежать проблем с построением маршрута
            self.courier_service.update_courier_geo(
                test_name,
                courier_id,
                geo_point["latitude"],
                geo_point["longitude"],
                courier_saas_auth_headers,
            )
            time.sleep(10)

        self.delivery_service.complete_delivery(
            test_name, order_id, "delivered", courier_saas_auth_headers
        )
        print(f"Order {order_id} delivered!\n")

    def update_geo_and_complete(
        self, test_name, courier_id, order_id, status, geo_point, headers
    ):
        """Обновляет геопозицию курьера и завершает заказ с указанным статусом."""
        self.courier_service.update_courier_geo(
            test_name,
            courier_id,
            geo_point["latitude"],
            geo_point["longitude"],
            headers,
        )
        time.sleep(10)

        self.delivery_service.complete_delivery(test_name, order_id, status, headers)
        time.sleep(10)

        # помогает избежать проблем с построением маршрута
        self.courier_service.update_courier_geo(
            test_name,
            courier_id,
            geo_point["latitude"],
            geo_point["longitude"],
            headers,
        )
        time.sleep(10)

    def complete_orders_by_courier_delivered_mode(
        self,
        test_name,
        order_ids,
        statuses,
        courier_delivered_mode,
        courier_saas_auth_headers,
        logistician_saas_auth_headers,
    ):
        """
        Завершает заказы в зависимости от режима доставки курьера.
        """
        for order_id in order_ids:
            if courier_delivered_mode == "allow":
                self.perform_delivery_completion(
                    test_name,
                    order_id,
                    courier_saas_auth_headers,
                    statuses,
                    self.delivery_service.complete_delivery,
                )
                time.sleep(10)

            elif courier_delivered_mode == "reason":
                reason = {"reason": 6, "comment": "Delivery completed for testing"}
                self.perform_delivery_completion(
                    test_name,
                    order_id,
                    courier_saas_auth_headers,
                    statuses,
                    self.delivery_service.complete_delivery_with_reason,
                    reason,
                )
                time.sleep(10)

            elif courier_delivered_mode == "forbid":
                print(
                    f"Courier delivered mode is 'forbid'. Completing order {order_id} as logistician."
                )
                self.perform_delivery_completion(
                    test_name,
                    order_id,
                    logistician_saas_auth_headers,
                    statuses,
                    self.
                    delivery_service.complete_delivery,
                )
                time.sleep(10)
