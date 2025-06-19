from enum import Enum
import httpx
from src.logger import get_logger
from settings import settings


class Role(str, Enum):
    """Роли пользователей."""
    ADMIN = "admin"
    LOGISTICIAN_SAAS = "logistician_saas"
    LOGISTICIAN_IIKO = "logistician_iiko"
    COURIER_SAAS = "courier_saas"
    COURIER_IIKO = "courier_iiko"

    @property
    def is_courier(self) -> bool:
        """Проверка, является ли роль курьером."""
        return self.name.startswith("COURIER_")

class AuthService:
    """
    Сервис для работы с аутентификацией и токенами.
    """

    logger = get_logger(__name__)
    _client = None

    @classmethod
    def _get_client(cls):
        """Ленивая инициализация клиента с текущим BASE_URL."""
        if cls._client is None:
            cls._client = httpx.Client(base_url=settings.BASE_URL)
        return cls._client

    @classmethod
    def _get_auth_credentials(cls, role: Role):
        """Получение учетных данных для роли из конфигурации."""
        role_name = role.name

        if role.is_courier:
            return {
                "phone": getattr(settings, f"{role_name}_PHONE"),
                "code": getattr(settings, f"{role_name}_CODE")
            }
        return {
            "username": getattr(settings, f"{role_name}_USERNAME"),
            "password": getattr(settings, f"{role_name}_PASSWORD")
        }

    @classmethod
    def get_access_token(cls, role: Role) -> str:
        """Универсальный метод получения токена."""
        credentials = cls._get_auth_credentials(role)
        url = "/login/phone/code" if role.is_courier else "/login/email"
        
        if role.is_courier:
            response = cls._get_client().post(url, json=credentials)
        else:
            response = cls._get_client().post(url, auth=(
                credentials["username"], credentials["password"]
            ))
        
        if response.status_code != 200:
            cls.logger.error(f"Auth failed: {response.status_code} for role {role}")
            raise Exception(f"Auth failed: {response.text}")
        
        return response.json().get("access_token")
    
    @classmethod
    def get_courier_id(cls, token: str) -> str:
        """Получение ID курьера на основе токена."""
        url = "/user"
        response = cls._get_client().get(url, headers=token)
        
        if response.status_code != 200:
            cls.logger.error(f"Failed to fetch courier ID: {response.status_code}. URL: {url}.")
            raise Exception(f"Failed to fetch courier ID: {response.text}")

        return response.json().get("id")
    
    @classmethod
    def request_sms_code(cls, phone: str) -> None:
        """Запрос SMS кода для авторизации курьера."""
        url = "/login/phone"
        response = cls._get_client().post(url, json={"phone": phone})

        if response.status_code != 204:
            cls.logger.error(f"SMS request failed: {response.status_code} for phone {phone}")
            raise Exception(f"SMS request failed: {response.text}")
        
    @classmethod
    def get_sms_code_for_courier(cls, courier_id: str, admin_headers: dict) -> str:
        """Получение SMS кода для курьера через админский эндпоинт."""
        url = f"/couriers/{courier_id}/sms_code"
        response = cls._get_client().get(url, headers=admin_headers)

        if response.status_code != 200 or response.json()["code"] == "":
            cls.logger.error(f"Failed to get SMS code: {response.status_code} for courier {courier_id}")
            raise Exception(f"Failed to get SMS code: {response.text}")
        return response.json()["code"]
    
    @classmethod
    def get_courier_phone(cls, courier_id: str, admin_headers: dict) -> str:
        """Получение номера телефона курьера."""
        url = f"/couriers/{courier_id}"
        response = cls._get_client().get(url, headers=admin_headers)

        if response.status_code != 200:
            cls.logger.error(f"Failed to get courier phone: {response.status_code}")
            raise Exception(f"Failed to get courier phone: {response.text}")
        return response.json()["user"]["phone"]
    
    @classmethod
    def get_courier_headers(cls, courier_id: str, admin_headers: dict) -> dict:
        """Получает auth headers для конкретного курьера."""
        phone = AuthService.get_courier_phone(courier_id, admin_headers)
        AuthService.request_sms_code(phone)
        sms_code = AuthService.get_sms_code_for_courier(courier_id, admin_headers)

        url = f"/login/phone/code"
        response = cls._get_client().post(url, json={"phone": phone, "code": sms_code})

        if response.status_code != 200:
            cls.logger.error(f"Failed to get courier headers: {response.status_code}")
            raise Exception(f"Failed to get courier headers: {response.text}")
    
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    @classmethod
    def close(cls):
        """Закрытие клиента."""
        cls._get_client().close()
