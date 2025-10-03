import allure
import pytest
import random
from http import HTTPStatus

from data import get_company_endpoints
from src.http_methods import MyRequests
from src.assertions import Assertions
from src.validator import Validator
from src.schemas import GetCompanySchemas
from src.prepare_data.prepare_company_data import PrepareCompanyData
from generator.company_generator import CompanyGenerator


@allure.epic("Testing create company")
class TestCreateCompany:
    request = MyRequests()
    url = get_company_endpoints()
    assertions = Assertions()
    validator = Validator()
    company_generator = CompanyGenerator()
    company_data = PrepareCompanyData()

    # ---- SAAS ----

    @allure.title("Create SAAS company with firms")
    @allure.testcase("https://wiki.yandex.ru/homepage/platforma/jj/test-kejjsy/test-kejjsy-297/#cmpn-001")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_create_saas_company_with_firms(self, get_test_name, admin_auth_headers):
        info = next(self.company_generator.generate_company(integration_source="saas", firms_count=random.randint(1, 10)))
        data = self.company_data.prepare_company_json(info=info)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.CREATED,
            test_name=get_test_name,
        )
        self.validator.validate_response(response=response, model=GetCompanySchemas.create_company)
    
    @allure.title("Create SAAS company without firms")
    @allure.testcase("https://wiki.yandex.ru/homepage/platforma/jj/test-kejjsy/test-kejjsy-297/#cmpn-002")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_create_saas_company_without_firms(self, get_test_name, admin_auth_headers):
        info = next(self.company_generator.generate_company(integration_source="saas"))
        data = self.company_data.prepare_company_json(info=info)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.CREATED,
            test_name=get_test_name,
        )
        self.validator.validate_response(response=response, model=GetCompanySchemas.create_company)

    @allure.title("Validation SAAS company name")
    @allure.testcase("https://wiki.yandex.ru/homepage/platforma/jj/test-kejjsy/test-kejjsy-297/#cmpn-003")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    @pytest.mark.parametrize("name", [
        "a" * 51,   # 51 chars (too long)
        "",         # empty string
        " ",        # whitespace
    ])
    def test_validate_saas_company_name(self, get_test_name, admin_auth_headers, name):
        info = next(self.company_generator.generate_company(integration_source="saas", name=name))
        data = self.company_data.prepare_company_json(info=info)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.BAD_REQUEST,
            test_name=get_test_name,
        )

    @allure.title("Create SAAS company without integration_source")
    @allure.description("Unable to create company coz integration_source is empty")
    @allure.testcase("https://wiki.yandex.ru/homepage/platforma/jj/test-kejjsy/test-kejjsy-297/#cmpn-004")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_create_company_without_integration_source(self, get_test_name, admin_auth_headers):
        info = next(self.company_generator.generate_company(integration_source=None))
        data = self.company_data.prepare_company_json(info=info)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.BAD_REQUEST,
            test_name=get_test_name,
        )

    @allure.title("Create SAAS company with integration_key")
    @allure.description("Unable to create company coz integration_key must be empty for saas integration_source")
    @allure.testcase("https://wiki.yandex.ru/homepage/platforma/jj/test-kejjsy/test-kejjsy-297/#cmpn-005")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_create_saas_company_with_integration_key(self, get_test_name, admin_auth_headers):
        info = next(self.company_generator.generate_company(
            integration_source="saas",
            integration_key_length=random.randint(8, 50),
        ))
        data = self.company_data.prepare_company_json(info=info)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.BAD_REQUEST,
            test_name=get_test_name,
        )

    @allure.title("Create SAAS company with invoice_customer_ids")
    @allure.description("Unable to create company coz setting invoice_customer_ids is forbidden for the current integration_source")
    @allure.testcase("https://wiki.yandex.ru/homepage/platforma/jj/test-kejjsy/test-kejjsy-297/#cmpn-006")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_create_saas_company_with_invoice_customer_ids(self, get_test_name, admin_auth_headers):
        info = next(self.company_generator.generate_company(integration_source="saas", invoice_customer_ids_count=random.randint(1, 10)))
        data = self.company_data.prepare_company_json(info=info)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.BAD_REQUEST,
            test_name=get_test_name,
        )

    # ---- IIKO ----
    
    @allure.title("Create IIKO company with firms and invoice_customer_ids")
    @allure.testcase("https://wiki.yandex.ru/homepage/platforma/jj/test-kejjsy/test-kejjsy-297/#cmpn-007")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_create_iiko_company_with_firms_and_invoice_customer_ids(self, get_test_name, admin_auth_headers):
        info = next(self.company_generator.generate_company(
            integration_source="iiko",
            integration_key_length=random.randint(8, 50),
            invoice_customer_ids_count=random.randint(1, 10),
            firms_count=random.randint(1, 10),
        ))
        data = self.company_data.prepare_company_json(info=info)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.CREATED,
            test_name=get_test_name,
        )
        self.validator.validate_response(response=response, model=GetCompanySchemas.create_company)

    @allure.title("Create IIKO company without firms")
    @allure.description("Company create failed because validate failed: firm list empty")
    @allure.testcase("https://wiki.yandex.ru/homepage/platforma/jj/test-kejjsy/test-kejjsy-297/#cmpn-008")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    def test_create_iiko_company_without_firms(self, get_test_name, admin_auth_headers):
        info = next(self.company_generator.generate_company(
            integration_source="iiko",
            integration_key_length=random.randint(8, 50),
            invoice_customer_ids_count=random.randint(1, 10),
        ))
        data = self.company_data.prepare_company_json(info=info)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.BAD_REQUEST,
            test_name=get_test_name,
        )

    @allure.title("Validation IIKO company integration_key")
    @allure.testcase("https://wiki.yandex.ru/homepage/platforma/jj/test-kejjsy/test-kejjsy-297/#cmpn-009")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    @pytest.mark.parametrize("key_length", [
        7,    # 7 chars (too short)
        51,   # 51 chars (too long)
        None  # null value
    ])
    def test_validate_iiko_company_integration_key(self, get_test_name, admin_auth_headers, key_length):
        info = next(self.company_generator.generate_company(
            integration_source="iiko",
            integration_key_length=key_length,
            invoice_customer_ids_count=random.randint(1, 10),
            firms_count=random.randint(1, 10),
        ))
        data = self.company_data.prepare_company_json(info=info)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.BAD_REQUEST,
            test_name=get_test_name,
        )

    # ---- RKEEPER, 1C ----

    @allure.title("Validation company integration_source")
    @allure.testcase("https://wiki.yandex.ru/homepage/platforma/jj/test-kejjsy/test-kejjsy-297/#cmpn-010")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.critical_path
    @pytest.mark.parametrize("integration_source, expected_status", [
        # Positive cases - valid integration sources
        ("1c", HTTPStatus.CREATED),                     # valid 1c source
        ("rkeeper", HTTPStatus.CREATED),                # valid rkeeper source

        # Negative cases - invalid integration sources  
        ("invalid_source", HTTPStatus.BAD_REQUEST),     # completely invalid value
        (" ", HTTPStatus.BAD_REQUEST),                  # whitespace only
        ("", HTTPStatus.BAD_REQUEST),                   # whitespace only
        (None, HTTPStatus.BAD_REQUEST),                 # whitespace only
        ("saas ", HTTPStatus.BAD_REQUEST),              # trailing space
        (" iiko", HTTPStatus.BAD_REQUEST),              # leading space
    ])
    def test_validate_company_integration_source(self, get_test_name, admin_auth_headers, integration_source, expected_status):
        info = next(self.company_generator.generate_company(
            integration_source=integration_source,
            integration_key_length=8 if integration_source in ["iiko", "rkeeper", "1c"] else None,
            invoice_customer_ids_count=1 if integration_source == "iiko" else 0,
            firms_count=1,
        ))
        data = self.company_data.prepare_company_json(info=info)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=expected_status,
            test_name=get_test_name,
        )
        if expected_status == HTTPStatus.CREATED:
            self.validator.validate_response(response=response, model=GetCompanySchemas.create_company)