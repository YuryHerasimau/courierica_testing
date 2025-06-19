import json
import pytest
from settings import settings
from functions import load_json
from src.http_methods import MyRequests
from data import get_iiko_endpoints


# Константы
COURIERS = {
    "3PL": "4f651a57-f4fc-426d-9065-c75726a8062e",
    "Федор": "f57bc04e-8a63-4813-a02d-759a3b5125c5",
    "Семен": "aaefc2fb-57fa-486a-ae23-fdd559207e47"
}

@pytest.fixture(scope="class")
def courier_iiko_data():
    return {
        "iiko_organization_id": settings.IIKO_ORGANIZATION_ID,
        "courierica_pickup_point_id": settings.COURIERICA_PICKUP_POINT_ID,
        "couriers": COURIERS
    }

@pytest.fixture
def iiko_headers():
    request = MyRequests()
    response = request.post(
        url=get_iiko_endpoints().access_token,
        data=json.dumps({"apiLogin": settings.IIKO_API_LOGIN}),
    )
    token = response.json().get("token")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

@pytest.fixture(scope='session')
def address_data():
    """Фикстура с данными адресов (загружается один раз на все тесты)"""
    return load_json("tests/e2e/config/iiko_address_data.json")