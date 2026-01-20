"""
Репозиторий для генерации отчётов.
Все запросы используют только агрегированные данные без ФИО респондентов.
Соответствует новой ER-модели.
"""

from app.db import fetchall, fetchone, execute


def get_all_surveys_list():
    """
    Отчёт a) Список всех опросов: тема, даты, количество участников.
    Участники считаются по таблице UCHASTIE.
    """
    query = """
        SELECT 
            o.ID_OPROSA AS "id_oprosa",
            o.TEMA AS "tema",
            o.DATA_NACHALA AS "data_nachala",
            o.DATA_OKONCH_PLN AS "data_okonch_pln",
            o.DATA_OKONCH_FAKT AS "data_okonch_fakt",
            o.STATUS AS "status",
            COUNT(DISTINCT u.ID_RESPONDENTA) AS "participants_count"
        FROM OPROS o
        LEFT JOIN UCHASTIE u ON u.ID_OPROSA = o.ID_OPROSA
        GROUP BY o.ID_OPROSA, o.TEMA, o.DATA_NACHALA, o.DATA_OKONCH_PLN, o.DATA_OKONCH_FAKT, o.STATUS
        ORDER BY o.DATA_NACHALA DESC
        LIMIT 50
    """
    return fetchall(query)


def get_answer_distribution(opros_id):
    """
    Отчёт b) Распределение ответов по каждому вопросу выбранного опроса.
    Использует OTVET → VARIANT_OTVETA.
    """
    query = """
        SELECT 
            v.ID_VOPROSA AS "id_voprosa",
            v.TEKST_VOPROSA AS "tekst_voprosa",
            v.PORYADOK AS "poryadok",
            vo.ID_VARIANTA AS "id_varianta",
            vo.TEKST_VARIANTA AS "tekst_varianta",
            vo.PRIZNAK_POLOZH AS "priznak_polozh",
            COUNT(o.ID_OTVETA) AS "answer_count",
            ROUND(
                COUNT(o.ID_OTVETA)::NUMERIC / NULLIF(
                    (SELECT COUNT(*) FROM OTVET o2 WHERE o2.ID_VOPROSA = v.ID_VOPROSA AND o2.ID_OPROSA = %s), 
                    0
                ) * 100, 
                2
            ) AS "percentage"
        FROM VOPROS v
        INNER JOIN VARIANT_OTVETA vo ON vo.ID_VOPROSA = v.ID_VOPROSA
        LEFT JOIN OTVET o ON o.ID_VARIANTA = vo.ID_VARIANTA AND o.ID_VOPROSA = v.ID_VOPROSA AND o.ID_OPROSA = %s
        WHERE v.ID_OPROSA = %s
        GROUP BY v.ID_VOPROSA, v.TEKST_VOPROSA, v.PORYADOK, vo.ID_VARIANTA, vo.TEKST_VARIANTA, vo.PRIZNAK_POLOZH, vo.PORYADOK
        ORDER BY v.PORYADOK, vo.PORYADOK
    """
    return fetchall(query, (opros_id, opros_id, opros_id))


def get_topic_dynamics(tema, start_date=None, end_date=None):
    """
    Отчёт c) Динамика изменения отношения к теме за период.
    Агрегация по неделям, доля положительных ответов.
    PRIZNAK_POLOZH = 1 означает положительный ответ.
    """
    query = """
        SELECT 
            DATE_TRUNC('week', o.DATA_OTVETA)::DATE AS "week_start",
            COUNT(*) FILTER (WHERE vo.PRIZNAK_POLOZH = 1) AS "positive_count",
            COUNT(*) AS "total_count",
            ROUND(
                COUNT(*) FILTER (WHERE vo.PRIZNAK_POLOZH = 1)::NUMERIC / 
                NULLIF(COUNT(*), 0) * 100, 
                2
            ) AS "positive_percentage"
        FROM OTVET o
        INNER JOIN OPROS op ON o.ID_OPROSA = op.ID_OPROSA
        INNER JOIN VARIANT_OTVETA vo ON o.ID_VARIANTA = vo.ID_VARIANTA
        WHERE op.TEMA = %s
    """
    params = [tema]
    
    if start_date:
        query += " AND o.DATA_OTVETA >= %s"
        params.append(start_date)
    if end_date:
        query += " AND o.DATA_OTVETA <= %s"
        params.append(end_date)
    
    query += """
        GROUP BY DATE_TRUNC('week', o.DATA_OTVETA)
        ORDER BY week_start
        LIMIT 50
    """
    
    return fetchall(query, tuple(params))


def get_respondent_statistics():
    """
    Отчёт d) Статистика по участию респондентов в опросах.
    Использует RESPONDENT + UCHASTIE.
    ФИО НЕ выводится (анонимность).
    """
    query = """
        SELECT 
            r.ID_RESPONDENTA AS "id_respondenta",
            r.DATA_ROZHDENIYA AS "data_rozhdeniya",
            EXTRACT(YEAR FROM AGE(r.DATA_ROZHDENIYA)) AS "age",
            p.NAIMENOVANIE AS "gender",
            reg.NAIMENOVANIE AS "region",
            u.NAIMENOVANIE AS "education_level",
            COUNT(DISTINCT uch.ID_OPROSA) AS "surveys_count",
            COUNT(o.ID_OTVETA) AS "total_answers_count"
        FROM RESPONDENT r
        INNER JOIN POL p ON r.ID_POLA = p.ID_POLA
        INNER JOIN REGION reg ON r.ID_REGIONA = reg.ID_REGIONA
        INNER JOIN UROVEN_OBRAZOVANIYA u ON r.ID_UROVNYA = u.ID_UROVNYA
        LEFT JOIN UCHASTIE uch ON uch.ID_RESPONDENTA = r.ID_RESPONDENTA
        LEFT JOIN OTVET o ON o.ID_RESPONDENTA = r.ID_RESPONDENTA
        GROUP BY r.ID_RESPONDENTA, r.DATA_ROZHDENIYA, p.NAIMENOVANIE, reg.NAIMENOVANIE, u.NAIMENOVANIE
        ORDER BY surveys_count DESC, total_answers_count DESC
        LIMIT 50
    """
    return fetchall(query)


def get_average_age_by_survey():
    """
    Отчёт e) Средний возраст участников по каждому опросу.
    Возраст считается по DATA_ROZHDENIYA.
    Участники считаются по UCHASTIE.
    """
    query = """
        SELECT 
            o.ID_OPROSA AS "id_oprosa",
            o.TEMA AS "tema",
            COUNT(DISTINCT u.ID_RESPONDENTA) AS "participants_count",
            ROUND(AVG(EXTRACT(YEAR FROM AGE(r.DATA_ROZHDENIYA))), 2) AS "average_age",
            MIN(EXTRACT(YEAR FROM AGE(r.DATA_ROZHDENIYA))) AS "min_age",
            MAX(EXTRACT(YEAR FROM AGE(r.DATA_ROZHDENIYA))) AS "max_age"
        FROM OPROS o
        INNER JOIN UCHASTIE u ON u.ID_OPROSA = o.ID_OPROSA
        INNER JOIN RESPONDENT r ON u.ID_RESPONDENTA = r.ID_RESPONDENTA
        GROUP BY o.ID_OPROSA, o.TEMA
        ORDER BY o.DATA_NACHALA DESC
        LIMIT 50
    """
    return fetchall(query)


def get_positive_surveys(threshold=70.0):
    """
    Отчёт f) Список опросов, в которых доля положительных ответов > threshold%.
    PRIZNAK_POLOZH = 1 означает положительный ответ.
    """
    query = """
        SELECT 
            o.ID_OPROSA AS "id_oprosa",
            o.TEMA AS "tema",
            o.DATA_NACHALA AS "data_nachala",
            o.DATA_OKONCH_PLN AS "data_okonch_pln",
            COUNT(*) FILTER (WHERE vo.PRIZNAK_POLOZH = 1) AS "positive_count",
            COUNT(*) AS "total_count",
            ROUND(
                COUNT(*) FILTER (WHERE vo.PRIZNAK_POLOZH = 1)::NUMERIC / 
                NULLIF(COUNT(*), 0) * 100, 
                2
            ) AS "positive_percentage"
        FROM OPROS o
        INNER JOIN OTVET ot ON ot.ID_OPROSA = o.ID_OPROSA
        INNER JOIN VARIANT_OTVETA vo ON ot.ID_VARIANTA = vo.ID_VARIANTA
        GROUP BY o.ID_OPROSA, o.TEMA, o.DATA_NACHALA, o.DATA_OKONCH_PLN
        HAVING 
            ROUND(
                COUNT(*) FILTER (WHERE vo.PRIZNAK_POLOZH = 1)::NUMERIC / 
                NULLIF(COUNT(*), 0) * 100, 
                2
            ) > %s
        ORDER BY positive_percentage DESC
        LIMIT 50
    """
    return fetchall(query, (threshold,))


def generate_xml_report(opros_id):
    """
    Отчёт g) Формирование сводного XML-отчёта по итогам опроса.
    Вызывает функцию БД GENERIROVAT_XML_OTCHET.
    """
    query = 'SELECT GENERIROVAT_XML_OTCHET(%s) AS "xml_content"'
    result = fetchone(query, (opros_id,))
    return result['xml_content'] if result else None
