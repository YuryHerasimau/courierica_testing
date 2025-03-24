import pytest
import os
import time
from services.auth_service import AuthService


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
    Универсальная фикстура для получения токенов авторизации.
    Принимает роль и тип пользователя (курьер или нет).
    """
    def get_headers(role, is_courier=False):
        if is_courier:
            token = AuthService.get_access_token_for_courier(role)
        else:
            token = AuthService.get_access_token(role)
        return {"Authorization": f"Bearer {token}"}

    return get_headers

@pytest.fixture
def admin_auth_headers(auth_headers):
    """
    Фикстура для получения headers администратора.
    """
    return auth_headers("ADMIN")

@pytest.fixture
def logistician_saas_auth_headers(auth_headers):
    """
    Фикстура для получения headers логиста SaaS.
    """
    return auth_headers("LOGISTICIAN_SAAS")

@pytest.fixture
def courier_saas_auth_headers(auth_headers):
    """
    Фикстура для получения headers курьера SaaS.
    """
    return auth_headers("COURIER_SAAS", is_courier=True)

@pytest.fixture
def logistician_iiko_auth_headers(auth_headers):
    """
    Фикстура для получения headers логиста iiko.
    """
    return auth_headers("LOGISTICIAN_IIKO")

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