import allure
import pytest
import json
from http import HTTPStatus
from data import get_pickup_point_endpoints

from src.http_methods import MyRequests
from src.assertions import Assertions
from src.validator import Validator
from src.schemas import GetPickupPointSchemas
from src.prepare_data.prepare_pickup_point_data import PreparePickupPointData
from generator.pickup_point_generator import PickupPointGenerator


@allure.epic("Testing create pickup point")
class TestCreatePickupPoint:
    request = MyRequests()
    url = get_pickup_point_endpoints()
    assertions = Assertions()
    validator = Validator()
    pickup_point_generator = PickupPointGenerator()
    pickup_point_data = PreparePickupPointData()

    @allure.title("Create SAAS pickup point with firm")
    @pytest.mark.critical_path
    def test_create_pickup_point_with_firm(self, get_test_name, admin_auth_headers, created_company_with_firm):
        company_id, firm_id = created_company_with_firm
        info = next(self.pickup_point_generator.generate_pickup_point(company_id=company_id, firm_id=firm_id))
        data = self.pickup_point_data.prepare_pickup_point_json(info=info)

        response = self.request.post(url=self.url.create_pickup_point, data=data, headers=admin_auth_headers)
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.CREATED, test_name=get_test_name)
        self.validator.validate_response(response=response, model=GetPickupPointSchemas.create_pickup_point)

    @allure.title("Create SAAS pickup point with required fields (no firm)")
    @pytest.mark.critical_path
    def test_create_pickup_point_without_firm(self, get_test_name, admin_auth_headers, created_company_id):
        company_id = created_company_id
        info = next(self.pickup_point_generator.generate_pickup_point(company_id=company_id))
        data = self.pickup_point_data.prepare_pickup_point_json(info=info)

        response = self.request.post(url=self.url.create_pickup_point, data=data, headers=admin_auth_headers)
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.CREATED, test_name=get_test_name)
        self.validator.validate_response(response=response, model=GetPickupPointSchemas.create_pickup_point)

    @allure.title("Create pickup point without company_id")
    @pytest.mark.critical_path
    def test_create_pickup_point_without_company_id(self, get_test_name, admin_auth_headers):
        info = next(self.pickup_point_generator.generate_pickup_point(company_id=None))
        data = {
            "company_id": None,
            "name": "Тест",
            "address": "Тест",
            "point": {"latitude": 0, "longitude": 0}
        }
        json_data = json.dumps(data)

        response = self.request.post(url=self.url.create_pickup_point, data=json_data, headers=admin_auth_headers)
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.BAD_REQUEST, test_name=get_test_name)
