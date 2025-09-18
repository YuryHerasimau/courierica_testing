import allure
import pytest
from uuid import uuid4

from data import get_company_endpoints
from src.http_methods import MyRequests
from src.assertions import Assertions
from src.validator import Validator
from src.schemas import GetCompanySchemas
from http import HTTPStatus
from settings import settings


@allure.epic("Testing get company by id")
class TestGetCompanyById:
    request = MyRequests()
    url = get_company_endpoints()
    assertions = Assertions()
    validator = Validator()

    @pytest.fixture
    def get_latest_company_id_from_first_page(self, admin_auth_headers):
        # Из первой страницы получаем ID последней созданной компании
        response = self.request.get(
            url=f"{self.url.list_of_companies}?page=1&per_page=10",
            headers=admin_auth_headers,
        )
        assert response.status_code == HTTPStatus.OK

        companies = response.json().get("companies")
        assert companies, "No companies found in the response"

        if companies:
            return companies[0].get("id")

    @allure.title("Get company by valid id")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_get_company_by_valid_id(
        self,
        get_test_name,
        admin_auth_headers,
        get_latest_company_id_from_first_page,
    ):
        response = self.request.get(
            url=f"{self.url.list_of_companies}/{get_latest_company_id_from_first_page}",
            headers=admin_auth_headers,
        )
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.OK,
            test_name=get_test_name,
        )
        self.validator.validate_response(response=response, model=GetCompanySchemas.get_company_by_id)

    @allure.title("Get company by random id")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_get_company_by_random_id(self, get_test_name, admin_auth_headers):
        response = self.request.get(
            url=f"{self.url.list_of_companies}/{str(uuid4())}",
            headers=admin_auth_headers,
        )
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.NOT_FOUND,
            test_name=get_test_name,
        )

    @allure.title("Get company by invalid id")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "invalid_id",
        [
            "",
            "12345",
            "invalid-uuid",
            "non-existent-id",
        ],
    )
    @pytest.mark.extended
    def test_get_company_by_invalid_id(self, get_test_name, admin_auth_headers, invalid_id):
        response = self.request.get(
            url=f"{self.url.list_of_companies}/{invalid_id}",
            headers=admin_auth_headers,
        )
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.BAD_REQUEST,
            test_name=get_test_name,
        )

    @allure.title("Get company by id without auth")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_get_company_by_id_without_auth(self, get_test_name, get_latest_company_id_from_first_page):
        response = self.request.get(
            url=f"{self.url.list_of_companies}/{get_latest_company_id_from_first_page}"
        )
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.BAD_REQUEST,
            test_name=get_test_name,
        )

    @allure.title("Get company by id with extra params")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.extended
    def test_get_company_by_id_with_extra_params(
        self,
        get_test_name,
        admin_auth_headers,
        get_latest_company_id_from_first_page,
    ):
        response = self.request.get(
            url=f"{self.url.list_of_companies}/{get_latest_company_id_from_first_page}?filter=invalid",
            headers=admin_auth_headers,
        )
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.OK,
            test_name=get_test_name,
        )


    # PERMISSIONS AND ROLES

    @allure.title("Check permissions for manual creation of system entities (without external_id) by roles")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    @pytest.mark.parametrize("role, expected_status", [
        ("ADMIN", HTTPStatus.OK), # Ожидаем, что админ SAAS может просматривать компанию
        ("LOGISTICIAN", HTTPStatus.FORBIDDEN), # Ожидаем, что логист SAAS НЕ может просматривать компанию
    ])
    def test_get_saas_company_by_id_based_on_role(self, role, expected_status, get_test_name, request):
        if role == "ADMIN":
            headers = request.getfixturevalue("admin_auth_headers")
        elif role == "LOGISTICIAN":
            headers = request.getfixturevalue("logistician_saas_auth_headers")

        response = self.request.get(
            url=f"{self.url.list_of_companies}/{settings.COURIER_COMPANY_ID}",
            headers=headers,
        )
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=expected_status,
            test_name=get_test_name,
        )
        if expected_status == HTTPStatus.OK:
            self.validator.validate_response(response=response, model=GetCompanySchemas.get_company_by_id)