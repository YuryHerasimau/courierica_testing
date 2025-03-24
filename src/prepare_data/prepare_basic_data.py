import json
import allure
from httpx import Response, Request


class BaseTestData:
    """
    Базовый класс для подготовки и форматирования тестовых данных.
    Включает методы для преобразования данных в JSON и прикрепления запросов/ответов к Allure-отчетам.
    """

    @staticmethod
    def format_data_as_json(self, data):
        json_data = json.dumps(data)
        return json_data

    @staticmethod
    def attach_request(request: Request):
        # request_data = request.json()

        formatted_request = json.dumps(request, indent=4, ensure_ascii=False)
        allure.attach(
            name="Request",
            body=formatted_request,
            attachment_type=allure.attachment_type.JSON,
        )

    @staticmethod
    def attach_response(response: Response, method: str):
        if response.status_code == 204:
            print("No content to attach (204 status code).")
            return
            
        try:
            response_data = response.json()
        except ValueError:
            print("Response is not valid JSON.")
            response_data = {}

        formatted_response = json.dumps(response_data, indent=4, ensure_ascii=False)
        allure.attach(
            name=f"{method} Response",
            body=formatted_response,
            attachment_type=allure.attachment_type.JSON,
        )
