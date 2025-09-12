import json
import uuid
import time
import subprocess

import pytest
import redis
from settings import settings


@pytest.fixture(scope="session")
def ssh_tunnel():
    """Поднимает ssh-туннель к Redis, если он не поднят"""
    ssh_target = settings.REDIS_SSH_ALIAS
    local_port = settings.REDIS_PORT
    if not ssh_target:
        pytest.skip("REDIS_SSH_ALIAS не задан, пропускаем ssh-туннель")

    # Проверим, не висит ли уже процесс ssh
    proc = subprocess.Popen(
        ["ssh", "-N", "-L", f"{local_port}:localhost:{local_port}", ssh_target],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)  # ждём пока поднимется туннель
    yield
    proc.terminate()

@pytest.fixture(scope="session")
def redis_client(ssh_tunnel):
    """Возвращает Redis client для тестов"""
    host = settings.REDIS_HOST
    port = settings.REDIS_PORT
    client = redis.Redis(host=host, port=port, decode_responses=True)
    try:
        client.ping()
    except redis.exceptions.ConnectionError:
        pytest.skip(f"Нет подключения к Redis {host}:{port}")
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