def get_json_id(response):
    """Получение ID из JSON-ответа"""
    try:
        return response.json().get("id")
    except ValueError:
        raise ValueError("Invalid JSON response")


# def get_delivery_id(self, response):
#     """Получение ID доставки из ответа."""
#     response_json = response.json()
#     return response_json.get("id") if "id" in response_json else None