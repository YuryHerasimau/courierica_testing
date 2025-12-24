import allure
import pytest
import time
import json
from datetime import datetime, timezone

from services.auth_service import AuthService
from services.courier_service import CourierService
from services.pickup_point_service import PickupPointService
from services.delivery_service import DeliveryService
from generator.delivery_generator import DeliveryGenerator
from src.prepare_data.prepare_delivery_data import PrepareDeliveryData
from settings import settings


@allure.feature("Testing ClickHouse Data Quality")
@pytest.mark.integration
@pytest.mark.clickhouse
class TestClickHouseData:
    """Интеграционные тесты для проверки качества данных в ClickHouse"""

    @allure.title("Проверка количества событий за последние 24 часа")
    def test_recent_events_count(self, clickhouse_client):
        result = clickhouse_client.query("""
            SELECT type, COUNT(*) as count
            FROM events 
            WHERE timestamp >= now() - INTERVAL 24 HOUR
            GROUP BY type
            ORDER BY count DESC
        """)
        
        events_count = dict(result.result_rows)
        total_events = sum(events_count.values())
        
        assert total_events > 0, "За последние 24 часа событий не найдено"
        assert len(events_count) > 0, "Не найдено ни одного типа событий за последние 24 часа"

    @allure.title("Проверка качества данных в таблице events")
    def test_events_data_quality(self, clickhouse_client):
        result = clickhouse_client.query("""
            SELECT 
                COUNTIf(id = '00000000-0000-0000-0000-000000000000') as empty_event_id,
                COUNTIf(type = '') as empty_event_type,
                COUNTIf(timestamp is NULL) as null_timestamp,
                COUNTIf(courier_id = '00000000-0000-0000-0000-000000000000') as empty_courier_id
            FROM events
            WHERE timestamp >= now() - INTERVAL 1 HOUR
        """)
        
        empty_event_id, empty_event_type, null_timestamp, empty_source = result.result_rows[0]
        
        assert empty_event_id == 0, f"Найдены события с пустым event_id: {empty_event_id}"
        assert empty_event_type == 0, f"Найдены события с пустым event_type: {empty_event_type}"
        assert null_timestamp == 0, f"Найдены события с NULL timestamp: {null_timestamp}"
        assert empty_source == 0, f"Найдены события с пустым source: {empty_source}"
        
    @allure.title("Проверка корректности временных меток событий")
    def test_events_have_valid_timestamps(self, clickhouse_client):
        result = clickhouse_client.query("""
            SELECT 
                min(timestamp) as oldest_event,
                max(timestamp) as newest_event,
                count(*) as total_events
            FROM events
            WHERE timestamp >= now() - INTERVAL 7 DAY
        """)
        
        oldest, newest, total = result.result_rows[0]
        
        # Проверяем, что события не из будущего
        assert newest <= datetime.now(), f"Найдены события из будущего: {newest}"
        print(f"Временной диапазон событий за 7 дней:")
        print(f"   Самое старое: {oldest}")
        print(f"   Самое новое: {newest}")
        print(f"   Всего событий: {total}")
        
        # Проверяем, что created_at позже timestamp (событие записано после того как произошло)
        invalid_order = clickhouse_client.query("""
            SELECT COUNT(*) 
            FROM events 
            WHERE created_at < timestamp
            AND timestamp >= now() - INTERVAL 7 DAY
        """).result_rows[0][0]
        
        assert invalid_order == 0, f"Найдены события, где created_at раньше timestamp: {invalid_order}"


@allure.feature("Testing ClickHouse event flow")
@pytest.mark.integration
@pytest.mark.clickhouse
@pytest.mark.slow
class TestClickHouseEvents:
    """Интеграционные тесты для проверки потока событий"""
    auth_service = AuthService()
    courier_service = CourierService()
    pickup_point_service = PickupPointService()
    delivery_service = DeliveryService()
    delivery_generator = DeliveryGenerator()
    delivery_data = PrepareDeliveryData()

    COMPANY_ID = settings.COURIER_COMPANY_ID
    PICKUP_POINT_ID = settings.COURIER_PICKUP_POINT_ID
    COURIER_ID = settings.COURIER_SAAS_ID
    
    @allure.title("Проверка потока событий после завершения доставки")
    def test_event_flow_after_delivery_completion(self, clickhouse_client, get_test_name, logistician_saas_auth_headers):
        result_before = clickhouse_client.query("""
            SELECT COUNT(*) 
            FROM events 
            WHERE type = 'order.completed' 
            AND timestamp >= now() - INTERVAL 5 MINUTE
        """)
        count_before = result_before.result_rows[0][0]
        print(f"📊 Событий order.completed за последние 5 минут до теста: {count_before}")

        now_utc = datetime.now(timezone.utc)
        info = next(
                self.delivery_generator.generate_delivery(
                    company_id=self.COMPANY_ID,
                    pickup_point_id=self.PICKUP_POINT_ID,
                    recipient_address="Беларусь, г Минск, ул Веры Хоружей, д 25/3",
                    recipient_point={"latitude": 53.921625, "longitude": 27.563493},
                    time_from=None,
                    time_till=f"{now_utc.date()}T22:30:00Z",
                )
            )
        data = self.delivery_data.prepare_delivery_data(info=info)
        delivery_id = self.delivery_service.create_delivery(get_test_name, data, logistician_saas_auth_headers)
        self.delivery_service.assign_delivery(get_test_name, delivery_id, settings.COURIER_SAAS_ID, logistician_saas_auth_headers)
        self.delivery_service.complete_delivery(get_test_name, delivery_id, "delivered", logistician_saas_auth_headers)
        
        time.sleep(1)
        
        result_after = clickhouse_client.query("""
            SELECT COUNT(*) 
            FROM events 
            WHERE type = 'order.completed' 
            AND timestamp >= now() - INTERVAL 5 MINUTE
        """)
        count_after = result_after.result_rows[0][0]
        print(f"📊 Событий order.completed за последние 5 минут после теста: {count_after}")
        
        # Проверяем, что появились новые события
        assert count_after > count_before, f"Новые события order.completed не обнаружены. Было: {count_before}, стало: {count_after}"

    @allure.title("Проверка правильности потока событий при открытии/закрытии смены курьера")
    def test_shift_events_flow(self, clickhouse_client, get_test_name, logistician_saas_auth_headers):
        self.courier_service.close_all_active_shifts(get_test_name, self.COURIER_ID, logistician_saas_auth_headers)

        self.courier_service.turn_on_shift(
            get_test_name, self.COURIER_ID, self.PICKUP_POINT_ID, logistician_saas_auth_headers
        )

        self.courier_service.close_shift(
            get_test_name, self.COURIER_ID, self.PICKUP_POINT_ID, logistician_saas_auth_headers
        )

        time.sleep(1)
        courier_events = clickhouse_client.query("""
            SELECT COUNT(*)
            FROM events 
            WHERE type IN ('courier.shift.started', 'courier.shift.closed')
            AND courier_id = %(courier_id)s
            AND timestamp >= now() - INTERVAL 10 MINUTE
        """, {'courier_id': self.COURIER_ID})
        
        event_count = courier_events.result_rows[0][0]
        assert event_count > 0, f"Не найдено событий смен для курьера {self.COURIER_ID}"

    @allure.title("Проверка статистики событий")
    def test_events_statistics(self, clickhouse_client):
        result = clickhouse_client.query("""
            SELECT 
                toDate(timestamp) as date,
                type,
                COUNT(*) as count,
                COUNT(DISTINCT courier_id) as unique_couriers
            FROM events 
            WHERE timestamp >= now() - INTERVAL 30 DAY
            GROUP BY date, type
            ORDER BY date DESC, count DESC
        """)
        
        assert len(result.result_rows) > 0, "Нет данных о событиях за последние 30 дней"
        
        for date, event_type, count, unique_couriers in result.result_rows:
            assert date is not None, "Найдена запись с пустой датой"
            assert event_type is not None, "Найдена запись с пустым типом события"
            assert count > 0, f"Найдена запись с нулевым количеством событий: {date}, {event_type}"
            assert unique_couriers >= 0, f"Отрицательное количество уникальных курьеров: {date}, {event_type}"