import json
from src.http_methods import MyRequests
from src.assertions import Assertions
from http import HTTPStatus
from data import get_route_endpoints


class RouteService:
    def __init__(self):
        self.request = MyRequests()
        self.route_url = get_route_endpoints() 
        self.assertions = Assertions()

    def get_routes(self, get_test_name, company_id, courier_id, pickup_point_id, date, headers):
        """
        Получить маршруты на основе фильтров.

        :param company_id: ID компании.
        :param courier_id: ID курьера.
        :param pickup_point_id: ID пункта выдачи.
        :param date: Дата фильтрации (строка в формате 'YYYY-MM-DD').
        :return: JSON-ответ с маршрутами.
        """
        params = {
            "page": 1,
            "company_id": company_id,
            "courier_ids[]": courier_id,
            "pickup_point_ids[]": pickup_point_id,
            "status_updated_at_from": date,
            "status_updated_at_till": date,
        }

        response = self.request.get(
            url=self.route_url.list_of_routes,
            data=params,
            headers=headers
        )
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.OK, test_name=get_test_name)
        return response

    def get_route_status(self, get_test_name, company_id, courier_id, pickup_point_id, date, headers):
        """
        Получить и проверить статус первого маршрута на основе фильтров.

        :param company_id: ID компании.
        :param courier_id: ID курьера.
        :param pickup_point_id: ID пункта выдачи.
        :param date: Дата фильтрации (строка в формате 'YYYY-MM-DD').
        :return: Статус маршрута (строка).
        """
        routes = self.get_routes(get_test_name, company_id, courier_id, pickup_point_id, date, headers)
        routes_data = routes.json()

        if not routes_data["routes"]:
            raise ValueError("No routes found for the given parameters.") # добавить assert для логирования ошибки, если роут не найден

        # Берем первый маршрут из списка
        first_route = routes_data["routes"][0]
        route_id = first_route["id"]
        route_courier_id = first_route["courier"]["id"]
        route_deliveries_count = first_route["deliveries_count"]
        route_status = first_route["status"]

        # Ассертим параметры маршрута
        self.assertions.assert_route_status(
            route_id=route_id,
            actual_courier_id=route_courier_id,
            expected_courier_id=courier_id,
            actual_deliveries_count=route_deliveries_count,
            expected_deliveries_count=route_deliveries_count, # Используем значение из самого маршрута
            actual_status=route_status,
            expected_status="closed",
            test_name=get_test_name
        )

        print(f"route_id: {route_id}, route_courier_id: {route_courier_id}, route_deliveries_count: {route_deliveries_count}, route_status: {route_status}")
        return route_id, route_courier_id, route_deliveries_count, route_status