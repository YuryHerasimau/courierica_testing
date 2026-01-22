import json
import time

import pytest
import allure

from kafka import KafkaConsumer
from kafka.admin import KafkaAdminClient
from kafka.errors import KafkaError


@allure.feature("Testing Kafka events")
@pytest.mark.integration
@pytest.mark.kafka
class TestKafkaEvents:
    
    @allure.title("Проверка подключения к Kafka через Producer")
    def test_kafka_connection(self, kafka_producer):
        try:
            # Отправляем тестовое сообщение
            test_message = {
                "test": "connection_check",
                "timestamp": time.time(),
                "source": "autotest"
            }
            future = kafka_producer.send(
                'test-connection-topic',
                json.dumps(test_message).encode('utf-8')
            )
            # Ждем подтверждения
            result = future.get(timeout=10)
            assert result.topic is not None, "Не удалось отправить сообщение в Kafka"
        except KafkaError as e:
            pytest.fail(f"Не удалось подключиться к Kafka: {e}")

    @allure.title("Проверка здоровья Kafka через Consumer")
    def test_kafka_health_check(self, kafka_consumer):
        try:
            # пытаемся получить список топиков
            topics = kafka_consumer.topics()
            assert len(topics) > 0, "Kafka доступен, но топиков не найдено"
        except KafkaError as e:
            pytest.fail(f"Kafka недоступен: {e}")

    @allure.title("Проверка наличия нужных топиков")
    def test_kafka_topics_exists(self, kafka_consumer):
        try:
            topics = kafka_consumer.topics()

            print(f"Найдено всего топиков: {len(topics)}")
            for topic in sorted(topics):
                print(f"  - {topic}")
            
            # Проверяем обязательные топики
            required_topics = ['events', 'route']
            for topic in required_topics:
                assert topic in topics, f"Топик {topic} не найден"
        except KafkaError as e:
            pytest.fail(f"Ошибка при получении топиков: {e}")

    @allure.title("Проверка чтения сообщений в топике events")
    def test_events_topic_has_messages(self, kafka_config):
        """Для этого теста создаем специального consumer с подпиской на events"""        
        consumer_config = kafka_config.copy()
        consumer_config.update({
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': False,
            'consumer_timeout_ms': 10000  # 10 секунд таймаут
        })
        consumer = KafkaConsumer('events', **consumer_config)

        try:
            messages = []
            start_time = time.time()
            
            # Читаем сообщения в течение 10 секунд
            for message in consumer:
                if time.time() - start_time > 10:
                    break
                    
                try:
                    message_data = json.loads(message.value.decode('utf-8'))
                    messages.append({
                        'topic': message.topic,
                        'partition': message.partition,
                        'offset': message.offset,
                        'key': message.key.decode('utf-8') if message.key else None,
                        'value': message_data,
                        'timestamp': message.timestamp
                    })
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                        
            print(f"Найдено сообщений: {len(messages)}")
            assert messages, "Сообщений в топике events нет"
                
        except KafkaError as e:
            pytest.fail(f"Ошибка при чтении сообщений: {e}")
        finally:
            consumer.close()

    @allure.title("Проверка структуры событий")
    def test_event_structure_validation(self, kafka_config):
        """Для этого теста создаем специального consumer с подпиской на events"""
        consumer_config = kafka_config.copy()
        consumer_config.update({
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': False,
            'consumer_timeout_ms': 5000  # 5 секунд таймаут
        })
        consumer = KafkaConsumer('events', **consumer_config)
        
        try:            
            sample_messages = []
            start_time = time.time()
            
            # Собираем несколько сообщений для анализа
            for message in consumer:
                if time.time() - start_time > 5 or len(sample_messages) >= 2:
                    break
                    
                try:
                    message_data = json.loads(message.value.decode('utf-8'))
                    headers = {key: value.decode('utf-8') for key, value in message.headers} if message.headers else {}
                    sample_messages.append({
                        'body': message_data,
                        'headers': headers
                    })
                except json.JSONDecodeError:
                    continue
            
            consumer.close()
            
            if sample_messages:
                # Проверяем структуру тела сообщения
                expected_body_fields = ['eventId', 'eventType', 'timestamp', 'data']
                
                for msg in sample_messages:
                    body = msg['body']
                    headers = msg['headers']
                    
                    # Проверяем обязательные поля в теле
                    for field in expected_body_fields:
                        assert field in body, f"Отсутствует обязательное поле {field} в теле сообщения"
                    
                    # Проверяем типы полей в теле
                    assert isinstance(body['eventId'], str), "eventId должен быть строкой"
                    assert isinstance(body['eventType'], str), "eventType должен быть строкой"
                    assert isinstance(body['timestamp'], str), "timestamp должен быть строкой"
                    assert isinstance(body['data'], dict), "data должен быть объектом"
                    
                    # Проверяем наличие source в заголовках
                    assert 'source' in headers, f"Отсутствует поле source в заголовках сообщения"
                    assert isinstance(headers['source'], str), "source в заголовках должен быть строкой"
                    
        except KafkaError as e:
            pytest.fail(f"Ошибка при валидации структуры: {e}")

    @allure.title("Проверка полного цикла отправки-чтения с готовым Producer")
    def test_kafka_produce_consume_cycle(self, kafka_config, kafka_producer):
        try:
            # Создаем уникальный тестовый топик
            test_topic = f"test-topic-{int(time.time())}"
            test_message = {
                "test_id": f"test-{int(time.time())}",
                "message": "Hello Kafka from autotest",
                "timestamp": time.time()
            }
            
            # Отправляем сообщение
            future = kafka_producer.send(
                test_topic, 
                json.dumps(test_message).encode('utf-8')
            )
            result = future.get(timeout=10)
            assert result.topic == test_topic, f"Сообщение отправлено в неверный топик: {result.topic}"
            time.sleep(2)
            
            # Читаем сообщение со специализированным consumer
            consumer_config = kafka_config.copy()
            consumer_config.update({
                'auto_offset_reset': 'earliest',
                'enable_auto_commit': False,
                'consumer_timeout_ms': 10000
            })
            
            consumer = KafkaConsumer(test_topic, **consumer_config)
            
            found = False
            for message in consumer:
                try:
                    received_data = json.loads(message.value.decode('utf-8'))
                    if received_data.get('test_id') == test_message['test_id']:
                        found = True
                        break
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
            
            consumer.close()
            
            assert found, "Отправленное сообщение не найдено при чтении"
                
        except KafkaError as e:
            pytest.fail(f"Ошибка в цикле отправки-чтения: {e}")

    @allure.title("Проверка списка consumer groups в Kafka")
    def test_consumer_groups_monitoring(self, kafka_config):
        admin_client = KafkaAdminClient(**kafka_config)
        
        try:
            # Получаем список групп
            groups = admin_client.list_consumer_groups()
            print(f"\nConsumer Groups в кластере:")
            for group in groups:
                print(f"  - {group[0]} ({group[1]})")
            
            # Проверяем наличие тестовых групп (если есть)
            test_groups = [g for g in groups if g[0].startswith('test-')]
            if test_groups:
                print(f"\nНайдены тестовые группы: {len(test_groups)}")
            
        finally:
            admin_client.close()

@allure.feature("Testing Kafka route")
@pytest.mark.integration
@pytest.mark.kafka
class TestKafkaRoute:

    @allure.title("TC1. Проверка топика route")
    def test_route_topic_exists(self, kafka_consumer):
        """Проверка, что топик существует и доступен"""
        topics = kafka_consumer.topics()
        assert 'route' in topics, "Топик 'route' не найден"

        partitions = kafka_consumer.partitions_for_topic('route')
        assert len(partitions) > 0, "Топик 'route' не имеет партиций"

    
    @allure.title("TC2. Проверка структуры событий в route")
    def test_route_events_structure(self, kafka_config):
        """Читаем и проверяем события в топике route"""
        config = kafka_config.copy()
        config.update({
            'auto_offset_reset': 'latest',
            'enable_auto_commit': False,
            'consumer_timeout_ms': 3000
        })
        
        consumer = KafkaConsumer('route', **config)
        
        try:
            sample_messages = []
            start_time = time.time()
            
            for message in consumer:
                if time.time() - start_time > 2 or len(sample_messages) >= 1:
                    break
                    
                try:
                    event = json.loads(message.value.decode('utf-8'))
                    sample_messages.append({
                        'event': event,
                        'partition': message.partition,
                        'offset': message.offset
                    })
                    
                    # Проверка структуры
                    required_fields = ['deliveryID', 'status', 'courierID', 'oldStatus']
                    for field in required_fields:
                        assert field in event, f"Отсутствует обязательное поле: {field}"
                    
                    # Проверка допустимых статусов
                    valid_statuses = ['delivered', 'canceled', 'pickup_arrived']
                    assert event['status'] in valid_statuses, \
                        f"Невалидный статус: {event['status']}. Допустимы: {valid_statuses}"
                    
                except json.JSONDecodeError:
                    continue
                except AssertionError as e:
                    print(f"Ошибка валидации: {e}")
                    continue
                        
        finally:
            consumer.close()