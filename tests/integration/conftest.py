import json
import uuid
import time
import socket
import subprocess

import pytest
import redis
from settings import settings


def wait_for_port(host, port, timeout=5):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False

@pytest.fixture(scope="session")
def ssh_tunnel():
    """Поднимает ssh-туннель к Redis, если он не поднят"""
    if not settings.REDIS_SSH_HOST:
        pytest.skip("REDIS_SSH_HOST не задан, пропускаем ssh-туннель")

    local_host = settings.REDIS_HOST
    local_port = settings.REDIS_PORT
    ssh_host = settings.REDIS_SSH_HOST
    ssh_port = settings.REDIS_SSH_PORT
    ssh_user = settings.REDIS_SSH_USER
    ssh_key = settings.REDIS_SSH_KEY

    # Проверим, не висит ли уже процесс ssh
    cmd = [
        "ssh",
        "-i", ssh_key,
        "-p", str(ssh_port),
        "-N",
        "-L", f"{local_port}:{local_host}:{local_port}",
        f"{ssh_user}@{ssh_host}"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # ждём пока поднимется туннель
    if not wait_for_port(local_host, local_port, timeout=5):
        proc.terminate()
        pytest.skip("Не удалось поднять ssh-туннель к Redis")

    yield
    proc.terminate()

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
        print(f"Connecting to Redis {host}:{port} with password={bool(password)}")
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