import json
import uuid
import pytest
import allure
from datetime import datetime, timedelta


@allure.feature("Redis Route Cache")
@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.redis_route_cache
class TestRouteCache:

    @allure.title("Проверка создания и чтения активного маршрута")
    def test_active_route_creation(self, redis_client, sample_active_route):
        """Тест создания активного маршрута в кеше"""
        route_id, _ = sample_active_route
        
        # Проверяем, что маршрут создан
        key = f"active_route:{route_id}"
        cached_value = redis_client.get(key)
        
        assert cached_value is not None, "Маршрут должен быть в кеше"
        
        # Проверяем структуру данных
        cached_data = json.loads(cached_value)
        assert cached_data["route_id"] == route_id
        assert cached_data["status"] == "performing"
        assert "courier_id" in cached_data
        assert "steps" in cached_data
        assert len(cached_data["steps"]) == 2
        
        print(f"\nActive route {route_id} создан в кеше")
        print(f"Данные маршрута: {cached_data}")

    @allure.title("Проверка TTL активного маршрута")
    def test_active_route_ttl(self, redis_client, sample_active_route):
        """Тест времени жизни кеша маршрута"""
        route_id, _ = sample_active_route
        key = f"active_route:{route_id}"
        
        # Проверяем TTL
        ttl = redis_client.ttl(key)
        assert ttl > 0, "TTL должен быть установлен"
        assert ttl <= 86400, "TTL не должен превышать 24 часа по умолчанию"
        
        print(f"\nTTL активного маршрута {route_id}: {ttl} секунд")

    @allure.title("Проверка удаления маршрута из кеша")
    def test_active_route_deletion(self, redis_client, sample_active_route):
        """Тест удаления маршрута из кеша (имитация закрытия маршрута)"""
        route_id, _ = sample_active_route
        key = f"active_route:{route_id}"
        
        # Проверяем, что маршрут существует
        assert redis_client.exists(key) == 1
        # Имитируем закрытие маршрута (удаление из кеша)
        redis_client.delete(key)
        
        # Проверяем, что маршрут удален
        assert redis_client.exists(key) == 0

        print(f"\nМаршрут {route_id} удален из кеша")

    @allure.title("Проверка формата ключа active_route")
    def test_active_route_key_pattern(self, redis_client):
        """Тест паттерна ключей active_route"""
        keys = redis_client.keys("active_route:*")
        
        for key in keys:
            # Проверяем формат ключа
            assert key.startswith("active_route:"), f"Ключ {key} должен начинаться с 'active_route:'"
            
            # Извлекаем route_id
            route_id = key.split(":", 1)[1]
            assert len(route_id) > 0, "Route ID не должен быть пустым"
            
            # Проверяем, что значение можно распарсить как JSON
            value = redis_client.get(key)
            if value:
                try:
                    route_data = json.loads(value)
                    assert "route_id" in route_data
                    assert "status" in route_data
                except json.JSONDecodeError:
                    pytest.fail(f"Невалидный JSON в ключе {key}")
        
        print(f"\nНайдено {len(keys)} активных маршрутов")

    @allure.title("Проверка структуры данных маршрута")
    def test_route_data_structure(self, redis_client, sample_active_route):
        """Тест структуры данных маршрута"""
        route_id, _ = sample_active_route
        key = f"active_route:{route_id}"
        
        value = redis_client.get(key)
        route_data = json.loads(value)
        
        # Обязательные поля
        required_fields = ["route_id", "status", "courier_id", "started_at", "steps"]
        for field in required_fields:
            assert field in route_data, f"Поле {field} обязательно в данных маршрута"
        
        # Проверяем структуру steps
        steps = route_data["steps"]
        assert isinstance(steps, list)
        
        for step in steps:
            required_step_fields = ["delivery_id", "status", "address", "time_till"]
            for field in required_step_fields:
                assert field in step, f"Поле {field} обязательно в шаге маршрута"
        
        print(f"\nСтруктура маршрута {route_id} валидна")


@allure.feature("Redis Route Auto Close")
@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.redis_route_auto_close
class TestRouteAutoClose:

    @allure.title("Поиск старых маршрутов для автоматического закрытия")
    def test_find_old_routes_for_auto_close(self, redis_client, sample_old_active_route):
        """
        Тест поиска старых маршрутов для автоматического закрытия
        Согласно ТЗ: started_at < now - 1 day
        """
        route_id, _ = sample_old_active_route
        
        # Получаем все активные маршруты
        keys = redis_client.keys("active_route:*")
        old_routes = []
        
        for key in keys:
            value = redis_client.get(key)
            if value:
                try:
                    data = json.loads(value)
                    
                    # Проверяем дату started_at
                    if "started_at" in data:
                        started_at = datetime.fromisoformat(data["started_at"].replace('Z', '+00:00'))
                        
                        # Маршрут старше суток
                        if datetime.now() - started_at > timedelta(days=1):
                            old_routes.append({
                                "key": key,
                                "data": data,
                                "age_days": (datetime.now() - started_at).days
                            })
                            
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Ошибка обработки маршрута {key}: {e}")
        
        # Проверяем, что наш старый маршрут найден
        found = any(r["data"]["route_id"] == route_id for r in old_routes)
        assert found, f"Старый маршрут {route_id} должен быть найден"
        
        print(f"\nНайдено {len(old_routes)} старых маршрутов для обработки")
        for route in old_routes:
            print(f"   - {route['data']['route_id']} (возраст: {route['age_days']} дней)")

    @allure.title("Проверка маршрутов с завершенными доставками")
    def test_routes_with_completed_deliveries(self, redis_client, sample_active_route):
        """
        Тест маршрутов, где все доставки в терминальном статусе
        Согласно ТЗ: если все заказы в терминальном статусе - на закрытие
        """
        route_id, _ = sample_active_route
        key = f"active_route:{route_id}"
        
        value = redis_client.get(key)
        route_data = json.loads(value)
        
        # Терминальные статусы доставок
        terminal_statuses = ["delivered", "canceled", "failed"]
        
        # Проверяем статусы всех доставок в маршруте
        all_terminal = True
        for step in route_data.get("steps", []):
            if step.get("status") not in terminal_statuses:
                all_terminal = False
                break
        
        # В нашем тестовом маршруте не все доставки завершены
        assert not all_terminal, "В тестовом маршруте не все доставки должны быть завершены"
        
        print(f"\nМаршрут {route_id}: все доставки завершены? {all_terminal}")

    @allure.title("Проверка очистки невалидных маршрутов")
    def test_invalid_routes_cleanup(self, redis_client):
        """
        Тест сценариев очистки невалидных маршрутов
        Согласно ТЗ:
        1. Маршрут не найден в БД - удаляем из кеша
        2. Нет шагов - удаляем маршрут
        3. Только шаг возврата - удаляем маршрут
        4. Не назначен на курьера - игнорируем
        """
        # Тест 1: Маршрут без шагов
        empty_route_id = str(uuid.uuid4())
        empty_route_data = {
            "route_id": empty_route_id,
            "status": "new",
            "courier_id": None,  # Не назначен на курьера
            "started_at": datetime.now().isoformat(),
            "steps": []  # Нет шагов
        }
        
        key = f"active_route:{empty_route_id}"
        redis_client.set(key, json.dumps(empty_route_data), ex=300)
        
        # Проверяем создание
        assert redis_client.exists(key) == 1
        
        # Имитируем очистку (удаляем)
        redis_client.delete(key)
        assert redis_client.exists(key) == 0
        
        print(f"\nНевалидный маршрут {empty_route_id} очищен")

    @allure.title("Проверка поиска всех активных маршрутов")
    def test_get_all_active_routes(self, redis_client, sample_active_route):
        """Тест получения всех активных маршрутов из кеша"""
        # Создаем несколько маршрутов
        routes_count = 3
        route_ids = []
        
        for _ in range(routes_count):
            route_id = str(uuid.uuid4())
            route_data = {
                "route_id": route_id,
                "status": "in_progress",
                "courier_id": str(uuid.uuid4()),
                "started_at": datetime.now().isoformat(),
                "steps": []
            }
            redis_client.set(f"active_route:{route_id}", json.dumps(route_data), ex=300)
            route_ids.append(route_id)
        
        try:
            # Получаем все активные маршруты
            keys = redis_client.keys("active_route:*")
            
            # Проверяем, что наши маршруты найдены
            found_count = 0
            for route_id in route_ids:
                if redis_client.exists(f"active_route:{route_id}"):
                    found_count += 1
            
            assert found_count == routes_count, f"Должно быть найдено {routes_count} маршрутов"
            
            print(f"\nВсего активных маршрутов: {len(keys)}: {keys}")
            print(f"Созданных в тесте: {found_count}: {route_ids}")
            
        finally:
            for route_id in route_ids:
                print(f"Удаляем маршрут {route_id}")
                redis_client.delete(f"active_route:{route_id}")
