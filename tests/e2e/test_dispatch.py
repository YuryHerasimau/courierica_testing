import allure
import pytest
import time
from datetime import datetime, timedelta

from data import get_iiko_endpoints
from services.auth_service import AuthService
from services.iiko_delivery_service import IikoDeliveryService
from services.courier_service import CourierService
from src.http_methods import MyRequests
from src.assertions import Assertions
from src.prepare_data.prepare_iiko_delivery_data import PrepareIikoDeliveryData
from generator.iiko_delivery_generator import IikoDeliveryGenerator
from tests.e2e.utils.dispatch_calc import DeliveryTimeCalculator
from functions import load_json


@allure.epic("Testing dispatch v.2.0")
@pytest.mark.dispatch_v2
class TestDispatchIIKO:
    delivery_service = IikoDeliveryService()
    
    request = MyRequests()
    iiko_url = get_iiko_endpoints()
    assertions = Assertions()
    iiko_delivery_generator = IikoDeliveryGenerator()
    iiko_delivery_data = PrepareIikoDeliveryData(generator=iiko_delivery_generator)
    courier_service = CourierService()

    ADDRESS_DATA = load_json("tests/e2e/config/iiko_address_data.json")
    pickup_point = ADDRESS_DATA["ПВ Курьерика"]
    
    def _setup_required_couriers(self, get_test_name, admin_auth_headers, courier_iiko_data, courier_names=None):
        """Фикстура для настройки только указанных курьеров перед тестами."""
        if courier_names is None:
            courier_names = ["Семен", "Федор"]  # значения по умолчанию
        
        # Открываем смены и устанавливаем координаты для курьеров
        for courier_name in courier_names:
            courier_id = courier_iiko_data["couriers"][courier_name]
            # Авторизуемся под курьером
            courier_headers = AuthService.get_courier_headers(courier_id, admin_auth_headers)

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
    @allure.severity(allure.severity_level.CRITICAL)
    def test_order_rebatch_to_specific_batch(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        """
        1. Создаем первый батч (ближние адреса)
        2. Создаем второй батч (дальние адреса)
        3. Создаем новый готовящийся заказ с ближним адресом
        4. Проверяем что готовящийся заказ объединился с ближними заказами (перешел в первый батч)
        """
        # Настраиваем только нужных курьеров ["Семен", "Федор"]
        # 1. Создаем первый батч
        batch_1_orders = [
            self.delivery_service.create_order("Башиловская 22", 30, iiko_headers),
            self.delivery_service.create_order("Башиловская 22", 45, iiko_headers)
        ]

        # 2. Создаем второй батч
        batch_2_orders = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers),
            self.delivery_service.create_order("Сущёвский Вал 55", 90, iiko_headers)
        ]

        # 3. Создаем тестовый заказ, который должен попасть в 1й батч по критериям батчинга
        test_order = self.delivery_service.create_order("Хуторская 38Ас23", 100, iiko_headers)
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
            courier_headers = AuthService.get_courier_headers(courier_id, admin_auth_headers)
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
    @allure.severity(allure.severity_level.CRITICAL)
    def test_no_time_to_wait_rebatch_to_existing(self, get_test_name, iiko_headers):
        """
        1. Создаем первый батч с готовящимся заказом                                # 09, 10, 11(+) ---> 11(+)
        2. Создаем второй батч (любой)                                              # 08            ---> 09(+), 10(+), 08(+3PL)
        3. Имитируем ситуацию "нет времени ждать" для первого батча
        4. Проверяем что заказ перешел во второй батч
        """
        # 1. Создаем первый батч с готовящимся заказом
        first_batch = [
            self.delivery_service.create_order("Ямская 10", 15, iiko_headers), # READY
            self.delivery_service.create_order("Ямская 10", 60, iiko_headers),
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers),
        ]
        
        # 2. Создаем второй батч (любой)
        other_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 15, iiko_headers), # 15 вместо 45
        ]

        # 3.1. Назначаем 1 готовый заказ из первого батча на курьера (в терминале)
        
        # 4. Имитируем ситуацию "нет времени ждать" для первого батча
        # self._simulate_no_time_to_wait(preparing_order)

        # 5. Проверки батчинга
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
            self.delivery_service.create_order("Башиловская 22", 15, iiko_headers), # READY
            self.delivery_service.create_order("Башиловская 22", 40, iiko_headers)
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
        # Настраиваем только нужных курьеров ["Семен", "Федор", "3PL"]

        # 1. Создаем батч с готовящимся заказом
        test_duration_1 = 30
        test_duration_2 = 15

        batch = [
            self.delivery_service.create_order("Башиловская 22", test_duration_1, iiko_headers), # 
            self.delivery_service.create_order("Башиловская 22", test_duration_2, iiko_headers), # READY
        ]

        ROUTE_TIME = 12 # Планируемое время из маршрута - 34 мин, по ЯКарте - 12...13 мин на авто

        # 2. Курьера без батча располагаем далеко от ПВЗ
        # 3. Курьера с батчем тоже располагаем далеко от ПВЗ или же нажимаем "Забрал" в мобилке

        # 4. Имитируем ситуацию "нет времени ждать"
        # self._simulate_no_time_to_wait(preparing_order)
        
        # 5. Проверки

        # Рассчитываем ожидаемое время вызова 3PL
        creation_time = datetime.now()
        time_till = creation_time + timedelta(minutes=test_duration_1)
        expected_call_time = (
            time_till +
            timedelta(minutes=DeliveryTimeCalculator.TIME_LATE_3PL) -
            timedelta(minutes=DeliveryTimeCalculator.TIME_ARRIVE_3PL) -
            timedelta(minutes=ROUTE_TIME)
        )
        print(f"creation_time: {creation_time}")
        print(f"time_till: {time_till}")
        print(f"expected_call_time: {expected_call_time}")
        # AR: таймер = null, т.к. заказ в батче

        # ... (реализация проверок)
        # ... (""3PL должен быть вызван для заказа"")
        # ... ("Исходный батч должен быть закрыт")
        # ... 

    @allure.title("8, 9 - Перебэтч - Открытие / Закрытие явки курьера")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_open_and_close_shift_for_couriers(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        """
        Предусловия:
        1. Ставим геоточки курьеров в ПВЗ!!! (см предыдущий тест)
        2. Выключаем смены курьерам
        """
        # 1. Создаем первый заказ
        first_order = self.delivery_service.create_order("Башиловская 22", 30, iiko_headers)

        # 2. Открываем смену и патчим геоточку для ["Семен"]
        time.sleep(15)

        # 3. Проверяем батч курьера Семен
        # ... (1 заказ должен попасть в батч Семену)

        # 4. Создаем второй заказ недалеко от первого
        second_order = self.delivery_service.create_order("Хуторская 38Ас23", 40, iiko_headers)
        time.sleep(15)
        
        # Проверяем батч? (оба у Семена)

        # 5. Открываем смену и патчим геоточку для ["Федор"]
        time.sleep(90)

        # 6. Проверяем батч курьеров Семен и Федор
        # ... (перебатчинг после открытия смены у второго курьера?)

        # 7. Закрываем смену для того курьера, у которого батч с 2мя заказами
        self.courier_service.close_shift(
            get_test_name,
            courier_iiko_data["couriers"]["Семен"],
            courier_iiko_data["courierica_pickup_point_id"],
            admin_auth_headers
        )

        # 8. Проверяем перебатчинг
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
        # !!!!!!!!!!!! Отключить 3PL и убрать его со смены
        # Настраиваем только нужных курьеров ["Семен", "Федор"]

        # 1. Создаем батч
        ready_orders = [
            self.delivery_service.create_order("Башиловская 22", 30, iiko_headers), # READY
            self.delivery_service.create_order("Башиловская 22", 45, iiko_headers) # READY
        ]
        preparing_order = self.delivery_service.create_order("Хуторская 38Ас23", 100, iiko_headers)
        
        # Назначаем 2 готовых заказа на курьера (в терминале)
        time.sleep(90)

        # 2. Отменяем готовящийся заказ
        self.delivery_service.cancel_order(preparing_order[0], iiko_headers)

    @allure.title("12 - Перебэтч - Отмена заказа с перераспределением (готовящийся заказ)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_preparing_order_with_ready_orders_requires_rebatch(self, get_test_name, iiko_headers):
        """
        Проверка перераспределения заказов после отмены готовящегося заказа
        
        Шаги:
        1. Создать два батча:
           - батч 1: 1 готовый + 1 готовящийся (будет отменен)                 # 35 (+), 36 (X), 38 --- 35 (+), 37, 38 
           - батч 2: 2 готовящихся                                             # 37                 --- None
        2. Отменить готовящийся заказ в батче 1
        3. Проверить что:
           - Произошел перебатч
           - Один заказ из батча 2 перемещен в батч 1
           - батчи имеют корректный статус
        """
        # Обратить внимание на критерии ранжирования (в частности, TPH)

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers), # READY
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers), # -> CANCEL
            self.delivery_service.create_order("Ямская 10", 45, iiko_headers),
        ]
        
        second_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 160, iiko_headers),
        ]

        # Назначаем 1 готовый заказ из батча 1 на курьера (в терминале)
        # self.assign_order(first_batch[0], iiko_headers, get_test_name)
        time.sleep(120)

        # 2. Отменяем готовящийся заказ из батча 1
        self.delivery_service.cancel_order(first_batch[1][0], iiko_headers)
        
        # 3. Проверки
        # Забирается заказ из другого бэтча и кладется в этот бэтч, в котором произошла отмена, так как по кол-ву заказов в бэтче,
        # и/или длине маршрута и/или TPH так эффективнее. Если этот заказ готов, бэтч сразу захлопывается (ведь в нем все заказы готовы).
        # Если этот заказ готовится, бэтч ожидает окончания приготовления.

    @allure.title("11 - Перебэтч - Отмена заказа в незахлопнутом бэтче и нужно перераспределить заказы")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_preparing_order_with_rebatch_1(self, get_test_name, iiko_headers):
        """
        Проверка перераспределения заказов после отмены готовящегося заказа
        """
        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers), # READY
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers), # READY
            self.delivery_service.create_order("Ямская 10", 45, iiko_headers), # -> CANCEL
        ]
        
        second_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 160, iiko_headers),
        ]

        # Назначаем 1 готовый заказ из батча 1 на курьера (в терминале)
        # self.assign_order(first_batch[0], iiko_headers)
        time.sleep(90)

        # 2. Отменяем готовящийся заказ из батча 1
        # (ВРУЧНУЮ ОТМЕНЯЕМ ИМЕННО ГОТОВЯЩИЙСЯ ЗАКАЗ ИЗ БАТЧА 1)
        # self.delivery_service.cancel_order(first_batch[1][0], iiko_headers)

    @allure.title("13 - Перебэтч - Отмена заказа в незахлопнутом бэтче и нужно перераспределить заказы")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_preparing_order_with_rebatch_2(self, get_test_name, iiko_headers):
        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers), 
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers), # READY -> CANCEL
            self.delivery_service.create_order("Ямская 10", 45, iiko_headers),
        ]
        
        second_batch = [
            self.delivery_service.create_order("Ямская 10", 150, iiko_headers),
        ]

        # Назначаем 1 готовый заказ из батча 1 на курьера (в терминале)
        # self.assign_order(first_batch[1], iiko_headers)
        time.sleep(90)

        # 2. Отменяем ГОТОВЫЙ заказ из батча 1
        # (ВРУЧНУЮ ОТМЕНЯЕМ ИМЕННО ГОТОВЫЙ ЗАКАЗ ИЗ БАТЧА 1)
        # self.delivery_service.cancel_order(first_batch[1][0], iiko_headers)

    @allure.title("14 - Перебэтч - Отмена заказа в незахлопнутом бэтче и НЕ нужно перераспределять заказы")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_preparing_order_without_rebatch_1(self, get_test_name, iiko_headers):

        # Устанавливаем на ПВ default_max_deliveries_for_courier=4
        # Перемотреть тестовые данные, чтобы пачка заказов была в одном месте, а у другого курьера - в другом месте пачка

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers), # READY
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers), # READY
            self.delivery_service.create_order("Ямская 10", 45, iiko_headers), # -> CANCEL
            self.delivery_service.create_order("Ямская 10", 150, iiko_headers),
        ]

        time.sleep(30)

        second_batch = [
            self.delivery_service.create_order("Больничный переулок, 2", 60, iiko_headers),
            self.delivery_service.create_order("Больничный переулок, 2", 70, iiko_headers),
        ]

        # Готовим 2 заказа из батча 1 (происходит назначение их на курьера)
        time.sleep(30)


        # 2. Отменяем 1 готовящийся заказ из батча 1
        self.delivery_service.cancel_order(first_batch[2][0], iiko_headers)

        # 3. Проверка
        # Продолжается ожидание приготовления последнего готовящегося заказа в этом бэтче.

    @allure.title("15 - Перебэтч - Отмена заказа в незахлопнутом бэтче и НЕ нужно перераспределять заказы")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_preparing_order_without_rebatch_2(self, get_test_name, iiko_headers):
        """перераспределить заказы эффективнее, чем есть сейчас, нельзя."""

        # Устанавливаем на ПВ default_max_deliveries_for_courier=4
        # Перемотреть тестовые данные, чтобы пачка заказов была в одном месте, а у другого курьера - в другом месте пачка

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers), # READY
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers), # READY
            self.delivery_service.create_order("Ямская 10", 45, iiko_headers), # -> CANCEL
        ]

        time.sleep(30)
        
        second_batch = [
            self.delivery_service.create_order("Больничный переулок, 2", 60, iiko_headers),
            self.delivery_service.create_order("Больничный переулок, 2", 70, iiko_headers),
        ]

        # Готовим 2 заказа из батча 1 (происходит назначение их на курьера)
        time.sleep(30)

        # 2. Отменяем готовящийся заказ из батча 1
        self.delivery_service.cancel_order(first_batch[2][0], iiko_headers)
        
        # По итогу перебэтча оказывается, что перераспределять заказы в этот бэтч из других бэтчей нет смысла
        # (не проходят по критериям или неэффективно по ранжированию), и этот бэтч (в котором отменился заказ) захлопывается,
        # так как в нем теперь все заказы готовы

    @allure.title("16 - Перебэтч - Отмена заказа в незахлопнутом бэтче и НЕ нужно перераспределять заказы")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_preparing_order_without_rebatch_3(self, get_test_name, iiko_headers):

        # Устанавливаем на ПВ default_max_deliveries_for_courier=4
        # Перемотреть тестовые данные, чтобы пачка заказов была в одном месте, а у другого курьера - в другом месте пачка

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers), 
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers), # READY -> CANCEL
            self.delivery_service.create_order("Ямская 10", 45, iiko_headers),
        ]
        
        time.sleep(30)
        
        second_batch = [
            self.delivery_service.create_order("Больничный переулок, 2", 60, iiko_headers),
            self.delivery_service.create_order("Больничный переулок, 2", 70, iiko_headers),
        ]

        # Готовим заказ из батча 1 (происходит назначение на курьера)
        # self.assign_order(first_batch[1], iiko_headers)
        time.sleep(30)

        # 2. Отменяем ГОТОВЫЙ заказ из батча 1
        self.delivery_service.cancel_order(first_batch[1][0], iiko_headers)

        # 3. Проверка
        # По итогу перебэтча оказывается, что перераспределять заказы в этот бэтч из других бэтчей нет смысла
        # (не проходят по критериям или неэффективно по ранжированию).
        # Продолжается ожидание приготовления готовящихся заказов в этом бэтче.

    @allure.title("17 - Перебэтч - Отмена заказа в захлопнутом бэтче")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_cancel_order_in_closed_batch(self, get_test_name, iiko_headers):
        # 1. Создаем батч
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers), # READY
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers), # READY
        ]

        # Готовим 2 заказа из батча 1 (происходит назначение на курьера)
        # self.assign_order(first_batch[1], iiko_headers)
        time.sleep(90)

        # 2. Отменяется один из заказов
        self.delivery_service.cancel_order(first_batch[1][0], iiko_headers)

    @allure.title(
        "18 - Перебэтч - Параметры <Время приготовления заказа>,"
        "<Время на получение заказа>, <Время на передачу заказа клиенту> и <Допустимое время опоздания>," \
        "а также ожидаемое время возвращения курьера на филиал учитываются корректно"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_new_order_exceeds_max_delivery_time_triggers_3pl(self, get_test_name, iiko_headers):
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 80, iiko_headers), # чтоб не ждать 1 ч до вызова 3PL - подобрать меньшие таймтил
            self.delivery_service.create_order("Ямская 10", 60, iiko_headers),
        ]

        time.sleep(30)

        # при time_till >= 13 (или 15?) минут - все 3 заказа будут в батче у курьера
        third_order_for_first_batch = [
            self.delivery_service.create_order("Октябрьская 105", 12, iiko_headers),
        ]

        # 2. Нажимаем "Забрал" в мобилке на 2-х готовых заказах

    @allure.title(
        "21 - Приоритизация. Выбор бэтча для заказа, когда под критерии бэтчинга для этого заказа подходит несколько бэтчей - "
        "Ранжирование по кол-ву заказов в бэтче."
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_batch_priority_by_orders_count(self, get_test_name, iiko_headers):
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # TPH у курьеров должен быть одинаков

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers),
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers),
        ]

        second_batch = [
            self.delivery_service.create_order("Анненская 2", 45, iiko_headers),
        ]

        time.sleep(15)

        # 2. Появляется новый готовящийся заказ
        new_order = self.delivery_service.create_order("Анненская 17", 60, iiko_headers)

        # 3. Проверка
        # Заказ попадает в бэтч с меньшем кол-во заказов (согласно логике ранжирования).

    @allure.title(
        "22 - Приоритизация. Выбор бэтча для заказа, когда под критерии бэтчинга для этого заказа подходит несколько бэтчей - "
        "Ранжирование по средней длине маршрута на один заказ."
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_batch_priority_by_avg_route_length(self, get_test_name, iiko_headers):
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3

        # TPH: у Семена - 6 заказа (TPH:1.601586006331217)
        # TPH: у Федора - 9 заказов (TPH:2.133116374014157)

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Марьиной Рощи 9", 60, iiko_headers),
            self.delivery_service.create_order("Марьиной Рощи 9", 30, iiko_headers),
        ]

        second_batch = [
            self.delivery_service.create_order("Анненская 17", 60, iiko_headers),
            self.delivery_service.create_order("Анненская 17", 45, iiko_headers),
        ]

        time.sleep(15)

        # 2. Появляется новый готовящийся заказ
        new_order = self.delivery_service.create_order("Анненская 2", 60, iiko_headers)

        # Логи (факт):
        # courierID=aaefc2fb-57fa-486a-ae23-fdd559207e47
        # deliverYIDs=\"[3e6f12b0-f240-465e-9d52-4277d67160bc a57afdef-efe0-4057-b0f0-8dc9f4b3323f d3279f39-9355-44a8-9d97-6e2a7c5b9ec6]

        # avg distance first=1414
        # avg distance second=1667
        # combination first=\"{[d3279f39-9355-44a8-9d97-6e2a7c5b9ec6 3e6f12b0-f240-465e-9d52-4277d67160bc a57afdef-efe0-4057-b0f0-8dc9f4b3323f]
        # aaefc2fb-57fa-486a-ae23-fdd559207e47 4244.4 map[]
        # combination second=\"{[a57afdef-efe0-4057-b0f0-8dc9f4b3323f 3e6f12b0-f240-465e-9d52-4277d67160bc a9642d6b-df54-4741-ac2a-dbaac580478d]
        # aaefc2fb-57fa-486a-ae23-fdd559207e47 5002.200000000001 map[]

        # Расчет:
        # Планируемый пробег 4.20 км / Количество заказов 3 = 1400 м
        
        # Расчет (для меньшего батча):
        # Планируемый пробег 5.00 км / Количество заказов 2 = 2500 м

        # 3. Проверка
        # Происходит перебэтч.
        # По итогам перебэтча перераспределение заказов между двумя незахлопнутыми бэтчами не происходит.
        # Новый заказ попадает во 2 бэтч, у курьера которого TPH ниже, несмотря на то, что длина маршрута на один заказ
        # при добавлении в 1 бэтч была бы ниже (но незначительно ниже)."

    @allure.title(
        "23 - Приоритизация. Выбор бэтча для заказа, когда под критерии бэтчинга для этого заказа подходит несколько бэтчей - "
        "Ранжирование по TPH курьера."
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_batch_priority_by_tph(self, get_test_name, iiko_headers):
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3

        # TPH: у Семена - 9 заказа (TPH:2.1413962696439914)
        # TPH: у Федора - 11 заказа (TPH:2.139832609049052)

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers),
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers),
        ]

        second_batch = [
            self.delivery_service.create_order("Анненская 17", 60, iiko_headers),
            self.delivery_service.create_order("Анненская 17", 45, iiko_headers),
        ]

        time.sleep(15)

        # 2. Появляется новый готовящийся заказ
        new_order = self.delivery_service.create_order("Веткина 2Ас7", 60, iiko_headers)

        # Логи:
        # avg distance second=
        # combination second=

        # Расчет:
        # Планируемый пробег  км / Количество заказов  =  м

        # 3. Проверка
        # Происходит перебэтч.
        # По итогам перебэтча перераспределение заказов между двумя незахлопнутыми бэтчами не происходит.
        # Новый заказ попадает в певрвый бэтч (в котором общая длина маршрута (с учетом возврата на филиал) оказывается меньше),
        # несмотря на то, что у первого курьера TPH выше.

    @allure.title(
        "24 - Приоритизация - "
        "Создание нового бэтча при появлении нового готовящегося заказа."
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_new_batch_creation_when_new_cooking_order_appears(self, get_test_name, iiko_headers):
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # TPH у курьеров должен быть одинаков?

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers),
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers),
        ]

        time.sleep(30)

        # 2. Появляется новый готовящийся заказ
        new_order = self.delivery_service.create_order("Олимпийский 26с1", 80, iiko_headers)

        # 3. Проверка
        # Создается новый бэтч на одного из курьеров, у которого нет незахлопнутного бэтча.


    @allure.title("25 - Захлопывание батча - Завершено приготовление всех заказов в батче")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_batch_close_all_orders_completed(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        """
        1. Создаем незахлопнутый батч с несколькими заказами (1..N)
        2. Все заказы завершают приготовление
        3. Проверяем что батч захлопнулся и выполнены все необходимые действия
        """
        # Настраиваем курьера ["Семен"]

        # 1. Создаем батч с несколькими заказами
        batch_orders = [
            self.delivery_service.create_order("Башиловская 22", 30, iiko_headers), # READY
            self.delivery_service.create_order("Башиловская 22", 45, iiko_headers) # READY
        ]
        
        # 2. Готовим заказы из батча 1 (происходит назначение на курьера)
        time.sleep(60)  # Ждем завершения приготовления
        
        # 3. Проверяем что батч захлопнут
        courier_id = courier_iiko_data["couriers"]["Семен"]
        courier_headers = AuthService.get_courier_headers(courier_id, admin_auth_headers)
        batch_info = self.courier_service.get_courier_batch_deliveries(get_test_name, courier_headers)
        print(batch_info)
        
        # Проверяем что все заказы в статусе готово к доставке
        # Проверяем что батч захлопнут (нет готовящихся заказов)
        assert batch_info['deliveries'] == []
        assert len(batch_info['deliveries']) == 0
        # Проверяем что курьер получил уведомление

    @allure.title("26 - Захлопывание ботча - Завершено приготовление единственного заказа в батче")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_batch_close_single_order_completed(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        """
        1. Создаем батч ровно с одним заказом
        2. Заказ завершает приготовление
        3. Проверяем что батч захлопнулся
        """
        # Настраиваем курьера ["Семен"]
        
        # 1. Создаем батч с одним заказом
        single_order = self.delivery_service.create_order("Башиловская 22", 30, iiko_headers) # READY
        
        # 2. Готовим заказы из батча 1 (происходит назначение на курьера)
        time.sleep(30) # Ждем завершения приготовления
        
        # 3. Проверяем статус батча
        courier_id = courier_iiko_data["couriers"]["Семен"]
        courier_headers = AuthService.get_courier_headers(courier_id, admin_auth_headers)
        batch_info = self.courier_service.get_courier_batch_deliveries(get_test_name, courier_headers)
        print(batch_info)

        # Проверяем что все заказы в статусе готово к доставке
        # Проверяем что батч захлопнут (нет готовящихся заказов)
        assert batch_info['deliveries'] == []
        assert len(batch_info['deliveries']) == 0
        # Проверяем что курьер получил уведомление

    @allure.title("27 - Захлопывание ботча - Некогда ждать")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_batch_close_no_time_to_wait(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        """
        1. Создаем ботч с готовыми и готовящимися заказами
        2. Имитируем ситуацию "некогда ждать" (готовые заказы могут опоздать)
        3. Проверяем что:
        - Бaтч захлопнут
        - Неготовый заказ возвращен в пул распределения
        """
        # Настраиваем курьера ["Семен"]
        
        # 1. Создаем ботч с разными заказами
        ready_order = self.delivery_service.create_order("Башиловская 22", 15, iiko_headers) # READY
        cooking_order = self.delivery_service.create_order("Башиловская 22", 60, iiko_headers)
        
        # 2. Готовим заказ из батча (происходит назначение на курьера)
        time.sleep(30) # Ждем завершения приготовления
        
        # 3. Имитируем ситуацию "нет времени ждать"
        # self._simulate_no_time_to_wait(preparing_order)
        # ближний заказ готовим (назначаем)

        # 4. Прожимаем "Забрал" в мобилке на готовом заказе

    @allure.title("28 - Вызов 3PL - Курьер нажимает 'Не буду ждать' на единственный готовящийся заказ")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_batch_close_courier_refuse_single_cooking(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        pass

    @allure.title(
        "31 - Вызов 3PL -" \
        "<Время подачи внешнего курьера>, <Время на получение заказа>, расчетное время в пути <Время на передачу заказа клиенту>, " \
        "time_till и <Допустимое время опоздания 3PL> корректно учитываются при расчете времени, когда нужно вызвать 3PL"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_order_cannot_be_added_to_any_batch(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        """
        1. Создаем заказ с параметрами, которые не проходят по критериям батчинга
        2. Проверяем что заказ не был добавлен ни в один батч
        3. Проверяем что время для вызова 3PL рассчитывается корректно
        """
        # Настраиваем курьеров ["Семен", "Федор", "3PL"]

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers),
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers),
        ]

        second_batch = [
            self.delivery_service.create_order("Анненская 17", 60, iiko_headers),
            self.delivery_service.create_order("Анненская 17", 45, iiko_headers),
        ]

        time.sleep(15)

        # 2. Появляется новый готовящийся заказ с уникальными параметрами (например, очень далекий адрес)
        test_duration = 120
        new_order = self.delivery_service.create_order("Чертановская 26", test_duration, iiko_headers)
        ROUTE_TIME = 65 # по ЯКартам - 65...93 мин, разница с time_deadline_3pl = 23 мин
        
        # Ждем достаточно времени для обработки батчинга
        time.sleep(60)
        
        # 3. Проверки
        # Проверяем что заказ не в батчах у курьеров
        
        # Рассчитываем ожидаемое время вызова 3PL
        creation_time = datetime.now()
        time_till = creation_time + timedelta(minutes=test_duration)
        expected_call_time = (
            time_till +
            timedelta(minutes=DeliveryTimeCalculator.TIME_LATE_3PL) -
            timedelta(minutes=DeliveryTimeCalculator.TIME_ARRIVE_3PL) -
            timedelta(minutes=ROUTE_TIME)
        )
        print(f"creation_time: {creation_time}")
        print(f"time_till: {time_till}")
        print(f"expected_call_time: {expected_call_time}")

    @allure.title(
        "32 - Вызов 3PL -" \
        "Изначально (при создании) нераспределенный ни в один бэтч заказ попадает в какой-либо бэтч до вызова 3PL " \
        "и этот бэтч захлопывается с этим заказом"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_order_added_to_batch_before_call_3pl_success(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        """
        1. Создан новый заказ.
        2. Этот заказ не смог сбэтчится ни на одного курьера (не прошел по критериям бэтчинга).
        3. Через несколько минут происходит триггер перебэтчинга, и в результате этого ребэтча заказ должен сбэтчиться в какой-либо бэтч.
        4. Еще через некоторое время бэтч, в который попал этот заказ, захлопывается.
        """
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # Настраиваем курьеров ["Семен", "Федор", "3PL"]

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 15, iiko_headers), # CANCEL
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers),
            self.delivery_service.create_order("Октябрьская 105", 40, iiko_headers),
            self.delivery_service.create_order("Октябрьская 105", 20, iiko_headers),
        ]

        second_batch = [
            self.delivery_service.create_order("Анненская 2", 45, iiko_headers),
            self.delivery_service.create_order("Анненская 17", 60, iiko_headers),
        ]

        # 2. Отменяем из батча заказ, парный с нераспределенным заказом по адресу (триггер перебэтчинга)
        # 3. Ждем захлопывания бэтча
        # 4. Проверки
        # - Заказ бэтчится в какой-либо бэтч.
        # - Таймер 3PL для этого заказа не удаляется до тех пор, пока бэтч с этим заказом не захлопнется.
        # - После залопывания бэтча с этим заказом таймер 3PL для этого заказа удаляется.

    @allure.title(
        "33 - Вызов 3PL - " \
        "Изначально (при создании) нераспределенный ни в один бэтч заказ попадает в какой-либо бэтч до вызова 3PL, " \
        "но курьер отказывается от этого заказа"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_order_added_to_batch_before_call_3pl_2(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        """
        1. Создан новый заказ.
        2. Этот заказ не смог сбэтчится ни на одного курьера (не прошел по критериям бэтчинга).
        3. Через несколько минут происходит триггер перебэтчинга, и в результате этого ребэтча заказ должен сбэтчиться в какой-либо бэтч.
        4. После этого курьер нажимает ""Не буду ждать"" на этот заказ и он убирается из бэтча."
        """
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # Настраиваем курьеров ["Семен", "Федор"]
        
        # 2. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 15, iiko_headers), # CANCEL
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers),
            self.delivery_service.create_order("Октябрьская 105", 40, iiko_headers),
            self.delivery_service.create_order("Октябрьская 105", 20, iiko_headers),
        ]

        second_batch = [
            self.delivery_service.create_order("Анненская 2", 45, iiko_headers),
            self.delivery_service.create_order("Анненская 17", 60, iiko_headers),
        ]

        # 3. Отменяем из батча заказ, парный с нераспределенным заказом по адресу (триггер перебэтчинга)
        # 4. Нажимаем "Не буду ждать" на заказе
        # 5. Проверки

    @allure.title(
        "34 - Вызов 3PL -" \
        "Изначально (при создании) нераспределенный ни в один бэтч заказ не попал в бэтч даже после нескольких триггеров ребэтча и в итоге вызван 3PL"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_order_added_to_batch_before_call_3pl_3(self, get_test_name, iiko_headers, admin_auth_headers, courier_iiko_data):
        """
        1. Создан новый заказ.
        2. Этот заказ не смог сбэтчится ни на одного курьера (не прошел по критериям бэтчинга).
        3. Через некоторое время происходит триггер перебэтчинга, в результате которого заказ опять не сбэтчился ни в один бэтч.
        4. Еще через некоторое время происходит еще один триггер перебэтчинга, в результате которого заказ опять не сбэтчился ни в один бэтч.
        5. Еще через некоторое время наступает время, когда с учетом <Время подачи внешнего курьера>, <Время на получение заказа>,
        расчетное время в пути <Время на передачу заказа клиенту> и <Допустимое время опоздания 3PL> не остается времени ждать и нужно вызывать 3PL.
        """
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # Настраиваем курьеров ["Семен", "Федор", "3PL"]

        # 2. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 15, iiko_headers), # UNDISTRIBUTED
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers),
            self.delivery_service.create_order("Октябрьская 105", 40, iiko_headers),
            self.delivery_service.create_order("Октябрьская 105", 20, iiko_headers),
        ]

        second_batch = [
            self.delivery_service.create_order("Анненская 2", 45, iiko_headers),
            self.delivery_service.create_order("Анненская 17", 60, iiko_headers),
        ]

        # 3. Меняем таймтил на любом заказе кроме нераспределенного (1й триггер перебэтчинга)
        # 4. Меняем таймтил на любом заказе кроме нераспределенного (2й триггер перебэтчинга)
        # 4.1 МОЖНО ПОПРОБОВАТЬ ВЫЗВАТЬ ТРИГГЕР NO_TIME_TO_WAIT ЕСЛИ ПРИГОТОВИТЬ 1Й ПОДГОРАЮЩИЙ ЗАКАЗ ИЗ 1-ГО БАТЧА
        # 5. Ждем захлопывания бэтча
        # 6. Проверки
        # - Заказ бэтчится в какой-либо бэтч.
        # - Таймер 3PL для этого заказа не удаляется до тех пор, пока бэтч с этим заказом не захлопнется.
        # - После залопывания бэтча с этим заказом таймер 3PL для этого заказа удаляется.

    @allure.title(
        "36 - Вмешательство логиста - " \
        "Логист переназначил заказ из захлопнувшегося бэтча, и у курьера, на которого переназначен заказ, есть незахлопнутый бэтч, " \
        "в который переназначенный заказ проходит по критериям. Называем это именно 'переназначением', потому что после " \
        "захлопывания бэтча должно сразу произойти назначение курьера на заказ в iiko."
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_logistician_reassigns_order_from_closed_batch_to_another_courier_successfully(self, get_test_name, iiko_headers, admin_auth_headers):
        """
        1. Бэтч захлопнут
        2. Логист вручную в iikoFront переназначает один из заказов этого бэтча на другого курьера
        3. У курьера, на которого переназначили этот заказ, есть незахлопнутый бэтч, в которых этот переназначенный заказ
        проходит и по размеру бэтча, и по другим критериям (<Радиус объединения доставок>, <Допустимое время опоздания> и т.д.)"
        """
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # Настраиваем курьеров ["Семен", "Федор"]

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers),
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers), 
            self.delivery_service.create_order("Ямская 10", 60, iiko_headers),
        ]

        second_batch = [
            self.delivery_service.create_order("Ямская 10", 45, iiko_headers), # READY
            self.delivery_service.create_order("Сущёвский Вал 55", 20, iiko_headers),
        ]
        
        # 2. Готовим единственный заказ из 2-го батча (они назначаются на курьера)
        # 3. Отменяем парный по адресу заказ из 1-го батча (т.к. макс в руки = 3)
        # 4. Логист в терминале переназначает один из заказов этого бэтча на другого курьера
        
        # 5. Проверки:
        # - Переназначенный заказ попадает в бэтч курьера, на которого переназначили этот заказ.
        # - Нужно, чтобы заказ попал именно в бэтч, чтобы этот заказ учитывался при следующих калькуляциях ребэтча с точки зрения лимита бэтча
        # - Как всегда при ручном назначении логистом, этот заказ больше не может быть снят с этого курьера АН-ом (ручное назначение важнее АН). 
        # - Жизненный цикл бэтча далее стандартный (захлопывается по триггерам захлопывания).

    @allure.title(
        "37 - Вмешательство логиста - " \
        "Логист переназначил заказ из захлопнувшегося бэтча, и у курьера, на которого переназначен заказ, есть незахлопнутый бэтч, " \
        "в который переназначенный заказ проходит по размеру бэтча, но не проходит хотя бы по 1 другому критерию."
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_logistican_reassigns_order_from_closed_batch_to_another_courier_without_reaching_time_late_criteria(
            self, get_test_name, iiko_headers, admin_auth_headers
        ):
        """
        1. Бэтч захлопнут
        2. Логист вручную в iikoFront переназначает один из заказов этого бэтча на другого курьера
        3. У курьера, на которого переназначили этот заказ, есть незахлопнутый бэтч, в которых этот переназначенный заказ проходит
        по размеру бэтча (<Максимальное количество заказов в руки>), но не проходит хотя бы по одному из других критериев.
        """
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # Настраиваем курьеров ["Семен", "Федор"]

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 80, iiko_headers),
            self.delivery_service.create_order("Ямская 10", 60, iiko_headers),
        ]

        # при time_till >= 13 (или 15?) минут - все 3 заказа будут в батче у курьера
        third_order_for_first_batch = [
            self.delivery_service.create_order("Октябрьская 105", 12, iiko_headers), # READY
        ]
        
        # 2. Готовим заказ из 1-го батча (они назначаются на курьера)
        # 3. Логист в терминале переназначает один из заказов этого бэтча на другого курьера
        # 4. Проверки:

    @allure.title(
        "38 - Вмешательство логиста - " \
        "Логист переназначил заказ из захлопнувшегося бэтча, и у курьера, на которого переназначен заказ, есть незахлопнутый бэтч, " \
        "но переназначенный заказ не проходит по размеру бэтча."
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_logistician_reassigns_order_from_closed_batch_to_another_courier_with_reaching_batch_size_limit(
            self, get_test_name, iiko_headers, admin_auth_headers
        ):
        """
        1. Бэтч захлопнут
        2. Логист вручную в iikoFront переназначает один из заказов этого бэтча на другого курьера
        3. У курьера, на которого переназначили этот заказ, есть незахлопнутый бэтч, в который этот переназначенный заказ не проходит
        по <Максимальное количество заказов в руки>.
        """
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # Настраиваем курьеров ["Семен", "Федор"]

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers),
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers), 
            self.delivery_service.create_order("Ямская 10", 60, iiko_headers),
        ]

        second_batch = [
            self.delivery_service.create_order("Ямская 10", 45, iiko_headers), # READY
        ]
        
        # 2. Готовим заказ из 1-го батча (они назначаются на курьера)
        # 3. Логист в терминале переназначает один из заказов этого бэтча на другого курьера
        # 4. Проверки:

    @allure.title(
        "39 - Вмешательство логиста - " \
        "Логист переназначил заказ из захлопнувшегося бэтча, и у курьера, на которого переназначен заказ, есть захлопнутый бэтч."
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_logistician_reassigns_order_from_closed_batch_to_another_courier_with_existing_closed_batch(
            self, get_test_name, iiko_headers, admin_auth_headers
        ):
        """
        1. Бэтч захлопнут
        2. Логист вручную в iikoFront переназначает один из заказов этого бэтча на другого курьера
        3. У курьера, на которого переназначили этот заказ, есть захлопнутый бэтч.
        """
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # Настраиваем курьеров ["Семен", "Федор"]

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers), # READY
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers), # READY
            self.delivery_service.create_order("Ямская 10", 60, iiko_headers), # READY
        ]

        second_batch = [
            self.delivery_service.create_order("Ямская 10", 45, iiko_headers), # READY
        ]
        
        # 2. Готовим все заказы (они назначаются на курьеров и у нас будет 2 закрытых батча)
        # 3. Логист в терминале переназначает один из заказов 1-го закрытого бэтча на другого курьера
        # 4. Проверки:

    @allure.title(
        "40 - Вмешательство логиста - " \
        "Логист назначил последний готовящийся заказ из незахлопнутного бэтча на другого курьера"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_logistician_reassigns_last_preparing_order_from_not_closed_batch_to_another_courier(
            self, get_test_name, iiko_headers, admin_auth_headers
        ):
        """
        1. Бэтч не захлопнут.
        2. Логист вручную в iikoFront переназначает один из заказов этого бэтча на другого курьера
        """
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # Настраиваем курьеров ["Семен", "Федор"]

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers), # READY
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers), # READY
            # self.delivery_service.create_order("Ямская 10", 60, iiko_headers),
            self.delivery_service.create_order("Веткина 2Ас7", 100, iiko_headers), 
        ]

        second_batch = [
            self.delivery_service.create_order("Ямская 10", 45, iiko_headers),
        ]

        # 2. Готовим 2 из 3-х заказов в 1-м батче
        # 3. Переназначаем последний готовящийся заказ из незахлопнутного бэтча на другого курьера
        # 4. Проверки:

    @allure.title(
        "41 - Вмешательство логиста - " \
        "Логист назначил заказ из незахлопнутного бэтча на курьера этого же бэтча"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_logistician_reassigns_order_from_not_closed_batch_to_the_same_courier(
            self, get_test_name, iiko_headers, admin_auth_headers
        ):
        """
        1. Бэтч не захлопнут.
        2. Логист назначает курьера этого бэтча на этот заказ в iiko.
        """
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # Настраиваем курьеров ["Семен", "Федор"]

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers),
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers),
            self.delivery_service.create_order("Ямская 10", 60, iiko_headers), 
        ]

        # 2. Логист назначает курьера этого бэтча на этот заказ в терминале
        # 3. Проверки:

    @allure.title(
        "42 - Вмешательство логиста - " \
        "Логист назначил заказ, который не находится ни в каком бэтче (нераспределенный заказ), " \
        "на курьера, у которого есть незахлопнутый бэтч и этот заказ проходит по всем критериям бэтчинга."
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_logistician_reassigns_order_not_belongs_to_any_batch_to_courier(
            self, get_test_name, iiko_headers, admin_auth_headers
        ):
        """
        1. Заказ не относится ни к одному бэтчу.
        2. Логист назначает заказ на курьера, у которого есть незахлопнутый бэтч, и этот заказ проходит по всем критериям бэтчинга.
        """
        pass

    @allure.title(
        "43 - Вмешательство логиста - " \
        "Логист назначил заказ, который не находится ни в каком бэтче (нераспределенный заказ), на курьера, " \
        "у которого есть незахлопнутый бэтч, но этот заказ не проходит хотя бы по одному критерию бэтчинга"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_logistician_reassigns_order_not_belongs_to_any_batch_to_courier_2(
            self, get_test_name, iiko_headers, admin_auth_headers
        ):
        """
        1. Заказ не относится ни к одному бэтчу.
        2. Логист назначает заказ на курьера, у которого есть незахлопнутый бэтч, и этот заказ не проходит хотя бы по одному критерию бэтчинга.
        """
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # Настраиваем курьеров ["Семен", "3PL"]

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers),
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers),
            self.delivery_service.create_order("Ямская 10", 60, iiko_headers), 
        ]

        time.sleep(15)
        undistributed_order = [
            self.delivery_service.create_order("Ямская 10", 45, iiko_headers),
        ]

        # 2. Логист назначает нераспределенный заказ в терминале на курьера
        # 3. Проверки:
        # - для нераспределенного заказа должен был включиться таймер для отправки в 3PL еще до ручного вмешательства логиста
        # - этот заказ больше не может быть снят с этого курьера АН-ом (ручное назначение важнее АН)
        # - Таймер 3PL для этого заказа удаляется

    @allure.title(
        "44 - Вмешательство логиста - " \
        "Логист назначил заказ, который не находится ни в каком бэтче (нераспределенный заказ), на курьера, у которого есть захлопнутый бэтч"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_logistician_reassigns_order_not_belongs_to_any_batch_to_courier_3(
            self, get_test_name, iiko_headers, admin_auth_headers
        ):
        """
        1. Заказ не относится ни к одному бэтчу.
        2. Логист назначает заказ на курьера, у которого есть захлопнутый бэтч
        """
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # Настраиваем курьеров ["Семен", "3PL"]

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers), # READY
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers), # READY
            self.delivery_service.create_order("Ямская 10", 60, iiko_headers), # READY
        ]

        # 2. Готовим заказы из батча 1 (они назначатся на курьера)
        time.sleep(60)

        # 3. Создаем нераспределенный заказ
        undistributed_order = [
            self.delivery_service.create_order("Ямская 10", 45, iiko_headers),
        ]

        # 4. Логист назначает нераспределенный заказ в терминале на курьера, у которого есть захлопнутый бэтч
        # 5. Проверки:

    @allure.title(
        "45 - Вмешательство логиста - " \
        "Логист назначил заказ, который не находится ни в каком бэтче (нераспределенный заказ), на курьера 3PL"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_logistician_reassigns_order_not_belongs_to_any_batch_to_3PL(
            self, get_test_name, iiko_headers, admin_auth_headers
        ):
        """
        1. Заказ не относится ни к одному бэтчу.
        2. Логист назначает заказ на курьера 3PL.
        """
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # Настраиваем курьеров ["Семен", "3PL"]

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers),
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers),
            self.delivery_service.create_order("Ямская 10", 60, iiko_headers),
        ]

        undistributed_order = [
            self.delivery_service.create_order("Ямская 10", 45, iiko_headers),
        ]

        # 2. Логист назначает нераспределенный заказ в терминале на 3PL
        # 3. Проверки:

    @allure.title("46 - Вмешательство логиста - Логист снял курьера с заказа")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_logistician_removes_courier_from_order(self, get_test_name, iiko_headers, admin_auth_headers):
        """
        1. У заказа в iiko назначен курьер.
        2. Логист убирает курьера с заказа (не назначает другого курьера, а именно оставляет поле Курьер пустым) и сохраняет заказ.
        """
        # Устанавливаем на ПВ default_max_deliveries_for_courier=3
        # Настраиваем курьеров ["Семен", "Федор", "3PL"]

        # 1. Создаем батчи
        first_batch = [
            self.delivery_service.create_order("Сущёвский Вал 55", 60, iiko_headers),
            self.delivery_service.create_order("Сущёвский Вал 55", 30, iiko_headers), # ASSIGN COURIER -> SKIP COURIER
            self.delivery_service.create_order("Ямская 10", 60, iiko_headers),
        ]

        # 2. Логист готовит 1 из заказов батча (он назначается на курьера)
        # 3. Логист убирает курьера с заказа
        # 4. Проверки:

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
