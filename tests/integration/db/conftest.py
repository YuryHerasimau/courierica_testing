import pytest
import psycopg2
from psycopg2.extras import RealDictCursor

from settings import settings


@pytest.fixture(scope="session")
def db_connection():
    """Создаем соединение с БД для тестов (только чтение)"""
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        
        # Проверяем, что можем хотя бы читать
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        yield conn
        conn.close()
        
    except psycopg2.OperationalError as e:
        pytest.skip(f"Нет подключения к БД: {e}")
    except psycopg2.Error as e:
        pytest.skip(f"Ошибка подключения к БД: {e}")

@pytest.fixture
def db_cursor(db_connection):
    """Курсор БД для тестов (только чтение)"""
    cursor = db_connection.cursor()
    yield cursor
    cursor.close()

# @pytest.fixture(autouse=True)
# def cleanup_test_data(db_connection):
#     """Автоматическая очистка тестовых данных"""
#     yield

#     with db_connection.cursor() as cursor:
#         cursor.execute("""
#             DELETE FROM journal_route_unprocessed 
#             WHERE route_id::text LIKE 'test_%'
#         """)
#         db_connection.commit()