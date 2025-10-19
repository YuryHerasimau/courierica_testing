import redis
import pytest
import allure


@allure.feature("Redis tests")
@pytest.mark.integration
@pytest.mark.redis
class TestRedisBasic:

    @allure.title("Проверка доступности Redis")
    def test_list_keys(self, redis_client):
        keys = redis_client.keys("*")
        print("\n🔑 Keys in Redis:", keys)
        assert isinstance(keys, list)

    @allure.title("Проверка содержимого Redis")
    def test_read_existing_keys(self, redis_client):
        keys = redis_client.keys("*")
        for key in keys:
            try:
                value = redis_client.get(key)
                print(f"\n📦 {key} -> {value}")
            except redis.exceptions.ResponseError:
                value = redis_client.type(key)
                print(f"\n📦 {key} is not string, type={value}")

    @allure.title("Проверка содержимого ключей для delivery")
    def test_delivery_object(self, redis_client, sample_delivery):
        delivery_id, _ = sample_delivery
        value = redis_client.get(f"delivery:{delivery_id}")
        assert value is not None
        print("\n📦 Delivery JSON:", value)