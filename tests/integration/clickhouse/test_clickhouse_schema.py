import allure
import pytest


@allure.feature("ClickHouse Schema")
@pytest.mark.integration
@pytest.mark.clickhouse
class TestClickHouseSchema:
    
    @allure.title("Проверка существования таблицы events")
    def test_events_table_exists(self, clickhouse_client):
        result = clickhouse_client.query(
            "SHOW TABLES FROM default LIKE 'events'"
        )

        assert result.result_rows, "Таблица events не найдена в базе default"
        table_name = result.result_rows[0][0]
        assert table_name == 'events', f"Найдена таблица {table_name}, но ожидалась events"

    @allure.title("Проверка структуры таблицы events")
    def test_events_table_structure(self, clickhouse_client):
        result = clickhouse_client.query("DESCRIBE events")
        
        # Преобразуем результат в словарь для удобства
        columns = {row[0]: row[1] for row in result.result_rows}
        
        expected_columns = ['id', 'courier_id', 'pickup_point_id', 'type', 'payload', 'timestamp', 'timezone', 'created_at']
        for column in expected_columns:
            assert column in columns, f"Отсутствует колонка {column}"

        assert columns['id'].startswith('UUID'), f"Неправильный тип для id: {columns['id']}"
        assert columns['courier_id'].startswith('UUID'), f"Неправильный тип для courier_id: {columns['courier_id']}"
        assert columns['pickup_point_id'].startswith('UUID'), f"Неправильный тип для pickup_point_id: {columns['pickup_point_id']}"
        assert columns['type'].startswith('String'), f"Неправильный тип для type: {columns['type']}"
        assert columns['payload'].startswith('JSON'), f"Неправильный тип для payload: {columns['payload']}"
        assert columns['timestamp'].startswith('DateTime'), f"Неправильный тип для timestamp: {columns['timestamp']}"
        assert columns['timezone'].startswith('Nullable(String)'), f"Неправильный тип для timezone: {columns['timezone']}"
        assert columns['created_at'].startswith('DateTime'), f"Неправильный тип для created_at: {columns['created_at']}"