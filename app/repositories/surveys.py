"""
Репозиторий для работы с опросами (OPROS).
CRUD операции без использования ORM.
"""

from app.db import fetchall, fetchone, execute, transaction


def get_all():
    """Получить все опросы."""
    query = """
        SELECT 
            ID_OPROSA AS "id_oprosa", TEMA AS "tema", OPISANIE AS "opisanie", 
            DATA_NACHALA AS "data_nachala", DATA_OKONCH_PLN AS "data_okonch_pln", 
            DATA_OKONCH_FAKT AS "data_okonch_fakt", MIN_KOL_OTVETOV AS "min_kol_otvetov", 
            STATUS AS "status"
        FROM OPROS
        ORDER BY DATA_NACHALA DESC
    """
    return fetchall(query)


def get_by_id(opros_id):
    """Получить опрос по ID."""
    query = """
        SELECT 
            ID_OPROSA AS "id_oprosa", TEMA AS "tema", OPISANIE AS "opisanie", 
            DATA_NACHALA AS "data_nachala", DATA_OKONCH_PLN AS "data_okonch_pln", 
            DATA_OKONCH_FAKT AS "data_okonch_fakt", MIN_KOL_OTVETOV AS "min_kol_otvetov", 
            STATUS AS "status"
        FROM OPROS
        WHERE ID_OPROSA = %s
    """
    return fetchone(query, (opros_id,))


def create(tema, opisanie, data_nachala, data_okonch_pln, min_kol_otvetov, status='draft'):
    """Создать новый опрос."""
    query = """
        INSERT INTO OPROS (TEMA, OPISANIE, DATA_NACHALA, DATA_OKONCH_PLN, MIN_KOL_OTVETOV, STATUS)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING ID_OPROSA
    """
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (tema, opisanie, data_nachala, data_okonch_pln, min_kol_otvetov, status))
            result = cursor.fetchone()
            return result[0] if result else None


def update(opros_id, tema, opisanie, data_nachala, data_okonch_pln, min_kol_otvetov, status):
    """Обновить опрос."""
    query = """
        UPDATE OPROS
        SET TEMA = %s, OPISANIE = %s, DATA_NACHALA = %s, DATA_OKONCH_PLN = %s, 
            MIN_KOL_OTVETOV = %s, STATUS = %s
        WHERE ID_OPROSA = %s
    """
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (tema, opisanie, data_nachala, data_okonch_pln, min_kol_otvetov, status, opros_id))
            return cursor.rowcount > 0


def delete(opros_id):
    """Удалить опрос."""
    query = "DELETE FROM OPROS WHERE ID_OPROSA = %s"
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (opros_id,))
            return cursor.rowcount > 0


def activate(opros_id):
    """Активировать опрос."""
    query = "UPDATE OPROS SET STATUS = 'active' WHERE ID_OPROSA = %s"
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (opros_id,))
            return cursor.rowcount > 0


def close(opros_id):
    """Закрыть опрос (триггер может продлить срок при недостатке участников)."""
    query = "UPDATE OPROS SET STATUS = 'closed' WHERE ID_OPROSA = %s"
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (opros_id,))
            return cursor.rowcount > 0


def get_active():
    """Получить все активные опросы."""
    query = """
        SELECT 
            ID_OPROSA AS "id_oprosa", TEMA AS "tema", OPISANIE AS "opisanie", 
            DATA_NACHALA AS "data_nachala", DATA_OKONCH_PLN AS "data_okonch_pln", 
            DATA_OKONCH_FAKT AS "data_okonch_fakt", MIN_KOL_OTVETOV AS "min_kol_otvetov", 
            STATUS AS "status"
        FROM OPROS
        WHERE STATUS = 'active'
        ORDER BY DATA_NACHALA DESC
    """
    return fetchall(query)
