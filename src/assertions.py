from httpx import Response
from src.logger import get_logger


class Assertions:
    """
    Класс для проверки утверждений (assertions) в тестах.
    """

    @staticmethod
    def assert_status_code(response: Response, expected_status_code: int, test_name: str = None):
        actual_status_code = response.status_code

        if actual_status_code != expected_status_code:
            # Получаем X-Request-ID из заголовка, если есть
            request_id = response.headers.get("X-Request-ID")
            request_id_info = f" | X-Request-ID: {request_id}" if request_id else ""

            # Логируем с X-Request-ID
            get_logger(test_name).error(
                f"Expected {expected_status_code} status code but got {actual_status_code} status code instead{request_id_info}"
            )

        assert actual_status_code == expected_status_code, (
            f"Expected {expected_status_code} status code but got {actual_status_code} status code instead"
        )

    @staticmethod
    def assert_bool(response: Response, expected_bool: bool, field_name: str, test_name: str):
        json_response = response.json()
        actual_bool = json_response[field_name]
        assert actual_bool == expected_bool, get_logger(test_name).error(
            f"Expected {expected_bool} but got {actual_bool} instead"
        )

    @staticmethod
    def assert_pagination(
        response: Response,
        expected_page: int,
        expected_per_page: int,
        expected_total: int,
        test_name: str,
    ):
        json_response = response.json()
        pagination = json_response["pagination"]
        # Проверка текущей страницы
        actual_page = pagination["page"]
        assert actual_page == expected_page, get_logger(test_name).error(
            f"Expected {expected_page} page but got {actual_page} page instead"
        )

        # Проверка количества элементов на странице
        actual_per_page = pagination["per_page"]
        assert actual_per_page == expected_per_page, get_logger(test_name).error(
            f"Expected {expected_per_page} per_page but got {actual_per_page} per_page instead"
        )

        # Проверка общего количества элементов
        actual_total = pagination["total"]
        assert actual_total == expected_total, get_logger(test_name).error(
            f"Expected {expected_total} total count but got {actual_total} total count instead"
        )

    @staticmethod
    def assert_route_status(
        route_id,
        actual_courier_id,
        expected_courier_id,
        actual_deliveries_count,
        expected_deliveries_count,
        actual_status,
        expected_status,
        test_name
    ):
        """
        Проверяет корректность параметров маршрута.
        """
        assert actual_courier_id == expected_courier_id, get_logger(test_name).error(
            f"Expected courier ID '{expected_courier_id}', but got '{actual_courier_id}' for route {route_id}."
        )
        assert actual_deliveries_count == expected_deliveries_count, get_logger(test_name).error(
            f"Expected deliveries count '{expected_deliveries_count}', but got '{actual_deliveries_count}' for route {route_id}."
        )
        assert actual_status == expected_status, get_logger(test_name).error(
            f"Expected status '{expected_status}', but got '{actual_status}' for route {route_id}."
        )
