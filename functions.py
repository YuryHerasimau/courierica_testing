import os
import json
import time
from functools import wraps
from typing import Callable, Optional, Type, Union, Tuple


def get_current_path(file_name: str):
    """
    Returns the absolute path of a file relative to the current file.

    Args:
        file_name (str): The name of the file.

    Returns:
        str: The absolute path of the file.
    """
    current_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_path, file_name)


def load_json(file_name: str):
    """
    Loads a JSON file.

    Args:
        file_name (str): The name of the JSON file.

    Returns:
        dict: The loaded JSON data.
    """
    with open(get_current_path(file_name), "r", encoding="utf-8") as file:
        return json.load(file)


def retry(
    max_attempts: int = 3,
    delay: Union[int, float] = 1,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    on_failure: Optional[Callable] = None, 
    exponential_backoff: bool = False,
    logger=None
):
    """
    Decorator for re-executing a function on exception.

    Parameters:
        max_attempts (int): Maximum number of attempts (default 3)
        delay (int/float): Delay between attempts in seconds (default 1)
        exceptions (Exception/tuple): Type of exceptions to catch (default all)
        on_failure (callable): Function to call after failure is fixed.
        exponential_backoff (bool): Use exponential backoff.
        logger: Logger to write messages to (default print)

    Example usage:
        @retry(max_attempts=5, delay=2, exceptions=(ConnectionError, TimeoutError))
        def some_function():
            # code that can throw exceptions
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_attempt = 0
            current_delay = delay

            while current_attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    current_attempt += 1

                    if current_attempt == max_attempts:
                        break

                    log_message = (
                        f"Attempt {current_attempt}/{max_attempts} failed for {func.__name__}. "
                        f"Error: {str(e)}. Retrying in {current_delay} seconds..."
                    )
                    if logger:
                        logger.warning(log_message)
                    else:
                        print(log_message)

                    time.sleep(current_delay)
                    if exponential_backoff:
                        current_delay *= 2

            if on_failure:
                on_failure(last_exception)

            raise last_exception

        return wrapper
    return decorator