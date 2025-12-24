import json
from src.http_methods import MyRequests
from src.assertions import Assertions
from http import HTTPStatus
from data import get_courier_endpoints
from datetime import datetime
from functions import retry


class CourierService:
    def __init__(self):
        self.request = MyRequests()
        self.courier_url = get_courier_endpoints()
        self.assertions = Assertions()

    def turn_on_shift(self, get_test_name, courier_id, pickup_point_id, headers):
        """Включение смены для курьера"""
        data = {"shifts": [{"pickup_point_id": pickup_point_id, "online": True}]}
        response = self.request.patch(
            url=f"{self.courier_url.list_of_couriers}/{courier_id}/shifts",
            headers=headers,
            data=json.dumps(data)
        )
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.NO_CONTENT, test_name=get_test_name)
        print(f"Courier {courier_id} shift on.")
        return response
    
    def close_shift(self, get_test_name, courier_id, pickup_point_id, headers):
        """Закрытие смены для курьера"""
        data = {"shifts": [{"pickup_point_id": pickup_point_id, "online": False}]}
        response = self.request.patch(
            url=f"{self.courier_url.list_of_couriers}/{courier_id}/shifts",
            headers=headers,
            data=json.dumps(data)
        )
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.NO_CONTENT, test_name=get_test_name)
        print(f"Courier {courier_id} shift off.")
        return response
    
    def close_all_active_shifts(self, get_test_name, courier_id, headers):
        """Закрытие всех активных смен курьера на ПВ"""
        
        # Сначала получаем информацию о курьере и его активных сменах
        response = self.request.get(
            url=f"{self.courier_url.list_of_couriers}/{courier_id}",
            headers=headers
        )
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.OK, test_name=get_test_name)
        
        courier_data = response.json()
        print(f"Courier {courier_id} info: {courier_data}")
        
        # Формируем данные для закрытия только АКТИВНЫХ смен
        shifts_data = []
        if "pickup_points" in courier_data:
            for pickup_point in courier_data["pickup_points"]:
                # Закрываем только те смены, которые сейчас открыты (online: true)
                if pickup_point.get("online") is True:
                    shifts_data.append({
                        "pickup_point_id": pickup_point["id"],
                        "online": False
                    })
        
        if not shifts_data:
            print(f"No active shifts found for courier {courier_id}")
            return None
        
        data = {"shifts": shifts_data}
        
        # Закрываем все активные смены
        response = self.request.patch(
            url=f"{self.courier_url.list_of_couriers}/{courier_id}/shifts",
            headers=headers,
            data=json.dumps(data)
        )
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.NO_CONTENT, test_name=get_test_name)
        print(f"All active shifts for courier {courier_id} have been closed. Closed {len(shifts_data)} shift(s).")
        return response

    def update_courier_geo(self, get_test_name, courier_id, latitude, longitude, headers):
        """Обновление геопозиции курьера"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = {"latitude": latitude, "longitude": longitude, "bearing": 0}

        response = self.request.patch(
            url=f"{self.courier_url.list_of_couriers}/{courier_id}/geo_point", 
            headers=headers, 
            data=json.dumps(data)
        )
        self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.OK, test_name=get_test_name)
        print(f"Courier {courier_id} geo point: {data}. Time: {current_time}.")

        return response
    
    def get_courier_batch_deliveries(self, get_test_name, headers, max_attempts=3, delay=5):
        """Получает заказы из batch курьера с ретраями."""
        @retry(max_attempts=max_attempts, delay=delay)
        def _get_batch_deliveries():
            response = self.request.get(
                url=f"{self.courier_url.create_courier}/batch/deliveries",
                headers=headers
            )
            # print("response from _get_batch_deliveries:", response.json())
            self.assertions.assert_status_code(response=response, expected_status_code=HTTPStatus.OK, test_name=get_test_name)
            return response.json()
        
        return _get_batch_deliveries()
