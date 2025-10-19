import pytest
import clickhouse_connect
from settings import settings


@pytest.fixture(scope="session")
def clickhouse_client():
    """Возвращает ClickHouse client для тестов"""
    host = settings.CLICKHOUSE_HOST
    port = settings.CLICKHOUSE_PORT
    user = settings.CLICKHOUSE_USER
    password = settings.CLICKHOUSE_PASSWORD
    database = settings.CLICKHOUSE_DATABASE

    try:
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=user,
            password=password,
            database=database
        )
        
        client.ping()
        print(f"🔑 Успешное подключение к ClickHouse {host}:{port}")
        return client
        
    except Exception as e:
        pytest.skip(f"Не удалось подключиться к ClickHouse: {e}")