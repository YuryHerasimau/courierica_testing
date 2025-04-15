from typing import Type, TypeVar
from pydantic import ValidationError, BaseModel
from httpx import Response
from src.logger import get_logger

# Создаём TypeVar для типизации Pydantic-моделей
T = TypeVar("T", bound=BaseModel)

class Validator:
    """
    Класс для валидации HTTP-ответов с использованием Pydantic-моделей.
    Обеспечивает проверку структуры и типов данных в ответах API.
    """
    
    logger = get_logger(__name__)

    @staticmethod
    def validate_response(response: Response, model: Type[T]) -> T:
        """
        Валидирует HTTP-ответ по указанной Pydantic-модели.

        Args:
            response: HTTP-ответ, полученный от сервера.
            model: Pydantic-модель (класс), по которой нужно валидировать данные.

        Returns:
            Экземпляр Pydantic-модели с данными из ответа.

        Raises:
            ValidationError: Если данные ответа не соответствуют модели.
            ValueError: Если ответ содержит пустые или невалидные данные.
            JSONDecodeError: Если тело ответа не является валидным JSON.
        """
        try:
            validation = model.model_validate_json(response.text)
            if validation.model_dump():
                return model(**response.json())
        except ValidationError as ex:
            Validator.logger.error(ex)
            raise ex
        except Exception as ex:
            Validator.logger.error(
                f"Unexpected error during validation of {model.__name__}: {ex}"
            )
            raise