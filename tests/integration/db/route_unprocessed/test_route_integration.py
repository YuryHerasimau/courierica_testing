import pytest
import allure
from unittest.mock import Mock, patch


@allure.feature("Route Cache and Unprocessed Integration - Simulation")
@pytest.mark.integration
@pytest.mark.route_integration
@pytest.mark.simulation
class TestRouteCacheDBIntegrationSimulation:

    @allure.title("Симуляция исключения маршрутов через моки")
    @patch('psycopg2.connect')
    def test_exclusion_logic_with_mocks(self, mock_connect, redis_client):
        print("\nТест с моками БД:")
        
        # Создаем мок для БД
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Настраиваем мок для возврата тестовых данных
        mock_cursor.fetchone.return_value = {'count': 2}
        mock_cursor.fetchall.return_value = [
            {'route_id': 'existing-route-1'},
            {'route_id': 'existing-route-2'}
        ]
        
        # Симуляция данных в Redis
        test_routes = ['route-a', 'route-b', 'route-c', 'existing-route-1', 'existing-route-2']
        for route_id in test_routes:
            redis_client.set(f"active_route:{route_id}", '{}', ex=10)
        
        try:
            # Шаг 1: Получаем маршруты из Redis
            redis_keys = redis_client.keys("active_route:*")
            redis_routes = [key.split(":", 1)[1] for key in redis_keys]
            print(f"   1. Маршруты в Redis: {redis_routes}")
            
            # Шаг 2: Получаем исключенные маршруты из БД (через мок)
            mock_cursor.execute("SELECT route_id FROM journal_route_unprocessed")
            excluded_routes = [r['route_id'] for r in mock_cursor.fetchall()]
            print(f"   2. Исключенные маршруты из БД: {excluded_routes}")
            
            # Шаг 3: Исключаем маршруты
            routes_to_process = [r for r in redis_routes if r not in excluded_routes]
            print(f"   3. Маршруты для обработки: {routes_to_process}")
            
            assert 'existing-route-1' not in routes_to_process
            assert 'existing-route-2' not in routes_to_process
            assert 'route-a' in routes_to_process
            assert 'route-b' in routes_to_process
            assert 'route-c' in routes_to_process
            print(f"\nЛогика исключения работает корректно с моками")
            
        finally:
            for route_id in test_routes:
                redis_client.delete(f"active_route:{route_id}")