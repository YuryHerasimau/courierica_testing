from math import radians, sin, cos, sqrt, atan2
from typing import List, Dict
from functions import load_json


ADDRESS_DATA = load_json("tests/e2e/config/iiko_address_data.json")
orders = [
    {
        "address_key": "Сущёвский Вал 55",
        "latitude": ADDRESS_DATA["Сущёвский Вал 55"]["latitude"],
        "longitude": ADDRESS_DATA["Сущёвский Вал 55"]["longitude"],
        "duration": 60,
    },
    {
        "address_key": "Сущёвский Вал 55",
        "latitude": ADDRESS_DATA["Сущёвский Вал 55"]["latitude"],
        "longitude": ADDRESS_DATA["Сущёвский Вал 55"]["longitude"],
        "duration": 30,
    },
    {
        "address_key": "Хуторская 38Ас23",
        "latitude": ADDRESS_DATA["Хуторская 38Ас23"]["latitude"],
        "longitude": ADDRESS_DATA["Хуторская 38Ас23"]["longitude"],
        "duration": 40,
    }
]

class DeliveryTimeCalculator:
    # Константы (в метрах)
    EARTH_RADIUS = 6371000  # радиус Земли
    DELIVERY_CONSOLIDATION_RADIUS = 1000  # радиус объединения доставок
    
    # Временные параметры (в минутах)
    TIME_PICKUP = 5    # время на получение заказа в ПВЗ
    TIME_COOKING = 20  # время приготовления
    TIME_DROP_OFF = 5  # время на передачу клиенту
    TIME_LATE = 10     # допустимое опоздание

    TIME_LATE_3PL = 10    # Допустимое время опоздания 3PL (мин)
    TIME_ARRIVE_3PL = 15  # Время подачи 3PL (мин)
    
    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Рассчитывает расстояние между двумя точками на сфере (в метрах)."""
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return DeliveryTimeCalculator.EARTH_RADIUS * c
    
    @classmethod
    def calculate_delivery_time(
        cls,
        orders: List[Dict],
        pickup_point: Dict,
        max_deliveries: int = 3
    ) -> Dict:
        """
        Рассчитывает общее время доставки для набора заказов.
        
        :param orders: Список заказов в формате:
            {
                "address_key": "Сущёвский Вал 55",
                "latitude": 55.793728,
                "longitude": 37.614428,
                "duration": 60
            }
        :param pickup_point: Данные ПВЗ из ADDRESS_DATA
        :param max_deliveries: Максимальное кол-во заказов у курьера
        :return: Словарь с расчетами {total_time, batches, routes}
        """
        # 1. Преобразуем заказы к нужному формату
        formatted_orders = []
        for idx, order in enumerate(orders, 1):
            formatted_orders.append({
                "id": idx,
                "address_key": order["address_key"],
                "latitude": order["latitude"],
                "longitude": order["longitude"],
                "line1": ADDRESS_DATA[order["address_key"]]["line1"],
                "duration": order["duration"]
            })
        
        # 2. Группируем заказы в батчи по критериям
        batches = cls._group_into_batches(formatted_orders, pickup_point, max_deliveries)
        
        # 3. Рассчитываем время для каждого батча
        total_time = 0
        result = {"batches": [], "total_time": 0}
        
        for batch in batches:
            batch_time = cls._calculate_batch_time(batch, pickup_point)
            route = cls._optimize_route(batch, pickup_point)
            
            result["batches"].append({
                "order_ids": [o["id"] for o in batch],
                "orders": [o["address_key"] for o in batch], # Уникальные адреса
                "batch_time": batch_time,
                "route": route,
                "details": [
                    {
                        "id": o["id"],
                        "address": o["address_key"],
                        "duration": o["duration"],
                        "coordinates": (o["latitude"], o["longitude"])
                    } for o in batch
                ]
            })
            result["total_time"] += batch_time
        
        return result
    
    @classmethod
    def _group_into_batches(
        cls,
        orders: List[Dict],
        pickup_point: Dict,
        max_deliveries: int = 3
    ) -> List[List[Dict]]:
        """Улучшенная группировка с приоритетом объединения близких адресов."""
        # Сортируем заказы по времени готовности (duration)
        sorted_orders = sorted(orders, key=lambda x: x["duration"])
        
        batches = []
        used_order_ids = set()
        
        for order in sorted_orders:
            if order["id"] in used_order_ids:
                continue
                
            # Пытаемся создать максимально полный батч
            current_batch = [order]
            used_order_ids.add(order["id"])
            current_max_duration = order["duration"]
            
            # Ищем заказы для объединения
            for other in sorted_orders:
                if (other["id"] not in used_order_ids and
                    len(current_batch) < max_deliveries):
                    
                    # Проверяем возможность объединения
                    new_batch = current_batch + [other]
                    new_max_duration = max(current_max_duration, other["duration"])
                    
                    if cls._can_be_batched(current_batch, other, pickup_point, new_max_duration):
                        current_batch.append(other)
                        used_order_ids.add(other["id"])
                        current_max_duration = new_max_duration
            
            batches.append(current_batch)
        
        return batches
    
    @classmethod
    def _can_add_to_batch(
        cls,
        current_batch: List[Dict],
        new_group: List[Dict],
        pickup_point: Dict,
        current_max_duration: float
    ) -> bool:
        """
        DEPRECATED!
        Проверяет можно ли добавить группу заказов в текущий батч.
        """
        if not current_batch:
            return True
        
        # Проверяем расстояние между адресами
        existing_address = (current_batch[0]["latitude"], current_batch[0]["longitude"])
        new_address = (new_group[0]["latitude"], new_group[0]["longitude"])
        
        # Если адреса одинаковые - можно объединять
        if existing_address == new_address:
            return True
        
        # Проверяем расстояние между разными адресами
        distance = cls.haversine(
            existing_address[0], existing_address[1],
            new_address[0], new_address[1]
        )
        if distance > cls.DELIVERY_CONSOLIDATION_RADIUS:
            return False
        
        # Проверяем временные ограничения
        new_max_duration = max(current_max_duration, max(o["duration"] for o in new_group))
        test_batch = current_batch + new_group
        batch_time = cls._calculate_batch_time(test_batch, pickup_point)
        
        return batch_time <= (new_max_duration + cls.TIME_LATE)
    
    @classmethod
    def _is_batch_time_valid(cls, batch: List[Dict], pickup_point: Dict, max_duration: float) -> bool:
        """
        DEPRECATED!
        Проверяет, что батч может быть доставлен вовремя с учетом всех временных ограничений.
        """
        # Расчет общего времени для батча
        batch_time = cls._calculate_batch_time(batch, pickup_point)
        
        # Проверяем что общее время меньше чем максимальное duration + допустимое опоздание
        # print(batch_time, max_duration, cls.TIME_LATE)
        return batch_time <= (max_duration + cls.TIME_LATE)
    
    @classmethod
    def _can_be_batched(
        cls,
        existing_orders: List[Dict],
        new_order: Dict,
        pickup_point: Dict,
        max_duration: float
    ) -> bool:
        """Проверяет можно ли добавить заказ в существующий батч."""
        # Проверяем расстояние до всех заказов в батче
        for order in existing_orders:
            distance = cls.haversine(
                order["latitude"], order["longitude"],
                new_order["latitude"], new_order["longitude"]
            )
            if distance > cls.DELIVERY_CONSOLIDATION_RADIUS:
                return False
        
        # Проверяем временные ограничения
        test_batch = existing_orders + [new_order]
        batch_time = cls._calculate_batch_time(test_batch, pickup_point)
        
        return batch_time <= (max_duration + cls.TIME_LATE)
    
    @classmethod
    def _calculate_batch_time(cls, batch: List[Dict], pickup_point: Dict) -> float:
        """Точный расчет времени доставки для батча с учетом всех параметров."""
        # Время на забор заказов в ПВЗ
        pickup_time = cls.TIME_PICKUP
        
        # Максимальное время приготовления в батче
        cooking_time = max(order.get("time_cooking", cls.TIME_COOKING) for order in batch)
        
        # Время движения по оптимальному маршруту
        route = cls._optimize_route(batch, pickup_point)
        movement_time = sum(leg["time"] for leg in route)
        
        # Время на передачу заказов клиентам
        drop_off_time = cls.TIME_DROP_OFF * len(batch)
        
        return pickup_time + cooking_time + movement_time + drop_off_time
    
    @classmethod
    def _optimize_route(cls, batch: List[Dict], pickup_point: Dict) -> List[Dict]:
        """Оптимизированный маршрут с учетом всех заказов."""
        if not batch:
            return []
        
        # Собираем все уникальные точки доставки
        delivery_points = []
        for order in batch:
            point = {
                "latitude": order["latitude"],
                "longitude": order["longitude"],
                "line1": order["line1"]
            }
            if point not in delivery_points:
                delivery_points.append(point)
        
        # Строим маршрут методом ближайшего соседа
        route = []
        current_point = pickup_point
        
        while delivery_points:
            # Находим ближайшую точку доставки
            next_point = min(
                delivery_points,
                key=lambda p: cls.haversine(
                    current_point["latitude"], current_point["longitude"],
                    p["latitude"], p["longitude"]
                )
            )
            
            # Рассчитываем время до точки
            distance = cls.haversine(
                current_point["latitude"], current_point["longitude"],
                next_point["latitude"], next_point["longitude"]
            )
            time = max(1, distance / 1000 * 6)  # 6 мин/км
            
            route.append({
                "from": current_point["line1"],
                "to": next_point["line1"],
                "distance": distance,
                "time": time
            })
            
            # Переходим к следующей точке
            current_point = next_point
            delivery_points.remove(next_point)
        
        return route

    
if __name__ == "__main__":
    calculator = DeliveryTimeCalculator()
    result = calculator.calculate_delivery_time(orders=orders, pickup_point=ADDRESS_DATA["ПВ Курьерика"])

    print(f"Общее время доставки: {result['total_time']:.1f} минут")
    for i, batch in enumerate(result["batches"], 1):
        print(f"\nБатч {i}:")
        print(f"Заказы: {batch['orders']}")
        print(f"Время батча: {batch['batch_time']} минут")
        print("Маршрут:")
        for leg in batch["route"]:
            print(f"  {leg['from']} -> {leg['to']} ({leg['distance']:.0f} м, {leg['time']:.1f} мин)")
