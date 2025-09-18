import json
import pytest
from pathlib import Path

from settings import settings
from functions import load_json
from src.http_methods import MyRequests
from data import get_iiko_endpoints


@pytest.fixture(scope="class")
def courier_iiko_data():
    config_file = Path(f"tests/e2e/config/couriers.{settings.TEST_ENV}.json")
    couriers = load_json(str(config_file))
    return {
        "iiko_organization_id": settings.IIKO_ORGANIZATION_ID,
        "courierica_pickup_point_id": settings.COURIERICA_PICKUP_POINT_ID,
        "couriers": couriers
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