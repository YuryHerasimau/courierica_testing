import os
import json


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
