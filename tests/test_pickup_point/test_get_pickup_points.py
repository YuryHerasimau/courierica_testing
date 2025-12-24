import allure
import pytest
from http import HTTPStatus
from src.http_methods import MyRequests
from data import get_pickup_point_endpoints
from src.assertions import Assertions
from src.validator import Validator
from src.schemas import GetPickupPointSchemas


@allure.epic("Testing get pickup point list")
class TestGetPickupPoints:
    request = MyRequests()
    url = get_pickup_point_endpoints()
    assertions = Assertions()
    validator = Validator()

    @pytest.fixture
    def total_pickup_points(self, admin_auth_headers):
        response = self.request.get(
            url=f"{self.url.list_of_pickup_points}?page=1&per_page=10",
            headers=admin_auth_headers,
        )
        self.assertions.assert_status_code(response, 200)
        return response.json()["pagination"]["total"]

    @allure.title("Get pickup points list with auth")
    @pytest.mark.critical_path
    def test_get_all_pickup_points_with_auth(self, get_test_name, admin_auth_headers):
        response = self.request.get(url=self.url.list_of_pickup_points, headers=admin_auth_headers)
        self.assertions.assert_status_code(response, HTTPStatus.OK, get_test_name)
        self.validator.validate_response(response, GetPickupPointSchemas.get_pickup_points)

        data = response.json()["pickup_points"]
        assert isinstance(data, list)
        for item in data:
            # assert item["company_id"]
            assert item["name"]
            assert item["address"]
            assert abs(item["point"]["latitude"]) <= 90
            assert abs(item["point"]["longitude"]) <= 180

    @allure.title("Get pickup points list without auth")
    @pytest.mark.extended
    def test_get_pickup_points_without_auth(self, get_test_name):
        response = self.request.get(url=self.url.list_of_pickup_points)
        self.assertions.assert_status_code(response, HTTPStatus.BAD_REQUEST, get_test_name)

    @allure.title("Get pickup points list filtered by company_id")
    @pytest.mark.extended
    def test_filter_pickup_points_by_company(self, get_test_name, admin_auth_headers, created_company_id):
        response = self.request.get(
            url=f"{self.url.list_of_pickup_points}?company_id={created_company_id}",
            headers=admin_auth_headers,
        )
        self.assertions.assert_status_code(response, 200, get_test_name)
        self.validator.validate_response(response, GetPickupPointSchemas.get_pickup_points)

        points = response.json()["pickup_points"]
        assert all(p["company_id"] == created_company_id for p in points)

    @allure.title("Search pickup points (min 3 symbols)")
    @pytest.mark.parametrize(
        "search, status",
        [("ab", 400), ("", 400), (None, 400), ("Мин", 200), ("г Мин", 200)]
    )
    def test_pickup_points_search(self, search, status, get_test_name, admin_auth_headers):
        response = self.request.get(
            url=f"{self.url.list_of_pickup_points}?search={search}",
            headers=admin_auth_headers,
        )
        self.assertions.assert_status_code(response, status, get_test_name)
        if status == 200:
            body = response.json()
            assert isinstance(body["pickup_points"], list)

    @allure.title("GET pickup points with pagination")
    @pytest.mark.parametrize(
        "page, per_page, status",
        [(1,10,200), (1,50,200), (0,5,400), (-1,5,400), ("x",5,400), (1,"z",400), (None,None,400)]
    )
    def test_pickup_points_pagination(self, page, per_page, status, get_test_name, admin_auth_headers, total_pickup_points):
        response = self.request.get(
            url=f"{self.url.list_of_pickup_points}?page={page}&per_page={per_page}",
            headers=admin_auth_headers
        )
        self.assertions.assert_status_code(response, status, get_test_name)
        if status == 200:
            self.assertions.assert_pagination(response, page, per_page, total_pickup_points, get_test_name)
            assert len(response.json()["pickup_points"]) <= per_page
