import pytest
from kafka import KafkaConsumer, KafkaProducer


@pytest.fixture
def kafka_config():
    return {
        'bootstrap_servers': ['85.234.110.123:9092'],
        'security_protocol': 'SASL_PLAINTEXT',
        'sasl_mechanism': 'PLAIN',
        'sasl_plain_username': 'admin',
        'sasl_plain_password': 'thoo1maeCieg8aXiNgush7nah6aT9Te1',
        'api_version': (2, 8, 0)
    }

@pytest.fixture
def kafka_producer(kafka_config):
    """Kafka producer"""
    producer = KafkaProducer(**kafka_config)
    yield producer
    producer.close()


@pytest.fixture
def kafka_consumer(kafka_config):
    """Kafka consumer с базовой конфигурацией"""
    config = kafka_config.copy()
    config.update({
        'auto_offset_reset': 'earliest',
        'enable_auto_commit': False,
        'consumer_timeout_ms': 10000
    })
    
    consumer = KafkaConsumer(**config)
    yield consumer
    consumer.close()