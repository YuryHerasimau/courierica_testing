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
    _client = httpx.Client(base_url=settings.BASE_URL)

    @classmethod
    def _get_auth_credentials(cls, role: Role):
        """Получение учетных данных для роли из конфигурации."""
        role_name = role.name # Например: "COURIER_SAAS"

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
            response = cls._client.post(url, json=credentials)
        else:
            response = cls._client.post(url, auth=(
                credentials["username"], credentials["password"]
            ))
        
        if response.status_code != 200:
            cls.logger.error(
                f"Authentication failed: {response.status_code} for role {role}"
            )
            raise Exception(f"Authentication failed: {response.text}")
        
        return response.json().get("access_token")
    
    @classmethod
    def get_courier_id(cls, token: str) -> str:
        """Получение ID курьера на основе токена."""
        url = "/user"
        response = cls._client.get(url, headers=token)
        
        if response.status_code != 200:
            cls.logger.error(
                f"Failed to fetch courier ID: {response.status_code}. URL: {url}."
            )
            raise Exception(f"Failed to fetch courier ID: {response.text}")

        return response.json().get("id")

    @classmethod
    def close(cls):
        """Закрытие клиента."""
        cls._client.close()
