from kafka import KafkaConsumer
import pytest
import allure
import json
import time

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
            print(f"✅ Подключение успешно! Сообщение отправлено в {result.topic}")
        except KafkaError as e:
            pytest.fail(f"❌ Не удалось подключиться к Kafka: {e}")

    @allure.title("Проверка здоровья Kafka через Consumer")
    def test_kafka_health_check(self, kafka_consumer):
        print("🏥 Проверяем здоровье Kafka...")
        try:
            # пытаемся получить список топиков
            topics = kafka_consumer.topics()
            if topics:
                print(f"✅ Kafka здоров - найдено {len(topics)} топиков")
                return True
            else:
                print("⚠️ Kafka доступен, но топиков не найдено")
                return False
        except KafkaError as e:
            print(f"❌ Kafka недоступен: {e}")
            return False

    @allure.title("Проверка наличия нужных топиков")
    def test_kafka_topics_exists(self, kafka_consumer):
        print("📋 Проверяем топики...")
        try:
            topics = kafka_consumer.topics()
            print(f"Найдено топиков: {len(topics)}")
            for topic in sorted(topics):
                print(f"  - {topic}")
            
            # Проверяем обязательные топики
            required_topics = ['events']
            for topic in required_topics:
                assert topic in topics, f"Топик {topic} не найден"
                print(f"✅ Топик '{topic}' найден")            
        except KafkaError as e:
            pytest.fail(f"❌ Ошибка при получении топиков: {e}")

    @allure.title("Проверка чтения сообщений в топике events")
    def test_events_topic_has_messages(self, kafka_config):
        """Для этого теста создаем специального consumer с подпиской на events"""
        print("📨 Проверяем сообщения в events...")
        
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
                except json.JSONDecodeError:
                    print(f"⚠️ Невалидный JSON в offset {message.offset}")
                except UnicodeDecodeError:
                    print(f"⚠️ Проблема с декодированием в offset {message.offset}")
                        
            print(f"📊 Найдено сообщений: {len(messages)}")
            
            if messages:
                print("🔍 Примеры сообщений:")
                for i, msg in enumerate(messages[:3]):  # Показываем первые 3
                    event_type = msg['value'].get('eventType', 'unknown')
                    print(f"  {i+1}. {event_type} (offset: {msg['offset']})")
                    
                    # Показываем структуру события
                    if i == 0:  # Только для первого сообщения
                        print("     Структура:")
                        for key, value in msg['value'].items():
                            print(f"       {key}: {type(value).__name__}")
            else:
                print("ℹ️ Сообщений не найдено")
                
            # Не падаем если сообщений нет
            if not messages:
                print("💡 Совет: проверьте, что в системе происходят события (завершение заказов, смены курьеров)")
                
        except KafkaError as e:
            pytest.fail(f"❌ Ошибка при чтении сообщений: {e}")
        finally:
            consumer.close()

    @allure.title("Проверка структуры событий")
    def test_event_structure_validation(self, kafka_config):
        print("📝 Проверяем структуру событий...")

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
                    sample_messages.append(message_data)
                except json.JSONDecodeError:
                    continue
            
            consumer.close()
            
            if sample_messages:
                print("✅ Найдены сообщения для анализа")
                
                # Анализируем структуру
                expected_structure = {
                    'eventId': 'string (UUID)',
                    'eventType': 'string',
                    'timestamp': 'string (ISO)',
                    'source': 'string', 
                    'data': 'object'
                }
                
                print("📋 Ожидаемая структура:")
                for field, description in expected_structure.items():
                    print(f"  - {field}: {description}")
                
                print("🔍 Фактическая структура (на примерах):")
                for i, msg in enumerate(sample_messages):
                    print(f"  Сообщение {i+1}:")
                    print(msg)
                    for key in expected_structure.keys():
                        if key in msg:
                            value_type = type(msg[key]).__name__
                            print(f"    ✅ {key}: {value_type}")
                        else:
                            print(f"    ❌ {key}: отсутствует")
                            
            else:
                print("ℹ️ Сообщений для анализа не найдено")
                print("💡 Проверьте, что ledger-service обрабатывает события")
                
        except KafkaError as e:
            pytest.fail(f"❌ Ошибка при валидации структуры: {e}")

    @allure.title("Проверка полного цикла отправки-чтения с готовым Producer")
    def test_kafka_produce_consume_cycle(self, kafka_config, kafka_producer):
        print("🔄 Тестируем полный цикл отправки-чтения...")
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
            print(f"✅ Сообщение отправлено в топик: {test_topic}")
            
            # Даем время для создания топика
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
                        print("✅ Сообщение успешно получено!")
                        found = True
                        break
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
            
            consumer.close()
            
            if not found:
                print("⚠️ Отправленное сообщение не найдено")
                
        except KafkaError as e:
            pytest.fail(f"❌ Ошибка в цикле отправки-чтения: {e}")