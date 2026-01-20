"""
Репозиторий для работы с респондентами (RESPONDENT) и справочниками.
CRUD операции без использования ORM.
"""

from app.db import fetchall, fetchone, execute, transaction


def get_all_pol():
    """Получить все значения справочника полов."""
    query = 'SELECT ID_POLA AS "id_pola", NAIMENOVANIE AS "naimenovanie" FROM POL ORDER BY ID_POLA'
    return fetchall(query)


def get_all_region():
    """Получить все значения справочника регионов."""
    query = 'SELECT ID_REGIONA AS "id_regiona", NAIMENOVANIE AS "naimenovanie" FROM REGION ORDER BY NAIMENOVANIE'
    return fetchall(query)


def get_all_uroven():
    """Получить все значения справочника уровней образования."""
    query = 'SELECT ID_UROVNYA AS "id_urovnya", NAIMENOVANIE AS "naimenovanie" FROM UROVEN_OBRAZOVANIYA ORDER BY ID_UROVNYA'
    return fetchall(query)


def get_all():
    """Получить всех респондентов (без ФИО для анонимности в отчётах)."""
    query = """
        SELECT 
            r.ID_RESPONDENTA AS "id_respondenta", 
            r.DATA_ROZHDENIYA AS "data_rozhdeniya", 
            p.NAIMENOVANIE AS "pol",
            reg.NAIMENOVANIE AS "region", 
            u.NAIMENOVANIE AS "uroven_obrazovaniya",
            EXTRACT(YEAR FROM AGE(r.DATA_ROZHDENIYA)) AS "age"
        FROM RESPONDENT r
        INNER JOIN POL p ON r.ID_POLA = p.ID_POLA
        INNER JOIN REGION reg ON r.ID_REGIONA = reg.ID_REGIONA
        INNER JOIN UROVEN_OBRAZOVANIYA u ON r.ID_UROVNYA = u.ID_UROVNYA
        ORDER BY r.ID_RESPONDENTA DESC
    """
    return fetchall(query)


def get_by_id(respondent_id):
    """Получить респондента по ID (включая ФИО для редактирования)."""
    query = """
        SELECT 
            r.ID_RESPONDENTA AS "id_respondenta",
            r.FAMILIYA AS "familiya",
            r.IMYA AS "imya",
            r.OTCHESTVO AS "otchestvo",
            r.DATA_ROZHDENIYA AS "data_rozhdeniya",
            r.ID_POLA AS "id_pola",
            r.ID_REGIONA AS "id_regiona",
            r.ID_UROVNYA AS "id_urovnya",
            p.NAIMENOVANIE AS "pol",
            reg.NAIMENOVANIE AS "region",
            u.NAIMENOVANIE AS "uroven_obrazovaniya",
            EXTRACT(YEAR FROM AGE(r.DATA_ROZHDENIYA)) AS "age"
        FROM RESPONDENT r
        INNER JOIN POL p ON r.ID_POLA = p.ID_POLA
        INNER JOIN REGION reg ON r.ID_REGIONA = reg.ID_REGIONA
        INNER JOIN UROVEN_OBRAZOVANIYA u ON r.ID_UROVNYA = u.ID_UROVNYA
        WHERE r.ID_RESPONDENTA = %s
    """
    return fetchone(query, (respondent_id,))


def create(familiya, imya, otchestvo, data_rozhdeniya, id_pola, id_regiona, id_urovnya):
    """Создать нового респондента."""
    query = """
        INSERT INTO RESPONDENT (FAMILIYA, IMYA, OTCHESTVO, DATA_ROZHDENIYA, ID_POLA, ID_REGIONA, ID_UROVNYA)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING ID_RESPONDENTA
    """
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (familiya, imya, otchestvo, data_rozhdeniya, id_pola, id_regiona, id_urovnya))
            result = cursor.fetchone()
            return result[0] if result else None


def update(respondent_id, familiya, imya, otchestvo, data_rozhdeniya, id_pola, id_regiona, id_urovnya):
    """Обновить респондента."""
    query = """
        UPDATE RESPONDENT
        SET FAMILIYA = %s, IMYA = %s, OTCHESTVO = %s, DATA_ROZHDENIYA = %s, 
            ID_POLA = %s, ID_REGIONA = %s, ID_UROVNYA = %s
        WHERE ID_RESPONDENTA = %s
    """
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (familiya, imya, otchestvo, data_rozhdeniya, id_pola, id_regiona, id_urovnya, respondent_id))
            return cursor.rowcount > 0


def delete(respondent_id):
    """Удалить респондента."""
    query = "DELETE FROM RESPONDENT WHERE ID_RESPONDENTA = %s"
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (respondent_id,))
            return cursor.rowcount > 0
