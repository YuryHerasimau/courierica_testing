from dataclasses import dataclass
from generator.base_generator import BaseGenerator
from datetime import datetime, timedelta
import random


base_gen = BaseGenerator()
now_utc = datetime.utcnow()

@dataclass
class Order:
    address: str
    latitude: float
    longitude: float
    time_from: str
    time_till: str

def generate_hardcoded_orders():
    """
    Генерирует список заказов для теста.
    :param date: Дата в формате YYYY-MM-DD
    :return: Список объектов Order
    """
    orders = [
        Order(
            address="Беларусь, г Минск, ул Веры Хоружей, д 25/3",
            latitude=53.921625,
            longitude=27.563493,
            time_from=None,
            time_till=f"{now_utc.date()}T22:30:00Z",
        ),
        Order(
            address="Беларусь, г Минск, б-р Шевченко, д 8",
            latitude=53.924757,
            longitude=27.556348,
            time_from=None,
            time_till=f"{now_utc.date()}T22:45:00Z",
        ),
        Order(
            address="Беларусь, г Минск, Старовиленский тракт, д 10",
            latitude=53.922723,
            longitude=27.549704,
            time_from=None,
            time_till=f"{now_utc.date()}T23:00:00Z",
        ),
    ]
    return orders

def generate_random_orders(count: int = 10):
    """
    Генерирует случайный список заказов для теста.
    :param count: Количество заказов (по умолчанию 10)
    :return: Список объектов Order
    """
    orders = []

    for _ in range(count):
        # Минимальный старт через 30-60 минут от текущего момента
        min_start_time = now_utc + timedelta(minutes=random.randint(30, 60))

        # Генерируем случайный интервал (минимум 1 час, максимум 6 часов)
        max_end_time = min_start_time + timedelta(hours=random.randint(1, 6))

        time_from = min_start_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        time_till = max_end_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

        # time_till = f"{date}T{random.randint(10, 22)}:{str(random.randint(0, 59)).zfill(2)}:00Z"

        order = Order(
            address=base_gen.get_address(None),
            latitude=round(random.uniform(53.8, 54.0), 6),  # Пример координат Минска
            longitude=round(random.uniform(27.4, 27.7), 6),
            time_from=time_from,
            time_till=time_till,
        )
        # print(f"Generated order: {order}")
        orders.append(order)

    return orders
