-- ============================================
-- Функции PL/pgSQL для бизнес-логики
-- ============================================

-- Функция для продления срока опроса при недостатке участников
-- Вызывается триггером при попытке закрыть опрос
-- Использует таблицу UCHASTIE для подсчёта участников
CREATE OR REPLACE FUNCTION PRODLENIE_OPROSA_ESLI_NEKHVATAET()
RETURNS TRIGGER AS $$
DECLARE
    v_kol_uchastnikov INTEGER;
    v_deficit INTEGER;
    v_base_duration_days INTEGER;
    v_extension_days INTEGER;
    v_new_end_date DATE;
BEGIN
    -- Проверяем только при попытке закрыть опрос
    IF NEW.STATUS = 'closed' AND OLD.STATUS != 'closed' THEN
        
        -- Подсчитываем количество участников опроса из таблицы UCHASTIE
        SELECT COUNT(DISTINCT ID_RESPONDENTA)
        INTO v_kol_uchastnikov
        FROM UCHASTIE
        WHERE ID_OPROSA = NEW.ID_OPROSA;
        
        -- Если участников меньше минимально необходимого
        IF v_kol_uchastnikov < NEW.MIN_KOL_OTVETOV THEN
            
            -- Вычисляем дефицит участников
            v_deficit := NEW.MIN_KOL_OTVETOV - v_kol_uchastnikov;
            
            -- Вычисляем базовую длительность опроса в днях
            v_base_duration_days := GREATEST(1, NEW.DATA_OKONCH_PLN - NEW.DATA_NACHALA);
            
            -- Если нет ни одного участника - удваиваем срок
            IF v_kol_uchastnikov = 0 THEN
                v_extension_days := v_base_duration_days;
            ELSE
                -- Иначе продлеваем пропорционально дефициту
                -- Формула: ceil(deficit / min_kol_otvetov * base_duration_days)
                v_extension_days := CEIL(v_deficit::NUMERIC / NEW.MIN_KOL_OTVETOV::NUMERIC * v_base_duration_days::NUMERIC)::INTEGER;
            END IF;
            
            -- Вычисляем новую плановую дату окончания
            v_new_end_date := NEW.DATA_OKONCH_PLN + (v_extension_days || ' days')::INTERVAL;
            
            -- Продлеваем опрос и оставляем статус 'active'
            NEW.DATA_OKONCH_PLN := v_new_end_date;
            NEW.STATUS := 'active';
            
            -- Логируем действие
            RAISE NOTICE 'Опрос % продлён до % (недостаточно участников: % из %)', 
                NEW.ID_OPROSA, v_new_end_date, v_kol_uchastnikov, NEW.MIN_KOL_OTVETOV;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION PRODLENIE_OPROSA_ESLI_NEKHVATAET() IS 
'Функция продления опроса при недостатке участников. 
Если при попытке закрыть опрос участников меньше MIN_KOL_OTVETOV:
- Если участников 0: срок удваивается
- Иначе: срок продлевается пропорционально дефициту участников
Участники считаются по таблице UCHASTIE';

-- Функция для генерации XML-отчёта по опросу
-- Возвращает XML с агрегированными данными (без ФИО респондентов)
CREATE OR REPLACE FUNCTION GENERIROVAT_XML_OTCHET(p_id_oprosa INTEGER)
RETURNS XML AS $$
DECLARE
    v_xml XML;
    v_opros RECORD;
    v_uchastnikov_count INTEGER;
BEGIN
    -- Получаем информацию об опросе
    SELECT 
        o.ID_OPROSA,
        o.TEMA,
        o.DATA_NACHALA,
        o.DATA_OKONCH_PLN,
        o.DATA_OKONCH_FAKT,
        COUNT(DISTINCT u.ID_RESPONDENTA) as participants
    INTO v_opros
    FROM OPROS o
    LEFT JOIN UCHASTIE u ON u.ID_OPROSA = o.ID_OPROSA
    WHERE o.ID_OPROSA = p_id_oprosa
    GROUP BY o.ID_OPROSA, o.TEMA, o.DATA_NACHALA, o.DATA_OKONCH_PLN, o.DATA_OKONCH_FAKT;
    
    IF v_opros IS NULL THEN
        RAISE EXCEPTION 'Опрос с ID % не найден', p_id_oprosa;
    END IF;
    
    v_uchastnikov_count := COALESCE(v_opros.participants, 0);
    
    -- Формируем XML
    SELECT xmlelement(
        NAME "survey",
        xmlattributes(
            v_opros.ID_OPROSA AS "id",
            v_opros.TEMA AS "topic",
            v_opros.DATA_NACHALA AS "start_date",
            v_opros.DATA_OKONCH_PLN AS "end_date_planned",
            v_opros.DATA_OKONCH_FAKT AS "end_date_fact",
            v_uchastnikov_count AS "participants"
        ),
        (
            SELECT xmlagg(
                xmlelement(
                    NAME "question",
                    xmlattributes(
                        v.ID_VOPROSA AS "id",
                        v.TEKST_VOPROSA AS "text"
                    ),
                    (
                        SELECT xmlagg(
                            xmlelement(
                                NAME "option",
                                xmlattributes(
                                    vo.ID_VARIANTA AS "id",
                                    vo.TEKST_VARIANTA AS "text",
                                    COUNT(ot.ID_OTVETA) AS "count",
                                    CASE 
                                        WHEN (SELECT COUNT(*) FROM OTVET ot2 WHERE ot2.ID_VOPROSA = v.ID_VOPROSA AND ot2.ID_OPROSA = p_id_oprosa) > 0 THEN 
                                            ROUND(COUNT(ot.ID_OTVETA)::NUMERIC / 
                                                NULLIF((SELECT COUNT(*) FROM OTVET ot2 WHERE ot2.ID_VOPROSA = v.ID_VOPROSA AND ot2.ID_OPROSA = p_id_oprosa), 0) * 100, 2)
                                        ELSE 0 
                                    END AS "percent"
                                )
                            )
                            ORDER BY vo.PORYADOK
                        )
                        FROM VARIANT_OTVETA vo
                        LEFT JOIN OTVET ot ON ot.ID_VARIANTA = vo.ID_VARIANTA AND ot.ID_VOPROSA = v.ID_VOPROSA AND ot.ID_OPROSA = p_id_oprosa
                        WHERE vo.ID_VOPROSA = v.ID_VOPROSA
                        GROUP BY vo.ID_VARIANTA, vo.TEKST_VARIANTA, vo.PORYADOK
                    )
                )
                ORDER BY v.PORYADOK
            )
            FROM VOPROS v
            WHERE v.ID_OPROSA = p_id_oprosa
        )
    ) INTO v_xml;
    
    RETURN v_xml;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION GENERIROVAT_XML_OTCHET(INTEGER) IS 
'Генерирует XML-отчёт по опросу. 
Включает агрегированные данные по вопросам и вариантам ответов.
Не содержит персональных данных респондентов (ФИО).';
