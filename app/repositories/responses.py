"""
Репозиторий для работы с участием (UCHASTIE) и ответами (OTVET).
CRUD операции без использования ORM.
"""

from app.db import fetchall, fetchone, execute, transaction


def create_uchastie(opros_id, respondent_id):
    """Создать запись об участии респондента в опросе."""
    query = """
        INSERT INTO UCHASTIE (ID_OPROSA, ID_RESPONDENTA)
        VALUES (%s, %s)
        RETURNING ID_UCHASTIYA
    """
    try:
        with transaction() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (opros_id, respondent_id))
                result = cursor.fetchone()
                return result[0] if result else None
    except Exception as e:
        # Проверяем, не дублируется ли участие
        if 'UCHASTIE_OPROS_RESPONDENT_UNIQUE' in str(e) or 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            raise ValueError("Респондент уже участвует в этом опросе")
        raise


def has_uchastie(opros_id, respondent_id):
    """Проверить, участвует ли респондент в опросе."""
    query = """
        SELECT COUNT(*) AS "count"
        FROM UCHASTIE
        WHERE ID_OPROSA = %s AND ID_RESPONDENTA = %s
    """
    result = fetchone(query, (opros_id, respondent_id))
    return result['count'] > 0 if result else False


def get_existing_otvet(opros_id, vopros_id, respondent_id):
    """Получить существующий ответ респондента на вопрос."""
    query = """
        SELECT ID_OTVETA AS "id_otveta", ID_VARIANTA AS "id_varianta"
        FROM OTVET
        WHERE ID_OPROSA = %s AND ID_VOPROSA = %s AND ID_RESPONDENTA = %s
    """
    return fetchone(query, (opros_id, vopros_id, respondent_id))


def update_otvet(otvet_id, variant_id):
    """Обновить существующий ответ."""
    query = """
        UPDATE OTVET
        SET ID_VARIANTA = %s, DATA_OTVETA = CURRENT_TIMESTAMP
        WHERE ID_OTVETA = %s
    """
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (variant_id, otvet_id))
            return cursor.rowcount > 0


def create_or_update_otvet(opros_id, vopros_id, respondent_id, variant_id):
    """Создать или обновить ответ респондента."""
    # Проверяем, есть ли уже ответ
    existing = get_existing_otvet(opros_id, vopros_id, respondent_id)
    
    if existing:
        # Обновляем существующий ответ
        update_otvet(existing['id_otveta'], variant_id)
        return existing['id_otveta']
    else:
        # Создаём новый ответ
        query = """
            INSERT INTO OTVET (ID_OPROSA, ID_VOPROSA, ID_RESPONDENTA, ID_VARIANTA)
            VALUES (%s, %s, %s, %s)
            RETURNING ID_OTVETA
        """
        try:
            with transaction() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (opros_id, vopros_id, respondent_id, variant_id))
                    result = cursor.fetchone()
                    return result[0] if result else None
        except Exception as e:
            # Проверяем, не дублируется ли ответ
            if 'OTVET_OPROS_VOPROS_RESPONDENT_UNIQUE' in str(e) or 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
                raise ValueError("Респондент уже ответил на этот вопрос")
            raise


def create_otvet(opros_id, vopros_id, respondent_id, variant_id):
    """Создать ответ респондента (для обратной совместимости)."""
    return create_or_update_otvet(opros_id, vopros_id, respondent_id, variant_id)


def get_by_opros(opros_id):
    """Получить все ответы по опросу."""
    query = """
        SELECT 
            o.ID_OTVETA AS "id_otveta", o.ID_OPROSA AS "id_oprosa", 
            o.ID_VOPROSA AS "id_voprosa", o.ID_RESPONDENTA AS "id_respondenta", 
            o.ID_VARIANTA AS "id_varianta", o.DATA_OTVETA AS "data_otveta",
            v.TEKST_VOPROSA AS "tekst_voprosa",
            vo.TEKST_VARIANTA AS "tekst_varianta",
            vo.PRIZNAK_POLOZH AS "priznak_polozh"
        FROM OTVET o
        INNER JOIN VOPROS v ON o.ID_VOPROSA = v.ID_VOPROSA
        INNER JOIN VARIANT_OTVETA vo ON o.ID_VARIANTA = vo.ID_VARIANTA
        WHERE o.ID_OPROSA = %s
        ORDER BY o.DATA_OTVETA DESC
    """
    return fetchall(query, (opros_id,))


def get_by_respondent_and_opros(respondent_id, opros_id):
    """Получить ответы респондента по опросу."""
    query = """
        SELECT 
            o.ID_OTVETA AS "id_otveta", o.ID_OPROSA AS "id_oprosa", 
            o.ID_VOPROSA AS "id_voprosa", o.ID_RESPONDENTA AS "id_respondenta", 
            o.ID_VARIANTA AS "id_varianta", o.DATA_OTVETA AS "data_otveta",
            v.TEKST_VOPROSA AS "tekst_voprosa",
            vo.TEKST_VARIANTA AS "tekst_varianta"
        FROM OTVET o
        INNER JOIN VOPROS v ON o.ID_VOPROSA = v.ID_VOPROSA
        INNER JOIN VARIANT_OTVETA vo ON o.ID_VARIANTA = vo.ID_VARIANTA
        WHERE o.ID_RESPONDENTA = %s AND o.ID_OPROSA = %s
        ORDER BY v.PORYADOK
    """
    return fetchall(query, (respondent_id, opros_id))


def has_answered(respondent_id, opros_id, vopros_id):
    """Проверить, ответил ли респондент на вопрос."""
    query = """
        SELECT COUNT(*) AS "count"
        FROM OTVET
        WHERE ID_RESPONDENTA = %s AND ID_OPROSA = %s AND ID_VOPROSA = %s
    """
    result = fetchone(query, (respondent_id, opros_id, vopros_id))
    return result['count'] > 0 if result else False


def get_answered_voprosy(respondent_id, opros_id):
    """Получить список ID вопросов, на которые уже ответил респондент."""
    query = """
        SELECT ID_VOPROSA AS "id_voprosa"
        FROM OTVET
        WHERE ID_RESPONDENTA = %s AND ID_OPROSA = %s
    """
    results = fetchall(query, (respondent_id, opros_id))
    return [r['id_voprosa'] for r in results]


def delete_otvet(otvet_id):
    """Удалить ответ."""
    query = "DELETE FROM OTVET WHERE ID_OTVETA = %s"
    with transaction() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (otvet_id,))
            return cursor.rowcount > 0
