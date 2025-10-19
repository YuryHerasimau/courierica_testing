import allure
import pytest


@allure.feature("ClickHouse Schema")
@pytest.mark.integration
@pytest.mark.clickhouse
class TestClickHouseSchema:
    
    @allure.title("Проверка существования таблицы events")
    def test_events_table_exists(self, clickhouse_client):
        """Проверяем, что таблица events существует"""
        result = clickhouse_client.query(
            "SHOW TABLES FROM default LIKE 'events'"
        )
        
        assert result.result_rows, "Таблица events не найдена в базе default"
        print("Таблица events существует")

    @allure.title("Проверка структуры таблицы events")
    def test_events_table_structure(self, clickhouse_client):
        """Проверяем структуру таблицы events"""
        result = clickhouse_client.query("DESCRIBE events")
        
        # Преобразуем результат в словарь для удобства
        columns = {row[0]: row[1] for row in result.result_rows}
        
        expected_columns = ['id', 'courier_id', 'pickup_point_id', 'type', 'payload', 'timestamp', 'timezone', 'created_at']
        for column in expected_columns:
            assert column in columns, f"Отсутствует колонка {column}"
        
        print("Структура таблицы events корректна")
        print("Структура таблицы:")
        for row in result.result_rows:
            print(f"  {row[0]} - {row[1]}")