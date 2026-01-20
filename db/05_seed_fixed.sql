-- ============================================
-- Тестовые данные для демонстрации функциональности
-- Соответствует новой ER-модели
-- ============================================

-- Справочник полов
INSERT INTO POL (ID_POLA, NAIMENOVANIE) VALUES
(nextval('POL_ID_POLA_SEQ'), 'Мужской'),
(nextval('POL_ID_POLA_SEQ'), 'Женский'),
(nextval('POL_ID_POLA_SEQ'), 'Другое');

-- Справочник регионов
INSERT INTO REGION (ID_REGIONA, NAIMENOVANIE) VALUES
(nextval('REGION_ID_REGIONA_SEQ'), 'Москва'),
(nextval('REGION_ID_REGIONA_SEQ'), 'Санкт-Петербург'),
(nextval('REGION_ID_REGIONA_SEQ'), 'Новосибирск'),
(nextval('REGION_ID_REGIONA_SEQ'), 'Екатеринбург'),
(nextval('REGION_ID_REGIONA_SEQ'), 'Казань'),
(nextval('REGION_ID_REGIONA_SEQ'), 'Краснодар'),
(nextval('REGION_ID_REGIONA_SEQ'), 'Ростов-на-Дону'),
(nextval('REGION_ID_REGIONA_SEQ'), 'Воронеж'),
(nextval('REGION_ID_REGIONA_SEQ'), 'Самара'),
(nextval('REGION_ID_REGIONA_SEQ'), 'Нижний Новгород');

-- Справочник уровней образования
INSERT INTO UROVEN_OBRAZOVANIYA (ID_UROVNYA, NAIMENOVANIE) VALUES
(nextval('UROVEN_OBRAZOVANIYA_ID_UROVNYA_SEQ'), 'Среднее'),
(nextval('UROVEN_OBRAZOVANIYA_ID_UROVNYA_SEQ'), 'Среднее специальное'),
(nextval('UROVEN_OBRAZOVANIYA_ID_UROVNYA_SEQ'), 'Высшее'),
(nextval('UROVEN_OBRAZOVANIYA_ID_UROVNYA_SEQ'), 'Неоконченное высшее');

-- Респонденты (20 человек с разными характеристиками)
-- Получаем ID из справочников
INSERT INTO RESPONDENT (ID_RESPONDENTA, FAMILIYA, IMYA, OTCHESTVO, DATA_ROZHDENIYA, ID_POLA, ID_REGIONA, ID_UROVNYA) VALUES
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Иванов', 'Иван', 'Иванович', '1990-05-15', 1, 1, 3),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Петрова', 'Мария', 'Сергеевна', '1985-08-22', 2, 2, 3),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Сидоров', 'Петр', 'Александрович', '1995-03-10', 1, 3, 1),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Козлова', 'Анна', 'Дмитриевна', '1988-11-30', 2, 4, 3),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Морозов', 'Дмитрий', 'Викторович', '1992-07-18', 1, 1, 1),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Волкова', 'Елена', 'Павловна', '1987-01-25', 2, 5, 3),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Новиков', 'Сергей', 'Олегович', '1998-09-12', 1, 2, 1),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Лебедева', 'Ольга', 'Игоревна', '1983-04-05', 2, 1, 3),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Соколов', 'Андрей', 'Николаевич', '1991-12-20', 1, 6, 1),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Федорова', 'Татьяна', 'Владимировна', '1986-06-14', 2, 1, 3),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Михайлов', 'Алексей', 'Борисович', '1993-02-28', 1, 2, 3),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Павлова', 'Светлана', 'Юрьевна', '1989-10-08', 2, 7, 1),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Алексеев', 'Владимир', 'Петрович', '1996-08-03', 1, 1, 1),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Николаева', 'Ирина', 'Анатольевна', '1984-05-17', 2, 2, 3),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Орлов', 'Максим', 'Сергеевич', '1994-11-22', 1, 8, 3),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Романова', 'Юлия', 'Дмитриевна', '1997-07-09', 2, 1, 1),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Семенов', 'Игорь', 'Викторович', '1990-03-31', 1, 9, 3),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Титова', 'Наталья', 'Олеговна', '1985-09-16', 2, 2, 3),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Ушаков', 'Роман', 'Александрович', '1992-01-27', 1, 1, 1),
(nextval('RESPONDENT_ID_RESPONDENTA_SEQ'), 'Яковлева', 'Екатерина', 'Павловна', '1988-12-11', 2, 10, 3);

-- Опрос 1: "Отношение к цифровизации"
INSERT INTO OPROS (ID_OPROSA, TEMA, OPISANIE, DATA_NACHALA, DATA_OKONCH_PLN, MIN_KOL_OTVETOV, STATUS) VALUES
(nextval('OPROS_ID_OPROSA_SEQ'), 'Отношение к цифровизации', 'Изучение мнения населения о цифровизации', '2024-01-01', '2024-01-31', 15, 'active');

-- Вопросы для опроса 1
INSERT INTO VOPROS (ID_VOPROSA, ID_OPROSA, TEKST_VOPROSA, PORYADOK) VALUES
(nextval('VOPROS_ID_VOPROSA_SEQ'), 1, 'Считаете ли вы, что цифровизация улучшает качество жизни?', 1),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 1, 'Готовы ли вы полностью перейти на цифровые услуги?', 2),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 1, 'Обеспокоены ли вы проблемами кибербезопасности?', 3),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 1, 'Поддерживаете ли вы внедрение цифровых технологий в образование?', 4),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 1, 'Считаете ли вы, что цифровизация создаёт новые рабочие места?', 5);

-- Варианты ответов для опроса 1
INSERT INTO VARIANT_OTVETA (ID_VARIANTA, ID_VOPROSA, TEKST_VARIANTA, PRIZNAK_POLOZH, PORYADOK)
SELECT 
    nextval('VARIANT_OTVETA_ID_VARIANTA_SEQ'),
    v.ID_VOPROSA,
    opt.text,
    opt.is_positive,
    opt.order_no
FROM VOPROS v,
(VALUES 
    ('Да', 1, 1),
    ('Нет', 0, 2),
    ('Затрудняюсь ответить', 0, 3)
) AS opt(text, is_positive, order_no)
WHERE v.ID_OPROSA = 1;

-- Опрос 2: "Отношение к цифровизации" (вторая волна для динамики)
INSERT INTO OPROS (ID_OPROSA, TEMA, OPISANIE, DATA_NACHALA, DATA_OKONCH_PLN, MIN_KOL_OTVETOV, STATUS) VALUES
(nextval('OPROS_ID_OPROSA_SEQ'), 'Отношение к цифровизации', 'Изучение мнения населения о цифровизации (вторая волна)', '2024-02-01', '2024-02-28', 15, 'active');

-- Вопросы для опроса 2 (те же вопросы)
INSERT INTO VOPROS (ID_VOPROSA, ID_OPROSA, TEKST_VOPROSA, PORYADOK) VALUES
(nextval('VOPROS_ID_VOPROSA_SEQ'), 2, 'Считаете ли вы, что цифровизация улучшает качество жизни?', 1),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 2, 'Готовы ли вы полностью перейти на цифровые услуги?', 2),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 2, 'Обеспокоены ли вы проблемами кибербезопасности?', 3),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 2, 'Поддерживаете ли вы внедрение цифровых технологий в образование?', 4),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 2, 'Считаете ли вы, что цифровизация создаёт новые рабочие места?', 5);

-- Варианты ответов для опроса 2
INSERT INTO VARIANT_OTVETA (ID_VARIANTA, ID_VOPROSA, TEKST_VARIANTA, PRIZNAK_POLOZH, PORYADOK)
SELECT 
    nextval('VARIANT_OTVETA_ID_VARIANTA_SEQ'),
    v.ID_VOPROSA,
    opt.text,
    opt.is_positive,
    opt.order_no
FROM VOPROS v,
(VALUES 
    ('Да', 1, 1),
    ('Нет', 0, 2),
    ('Затрудняюсь ответить', 0, 3)
) AS opt(text, is_positive, order_no)
WHERE v.ID_OPROSA = 2;

-- Опрос 3: "Экологическая сознательность"
INSERT INTO OPROS (ID_OPROSA, TEMA, OPISANIE, DATA_NACHALA, DATA_OKONCH_PLN, MIN_KOL_OTVETOV, STATUS) VALUES
(nextval('OPROS_ID_OPROSA_SEQ'), 'Экологическая сознательность', 'Изучение экологической сознательности населения', '2024-03-01', '2024-03-31', 12, 'active');

-- Вопросы для опроса 3
INSERT INTO VOPROS (ID_VOPROSA, ID_OPROSA, TEKST_VOPROSA, PORYADOK) VALUES
(nextval('VOPROS_ID_VOPROSA_SEQ'), 3, 'Сортируете ли вы мусор?', 1),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 3, 'Готовы ли вы платить больше за экологически чистые продукты?', 2),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 3, 'Используете ли вы общественный транспорт вместо личного автомобиля?', 3),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 3, 'Поддерживаете ли вы развитие возобновляемых источников энергии?', 4),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 3, 'Считаете ли вы проблему изменения климата критической?', 5),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 3, 'Участвуете ли вы в экологических акциях?', 6),
(nextval('VOPROS_ID_VOPROSA_SEQ'), 3, 'Считаете ли вы, что государство должно больше инвестировать в экологию?', 7);

-- Варианты ответов для опроса 3
INSERT INTO VARIANT_OTVETA (ID_VARIANTA, ID_VOPROSA, TEKST_VARIANTA, PRIZNAK_POLOZH, PORYADOK)
SELECT 
    nextval('VARIANT_OTVETA_ID_VARIANTA_SEQ'),
    v.ID_VOPROSA,
    opt.text,
    opt.is_positive,
    opt.order_no
FROM VOPROS v,
(VALUES 
    ('Да', 1, 1),
    ('Нет', 0, 2),
    ('Затрудняюсь ответить', 0, 3)
) AS opt(text, is_positive, order_no)
WHERE v.ID_OPROSA = 3;

-- Генерация участий и ответов
-- Опрос 1: участие и ответы в январе 2024
INSERT INTO UCHASTIE (ID_UCHASTIYA, ID_OPROSA, ID_RESPONDENTA, DATA_UCHASTIYA)
SELECT 
    nextval('UCHASTIE_ID_UCHASTIYA_SEQ'),
    1,
    r.ID_RESPONDENTA,
    (TIMESTAMP '2024-01-01 00:00:00'
        + ((random() * 30)::int) * INTERVAL '1 day'
        + (8 + (random() * 12)::int) * INTERVAL '1 hour'
        + ((random() * 60)::int) * INTERVAL '1 minute')
FROM RESPONDENT r
ORDER BY random()
LIMIT 18;

-- Ответы для опроса 1
INSERT INTO OTVET (ID_OTVETA, ID_OPROSA, ID_VOPROSA, ID_RESPONDENTA, ID_VARIANTA, DATA_OTVETA)
SELECT 
    nextval('OTVET_ID_OTVETA_SEQ'),
    1,
    v.ID_VOPROSA,
    u.ID_RESPONDENTA,
    vo.ID_VARIANTA,
    u.DATA_UCHASTIYA + (random() * interval '1 hour')
FROM UCHASTIE u
CROSS JOIN VOPROS v
CROSS JOIN LATERAL (
    SELECT ID_VARIANTA FROM VARIANT_OTVETA 
    WHERE ID_VOPROSA = v.ID_VOPROSA 
    ORDER BY random() 
    LIMIT 1
) vo
WHERE u.ID_OPROSA = 1 AND v.ID_OPROSA = 1
LIMIT 90;

-- Опрос 2: участие и ответы в феврале 2024
INSERT INTO UCHASTIE (ID_UCHASTIYA, ID_OPROSA, ID_RESPONDENTA, DATA_UCHASTIYA)
SELECT 
    nextval('UCHASTIE_ID_UCHASTIYA_SEQ'),
    2,
    r.ID_RESPONDENTA,
    (TIMESTAMP '2024-02-01 00:00:00'
        + ((random() * 28)::int) * INTERVAL '1 day'
        + (8 + (random() * 12)::int) * INTERVAL '1 hour'
        + ((random() * 60)::int) * INTERVAL '1 minute')
FROM RESPONDENT r
ORDER BY random()
LIMIT 16;

-- Ответы для опроса 2
INSERT INTO OTVET (ID_OTVETA, ID_OPROSA, ID_VOPROSA, ID_RESPONDENTA, ID_VARIANTA, DATA_OTVETA)
SELECT 
    nextval('OTVET_ID_OTVETA_SEQ'),
    2,
    v.ID_VOPROSA,
    u.ID_RESPONDENTA,
    vo.ID_VARIANTA,
    u.DATA_UCHASTIYA + (random() * interval '1 hour')
FROM UCHASTIE u
CROSS JOIN VOPROS v
CROSS JOIN LATERAL (
    SELECT ID_VARIANTA FROM VARIANT_OTVETA 
    WHERE ID_VOPROSA = v.ID_VOPROSA 
    ORDER BY random() 
    LIMIT 1
) vo
WHERE u.ID_OPROSA = 2 AND v.ID_OPROSA = 2
LIMIT 80;

-- Опрос 3: участие и ответы в марте 2024
INSERT INTO UCHASTIE (ID_UCHASTIYA, ID_OPROSA, ID_RESPONDENTA, DATA_UCHASTIYA)
SELECT 
    nextval('UCHASTIE_ID_UCHASTIYA_SEQ'),
    3,
    r.ID_RESPONDENTA,
    (TIMESTAMP '2024-03-01 00:00:00'
        + ((random() * 31)::int) * INTERVAL '1 day'
        + (8 + (random() * 12)::int) * INTERVAL '1 hour'
        + ((random() * 60)::int) * INTERVAL '1 minute')
FROM RESPONDENT r
ORDER BY random()
LIMIT 15;

-- Ответы для опроса 3
INSERT INTO OTVET (ID_OTVETA, ID_OPROSA, ID_VOPROSA, ID_RESPONDENTA, ID_VARIANTA, DATA_OTVETA)
SELECT 
    nextval('OTVET_ID_OTVETA_SEQ'),
    3,
    v.ID_VOPROSA,
    u.ID_RESPONDENTA,
    vo.ID_VARIANTA,
    u.DATA_UCHASTIYA + (random() * interval '1 hour')
FROM UCHASTIE u
CROSS JOIN VOPROS v
CROSS JOIN LATERAL (
    SELECT ID_VARIANTA FROM VARIANT_OTVETA 
    WHERE ID_VOPROSA = v.ID_VOPROSA 
    ORDER BY random() 
    LIMIT 1
) vo
WHERE u.ID_OPROSA = 3 AND v.ID_OPROSA = 3
LIMIT 105;

-- Обновляем статистику sequences
SELECT setval('POL_ID_POLA_SEQ', (SELECT MAX(ID_POLA) FROM POL));
SELECT setval('REGION_ID_REGIONA_SEQ', (SELECT MAX(ID_REGIONA) FROM REGION));
SELECT setval('UROVEN_OBRAZOVANIYA_ID_UROVNYA_SEQ', (SELECT MAX(ID_UROVNYA) FROM UROVEN_OBRAZOVANIYA));
SELECT setval('OPROS_ID_OPROSA_SEQ', (SELECT MAX(ID_OPROSA) FROM OPROS));
SELECT setval('VOPROS_ID_VOPROSA_SEQ', (SELECT MAX(ID_VOPROSA) FROM VOPROS));
SELECT setval('VARIANT_OTVETA_ID_VARIANTA_SEQ', (SELECT MAX(ID_VARIANTA) FROM VARIANT_OTVETA));
SELECT setval('RESPONDENT_ID_RESPONDENTA_SEQ', (SELECT MAX(ID_RESPONDENTA) FROM RESPONDENT));
SELECT setval('UCHASTIE_ID_UCHASTIYA_SEQ', (SELECT MAX(ID_UCHASTIYA) FROM UCHASTIE));
SELECT setval('OTVET_ID_OTVETA_SEQ', (SELECT MAX(ID_OTVETA) FROM OTVET));
