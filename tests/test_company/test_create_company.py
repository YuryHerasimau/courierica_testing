import allure
from data import get_company_endpoints
from src.http_methods import MyRequests
from src.assertions import Assertions
from src.validator import Validator
from src.schemas import GetCompanySchemas
from generator.company_generator import CompanyGenerator
from src.prepare_data.prepare_company_data import PrepareCompanyData
from http import HTTPStatus
import pytest
import random


@allure.epic("Testing create company")
class TestCreateCompany:
    request = MyRequests()
    url = get_company_endpoints()
    assertions = Assertions()
    validator = Validator()
    company_generator = CompanyGenerator()
    company_data = PrepareCompanyData()

    @allure.title("Create SAAS company with firms")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_saas_company_with_firms(self, get_test_name, admin_auth_headers):
        info = next(self.company_generator.generate_company(integration_source="saas", firms_count=random.randint(1, 10)))
        data = self.company_data.prepare_company_json(info=info)
        # print(data)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        # print(response.json())
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.CREATED,
            test_name=get_test_name,
        )
        self.validator.validate_response(response=response, model=GetCompanySchemas.create_company)
    
    @allure.title("Create SAAS company without firms")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_saas_company_without_firms(self, get_test_name, admin_auth_headers):
        info = next(self.company_generator.generate_company(integration_source="saas"))
        data = self.company_data.prepare_company_json(info=info)
        # print(data)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        # print(response.json())
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.CREATED,
            test_name=get_test_name,
        )
        self.validator.validate_response(response=response, model=GetCompanySchemas.create_company)

    @allure.title("Create SAAS company with invoice customer ids")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Company create failed because it is forbidden to set invoice customer ids for the current integration source"
    )
    def test_create_saas_company_with_invoice_customer_ids(self, get_test_name, admin_auth_headers):
        info = next(self.company_generator.generate_company(integration_source="saas", invoice_customer_ids_count=random.randint(1, 10)))
        data = self.company_data.prepare_company_json(info=info)
        # print(data)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        # print(response.json())
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.BAD_REQUEST,
            test_name=get_test_name,
        )

    @allure.title("Create SAAS company with firms and invoice customer ids")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_iiko_company_with_firms_and_invoice_customer_ids(self, get_test_name, admin_auth_headers):
        info = next(self.company_generator.generate_company(
            integration_source="iiko",
            integration_key_length=random.randint(8, 50),
            invoice_customer_ids_count=random.randint(1, 10),
            firms_count=random.randint(1, 10),
        ))
        data = self.company_data.prepare_company_json(info=info)
        # print(data)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        # print(response.json())
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.CREATED,
            test_name=get_test_name,
        )
        self.validator.validate_response(response=response, model=GetCompanySchemas.create_company)

    @allure.title("Create SAAS company without firms")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Company create failed because validate failed: firm list empty"
    )
    def test_create_iiko_company_without_firms(self, get_test_name, admin_auth_headers):
        info = next(self.company_generator.generate_company(
            integration_source="iiko",
            integration_key_length=random.randint(8, 50),
            invoice_customer_ids_count=random.randint(1, 10),
        ))
        data = self.company_data.prepare_company_json(info=info)
        # print(data)
        response = self.request.post(url=self.url.create_company, data=data, headers=admin_auth_headers)
        # print(response.json())
        self.assertions.assert_status_code(
            response=response,
            expected_status_code=HTTPStatus.BAD_REQUEST,
            test_name=get_test_name,
        )
