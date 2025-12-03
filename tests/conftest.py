import json
import random
import pytest
from pathlib import Path
from http import HTTPStatus

from settings import settings
from functions import load_json
from src.http_methods import MyRequests
from data import get_iiko_endpoints, get_company_endpoints, get_pickup_point_endpoints
from src.prepare_data.prepare_company_data import PrepareCompanyData
from src.prepare_data.prepare_pickup_point_data import PreparePickupPointData
from generator.company_generator import CompanyGenerator
from generator.pickup_point_generator import PickupPointGenerator


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


@pytest.fixture(scope="function")
def created_company_id(admin_auth_headers):
    """
    Создает тестовую компанию и возвращает её id.
    Используется как зависимость для тестов pickup_point.
    """
    company_generator = CompanyGenerator()
    company_data = PrepareCompanyData()
    request = MyRequests()
    url = get_company_endpoints()

    info = next(company_generator.generate_company(integration_source="saas"))
    data = company_data.prepare_company_json(info=info)

    response = request.post(url=url.create_company, data=data, headers=admin_auth_headers)
    assert response.status_code == HTTPStatus.CREATED, f"Не удалось создать компанию: {response.text}"
    return response.json().get("id")


@pytest.fixture(scope="function")
def created_company_with_firm(admin_auth_headers):
    """Создаёт компанию с фирмами и возвращает кортеж (company_id, firm_id)."""
    company_generator = CompanyGenerator()
    company_data = PrepareCompanyData()
    request = MyRequests()
    url = get_company_endpoints()

    info = next(company_generator.generate_company(integration_source="saas", firms_count=1))
    data = company_data.prepare_company_json(info=info)

    response = request.post(url=url.create_company, data=data, headers=admin_auth_headers)
    assert response.status_code == HTTPStatus.CREATED, f"Не удалось создать компанию: {response.text}"

    company_id = response.json().get("id")
    firm_id = response.json().get("firms")[0].get("id")
    return company_id, firm_id


@pytest.fixture(scope="function")
def created_pickup_point_id(admin_auth_headers, created_company_with_firm):
    """Создает пункт выдачи и возвращает его ID."""
    company_id, firm_id = created_company_with_firm
    generator = PickupPointGenerator()
    pickup_point_data = PreparePickupPointData()
    request = MyRequests()
    url = get_pickup_point_endpoints()

    info = next(generator.generate_pickup_point(company_id=company_id, firm_id=firm_id))
    data = pickup_point_data.prepare_pickup_point_json(info)

    response = request.post(url=url.create_pickup_point, data=data, headers=admin_auth_headers)
    assert response.status_code == HTTPStatus.CREATED, f"Не удалось создать ПВ: {response.text}"

    return response.json().get("id")