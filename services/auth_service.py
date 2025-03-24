import httpx
from src.logger import get_logger
from settings import settings


class AuthService:
    """
    Сервис для работы с аутентификацией и токенами.
    """

    logger = get_logger(__name__)
    
    @staticmethod
    def get_access_token(role: str) -> str:
        """Получение токена для логиста или суперадмина по роли"""
        username = getattr(settings, f"{role.upper()}_USERNAME")
        password = getattr(settings, f"{role.upper()}_PASSWORD")
        url = f"{settings.BASE_URL}/login/email"
        
        response = httpx.post(url, auth=(username, password))
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            AuthService.logger.error(
                f"Authentication failed: {response.status_code} for role {role} and username {username}"
            )
            raise Exception(f"Authentication failed: {response.text}")

    @staticmethod
    def get_access_token_for_courier(role: str) -> str:
        """Получение токена для курьера по телефону и коду"""
        phone = getattr(settings, f"{role.upper()}_PHONE")
        code = getattr(settings, f"{role.upper()}_CODE")
        url = f"{settings.BASE_URL}/login/phone/code"

        response = httpx.post(url, json={"phone": phone, "code": code})
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            AuthService.logger.error(
                f"Authentication failed: {response.status_code} for role {role} and phone {phone}"
            )
            raise Exception(f"Authentication failed: {response.text}")

    @staticmethod
    def get_courier_id(token: str) -> str:
        """Получение ID курьера на основе токена."""
        url = f"{settings.BASE_URL}/user"
        response = httpx.get(url, headers=token)
        if response.status_code == 200:
            return response.json().get("id")
        else:
            AuthService.logger.error(
                f"Failed to fetch courier ID: {response.status_code}. URL: {url}."
            )
            raise Exception(f"Failed to fetch courier ID: {response.text}")