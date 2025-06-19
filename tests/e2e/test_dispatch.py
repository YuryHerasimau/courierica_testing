import time
import allure
import pytest
import json
from datetime import datetime, timedelta
from data import get_iiko_endpoints
from services.auth_service import AuthService
from src.http_methods import MyRequests
from src.assertions import Assertions
from src.prepare_data.prepare_iiko_delivery_data import PrepareIikoDeliveryData
from http import HTTPStatus
from generator.iiko_delivery_generator import IikoDeliveryGenerator
from functions import load_json
from services.courier_service import CourierService
from settings import settings
from tests.e2e.utils.dispatch_calc import DeliveryTimeCalculator


@allure.epic(
    "Testing dispatch v.2.0"
)
class TestDispatchIIKO:
    request = MyRequests()
    iiko_url = get_iiko_endpoints()
    assertions = Assertions()
    iiko_delivery_generator = IikoDeliveryGenerator()
    iiko_delivery_data = PrepareIikoDeliveryData(generator=iiko_delivery_generator)
    courier_service = CourierService()

    ADDRESS_DATA = load_json("tests/e2e/config/iiko_address_data.json")
    pickup_point = ADDRESS_DATA["ПВ Курьерика"]
    
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

    def create_order(self, address_key, duration=60, iiko_headers=None, test_name=None):
        if iiko_headers is None:
            iiko_headers = self.iiko_headers
        if test_name is None:
            test_name = self._testMethodName
        
        # ADDRESS_DATA = load_json("tests/e2e/config/iiko_address_data.json")
        address_info = self.ADDRESS_DATA[address_key]
        
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

        self.assertions.assert_status_code(response, HTTPStatus.OK, test_name)
        order_id = response.json()["orderInfo"]["id"]
        correlation_id = response.json()["correlationId"]
        print(f"order_id is {order_id}, correlation_id is {correlation_id}")
        self._wait_for_order_status(iiko_headers, settings.IIKO_ORGANIZATION_ID, correlation_id)
        return order_id
    
    def cancel_order(self, order_id, iiko_headers, test_name=None):
        if test_name is None:
            test_name = self._testMethodName

        cancel_response = self.request.post(
            url=self.iiko_url.cancel_order,
            data=json.dumps({
                "organizationId": settings.IIKO_ORGANIZATION_ID,
                "orderId": order_id
            }),
            headers=iiko_headers    
        )
        self.assertions.assert_status_code(cancel_response, HTTPStatus.OK, test_name)
        
    
    def _setup_required_couriers(self, get_test_name, admin_auth_headers, courier_iiko_data, courier_names=None):
        """Фикстура для настройки только указанных курьеров перед тестами."""
        if courier_names is None:
            courier_names = ["Семен", "Федор"]  # значения по умолчанию
        
        # Получаем геоточку ПВЗ
        # ADDRESS_DATA = load_json("tests/e2e/config/iiko_address_data.json")
        # address_info = ADDRESS_DATA["ПВ Курьерика"]
        
        # Открываем смены и устанавливаем координаты для курьеров
        for courier_name in courier_names:
            courier_id = courier_iiko_data["couriers"][courier_name]
            # Авторизуемся под курьером
            courier_headers = AuthService.get_courier_headers(courier_id=courier_id, admin_headers=admin_auth_headers)

            # Открываем смену
            self.courier_service.turn_on_shift(
                get_test_name, 
                courier_id, 
                courier_iiko_data["courierica_pickup_point_id"], 
                admin_auth_headers
            )
            
            # Устанавливаем координаты курьера на ПВЗ
            self.courier_service.update_courier_geo(
                get_test_name,
                courier_id,
                self.pickup_point["latitude"],
                self.pickup_point["longitude"],
                courier_headers
            )

    @allure.title("2 - Перебэтч	- Новый заказ проходит по критериям только в один из незахлопнутых бэтчей")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_order_rebatch_to_specific_batch(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        """
        1. Создаем первый батч (ближние адреса)
        2. Создаем второй батч (дальние адреса)
        3. Создаем новый готовящийся заказ с ближним адресом
        4. Проверяем что готовящийся заказ объединился с ближними заказами (перешел в первый батч)
        """
        # Настраиваем только нужных курьеров
        self._setup_required_couriers(
            get_test_name,
            admin_auth_headers,
            courier_iiko_data,
            courier_names=["Семен", "Федор"]
        )
        # 1. Создаем первый батч
        batch_1_orders = [
            self.create_order("Башиловская 22", duration=30, iiko_headers=iiko_headers, test_name=get_test_name),
            self.create_order("Башиловская 22", duration=45, iiko_headers=iiko_headers, test_name=get_test_name)
        ]

        # 2. Создаем второй батч
        batch_2_orders = [
            self.create_order("Сущёвский Вал 55", duration=60, iiko_headers=iiko_headers, test_name=get_test_name),
            self.create_order("Сущёвский Вал 55", duration=90, iiko_headers=iiko_headers, test_name=get_test_name)
        ]

        # 3. Создаем тестовый заказ, который должен попасть в 1й батч по критериям батчинга
        test_order = self.create_order("Хуторская 38Ас23", duration=100, iiko_headers=iiko_headers, test_name=get_test_name)
        print("order_for_batch_1", test_order)
        time.sleep(90) # Ждем устаканивания перебэтча

        # 4. Проверки батчинга
        # Получаем информацию о курьерах и их батчах
        couriers = {
            "Семен": courier_iiko_data["couriers"]["Семен"],
            "Федор": courier_iiko_data["couriers"]["Федор"]
        }
        
        target_batch, other_batch = None, None

        for courier_name, courier_id in couriers.items():
            courier_headers = AuthService.get_courier_headers(courier_id=courier_id, admin_headers=admin_auth_headers)
            batch_info = self.courier_service.get_courier_batch_deliveries(get_test_name, courier_headers)

            if not batch_info.get('deliveries'):
                print(f"У курьера {courier_name} нет доставок")
                continue

            batch_order_ids = [delivery['external_id'] for delivery in batch_info['deliveries']]
            print(f"Курьер {courier_name} имеет заказы: {batch_order_ids}")
            
            # Проверяем содержит ли батч заказы из batch_1_orders
            if any(order in batch_order_ids for order in batch_1_orders):
                target_batch = batch_info
            # Проверяем содержит ли батч заказы из batch_2_orders
            elif any(order in batch_order_ids for order in batch_2_orders):
                other_batch = batch_info

        # Проверки
        assert target_batch is not None, "Не найден батч с заказами из batch_1_orders"
        assert other_batch is not None, "Не найден батч с заказами из batch_2_orders"
        
        # Получаем ID заказов в найденных батчах
        target_batch_order_ids = [delivery['external_id'] for delivery in target_batch['deliveries']]
        other_batch_order_ids = [delivery['external_id'] for delivery in other_batch['deliveries']]
        print("target_batch_order_ids", target_batch_order_ids)
        print("other_batch_order_ids", other_batch_order_ids)
        
        # Основная проверка: тестовый заказ должен быть в батче с ближними заказами
        assert test_order in target_batch_order_ids, (
            f"Тестовый заказ {test_order} должен быть в батче с заказами {batch_1_orders}"
            f"(по критериям расстояния), но найден в другом батче"
        )

        # Дополнительная проверка: тестовый заказ не должен быть в батче с дальними заказами
        assert test_order not in other_batch_order_ids, (
            f"Тестовый заказ {test_order} ошибочно попал в батч с заказами {batch_2_orders}"
        )
        
        # Проверяем что исходные заказы остались в своих батчах
        for order in batch_1_orders:
            assert order in target_batch_order_ids, (
                f"Исходный заказ {order} из batch_1_orders отсутствует в целевом батче"
            )

        for order in batch_2_orders:
            assert order in other_batch_order_ids, (
                f"Исходный заказ {order} из batch_2_orders отсутствует в другом батче"
            )
       
    @allure.title("5 - Перебэтч	- Нет времени ждать (заказ переходит в другой существующий батч)")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_no_time_to_wait_rebatch_to_existing(self, get_test_name, iiko_headers):
        """
        1. Создаем первый батч с готовящимся заказом                                # 47 (+), 48, 50 ---> 47 (+), 48, 49  --после триггера--> 47 (+), 48(+), 49(+), 50(+) # помимо дублей, мы превысили max_deliveries=3
        2. Создаем второй батч (любой)                                              # 49             ---> 50              --после триггера--> None
        3. Имитируем ситуацию "нет времени ждать" для первого батча
        4. Проверяем что заказ перешел во второй батч
        """
        # 1. Создаем первый батч с готовящимся заказом
        first_batch = [
            self.create_order("Ямская 10", duration=15, iiko_headers=iiko_headers, test_name=get_test_name), # READY
            self.create_order("Ямская 10", duration=60, iiko_headers=iiko_headers, test_name=get_test_name)
        ]
        
        # 2. Создаем второй батч (любой)
        other_batch = [
            self.create_order("Сущёвский Вал 55", duration=45, iiko_headers=iiko_headers, test_name=get_test_name),
            self.create_order("Сущёвский Вал 55", duration=30, iiko_headers=iiko_headers, test_name=get_test_name),
        ]

        # 3.1. Назначаем 1 готовый заказ из первого батча на курьера (в терминале)
        
        # 4. Имитируем ситуацию "нет времени ждать" для первого батча
        # self._simulate_no_time_to_wait(preparing_order)

        # 5. Проверки батчинга
        # ... (реализация проверок)
        # ... ("Исходный батч должен быть захлопнут")
        # ... ("Заказ должен быть в батче с Сущёвский Вал")
        # ... ("Курьер должен получить push-уведомление")

    @allure.title("6 - Перебэтч - Нет времени ждать (создается новый батч на другого курьера)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_no_time_to_wait_create_new_batch(self, get_test_name, iiko_headers):
        """
        1. Создаем батч с готовящимся заказом
        2. Добавляем второго курьера
        3. Имитируем ситуацию "нет времени ждать"
        4. Проверяем создание нового батча
        """
        # 1. Создаем батч с готовящимся заказом
        batch = [
            self.create_order("Башиловская 22", duration=15, iiko_headers=iiko_headers, test_name=get_test_name), # READY
            self.create_order("Башиловская 22", duration=40, iiko_headers=iiko_headers, test_name=get_test_name)
        ]
        
        # 2. Добавляем второго курьера
        # second_courier = self._add_courier_to_shift()
        
        # 3. Имитируем ситуацию "нет времени ждать"
        # self._simulate_no_time_to_wait(preparing_order)
        # ближний заказ готовим (назначаем)
        
        # 4. Проверки
        # ... (реализация проверок)
        # ... ("Заказ должен быть назначен второму курьеру")
        # ... ("Новый батч должен быть активным")
        # ... ("Исходный батч должен быть захлопнут")

    @allure.title("7 - Перебэтч - Нет времени ждать (вызов 3PL)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_no_time_to_wait_3pl_trigger(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        """
        1. Создаем батч с готовящимся заказом
        2. Имитируем ситуацию "нет времени ждать" без доступных курьеров
        3. Проверяем вызов 3PL
        """
        TIME_LATE_3PL = 10    # Допустимое время опоздания 3PL (мин)
        TIME_ARRIVE_3PL = 15  # Время подачи 3PL (мин)
        ROUTE_TIME = 20      # Время маршрута (мин), Планируемое время из маршрута - 34 мин, по ЯКарте - 20 мин на авто

        # Настраиваем только нужных курьеров
        self._setup_required_couriers(
            get_test_name,
            admin_auth_headers,
            courier_iiko_data,
            courier_names=["3PL"],
        )

        # 1. Создаем батч с готовящимся заказом
        test_duration_1 = 30
        test_duration_2 = 18
        batch = [
            self.create_order("Башиловская 22", duration=test_duration_1, iiko_headers=iiko_headers, test_name=get_test_name), # 
            self.create_order("Башиловская 22", duration=test_duration_2, iiko_headers=iiko_headers, test_name=get_test_name), # READY
        ]

        creation_time = datetime.now()
        print(f"creation_time: {creation_time}")
        time_till = creation_time + timedelta(minutes=test_duration_1)
        print(f"time_till: {time_till}")

        # 2. Рассчитываем ожидаемое время вызова 3PL
        expected_call_time = (
            time_till +
            timedelta(minutes=TIME_LATE_3PL) -
            timedelta(minutes=TIME_ARRIVE_3PL) -
            timedelta(minutes=ROUTE_TIME)
        )
        print(f"expected_call_time: {expected_call_time}")
        # AR: таймер = null, т.к. заказ в батче
        
        # 2. Имитируем ситуацию "нет времени ждать"
        # self._simulate_no_time_to_wait(preparing_order)
        # Первый заказ готовим, а второй - урезаем time_till
        
        # 3. Проверки
        # ... (реализация проверок)
        # ... (""3PL должен быть вызван для заказа"")
        # ... ("Исходный батч должен быть закрыт")
        # ... 

    @allure.title("8, 9 - Перебэтч - Открытие / Закрытие явки курьера")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_open_and_close_shift_for_couriers(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        """
        1. Создаем первый заказ
        2. Открываем смену для Семен
        3. Проверяем батч курьера
        4. Создаем второй заказ недалеко от первого
        5. Открываем смену для Федор
        6. Проверяем батч курьеров
        7. Закрываем смену для курьра, у которого есть батч
        8. Проверяем батч оставшегося на смене курьера
        """
        # Создаем первый заказ
        first_order = self.create_order("Башиловская 22", duration=30, iiko_headers=iiko_headers, test_name=get_test_name)

        # Открываем смену и патчим геоточку для Семен
        self._setup_required_couriers(
            get_test_name,
            admin_auth_headers,
            courier_iiko_data,
            courier_names=["Семен"]
        )
        time.sleep(15)

        # Проверяем батч курьера Семен
        # ... (1 заказ должен попасть в батч Семену)

        # Создаем второй заказ недалеко от первого
        second_order = self.create_order("Хуторская 38Ас23", duration=40, iiko_headers=iiko_headers, test_name=get_test_name)
        time.sleep(15)
        
        # Проверяем батч? (оба у Семена)

        # Открываем смену и патчим геоточку для Федор
        self._setup_required_couriers(
            get_test_name,
            admin_auth_headers,
            courier_iiko_data,
            courier_names=["Федор"]
        )
        time.sleep(90)

        # Проверяем батч курьеров Семен и Федор
        # ... (перебатчинг после открытия смены у второго курьера?)

        # Закрываем смену для того курьера, у которого батч с 2мя заказами
        self.courier_service.close_shift(
            get_test_name,
            courier_iiko_data["couriers"]["Семен"],
            courier_iiko_data["courierica_pickup_point_id"],
            admin_auth_headers
        )

        # Проверяем перебатчинг
        # ... (на смене 1 курьер и оба заказа должны быть в батче Федора)

    @allure.title("10 - Перебэтч - Отмена готовящегося заказа с захлопыванием батча")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_last_preparing_order_in_unclosed_batch(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        """
        Проверка отмены готовящегося заказа в батче с автоматическим захлопыванием
        
        Шаги:
        1. Создать батч с:
           - 2 готовыми заказами
           - 1 готовящимся заказом
        2. Отменить готовящийся заказ
        3. Проверить что:
           - Батч захлопнулся
           - Произошли все необходимые действия (пуш курьеру, вызов )
           - Отмененный заказ исчез из мобильного приложения курьера
        """
        self._setup_required_couriers(
            get_test_name,
            admin_auth_headers,
            courier_iiko_data,
            courier_names=["Семен", "Федор"]
        )

        # 1. Создаем батч
        ready_orders = [
            self.create_order("Башиловская 22", 30, iiko_headers, get_test_name), # READY
            self.create_order("Башиловская 22", 45, iiko_headers, get_test_name) # READY
        ]
        preparing_order = self.create_order("Хуторская 38Ас23", 100, iiko_headers, get_test_name)
        
        # Назначаем 2 готовых заказа на курьера (в терминале)
        time.sleep(90)

        # 2. Отменяем готовящийся заказ
        self.cancel_order(preparing_order, iiko_headers, get_test_name)

    @allure.title("11 - Перебэтч - Отмена заказа с перераспределением (готовящийся заказ)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_preparing_order_with_ready_orders_requires_rebatch(self, get_test_name, iiko_headers):
        """
        Проверка перераспределения заказов после отмены готовящегося заказа
        
        Шаги:
        1. Создать два батча:
           - батч 1: 1 готовый + 1 готовящийся (будет отменен)                 # 70 (+), 71 (X), 73 --- 70 (+), 72, 73 
           - батч 2: 2 готовящихся                                             # 72                 --- None
        2. Отменить готовящийся заказ в батче 1
        3. Проверить что:
           - Произошел перебатч
           - Один заказ из батча 2 перемещен в батч 1
           - батчи имеют корректный статус
        """
        # Обратит внимание на критерии ранжирования (в частности, TPH)

        # 1. Создаем батчи
        first_batch = [
            self.create_order("Сущёвский Вал 55", 60, iiko_headers, get_test_name), # READY
            self.create_order("Сущёвский Вал 55", 30, iiko_headers, get_test_name), # -> CANCEL
            self.create_order("Ямская 10", 45, iiko_headers, get_test_name),
        ]
        
        second_batch = [
            self.create_order("Сущёвский Вал 55", 160, iiko_headers, get_test_name),
        ]

        # Назначаем 1 готовый заказ из батча 1 на курьера (в терминале)
        # self.assign_order(first_batch[0], iiko_headers, get_test_name)
        time.sleep(120)

        # 2. Отменяем готовящийся заказ из батча 1
        self.cancel_order(first_batch[1], iiko_headers, get_test_name)
        
        # 3. Проверки
        # Забирается заказ из другого бэтча и кладется в этот бэтч, в котором произошла отмена, так как по кол-ву заказов в бэтче,
        # и/или длине маршрута и/или TPH так эффективнее. Если этот заказ готов, бэтч сразу захлопывается (ведь в нем все заказы готовы).
        # Если этот заказ готовится, бэтч ожидает окончания приготовления.

    @allure.title("12 - Перебэтч - Отмена заказа в незахлопнутом бэтче и нужно перераспределить заказы")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_preparing_order_with_rebatch_1(self, get_test_name, iiko_headers):
        """
        Проверка перераспределения заказов после отмены готовящегося заказа
        
        Шаги:
        1. Создать два батча:
           - батч 1: 1 готовый + 2 готовящийся (1 будет отменен)               # 
           - батч 2: 2 готовящихся                                             # 
        2. Отменить готовящийся заказ в батче 1
        3. Проверить что:
           - Произошел перебатч
           - Один заказ из батча 2 перемещен в батч 1
           - батчи имеют корректный статус
        """
        # 1. Создаем батчи
        first_batch = [
            self.create_order("Сущёвский Вал 55", 60, iiko_headers, get_test_name), # READY
            self.create_order("Ямская 10", 45, iiko_headers, get_test_name), # -> CANCEL
        ]
        
        second_batch = [
            self.create_order("Ямская 10", 150, iiko_headers, get_test_name),
        ]

        # Назначаем 1 готовый заказ из батча 1 на курьера (в терминале)
        # self.assign_order(first_batch[0], iiko_headers, get_test_name)
        time.sleep(90)

        # 2. Отменяем готовящийся заказ из батча 1
        self.cancel_order(first_batch[1], iiko_headers, get_test_name)

    @allure.title("13 - Перебэтч - Отмена заказа в незахлопнутом бэтче и нужно перераспределить заказы")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_preparing_order_with_rebatch_2(self, get_test_name, iiko_headers):
        # 1. Создаем батчи
        first_batch = [
            self.create_order("Сущёвский Вал 55", 60, iiko_headers, get_test_name), 
            self.create_order("Сущёвский Вал 55", 30, iiko_headers, get_test_name), # READY -> CANCEL
            self.create_order("Ямская 10", 45, iiko_headers, get_test_name),
        ]
        
        second_batch = [
            self.create_order("Ямская 10", 150, iiko_headers, get_test_name),
        ]

        # Назначаем 1 готовый заказ из батча 1 на курьера (в терминале)
        # self.assign_order(first_batch[1], iiko_headers, get_test_name)
        time.sleep(90)

        # 2. Отменяем ГОТОВЫЙ заказ из батча 1
        self.cancel_order(first_batch[1], iiko_headers, get_test_name)

    @allure.title("14 - Перебэтч - Отмена заказа в незахлопнутом бэтче и НЕ нужно перераспределять заказы")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_preparing_order_without_rebatch_1(self, get_test_name, iiko_headers):
        # 1. Создаем батчи
        first_batch = [
            self.create_order("Сущёвский Вал 55", 60, iiko_headers, get_test_name), # READY
            self.create_order("Ямская 10", 45, iiko_headers, get_test_name), # -> CANCEL
        ]
        
        second_batch = [
            self.create_order("Ямская 10", 150, iiko_headers, get_test_name),
        ]

        # Назначаем 1 готовый заказ из батча 1 на курьера (в терминале)
        # self.assign_order(first_batch[0], iiko_headers, get_test_name)
        time.sleep(90)

        # 2. Отменяем готовящийся заказ из батча 1
        self.cancel_order(first_batch[1], iiko_headers, get_test_name)

        # 3. Проверка
        # Продолжается ожидание приготовления последнего готовящегося заказа в этом бэтче.

    @allure.title("15 - Перебэтч - Отмена заказа в незахлопнутом бэтче и НЕ нужно перераспределять заказы")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_preparing_order_without_rebatch_2(self, get_test_name, iiko_headers):
        """перераспределить заказы эффективнее, чем есть сейчас, нельзя."""
        # 1. Создаем батчи
        first_batch = [
            self.create_order("Сущёвский Вал 55", 60, iiko_headers, get_test_name), # READY
            self.create_order("Сущёвский Вал 55", 30, iiko_headers, get_test_name),
            self.create_order("Ямская 10", 45, iiko_headers, get_test_name),
        ]
        
        second_batch = [
            self.create_order("Ямская 10", 150, iiko_headers, get_test_name),
        ]

        # Назначаем 1 готовый заказ из батча 1 на курьера (в терминале)
        # self.assign_order(first_batch[0], iiko_headers, get_test_name)
        time.sleep(90)

        # 2. Отменяем готовящийся заказ из батча 1
        self.cancel_order(first_batch[1], iiko_headers, get_test_name)
        
        # По итогу перебэтча оказывается, что перераспределять заказы в этот бэтч из других бэтчей нет смысла
        # (не проходят по критериям или неэффективно по ранжированию), и этот бэтч (в котором отменился заказ) захлопывается,
        # так как в нем теперь все заказы готовы

    @allure.title("16 - Перебэтч - Отмена заказа в незахлопнутом бэтче и НЕ нужно перераспределять заказы")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_preparing_order_without_rebatch_3(self, get_test_name, iiko_headers):
        # 1. Создаем батчи
        first_batch = [
            self.create_order("Сущёвский Вал 55", 60, iiko_headers, get_test_name), 
            self.create_order("Сущёвский Вал 55", 30, iiko_headers, get_test_name), # READY -> CANCEL
            self.create_order("Ямская 10", 45, iiko_headers, get_test_name),
        ]
        
        second_batch = [
            self.create_order("Ямская 10", 150, iiko_headers, get_test_name),
        ]

        # Назначаем 1 готовый заказ из батча 1 на курьера (в терминале)
        # self.assign_order(first_batch[1], iiko_headers, get_test_name)
        time.sleep(90)

        # 2. Отменяем ГОТОВЫЙ заказ из батча 1
        self.cancel_order(first_batch[1], iiko_headers, get_test_name)

        # 3. Проверка
        # По итогу перебэтча оказывается, что перераспределять заказы в этот бэтч из других бэтчей нет смысла
        # (не проходят по критериям или неэффективно по ранжированию).
        # Продолжается ожидание приготовления готовящихся заказов в этом бэтче.

    @allure.title("17 - Перебэтч - Отмена заказа в захлопнутом бэтче")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_order_in_closed_batch(self, get_test_name, iiko_headers):
        # 1. Создаем батч
        first_batch = [
            self.create_order("Сущёвский Вал 55", 60, iiko_headers, get_test_name), # READY
            self.create_order("Сущёвский Вал 55", 30, iiko_headers, get_test_name), # READY
        ]

        # Назначаем все заказы из батча на курьера (в терминале)
        # self.assign_order(first_batch[1], iiko_headers, get_test_name)
        time.sleep(90)

        # 2. Отменяется один из заказов
        self.cancel_order(first_batch[1], iiko_headers, get_test_name)

    @allure.title(
            "18 - Перебэтч - Параметры <Время приготовления заказа>,"
            "<Время на получение заказа>, <Время на передачу заказа клиенту> и <Допустимое время опоздания>," \
            "а также ожидаемое время возвращения курьера на филиал учитываются корректно"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_new_order_exceeds_max_delivery_time_triggers_3pl(self, get_test_name, iiko_headers):
        pass

    def test_calculate_delivery_time_for_orders(self):
        address_to_durations = [
            ("Сущёвский Вал 55", 45),
            ("Сущёвский Вал 55", 30),
            ("Ямская 10", 15),
            ("Ямская 10", 60),
        ]
        
        orders = []
        for address_key, duration in address_to_durations:
            orders.append({
                "address_key": address_key,
                "latitude": self.ADDRESS_DATA[address_key]["latitude"],
                "longitude": self.ADDRESS_DATA[address_key]["longitude"],
                "duration": duration,
            })

        calculator = DeliveryTimeCalculator()
        result = calculator.calculate_delivery_time(orders, self.pickup_point)

        print(f"\nОбщее время доставки: {result['total_time']:.2f} минут\n")
        for i, batch in enumerate(result["batches"], 1):
            print(f"Батч {i}:")
            print(f"Заказы: {len(batch['order_ids'])}")
            print("Детали заказов:")
            for detail in batch["details"]:
                print(f"  ID: {detail['id']}, Адрес: {detail['address']}, Время готовности: {detail['duration']} мин")
            
            print(f"\nМаршрут (время батча: {batch['batch_time']:.2f} мин):")
            for leg in batch["route"]:
                print(f"  {leg['from']} -> {leg['to']} ({leg['distance']:.0f} м, {leg['time']:.1f} мин)")
            print("\n" + "="*50 + "\n")
