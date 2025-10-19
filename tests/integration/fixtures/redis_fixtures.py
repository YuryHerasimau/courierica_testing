import json
import uuid
import pytest
import redis
from settings import settings


@pytest.fixture(scope="session")
def redis_client(ssh_tunnel):
    """Возвращает Redis client для тестов"""
    host = settings.REDIS_HOST
    port = settings.REDIS_PORT
    password = settings.REDIS_PASSWORD

    client = redis.Redis(
        host=host,
        port=port,
        password=password,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3
    )

    try:
        print(f"🔑 Подключаемся к Redis {host}:{port} с паролем={bool(password)}")
        client.ping()
    except redis.exceptions.ConnectionError:
        pytest.skip(f"Нет подключения к Redis {host}:{port}")
    except redis.exceptions.AuthenticationError:
        pytest.skip(f"Неверный пароль для Redis {host}:{port}")
    return client

@pytest.fixture
def sample_delivery(redis_client):
    """
    Создаёт два объекта:
    1. delivery:{delivery_id} — основной объект для отображения в web-view
    2. courier:{courier_id} — связка courier_id -> delivery_id для PingService
    """
    delivery_id = str(uuid.uuid4())
    courier_id = str(uuid.uuid4())

    delivery_obj = {
        "delivery": {
            "number": "4666",
            "destination": {"address": "Москва, Башиловская 22", "lat": 55.802619, "lon": 37.575316}
        },
        "courier": {
            "id": courier_id,
            "full_name": "Fedor",
            "route": [{"lat": 53.91402, "lon": 27.568382}]
        }
    }

    courier_obj = {courier_id: delivery_id}

    # Сохраняем в Redis с TTL 5 минут
    redis_client.set(f"delivery:{delivery_id}", json.dumps(delivery_obj), ex=300)
    redis_client.set(f"courier:{courier_id}", json.dumps(courier_obj), ex=300)

    yield delivery_id, courier_id

    # Очистка после теста
    redis_client.delete(f"delivery:{delivery_id}")
    redis_client.delete(f"courier:{courier_id}")