from src.http_methods import MyRequests
from src.assertions import Assertions
from http import HTTPStatus
from data import get_company_endpoints


class CompanyService:
    def __init__(self):
        self.request = MyRequests()
        self.company_url = get_company_endpoints()
        self.assertions = Assertions()

    def create_company(self, data, headers, get_test_name):
        """Создание компании"""
        response = self.request.post(url=self.company_url.create_company, data=data, headers=headers)
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.CREATED, test_name=get_test_name)
        return response.json().get("id")
