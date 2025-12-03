import time
import allure
import pytest
from uuid import uuid4

from http import HTTPStatus
from src.http_methods import MyRequests
from data import get_pickup_point_endpoints
from src.assertions import Assertions
from src.validator import Validator
from src.schemas import GetPickupPointSchemas


@allure.epic("Testing get pickup point by ID")
class TestGetPickupPointById:
    request = MyRequests()
    url = get_pickup_point_endpoints()
    assertions = Assertions()
    validator = Validator()

    @allure.title("Get pickup point by valid id")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_get_pickup_point_by_valid_id(self, get_test_name, admin_auth_headers, created_pickup_point_id):
        response = self.request.get(
            url=f"{self.url.list_of_pickup_points}/{created_pickup_point_id}",
            headers=admin_auth_headers,
        )
        self.assertions.assert_status_code(response, HTTPStatus.OK, get_test_name)
        self.validator.validate_response(response, GetPickupPointSchemas.get_pickup_point_by_id)

    @allure.title("Get pickup point by random id")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_get_pickup_point_by_random_id(self, get_test_name, admin_auth_headers):
        response = self.request.get(
            url=f"{self.url.list_of_pickup_points}/{str(uuid4())}",
            headers=admin_auth_headers,
        )
        self.assertions.assert_status_code(response, HTTPStatus.NOT_FOUND, get_test_name)
    
    @allure.title("Get pickup point by invalid ID")
    @pytest.mark.parametrize("invalid_id", ["", "123", None, "<script>", "!", 0, -1])
    def test_get_pickup_point_by_invalid_id(self, invalid_id, get_test_name, admin_auth_headers):
        response = self.request.get(
            url=f"{self.url.list_of_pickup_points}/{invalid_id}",
            headers=admin_auth_headers
        )
        self.assertions.assert_status_code(response, HTTPStatus.BAD_REQUEST, get_test_name)

    @allure.title("Get pickup point without auth")
    def test_pickup_point_without_auth(self, get_test_name, created_pickup_point_id):
        response = self.request.get(url=f"{self.url.list_of_pickup_points}/{created_pickup_point_id}")
        self.assertions.assert_status_code(response, HTTPStatus.BAD_REQUEST, get_test_name)

