"""
Модуль для работы с базой данных PostgreSQL.
Обеспечивает подключение, выполнение запросов и управление транзакциями.
"""

import os
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Глобальный пул соединений
_connection_pool = None


def init_pool():
    """Инициализация пула соединений с БД."""
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'survey_db'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', '12345678')
            )
        except Exception as e:
            raise ConnectionError(f"Не удалось создать пул соединений: {e}")


def get_connection():
    """Получить соединение из пула."""
    if _connection_pool is None:
        init_pool()
    return _connection_pool.getconn()


def return_connection(conn):
    """Вернуть соединение в пул."""
    if _connection_pool:
        _connection_pool.putconn(conn)


@contextmanager
def get_db_connection():
    """
    Контекстный менеджер для работы с БД.
    Автоматически получает и возвращает соединение.
    """
    conn = None
    try:
        conn = get_connection()
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            return_connection(conn)


@contextmanager
def transaction():
    """
    Контекстный менеджер для транзакций.
    Автоматически коммитит при успехе или откатывает при ошибке.
    """
    conn = None
    try:
        conn = get_connection()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            return_connection(conn)


def execute(query, params=None, fetch=False):
    """
    Выполнить SQL-запрос.
    
    Args:
        query: SQL-запрос (строка)
        params: Параметры запроса (кортеж или словарь)
        fetch: Если True, возвращает результат fetchall()
    
    Returns:
        Результат запроса или None
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return None


def fetchone(query, params=None):
    """
    Выполнить запрос и вернуть одну строку.
    
    Args:
        query: SQL-запрос
        params: Параметры запроса
    
    Returns:
        Словарь с результатом или None
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()


def fetchall(query, params=None):
    """
    Выполнить запрос и вернуть все строки.
    
    Args:
        query: SQL-запрос
        params: Параметры запроса
    
    Returns:
        Список словарей с результатами
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def execute_many(query, params_list):
    """
    Выполнить запрос для множества параметров.
    
    Args:
        query: SQL-запрос
        params_list: Список кортежей параметров
    """
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, params_list)


def close_pool():
    """Закрыть пул соединений."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None
