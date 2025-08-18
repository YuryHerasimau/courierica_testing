import allure
from services.iiko_delivery_service import IikoDeliveryService


# Текущие значения VRP конфига
VRP_MAX_ROUTE_DURATION = 12 * 60                # 720 мин, 43200 с в конфиге
VRP_MAX_WAITING_TIME = 0.5 * 60                 # 30 мин, 1800 с в конфиге
VRP_MAX_SOLVE_TIME = 0.5                        # 0.5 мин, 30 с в конфиге
VRP_TIMESLOT_DURATION = 60                      # 60 мин, 1 ч в конфиге
VRP_AVG_FUEL_CONSUMPTION_L_PER_100KM = 10.0     # 10 л/100км

@allure.epic("Testing regular dispatch (auto-assignment simulation)")
class TestRegularDispatch:
    delivery_service = IikoDeliveryService()

    # Preconditions:
    # Устанавливаем на ПВ default_max_deliveries_for_courier=30
    # Устанавливаем на ПВ auto_assign_version=regular_v1
    # Создаем 100 заказов
    # Настраиваем курьеров ["Семен", "Федор"]

    @allure.title("1 - Близкие адреса, одинаковый duration")
    def test_close_addresses_same_duration(self, iiko_headers):
        self.delivery_service.create_order("Башиловская 22", 60, iiko_headers)
        self.delivery_service.create_order("Хуторская 38Ас23", 60, iiko_headers)

    @allure.title("2 - Близкие адреса, разный duration")
    def test_close_addresses_diff_duration(self, iiko_headers):
        self.delivery_service.create_order("Башиловская 22", 45, iiko_headers)
        self.delivery_service.create_order("Хуторская 38Ас23", 90, iiko_headers)

    @allure.title("3 - Далёкие адреса, одинаковый duration")
    def test_far_addresses_same_duration(self, iiko_headers):
        self.delivery_service.create_order("Чертановская 26", 120, iiko_headers)
        self.delivery_service.create_order("Сущёвский Вал 55", 120, iiko_headers)

    @allure.title("4 - Далёкие адреса, разный duration")
    def test_far_addresses_diff_duration(self, iiko_headers):
        self.delivery_service.create_order("Чертановская 26", 60, iiko_headers)
        self.delivery_service.create_order("Сущёвский Вал 55", 180, iiko_headers)

    @allure.title("5 - Смешанный набор заказов (имитация реального дня)")
    def test_mixed_orders(self, iiko_headers):
        self.delivery_service.create_order("Башиловская 22", 30, iiko_headers)
        self.delivery_service.create_order("Сущёвский Вал 55", 120, iiko_headers)
        self.delivery_service.create_order("Хуторская 38Ас23", 180, iiko_headers)
        self.delivery_service.create_order("Чертановская 26", 240, iiko_headers)

    @allure.title("6 - Максимально допустимое время доставки")
    def test_max_duration_orders(self, iiko_headers):
        self.delivery_service.create_order("Усиевича 8", VRP_MAX_ROUTE_DURATION, iiko_headers)
        self.delivery_service.create_order("Шереметьевская 2", VRP_MAX_ROUTE_DURATION, iiko_headers)
