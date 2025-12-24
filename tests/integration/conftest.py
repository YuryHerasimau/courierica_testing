import time
import socket
import subprocess
import pytest

from .fixtures.redis_fixtures import *
from .fixtures.clickhouse_fixtures import *
from .fixtures.kafka_fixtures import *
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