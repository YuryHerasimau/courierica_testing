from pydantic import ValidationError
from httpx import Response
from src.logger import get_logger


class Validator:
    """
    Класс для валидации HTTP-ответов с использованием Pydantic-моделей.
    """
    
    logger = get_logger(__name__)

    @staticmethod
    def validate_response(response: Response, model):
        try:
            validation = model.model_validate_json(response.text)
            if validation.model_dump():
                return model(**response.json())
        except ValidationError as ex:
            Validator.logger.error(ex)
            raise ex
