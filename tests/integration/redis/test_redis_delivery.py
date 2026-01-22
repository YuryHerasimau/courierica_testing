import json
import time
import allure
import pytest


@allure.feature("Redis Delivery")
@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.redis_delivery
class TestRedisDelivery:

    @allure.title("Проверка существующих ключей")
    def test_keys_exist(self, redis_client, sample_delivery):
        delivery_id, courier_id = sample_delivery

        keys = redis_client.keys("*")
        print("🔑 Redis keys:", keys)

        assert f"delivery:{delivery_id}" in keys
        assert f"courier:{courier_id}" in keys

    @allure.title("Проверка содержимого ключей для delivery")
    def test_read_delivery_object(self, redis_client, sample_delivery):
        delivery_id, courier_id = sample_delivery

        value = redis_client.get(f"delivery:{delivery_id}")
        assert value is not None
        print("\n📦 Delivery JSON:", value)

        data = json.loads(value)
        assert data["delivery"]["number"] == "4666"
        assert data["courier"]["id"] == courier_id

    @allure.title("Проверка содержимого ключей для courier")
    def test_read_courier_object(self, redis_client, sample_delivery):
        delivery_id, courier_id = sample_delivery

        value = redis_client.get(f"courier:{courier_id}")
        assert value is not None

        data = json.loads(value)
        assert data[courier_id] == delivery_id

    @allure.title("Проверка TTL ключей")
    def test_ttl_decreases(self, redis_client, sample_delivery):
        delivery_id, _ = sample_delivery

        ttl_before = redis_client.ttl(f"delivery:{delivery_id}")
        assert ttl_before > 0

        time.sleep(2)
        ttl_after = redis_client.ttl(f"delivery:{delivery_id}")

        assert ttl_after < ttl_before
