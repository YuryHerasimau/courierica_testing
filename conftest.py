import httpx
import pytest
import os
import time
from services.auth_service import AuthService, Role
from settings import settings


@pytest.fixture
def get_test_name():
    """
    Фикстура для получения имени текущего теста.
    """
    test_name = os.environ.get("PYTEST_CURRENT_TEST")
    return test_name

@pytest.fixture
def auth_headers():
    """
    Универсальная фикстура для получения заголовков авторизации.
    Использует обновленный AuthService с поддержкой Role enum.
    
    Пример использования:
    - Для администратора: auth_headers(Role.ADMIN)
    - Для логиста: auth_headers(Role.LOGIST)
    - Для курьера: auth_headers(Role.COURIER)
    """
    def _get_headers(role: Role):
        token = AuthService.get_access_token(role)
        return {"Authorization": f"Bearer {token}"}
    
    return _get_headers

@pytest.fixture
def admin_auth_headers(auth_headers):
    """Фикстура для получения headers администратора."""
    return auth_headers(Role.ADMIN)

@pytest.fixture
def logistician_saas_auth_headers(auth_headers):
    """Фикстура для получения headers логиста SaaS."""
    return auth_headers(Role.LOGISTICIAN_SAAS)

@pytest.fixture
def courier_saas_auth_headers(auth_headers):
    """Фикстура для получения headers курьера SaaS."""
    return auth_headers(Role.COURIER_SAAS)

@pytest.fixture
def courier_iiko_auth_headers(auth_headers, request):
    """Фикстура для получения headers конкретного курьера IIKO."""
    # Если передали параметр courier_id - авторизуем конкретного курьера
    if hasattr(request, "param") and request.param:
        courier_id = request.param
        admin_headers = auth_headers(Role.ADMIN)

        # Получаем телефон курьера
        phone = AuthService.get_courier_phone(courier_id, admin_headers)
        # Запрашиваем SMS код
        AuthService.request_sms_code(phone)
        # Получаем SMS код через админский эндпоинт
        sms_code = AuthService.get_sms_code_for_courier(courier_id, admin_headers)

        # Авторизуемся как курьер
        response = httpx.post(
            f"{settings.BASE_URL}/login/phone/code",
            json={"phone": phone, "code": sms_code}
        )
        if response.status_code != 200:
            raise Exception(f"Courier auth failed: {response.text}")
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    # # Иначе используем стандартного тестового курьера
    # return auth_headers(Role.COURIER_IIKO)

@pytest.fixture
def logistician_iiko_auth_headers(auth_headers):
    """Фикстура для получения headers логиста iiko."""
    return auth_headers(Role.LOGISTICIAN_IIKO)

@pytest.fixture(scope="class")
def courier_data():
    """Данные компании и ПВ курьера для E2E теста."""
    return {
        "company_id": "ac6d1196-3488-49b0-b670-8361bca1d8d6", # BSL
        "pickup_point_id": "9f8896d7-3f85-4d8c-9d6e-e0b9c672cf9a", # ПВ в Минске
    }

@pytest.fixture
def timer(request):
    """Измерение времени выполнения теста."""
    start = time.time()
    yield
    end = time.time()
    print(f'''\n{request.node.name} finished in {end - start:.2f} seconds.''')