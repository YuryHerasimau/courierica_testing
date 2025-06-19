import os
import httpx
from src.prepare_data.prepare_basic_data import BaseTestData
from settings import settings


class MyRequests:
    """
    Класс для выполнения HTTP-запросов с поддержкой различных методов (GET, POST, PUT, PATCH, DELETE).
    """

    def post(self, url: str, data: str = None, headers: dict = None, cookies: dict = None):
        return self.__send(url, data, headers, cookies, method="POST")

    def get(self, url: str, data: str = None, headers: dict = None, cookies: dict = None):
        return self.__send(url, data, headers, cookies, method="GET")

    def put(self, url: str, data: str = None, headers: dict = None, cookies: dict = None):
        return self.__send(url, data, headers, cookies, method="PUT")

    def patch(self, url: str, data: str = None, headers: dict = None, cookies: dict = None):
        # print(f"PATCH url: {url}")
        return self.__send(url, data, headers, cookies, method="PATCH")

    def delete(self, url: str, data: str = None, headers: dict = None, cookies: dict = None):
        return self.__send(url, data, headers, cookies, method="DELETE")

    @staticmethod
    def __send(url: str, data: str, headers: dict, cookies: dict, method: str):
        if url.startswith(('http://', 'https://')):
            base_url = url
        else:
            base_url = f"{settings.BASE_URL}{url}"
        # print(f"Sending {method} request to {base_url} with data: {data} and headers: {headers}\n\n")

        if headers is None:
            headers = {"Content-Type": "application/json"}

        if cookies is None:
            cookies = {}

        try:
            # Если метод GET, передаем параметры как query string
            if method == "GET":
                # Используем `params` для передачи параметров в строке запроса
                response = httpx.request(method=method, url=base_url, params=data, headers=headers, cookies=cookies)
            else:
                # Для остальных методов передаем данные как тело запроса
                response = httpx.request(method=method, url=base_url, data=data, headers=headers, cookies=cookies)

            BaseTestData.attach_response(response=response, method=method)
            return response
        except httpx.RequestError as ex:
            raise Exception(f"HTTP request failed: {ex}")
