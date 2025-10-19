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

    @allure.title("Проверка количества событий за последние 24 часа")
    def test_recent_events_count(self, clickhouse_client):
        """Проверяем, что в таблице есть события за последние 24 часа"""
        result = clickhouse_client.query("""
            SELECT type, COUNT(*) as count
            FROM events 
            WHERE timestamp >= now() - INTERVAL 24 HOUR
            GROUP BY type
            ORDER BY count DESC
        """)
        
        events_count = dict(result.result_rows)
        total_events = sum(events_count.values())
        
        print(f"Событий за последние 24 часа: {total_events}")
        for event_type, count in events_count.items():
            print(f"  {event_type}: {count}")
        
        if total_events == 0:
            print("⚠️Внимание: за последние 24 часа событий не найдено")

    @allure.title("Проверка качества данных в таблице events")
    def test_events_data_quality(self, clickhouse_client):
        """Проверяем качество данных в таблице events"""
        # Проверяем, что нет записей с пустыми обязательными полями
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
        
        print("Качество данных в таблице events соответствует требованиям")

    @allure.title("Проверка типов событий")
    def test_specific_event_types_exist(self, clickhouse_client):
        """Проверяем наличие конкретных типов событий"""
        result = clickhouse_client.query("""
            SELECT DISTINCT type
            FROM events 
            WHERE timestamp >= now() - INTERVAL 1 HOUR
            ORDER BY type
        """)
        
        event_types = [row[0] for row in result.result_rows]
        print(f"Типы событий за последний час: {event_types}")
        
        # Проверяем ожидаемые типы событий
        expected_events = ['order.completed', 'courier.shift.started', 'courier.shift.closed']
        
        found_expected = [et for et in expected_events if et in event_types]
        if found_expected:
            print(f"Найдены ожидаемые типы событий: {found_expected}")
        else:
            print("⚠️Внимание: ожидаемые типы событий не найдены")

    @allure.title("Проверка временных меток событий")
    def test_events_have_valid_timestamps(self, clickhouse_client):
        """Проверяем, что временные метки событий логичны"""
        result = clickhouse_client.query("""
            SELECT 
                min(timestamp) as oldest_event,
                max(timestamp) as newest_event,
                count(*) as total_events
            FROM events
            WHERE timestamp >= now() - INTERVAL 7 DAY
        """)
        
        oldest, newest, total = result.result_rows[0]
        
        print(f"Временной диапазон событий за 7 дней:")
        print(f"   Самое старое: {oldest}")
        print(f"   Самое новое: {newest}")
        print(f"   Всего событий: {total}")
        
        # Проверяем, что события не из будущего
        assert newest <= datetime.now(), "Найдены события из будущего"
        
        # Проверяем, что created_at позже timestamp (событие записано после того как произошло)
        invalid_order = clickhouse_client.query("""
            SELECT COUNT(*) 
            FROM events 
            WHERE created_at < timestamp
            AND timestamp >= now() - INTERVAL 1 DAY
        """).result_rows[0][0]
        
        assert invalid_order == 0, f"Найдены события где created_at раньше timestamp: {invalid_order}"


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
    
    @allure.title("Проверка потока событий после завершения доставки")
    def test_event_flow_after_delivery_completion(self, clickhouse_client, get_test_name, logistician_saas_auth_headers):
        # Получаем количество событий до теста
        result_before = clickhouse_client.query("""
            SELECT COUNT(*) 
            FROM events 
            WHERE type = 'order.completed' 
            AND timestamp >= now() - INTERVAL 5 MINUTE
        """)
        count_before = result_before.result_rows[0][0]
        
        print(f"📊 Событий order.completed за последние 5 минут до теста: {count_before}")
        
        company_id = settings.COURIER_COMPANY_ID
        pickup_point_id = settings.COURIER_PICKUP_POINT_ID
        now_utc = datetime.now(timezone.utc)

        print(f"🔄 Начинаем создание заказа")
        info = next(
                self.delivery_generator.generate_delivery(
                    company_id=company_id,
                    pickup_point_id=pickup_point_id,
                    recipient_address="Беларусь, г Минск, ул Веры Хоружей, д 25/3",
                    recipient_point={"latitude": 53.921625, "longitude": 27.563493},
                    time_from=None,
                    time_till=f"{now_utc.date()}T22:30:00Z",
                )
            )
        data = self.delivery_data.prepare_delivery_data(info=info)
        delivery_id = self.delivery_service.create_delivery(get_test_name, data, logistician_saas_auth_headers)
        self.delivery_service.complete_delivery(get_test_name, delivery_id, "delivered", logistician_saas_auth_headers)
        print("✅ Заказ завершен")
        
        # Ждем появления события ?
        time.sleep(10)
        
        # Проверяем количество событий после теста
        result_after = clickhouse_client.query("""
            SELECT COUNT(*) 
            FROM events 
            WHERE type = 'order.completed' 
            AND timestamp >= now() - INTERVAL 5 MINUTE
        """)
        count_after = result_after.result_rows[0][0]
        
        print(f"📊 Событий order.completed за последние 5 минут после теста: {count_after}")
        
        # Этот тест может быть информационным или проверочным в зависимости от сценария
        if count_after > count_before:
            print("✅ Новые события order.completed обнаружены!")
        else:
            print("ℹ️ Новых событий order.completed не обнаружено")

    @allure.title("Проверка правильности потока событий при открытии/закрытии смены курьера")
    def test_shift_events_flow(self, clickhouse_client, get_test_name, logistician_saas_auth_headers, courier_saas_auth_headers):
        # Получаем количество событий смен до теста
        result_before = clickhouse_client.query("""
            SELECT COUNT(*) 
            FROM events 
            WHERE type IN ('courier.shift.started', 'courier.shift.closed')
            AND timestamp >= now() - INTERVAL 5 MINUTE
        """)
        count_before = result_before.result_rows[0][0]
        
        print(f"📊 Событий смен за последние 5 минут до теста: {count_before}")
        
        # логика вызова API для начала/окончания смены
        pickup_point_id = settings.COURIER_PICKUP_POINT_ID
        courier_id = settings.COURIER_SAAS_ID

        print(f"🔄 Начинаем смену для курьера {courier_id} на ПВ {pickup_point_id}")
        self.courier_service.turn_on_shift(
            get_test_name, courier_id, pickup_point_id, logistician_saas_auth_headers
        )
        print("✅ Смена начата")

        time.sleep(5)

        self.courier_service.close_shift(
            get_test_name, courier_id, pickup_point_id, logistician_saas_auth_headers
        )
        print("✅ Смена закрыта")
        
        # Ждем появления событий ?
        time.sleep(10)
        
        # Проверяем количество событий после теста
        result_after = clickhouse_client.query("""
            SELECT COUNT(*) 
            FROM events 
            WHERE type IN ('courier.shift.started', 'courier.shift.closed')
            AND timestamp >= now() - INTERVAL 5 MINUTE
        """)
        count_after = result_after.result_rows[0][0]
        
        print(f"📊 Событий смен за последние 5 минут после теста: {count_after}")
        
        # Этот тест может быть информационным или проверочным в зависимости от сценария
        if count_after > count_before:
            print("✅ Новые события смен обнаружены!")
            
            # Проверяем последовательность событий
            recent_events = clickhouse_client.query("""
                SELECT type, timestamp, courier_id
                FROM events 
                WHERE type IN ('courier.shift.started', 'courier.shift.closed')
                AND timestamp >= now() - INTERVAL 5 MINUTE
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            
            print("📋 Последние события смен:")
            for event_type, timestamp, courier_id in recent_events.result_rows:
                print(f"  {timestamp} - {event_type} - courier: {courier_id}")
                
        else:
            print("ℹ️  Новых событий смен не обнаружено")

    @allure.title("Проверка статистики событий")
    def test_events_statistics(self, clickhouse_client):
        """Получаем общую статистику по событиям для аналитики"""
        result = clickhouse_client.query("""
            SELECT 
                toDate(timestamp) as date,
                type,
                COUNT(*) as count,
                COUNT(DISTINCT courier_id) as unique_couriers
            FROM events 
            WHERE timestamp >= now() - INTERVAL 7 DAY
            GROUP BY date, type
            ORDER BY date DESC, count DESC
        """)
        
        print("📈 Статистика событий за 7 дней:")
        current_date = None
        for date, event_type, count, unique_couriers in result.result_rows:
            if date != current_date:
                print(f"\n📅 {date}:")
                current_date = date
            print(f"   {event_type}: {count} событий, {unique_couriers} уникальных курьеров")