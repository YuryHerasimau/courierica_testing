import allure
import pytest

from data import get_company_endpoints
from src.http_methods import MyRequests
from src.assertions import Assertions
from src.validator import Validator
from src.schemas import GetCompanySchemas
from http import HTTPStatus


@allure.epic("Testing get company list")
class TestGetCompanies:
    request = MyRequests()
    url = get_company_endpoints()
    assertions = Assertions()
    validator = Validator()

    @pytest.fixture
    def total_companies(self, admin_auth_headers):
        # Получаем общее количество компаний динамически
        response = self.request.get(
            url=f"{self.url.list_of_companies}?page=1&per_page=10",
            headers=admin_auth_headers,
        )
        assert response.status_code == HTTPStatus.OK
        return response.json().get("pagination").get("total")

    @allure.title("Get all companies")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_get_all_companies_with_auth(self, get_test_name, admin_auth_headers):
        response = self.request.get(
            url=self.url.list_of_companies, headers=admin_auth_headers
        )
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.OK,
            test_name=get_test_name,
        )
        self.validator.validate_response(response=response, model=GetCompanySchemas.get_companies)

    @allure.title("Get companies without auth")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_get_companies_without_auth(self, get_test_name):
        response = self.request.get(url=self.url.list_of_companies)
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.BAD_REQUEST,
            test_name=get_test_name,
        )

    @allure.title("Get companies with pagination")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "page, per_page, expected_status",
        [
            (1, 10, HTTPStatus.OK),
            (1, 100, HTTPStatus.OK),
            (50, 10, HTTPStatus.OK),
            (1, 200, HTTPStatus.OK),
            (0, 10, HTTPStatus.BAD_REQUEST),
            (-1, 10, HTTPStatus.BAD_REQUEST),
            (None, None, HTTPStatus.BAD_REQUEST),
            ("abc", 10, HTTPStatus.BAD_REQUEST),
            (1, "xyz", HTTPStatus.BAD_REQUEST),
        ],
    )
    @pytest.mark.extended
    def test_companies_pagination(
        self,
        get_test_name,
        admin_auth_headers,
        page,
        per_page,
        expected_status,
        total_companies,
    ):
        response = self.request.get(
            url=f"{self.url.list_of_companies}?page={page}&per_page={per_page}",
            headers=admin_auth_headers,
        )
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=expected_status,
            test_name=get_test_name,
        )
        if expected_status == HTTPStatus.OK:
            self.assertions.assert_pagination(
                response=response,
                expected_page=page,
                expected_per_page=per_page,
                expected_total=total_companies, # ПРОВЕРКА соотв-я эл-ов в массиве при получении списка компаний
                test_name=get_test_name,
            )
            self.validator.validate_response(response=response, model=GetCompanySchemas.get_companies)
