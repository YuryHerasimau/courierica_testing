import allure
import pytest

from settings import settings
from services.iiko_delivery_service import IikoDeliveryService
from services.delivery_service import DeliveryService
from generator.delivery_generator import DeliveryGenerator


# Текущие значения VRP конфига
VRP_MAX_ROUTE_DURATION = 12 * 60                # 720 мин, 43200 с
VRP_MAX_WAITING_TIME = 6 * 60                   # 360 мин, 21600 с
VRP_MAX_SOLVE_TIME = 10                         # 10 с
VRP_SOLVE_LOGGING = False
VRP_TIMESLOT_DURATION = 1                       # 60 мин
VRP_PENALTY = 14400                             # 4 ч
VRP_SAVE_SOLUTION_MAP_HTML = False
VRP_MAX_DEPOT_VISITS = 1
VRP_LATE_PENALTY_PER_SECOND = 10
VRP_AVG_FUEL_CONSUMPTION_L_PER_100KM = 10.0     # 10 л/100км

@allure.epic("Testing regular dispatch (auto-assignment simulation)")
@pytest.mark.dispatch_regular
class TestRegularDispatch:
    iiko_delivery_service = IikoDeliveryService()
    delivery_service = DeliveryService()
    order_generator = DeliveryGenerator()

    # Preconditions:
    # Устанавливаем на ПВ default_max_deliveries_for_courier=30
    # Устанавливаем на ПВ auto_assign_version=regular_v1
    # Создаем 100 заказов
    # Настраиваем курьеров ["Семен", "Федор"]

    @pytest.mark.skip
    @allure.title("1 - Близкие адреса, одинаковый duration")
    def test_close_addresses_same_duration(self, iiko_headers):
        self.iiko_delivery_service.create_order("Башиловская 22", 60, iiko_headers)
        self.iiko_delivery_service.create_order("Хуторская 38Ас23", 60, iiko_headers)

    @allure.title("2 - Близкие адреса, разный duration")
    def test_close_addresses_diff_duration(self, iiko_headers):
        self.iiko_delivery_service.create_order("Башиловская 22", 45, iiko_headers)
        self.iiko_delivery_service.create_order("Хуторская 38Ас23", 90, iiko_headers)

    @allure.title("3 - Далёкие адреса, одинаковый duration")
    def test_far_addresses_same_duration(self, iiko_headers):
        self.iiko_delivery_service.create_order("Чертановская 26", 120, iiko_headers)
        self.iiko_delivery_service.create_order("Сущёвский Вал 55", 120, iiko_headers)

    @allure.title("4 - Далёкие адреса, разный duration")
    def test_far_addresses_diff_duration(self, iiko_headers):
        self.iiko_delivery_service.create_order("Чертановская 26", 60, iiko_headers)
        self.iiko_delivery_service.create_order("Сущёвский Вал 55", 180, iiko_headers)

    @allure.title("5 - Смешанный набор заказов (имитация реального дня)")
    def test_mixed_orders(self, iiko_headers):
        self.iiko_delivery_service.create_order("Башиловская 22", 30, iiko_headers)
        self.iiko_delivery_service.create_order("Сущёвский Вал 55", 120, iiko_headers)
        self.iiko_delivery_service.create_order("Хуторская 38Ас23", 180, iiko_headers)
        self.iiko_delivery_service.create_order("Чертановская 26", 720, iiko_headers)

    @allure.title("6 - Максимально допустимое время доставки")
    def test_max_duration_orders(self, iiko_headers):
        self.iiko_delivery_service.create_order("Усиевича 8", VRP_MAX_ROUTE_DURATION, iiko_headers)
        self.iiko_delivery_service.create_order("Шереметьевская 2", VRP_MAX_ROUTE_DURATION, iiko_headers)

    @allure.title("7 - 10 фиксированных заказов по городу")
    def test_fixed_10_orders(self, iiko_headers):
        addresses = [
            "Башиловская 22",
            "Сущёвский Вал 55",
            "Хуторская 38Ас23",
            "Ямская 10",
            "Усиевича 8",
            "Шереметьевская 2",
            "Чертановская 26",
            "Олимпийский 26с1",
            "Завода Серп и Молот 6к1",
            "Марьиной Рощи 9",
        ]
        durations = [30, 60, 90, 120, 180, 240, 45, 75, 150, 200]
        for addr, dur in zip(addresses, durations):
            self.iiko_delivery_service.create_order(addr, dur, iiko_headers)

    @allure.title("8 - 30 фиксированных заказов по городу")
    def test_fixed_30_orders(self, iiko_headers):
        addresses = [
            "Башиловская 22",
            "Сущёвский Вал 55",
            "Хуторская 38Ас23",
            "Ямская 10",
            "Усиевича 8",
            "Шереметьевская 2",
            "Чертановская 26",
            "Олимпийский 26с1",
            "Завода Серп и Молот 6к1",
            "Марьиной Рощи 9",
            "Анненская 17",
            "Анненская 2",
            "Октябрьская 105",
            "Веткина 2Ас7",
            "Шоссе Энтузиастов 11Ак1",
            "Карачаровская 2/16",
            "Шоссе Энтузиастов 26",
            "Сторожевая 38",
            "Петровско-Разумовский 28",
            "Соломенная Сторожки 5к1",
            "Яблочкова 19",
            "Дмитровский 18",
            "Руставели 3к5",
            "Больничный переулок, 2",
            "Новоалексеевская 3",
            "ПВ Курьерика",
            "Хуторская 38Ас23",
            "Октябрьская 105",
            "Ямская 10",
            "Сущёвский Вал 55",
        ]
        durations = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200,
                     30, 45, 90, 110, 130, 150, 170, 190, 210, 230,
                     50, 70, 95, 115, 135, 155, 175, 195, 215, 240]
        for addr, dur in zip(addresses, durations):
            self.iiko_delivery_service.create_order(addr, dur, iiko_headers)

    @allure.title("9 - Имитация реального маршрута")
    def test_real_route(self, iiko_headers):
        """
        Маршрут № 7836750 Закрыт Айжигит Калыев +79998172021
        - https://app.courierica.ru/#/route/5e8ce2fb-4c83-46ca-98fb-eff7797a634b
        - https://app.courierica.ru/#/route/a9a482c7-554a-4fe0-810e-611a377a66ee
        """
        addresses = [
            "Петровско-Разумовский 28",
            "Соломенная Сторожки 5к1",
            "Яблочкова 19",
            "Дмитровский 18",
            "Руставели 3к5",
            "Вятская 47с16",
            "Башиловская 15",
            "Юннатов 4кВ",
        ]
        durations = [90, 120, 130, 150, 160, 180, 210, 90]
        for addr, dur in zip(addresses, durations):
            self.iiko_delivery_service.create_order(addr, dur, iiko_headers)

    @allure.title("10 - Имитация маршрута Fix Price")
    def test_fix_price_route(self, iiko_headers):
        addresses = [
            "Дмитровское шоссе 169к9",
            "Химки Горшина 9/2",
            "Софьи Ковалевской 2к1",
            "Митинская 44",
            "Авиационная 74к4",
            "Берзарина 3к1",
            "Софьи Ковалевской 8",
            "Панфилова 4к2",
            "Вилиса Лациса 25к2",
            "Шарикоподшипниковская 40",
            "Юрьевка 1А",
            "Большая Филёвская 16к1",
            "Винокурова 6",
            "Мясницкая 13стр18",
            "Люберцы Шама 1",
            "Балашиха Яганова 3",
            "Волгоградский пр-кт 70",
            "Химки Вахнеевка 9",
            "Волжский Бульвар 5"
        ]
        durations = [VRP_MAX_ROUTE_DURATION] * len(addresses)
        for addr, dur in zip(addresses, durations):
            self.iiko_delivery_service.create_order(addr, dur, iiko_headers)

    @allure.title("11 - Имитация оптимизированного маршрута Fix Price")
    def test_fix_price_optimized_route(self, iiko_headers):
        addresses = [
            "Солнцевский пр-кт 2",
            "Гарибальди 23",
            "Днепропетровская 2",
            "Нежинская 6к1",
        ]
        durations = [6 * 60] * len(addresses)
        for addr, dur in zip(addresses, durations):
            self.iiko_delivery_service.create_order(addr, dur, iiko_headers)