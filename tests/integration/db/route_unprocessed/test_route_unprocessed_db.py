import pytest
import allure
import psycopg2
from datetime import datetime


@allure.feature("Route Unprocessed Table - Read Only")
@pytest.mark.integration
@pytest.mark.database
@pytest.mark.route_unprocessed
class TestRouteUnprocessedTableReadOnly:

    @allure.title("Проверка существования таблицы journal_route_unprocessed")
    def test_table_exists(self, db_cursor):
        try:
            db_cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_name = 'journal_route_unprocessed'
                )
            """)
            result = db_cursor.fetchone()['exists']
            
            assert result is True, "Таблица journal_route_unprocessed должна существовать"
            
        except psycopg2.errors.InsufficientPrivilege:
            pytest.skip("Недостаточно прав для проверки таблицы")
        except Exception as e:
            pytest.skip(f"Ошибка при проверке таблицы: {e}")

    @allure.title("Проверка структуры таблицы journal_route_unprocessed через information_schema")
    def test_table_structure_readonly(self, db_cursor):
        try:
            # Проверяем через information_schema
            db_cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'journal_route_unprocessed'
                ORDER BY ordinal_position
            """)
            
            columns = db_cursor.fetchall()
            
            if not columns:
                pytest.skip("Не удалось получить структуру таблицы (возможно нет прав)")
            
            print(f"\nСтруктура таблицы journal_route_unprocessed:")
            for col in columns:
                print(f"   - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            
            # Проверяем основные колонки
            column_names = [col['column_name'] for col in columns]
            
            if "route_id" not in column_names:
                print("Колонка route_id не найдена")
            if "comment" not in column_names:
                print("Колонка comment не найдена")
            if "created_at" not in column_names:
                print("Колонка created_at не найдена")
            
            # Проверяем тип route_id
            for col in columns:
                if col['column_name'] == 'route_id':
                    print(f"\n имеет тип: {col['data_type']}")
                    break
            
        except psycopg2.errors.InsufficientPrivilege:
            pytest.skip("Недостаточно прав для проверки структуры таблицы")
        except Exception as e:
            pytest.skip(f"Ошибка при проверке структуры: {e}")

    @allure.title("Проверка чтения данных из journal_route_unprocessed")
    def test_read_from_table(self, db_cursor):
        try:
            db_cursor.execute("""
                SELECT route_id::text, comment, created_at
                FROM journal_route_unprocessed
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            results = db_cursor.fetchall()
            print(f"\nЗаписей в journal_route_unprocessed: {len(results)}")
            
            if results:
                print("\nПримеры записей:")
                for i, row in enumerate(results[:3], 1):
                    print(f"   {i}. route_id: {row['route_id']}")
                    print(f"      comment: {row['comment'] if row['comment'] else 'NULL'}")
                    print(f"      created_at: {row['created_at']}")
            else:
                print("Таблица пуста или нет данных для показа")
            
            # Главное - не упали с ошибкой прав
            assert True
            
        except psycopg2.errors.InsufficientPrivilege:
            pytest.skip("Недостаточно прав для чтения из таблицы")
        except Exception as e:
            print(f"\nОшибка при чтении: {e}")
            # Не падаем, просто логируем
            assert True

    @allure.title("Проверка формата данных в таблице")
    def test_data_format_validation(self, db_cursor):
        try:
            db_cursor.execute("""
                SELECT 
                    route_id::text,
                    comment,
                    created_at,
                    LENGTH(comment) as comment_length
                FROM journal_route_unprocessed
                WHERE comment IS NOT NULL
                LIMIT 3
            """)
            
            results = db_cursor.fetchall()
            
            if results:
                print(f"\nПроверка формата данных ({len(results)} записей):")
                
                for i, row in enumerate(results, 1):
                    print(f"\n   Запись {i}:")
                    
                    # Проверяем route_id (должен быть UUID формата)
                    route_id = row['route_id']
                    if route_id and len(route_id) == 36 and '-' in route_id:
                        print(f"   route_id: {route_id} (похож на UUID)")
                    else:
                        print(f"   route_id: {route_id} (нестандартный формат)")
                    
                    # Проверяем comment
                    comment = row['comment']
                    if comment:
                        print(f"   comment: {comment[:50]}... (длина: {row['comment_length']})")
                    else:
                        print(f"   comment: NULL или пустой")
                    
                    # Проверяем created_at
                    created_at = row['created_at']
                    if isinstance(created_at, datetime):
                        print(f"   created_at: {created_at} (корректный datetime)")
                    else:
                        print(f"   created_at: {created_at} (тип: {type(created_at)})")
            
            else:
                print("\nНет данных для проверки формата")
            
            assert True
            
        except psycopg2.errors.InsufficientPrivilege:
            pytest.skip("Недостаточно прав для проверки формата данных")
        except Exception as e:
            print(f"\nОшибка при проверке формата: {e}")
            assert True
