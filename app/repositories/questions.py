"""
Репозиторий для работы с вопросами (VOPROS) и вариантами ответов (VARIANT_OTVETA).
CRUD операции без использования ORM.
"""

from app.db import fetchall, fetchone, execute, transaction


def get_by_opros(opros_id):
    """Получить все вопросы опроса."""
    query = """
        SELECT ID_VOPROSA AS "id_voprosa", ID_OPROSA AS "id_oprosa", 
               TEKST_VOPROSA AS "tekst_voprosa", TIP_VOPROSA AS "tip_voprosa", 
               PORYADOK AS "poryadok"
        FROM VOPROS
        WHERE ID_OPROSA = %s
        ORDER BY PORYADOK
    """
    return fetchall(query, (opros_id,))


def get_by_id(vopros_id):
    """Получить вопрос по ID."""
    query = """
        SELECT ID_VOPROSA AS "id_voprosa", ID_OPROSA AS "id_oprosa", 
               TEKST_VOPROSA AS "tekst_voprosa", TIP_VOPROSA AS "tip_voprosa", 
               PORYADOK AS "poryadok"
        FROM VOPROS
        WHERE ID_VOPROSA = %s
    """
    return fetchone(query, (vopros_id,))


def create(opros_id, tekst_voprosa, tip_voprosa='single_choice', poryadok=None):
    """Создать новый вопрос."""
    # Если poryadok не указан, берём максимальный + 1
    if poryadok is None:
        max_order_query = 'SELECT COALESCE(MAX(PORYADOK), 0) + 1 AS "next_order" FROM VOPROS WHERE ID_OPROSA = %s'
        max_order = fetchone(max_order_query, (opros_id,))
        poryadok = max_order['next_order'] if max_order else 1
    
    query = """
        INSERT INTO VOPROS (ID_OPROSA, TEKST_VOPROSA, TIP_VOPROSA, PORYADOK)
        VALUES (%s, %s, %s, %s)
        RETURNING ID_VOPROSA
    """
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (opros_id, tekst_voprosa, tip_voprosa, poryadok))
            result = cursor.fetchone()
            return result[0] if result else None


def update(vopros_id, tekst_voprosa, poryadok):
    """Обновить вопрос."""
    query = """
        UPDATE VOPROS
        SET TEKST_VOPROSA = %s, PORYADOK = %s
        WHERE ID_VOPROSA = %s
    """
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (tekst_voprosa, poryadok, vopros_id))
            return cursor.rowcount > 0


def delete(vopros_id):
    """Удалить вопрос."""
    query = "DELETE FROM VOPROS WHERE ID_VOPROSA = %s"
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (vopros_id,))
            return cursor.rowcount > 0


def get_variants(vopros_id):
    """Получить все варианты ответов для вопроса."""
    query = """
        SELECT ID_VARIANTA AS "id_varianta", ID_VOPROSA AS "id_voprosa", 
               TEKST_VARIANTA AS "tekst_varianta", PRIZNAK_POLOZH AS "priznak_polozh", 
               PORYADOK AS "poryadok"
        FROM VARIANT_OTVETA
        WHERE ID_VOPROSA = %s
        ORDER BY PORYADOK
    """
    return fetchall(query, (vopros_id,))


def create_variant(vopros_id, tekst_varianta, priznak_polozh=0, poryadok=None):
    """Создать вариант ответа."""
    if poryadok is None:
        max_order_query = 'SELECT COALESCE(MAX(PORYADOK), 0) + 1 AS "next_order" FROM VARIANT_OTVETA WHERE ID_VOPROSA = %s'
        max_order = fetchone(max_order_query, (vopros_id,))
        poryadok = max_order['next_order'] if max_order else 1
    
    query = """
        INSERT INTO VARIANT_OTVETA (ID_VOPROSA, TEKST_VARIANTA, PRIZNAK_POLOZH, PORYADOK)
        VALUES (%s, %s, %s, %s)
        RETURNING ID_VARIANTA
    """
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (vopros_id, tekst_varianta, priznak_polozh, poryadok))
            result = cursor.fetchone()
            return result[0] if result else None


def update_variant(variant_id, tekst_varianta, priznak_polozh, poryadok):
    """Обновить вариант ответа."""
    query = """
        UPDATE VARIANT_OTVETA
        SET TEKST_VARIANTA = %s, PRIZNAK_POLOZH = %s, PORYADOK = %s
        WHERE ID_VARIANTA = %s
    """
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (tekst_varianta, priznak_polozh, poryadok, variant_id))
            return cursor.rowcount > 0


def delete_variant(variant_id):
    """Удалить вариант ответа."""
    query = "DELETE FROM VARIANT_OTVETA WHERE ID_VARIANTA = %s"
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (variant_id,))
            return cursor.rowcount > 0
