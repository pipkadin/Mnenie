--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

-- Started on 2026-01-20 06:23:11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 247 (class 1255 OID 25073)
-- Name: generirovat_xml_otchet(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.generirovat_xml_otchet(p_id_oprosa integer) RETURNS xml
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_opros record;
    v_uchastnikov_count integer;
    v_xml xml;
BEGIN
    -- Заголовок опроса
    SELECT
        o.id_oprosa,
        o.tema,
        o.data_nachala,
        o.data_okonch_pln,
        o.data_okonch_fakt
    INTO v_opros
    FROM opros o
    WHERE o.id_oprosa = p_id_oprosa;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Опрос с ID % не найден', p_id_oprosa;
    END IF;

    -- Количество участников (по UCHASTIE)
    SELECT COUNT(*) INTO v_uchastnikov_count
    FROM uchastie u
    WHERE u.id_oprosa = p_id_oprosa;

    /*
      Считаем статистику в 2 шага:
      1) option_counts: count ответов по каждому варианту (по вопросу)
      2) option_counts_with_total: добавляем total по вопросу (оконная сумма)
      Затем строим XML из уже готовых чисел.
    */
    WITH option_counts AS (
        SELECT
            v.id_voprosa,
            vo.id_varianta,
            vo.tekst_varianta,
            vo.poryadok,
            COUNT(ot.id_otveta) AS cnt
        FROM vopros v
        JOIN variant_otveta vo
            ON vo.id_voprosa = v.id_voprosa
        LEFT JOIN otvet ot
            ON ot.id_oprosa = p_id_oprosa
           AND ot.id_voprosa = v.id_voprosa
           AND ot.id_varianta = vo.id_varianta
        WHERE v.id_oprosa = p_id_oprosa
        GROUP BY
            v.id_voprosa, vo.id_varianta, vo.tekst_varianta, vo.poryadok
    ),
    option_counts_with_total AS (
        SELECT
            oc.*,
            SUM(oc.cnt) OVER (PARTITION BY oc.id_voprosa) AS total_cnt
        FROM option_counts oc
    )
    SELECT xmlelement(
        NAME "survey",
        xmlattributes(
            v_opros.id_oprosa      AS "id",
            v_opros.tema           AS "topic",
            v_opros.data_nachala   AS "start_date",
            v_opros.data_okonch_pln AS "end_date_planned",
            v_opros.data_okonch_fakt AS "end_date_fact",
            v_uchastnikov_count    AS "participants"
        ),
        xmlelement(
            NAME "questions",
            (
                SELECT xmlagg(
                    xmlelement(
                        NAME "question",
                        xmlattributes(
                            q.id_voprosa    AS "id",
                            q.tekst_voprosa AS "text",
                            q.poryadok      AS "order"
                        ),
                        xmlelement(
                            NAME "options",
                            (
                                SELECT xmlagg(
                                    xmlelement(
                                        NAME "option",
                                        xmlattributes(
                                            owt.id_varianta     AS "id",
                                            owt.tekst_varianta  AS "text",
                                            owt.cnt             AS "count",
                                            CASE
                                                WHEN owt.total_cnt > 0
                                                    THEN ROUND((owt.cnt::numeric / owt.total_cnt::numeric) * 100, 2)
                                                ELSE 0
                                            END AS "percent"
                                        )
                                    )
                                    ORDER BY owt.poryadok
                                )
                                FROM option_counts_with_total owt
                                WHERE owt.id_voprosa = q.id_voprosa
                            )
                        )
                    )
                    ORDER BY q.poryadok
                )
                FROM vopros q
                WHERE q.id_oprosa = p_id_oprosa
            )
        )
    )
    INTO v_xml;

    RETURN v_xml;
END;
$$;


ALTER FUNCTION public.generirovat_xml_otchet(p_id_oprosa integer) OWNER TO postgres;

--
-- TOC entry 4926 (class 0 OID 0)
-- Dependencies: 247
-- Name: FUNCTION generirovat_xml_otchet(p_id_oprosa integer); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.generirovat_xml_otchet(p_id_oprosa integer) IS 'Генерирует XML-отчёт по опросу. 
Включает агрегированные данные по вопросам и вариантам ответов.
Не содержит персональных данных респондентов (ФИО).';


--
-- TOC entry 235 (class 1255 OID 25072)
-- Name: prodlenie_oprosa_esli_nekhvataet(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.prodlenie_oprosa_esli_nekhvataet() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION public.prodlenie_oprosa_esli_nekhvataet() OWNER TO postgres;

--
-- TOC entry 4927 (class 0 OID 0)
-- Dependencies: 235
-- Name: FUNCTION prodlenie_oprosa_esli_nekhvataet(); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.prodlenie_oprosa_esli_nekhvataet() IS 'Функция продления опроса при недостатке участников. 
Если при попытке закрыть опрос участников меньше MIN_KOL_OTVETOV:
- Если участников 0: срок удваивается
- Иначе: срок продлевается пропорционально дефициту участников
Участники считаются по таблице UCHASTIE';


--
-- TOC entry 229 (class 1259 OID 25057)
-- Name: opros_id_oprosa_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.opros_id_oprosa_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.opros_id_oprosa_seq OWNER TO postgres;

--
-- TOC entry 4928 (class 0 OID 0)
-- Dependencies: 229
-- Name: SEQUENCE opros_id_oprosa_seq; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON SEQUENCE public.opros_id_oprosa_seq IS 'Sequence для генерации ID опроса';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 220 (class 1259 OID 24935)
-- Name: opros; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.opros (
    id_oprosa integer DEFAULT nextval('public.opros_id_oprosa_seq'::regclass) NOT NULL,
    tema character varying(255) NOT NULL,
    opisanie text,
    data_nachala date NOT NULL,
    data_okonch_pln date NOT NULL,
    data_okonch_fakt date,
    min_kol_otvetov integer NOT NULL,
    status character varying(20) NOT NULL,
    CONSTRAINT opros_dates_check CHECK ((data_nachala <= data_okonch_pln)),
    CONSTRAINT opros_min_kol_otvetov_check CHECK ((min_kol_otvetov > 0)),
    CONSTRAINT opros_status_check CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'active'::character varying, 'closed'::character varying])::text[])))
);


ALTER TABLE public.opros OWNER TO postgres;

--
-- TOC entry 4929 (class 0 OID 0)
-- Dependencies: 220
-- Name: TABLE opros; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.opros IS 'Опросы. Статусы: draft - черновик, active - активен, closed - закрыт';


--
-- TOC entry 4930 (class 0 OID 0)
-- Dependencies: 220
-- Name: COLUMN opros.data_okonch_fakt; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.opros.data_okonch_fakt IS 'Фактическая дата окончания (может отличаться от плановой при продлении)';


--
-- TOC entry 4931 (class 0 OID 0)
-- Dependencies: 220
-- Name: COLUMN opros.min_kol_otvetov; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.opros.min_kol_otvetov IS 'Минимальное количество участников для успешного завершения опроса';


--
-- TOC entry 234 (class 1259 OID 25062)
-- Name: otvet_id_otveta_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.otvet_id_otveta_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.otvet_id_otveta_seq OWNER TO postgres;

--
-- TOC entry 4932 (class 0 OID 0)
-- Dependencies: 234
-- Name: SEQUENCE otvet_id_otveta_seq; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON SEQUENCE public.otvet_id_otveta_seq IS 'Sequence для генерации ID ответа';


--
-- TOC entry 225 (class 1259 OID 25013)
-- Name: otvet; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.otvet (
    id_otveta integer DEFAULT nextval('public.otvet_id_otveta_seq'::regclass) NOT NULL,
    id_oprosa integer NOT NULL,
    id_voprosa integer NOT NULL,
    id_respondenta integer NOT NULL,
    id_varianta integer NOT NULL,
    data_otveta timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.otvet OWNER TO postgres;

--
-- TOC entry 4933 (class 0 OID 0)
-- Dependencies: 225
-- Name: TABLE otvet; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.otvet IS 'Ответы респондентов на вопросы опросов. Один респондент может ответить на вопрос опроса только один раз';


--
-- TOC entry 4934 (class 0 OID 0)
-- Dependencies: 225
-- Name: COLUMN otvet.data_otveta; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.otvet.data_otveta IS 'Время ответа (для анализа динамики)';


--
-- TOC entry 226 (class 1259 OID 25054)
-- Name: pol_id_pola_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pol_id_pola_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pol_id_pola_seq OWNER TO postgres;

--
-- TOC entry 4935 (class 0 OID 0)
-- Dependencies: 226
-- Name: SEQUENCE pol_id_pola_seq; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON SEQUENCE public.pol_id_pola_seq IS 'Sequence для генерации ID пола';


--
-- TOC entry 217 (class 1259 OID 24914)
-- Name: pol; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pol (
    id_pola integer DEFAULT nextval('public.pol_id_pola_seq'::regclass) NOT NULL,
    naimenovanie character varying(50) NOT NULL
);


ALTER TABLE public.pol OWNER TO postgres;

--
-- TOC entry 4936 (class 0 OID 0)
-- Dependencies: 217
-- Name: TABLE pol; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.pol IS 'Справочник полов';


--
-- TOC entry 227 (class 1259 OID 25055)
-- Name: region_id_regiona_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.region_id_regiona_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.region_id_regiona_seq OWNER TO postgres;

--
-- TOC entry 4937 (class 0 OID 0)
-- Dependencies: 227
-- Name: SEQUENCE region_id_regiona_seq; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON SEQUENCE public.region_id_regiona_seq IS 'Sequence для генерации ID региона';


--
-- TOC entry 218 (class 1259 OID 24921)
-- Name: region; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.region (
    id_regiona integer DEFAULT nextval('public.region_id_regiona_seq'::regclass) NOT NULL,
    naimenovanie character varying(100) NOT NULL
);


ALTER TABLE public.region OWNER TO postgres;

--
-- TOC entry 4938 (class 0 OID 0)
-- Dependencies: 218
-- Name: TABLE region; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.region IS 'Справочник регионов';


--
-- TOC entry 232 (class 1259 OID 25060)
-- Name: respondent_id_respondenta_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.respondent_id_respondenta_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.respondent_id_respondenta_seq OWNER TO postgres;

--
-- TOC entry 4939 (class 0 OID 0)
-- Dependencies: 232
-- Name: SEQUENCE respondent_id_respondenta_seq; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON SEQUENCE public.respondent_id_respondenta_seq IS 'Sequence для генерации ID респондента';


--
-- TOC entry 223 (class 1259 OID 24975)
-- Name: respondent; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.respondent (
    id_respondenta integer DEFAULT nextval('public.respondent_id_respondenta_seq'::regclass) NOT NULL,
    familiya character varying(100),
    imya character varying(100),
    otchestvo character varying(100),
    data_rozhdeniya date NOT NULL,
    id_pola integer NOT NULL,
    id_regiona integer NOT NULL,
    id_urovnya integer NOT NULL
);


ALTER TABLE public.respondent OWNER TO postgres;

--
-- TOC entry 4940 (class 0 OID 0)
-- Dependencies: 223
-- Name: TABLE respondent; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.respondent IS 'Респонденты. ФИО хранится, но НИКОГДА не выводится в отчётах (анонимность)';


--
-- TOC entry 4941 (class 0 OID 0)
-- Dependencies: 223
-- Name: COLUMN respondent.familiya; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.respondent.familiya IS 'Фамилия (не используется в отчётах)';


--
-- TOC entry 4942 (class 0 OID 0)
-- Dependencies: 223
-- Name: COLUMN respondent.imya; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.respondent.imya IS 'Имя (не используется в отчётах)';


--
-- TOC entry 4943 (class 0 OID 0)
-- Dependencies: 223
-- Name: COLUMN respondent.otchestvo; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.respondent.otchestvo IS 'Отчество (не используется в отчётах)';


--
-- TOC entry 233 (class 1259 OID 25061)
-- Name: uchastie_id_uchastiya_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.uchastie_id_uchastiya_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.uchastie_id_uchastiya_seq OWNER TO postgres;

--
-- TOC entry 4944 (class 0 OID 0)
-- Dependencies: 233
-- Name: SEQUENCE uchastie_id_uchastiya_seq; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON SEQUENCE public.uchastie_id_uchastiya_seq IS 'Sequence для генерации ID участия';


--
-- TOC entry 224 (class 1259 OID 24995)
-- Name: uchastie; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.uchastie (
    id_uchastiya integer DEFAULT nextval('public.uchastie_id_uchastiya_seq'::regclass) NOT NULL,
    id_oprosa integer NOT NULL,
    id_respondenta integer NOT NULL,
    data_uchastiya timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.uchastie OWNER TO postgres;

--
-- TOC entry 4945 (class 0 OID 0)
-- Dependencies: 224
-- Name: TABLE uchastie; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.uchastie IS 'Участие респондентов в опросах. Один респондент может участвовать в одном опросе только один раз';


--
-- TOC entry 228 (class 1259 OID 25056)
-- Name: uroven_obrazovaniya_id_urovnya_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.uroven_obrazovaniya_id_urovnya_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.uroven_obrazovaniya_id_urovnya_seq OWNER TO postgres;

--
-- TOC entry 4946 (class 0 OID 0)
-- Dependencies: 228
-- Name: SEQUENCE uroven_obrazovaniya_id_urovnya_seq; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON SEQUENCE public.uroven_obrazovaniya_id_urovnya_seq IS 'Sequence для генерации ID уровня образования';


--
-- TOC entry 219 (class 1259 OID 24928)
-- Name: uroven_obrazovaniya; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.uroven_obrazovaniya (
    id_urovnya integer DEFAULT nextval('public.uroven_obrazovaniya_id_urovnya_seq'::regclass) NOT NULL,
    naimenovanie character varying(100) NOT NULL
);


ALTER TABLE public.uroven_obrazovaniya OWNER TO postgres;

--
-- TOC entry 4947 (class 0 OID 0)
-- Dependencies: 219
-- Name: TABLE uroven_obrazovaniya; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.uroven_obrazovaniya IS 'Справочник уровней образования';


--
-- TOC entry 231 (class 1259 OID 25059)
-- Name: variant_otveta_id_varianta_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.variant_otveta_id_varianta_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.variant_otveta_id_varianta_seq OWNER TO postgres;

--
-- TOC entry 4948 (class 0 OID 0)
-- Dependencies: 231
-- Name: SEQUENCE variant_otveta_id_varianta_seq; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON SEQUENCE public.variant_otveta_id_varianta_seq IS 'Sequence для генерации ID варианта ответа';


--
-- TOC entry 222 (class 1259 OID 24961)
-- Name: variant_otveta; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.variant_otveta (
    id_varianta integer DEFAULT nextval('public.variant_otveta_id_varianta_seq'::regclass) NOT NULL,
    id_voprosa integer NOT NULL,
    tekst_varianta character varying(255) NOT NULL,
    poryadok integer NOT NULL,
    priznak_polozh integer DEFAULT 0 NOT NULL,
    CONSTRAINT variant_otveta_priznak_polozh_check CHECK ((priznak_polozh = ANY (ARRAY[0, 1])))
);


ALTER TABLE public.variant_otveta OWNER TO postgres;

--
-- TOC entry 4949 (class 0 OID 0)
-- Dependencies: 222
-- Name: TABLE variant_otveta; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.variant_otveta IS 'Варианты ответов на вопросы. PRIZNAK_POLOZH = 1 если ответ считается положительным';


--
-- TOC entry 4950 (class 0 OID 0)
-- Dependencies: 222
-- Name: COLUMN variant_otveta.priznak_polozh; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.variant_otveta.priznak_polozh IS '1 - положительный ответ, 0 - отрицательный (для анализа динамики)';


--
-- TOC entry 230 (class 1259 OID 25058)
-- Name: vopros_id_voprosa_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vopros_id_voprosa_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vopros_id_voprosa_seq OWNER TO postgres;

--
-- TOC entry 4951 (class 0 OID 0)
-- Dependencies: 230
-- Name: SEQUENCE vopros_id_voprosa_seq; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON SEQUENCE public.vopros_id_voprosa_seq IS 'Sequence для генерации ID вопроса';


--
-- TOC entry 221 (class 1259 OID 24945)
-- Name: vopros; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vopros (
    id_voprosa integer DEFAULT nextval('public.vopros_id_voprosa_seq'::regclass) NOT NULL,
    id_oprosa integer NOT NULL,
    tekst_voprosa text NOT NULL,
    poryadok integer NOT NULL,
    tip_voprosa character varying(20) DEFAULT 'single_choice'::character varying NOT NULL,
    CONSTRAINT vopros_tip_voprosa_check CHECK (((tip_voprosa)::text = 'single_choice'::text))
);


ALTER TABLE public.vopros OWNER TO postgres;

--
-- TOC entry 4952 (class 0 OID 0)
-- Dependencies: 221
-- Name: TABLE vopros; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.vopros IS 'Вопросы в опросах. Порядок определяется PORYADOK';


--
-- TOC entry 4906 (class 0 OID 24935)
-- Dependencies: 220
-- Data for Name: opros; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.opros (id_oprosa, tema, opisanie, data_nachala, data_okonch_pln, data_okonch_fakt, min_kol_otvetov, status) FROM stdin;
2	Отношение к цифровизации	Изучение мнения населения о цифровизации (вторая волна)	2024-02-01	2024-02-28	\N	15	active
3	Экологическая сознательность	Изучение экологической сознательности населения	2024-03-01	2024-03-31	\N	12	active
1	Отношение к цифровизации	Изучение мнения населения о цифровизации	2024-01-01	2024-01-31	\N	15	active
4	Тест		2026-01-18	2026-03-23	\N	6	active
\.


--
-- TOC entry 4911 (class 0 OID 25013)
-- Dependencies: 225
-- Data for Name: otvet; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.otvet (id_otveta, id_oprosa, id_voprosa, id_respondenta, id_varianta, data_otveta) FROM stdin;
1	1	18	54	52	2024-01-04 09:07:20.282572
2	1	19	54	57	2024-01-04 09:59:30.216091
3	1	20	54	59	2024-01-04 09:16:22.319055
4	1	21	54	63	2024-01-04 09:11:35.026969
5	1	22	54	65	2024-01-04 10:02:48.180023
6	1	18	48	52	2024-01-07 10:33:06.048859
7	1	19	48	57	2024-01-07 10:46:43.896918
8	1	20	48	59	2024-01-07 10:12:06.999577
9	1	21	48	63	2024-01-07 10:17:05.448671
10	1	22	48	65	2024-01-07 10:20:14.574519
11	1	18	47	52	2024-01-12 13:47:57.951205
12	1	19	47	57	2024-01-12 13:28:23.01306
13	1	20	47	59	2024-01-12 14:19:52.450267
14	1	21	47	63	2024-01-12 13:23:06.648352
15	1	22	47	65	2024-01-12 13:55:00.974076
16	1	18	49	52	2024-01-13 14:22:23.813132
17	1	19	49	57	2024-01-13 14:23:21.670782
18	1	20	49	59	2024-01-13 14:02:25.175084
19	1	21	49	63	2024-01-13 13:36:17.463375
20	1	22	49	65	2024-01-13 13:24:10.385882
21	1	18	43	52	2024-01-15 14:19:45.660982
22	1	19	43	57	2024-01-15 14:15:32.613386
23	1	20	43	59	2024-01-15 14:16:50.285119
24	1	21	43	63	2024-01-15 14:11:58.561305
25	1	22	43	65	2024-01-15 13:53:32.654309
26	1	18	60	52	2024-01-16 15:08:37.434908
27	1	19	60	57	2024-01-16 14:44:58.333709
28	1	20	60	59	2024-01-16 15:14:35.168055
29	1	21	60	63	2024-01-16 15:00:33.71635
30	1	22	60	65	2024-01-16 14:44:15.897225
31	1	18	51	52	2024-01-16 15:01:57.684751
32	1	19	51	57	2024-01-16 14:39:11.436538
33	1	20	51	59	2024-01-16 15:03:42.975479
34	1	21	51	63	2024-01-16 14:38:59.328071
35	1	22	51	65	2024-01-16 14:39:58.214161
36	1	18	41	52	2024-01-16 14:35:35.575235
37	1	19	41	57	2024-01-16 15:15:02.554919
38	1	20	41	59	2024-01-16 15:26:45.604539
39	1	21	41	63	2024-01-16 15:26:02.853742
40	1	22	41	65	2024-01-16 14:31:42.671683
41	1	18	58	52	2024-01-16 15:10:39.360745
42	1	19	58	57	2024-01-16 15:23:47.043841
43	1	20	58	59	2024-01-16 14:31:28.895878
44	1	21	58	63	2024-01-16 14:47:34.353457
45	1	22	58	65	2024-01-16 14:54:35.541593
46	1	18	59	52	2024-01-17 14:56:40.687104
47	1	19	59	57	2024-01-17 14:56:06.669134
48	1	20	59	59	2024-01-17 14:49:35.549704
49	1	21	59	63	2024-01-17 14:51:20.975859
50	1	22	59	65	2024-01-17 14:34:59.345717
51	1	18	55	52	2024-01-18 16:31:05.425893
52	1	19	55	57	2024-01-18 15:33:20.625771
53	1	20	55	59	2024-01-18 16:03:49.738996
54	1	21	55	63	2024-01-18 16:07:35.555521
55	1	22	55	65	2024-01-18 16:04:13.397505
56	1	18	56	52	2024-01-19 15:41:42.291765
57	1	19	56	57	2024-01-19 15:43:20.536057
58	1	20	56	59	2024-01-19 15:43:17.624275
59	1	21	56	63	2024-01-19 16:15:23.884917
60	1	22	56	65	2024-01-19 15:40:12.801041
61	1	18	45	52	2024-01-20 16:54:01.461696
62	1	19	45	57	2024-01-20 17:05:08.644768
63	1	20	45	59	2024-01-20 16:39:34.340622
64	1	21	45	63	2024-01-20 17:27:13.837915
65	1	22	45	65	2024-01-20 16:50:34.36537
66	1	18	50	52	2024-01-21 17:04:01.924421
67	1	19	50	57	2024-01-21 16:42:41.480128
68	1	20	50	59	2024-01-21 17:05:51.799565
69	1	21	50	63	2024-01-21 16:52:00.35314
70	1	22	50	65	2024-01-21 16:43:50.803903
71	1	18	42	52	2024-01-22 17:56:16.909534
72	1	19	42	57	2024-01-22 18:27:57.555255
73	1	20	42	59	2024-01-22 17:44:25.09261
74	1	21	42	63	2024-01-22 17:55:49.816126
75	1	22	42	65	2024-01-22 18:36:56.51303
76	1	18	57	52	2024-01-24 18:22:41.685748
77	1	19	57	57	2024-01-24 17:58:10.133644
78	1	20	57	59	2024-01-24 18:19:46.475712
79	1	21	57	63	2024-01-24 17:51:48.940943
80	1	22	57	65	2024-01-24 17:59:21.120523
81	1	18	44	52	2024-01-24 17:49:14.529114
82	1	19	44	57	2024-01-24 18:32:36.352314
83	1	20	44	59	2024-01-24 18:44:52.497244
84	1	21	44	63	2024-01-24 17:54:42.075391
85	1	22	44	65	2024-01-24 17:52:16.961054
86	1	18	46	52	2024-01-26 19:31:16.026572
87	1	19	46	57	2024-01-26 19:34:18.265098
88	1	20	46	59	2024-01-26 19:02:57.720083
89	1	21	46	63	2024-01-26 19:11:33.487934
90	1	22	46	65	2024-01-26 19:06:21.529941
91	2	23	53	68	2024-02-01 08:28:20.553912
92	2	24	53	71	2024-02-01 08:11:32.35563
93	2	25	53	75	2024-02-01 08:32:56.97319
94	2	26	53	78	2024-02-01 08:12:41.760815
95	2	27	53	79	2024-02-01 08:00:59.322748
96	2	23	58	68	2024-02-04 09:34:44.871368
97	2	24	58	71	2024-02-04 09:09:03.204116
98	2	25	58	75	2024-02-04 09:23:38.493072
99	2	26	58	78	2024-02-04 09:26:41.855007
100	2	27	58	79	2024-02-04 09:58:26.675436
101	2	23	42	68	2024-02-07 11:57:15.760863
102	2	24	42	71	2024-02-07 11:59:25.91585
103	2	25	42	75	2024-02-07 11:22:06.668736
104	2	26	42	78	2024-02-07 12:07:24.878671
105	2	27	42	79	2024-02-07 11:56:13.470336
106	2	23	41	68	2024-02-10 13:04:21.374674
107	2	24	41	71	2024-02-10 13:06:11.828155
108	2	25	41	75	2024-02-10 12:36:07.777097
109	2	26	41	78	2024-02-10 12:40:01.919004
110	2	27	41	79	2024-02-10 12:25:56.900552
111	2	23	45	68	2024-02-11 13:03:11.343182
112	2	24	45	71	2024-02-11 12:52:13.670399
113	2	25	45	75	2024-02-11 13:07:07.512634
114	2	26	45	78	2024-02-11 12:48:08.662726
115	2	27	45	79	2024-02-11 12:35:09.956836
116	2	23	52	68	2024-02-12 14:13:04.28793
117	2	24	52	71	2024-02-12 13:44:16.91656
118	2	25	52	75	2024-02-12 13:53:50.150715
119	2	26	52	78	2024-02-12 14:19:26.335336
120	2	27	52	79	2024-02-12 13:51:25.354084
121	2	23	43	68	2024-02-13 14:13:38.493325
122	2	24	43	71	2024-02-13 13:53:16.231822
123	2	25	43	75	2024-02-13 13:56:14.286943
124	2	26	43	78	2024-02-13 13:54:29.32319
125	2	27	43	79	2024-02-13 13:43:24.243054
126	2	23	46	68	2024-02-14 14:49:24.830981
127	2	24	46	71	2024-02-14 14:40:15.055966
128	2	25	46	75	2024-02-14 15:08:45.203741
129	2	26	46	78	2024-02-14 14:42:17.804389
130	2	27	46	79	2024-02-14 14:49:54.75128
131	2	23	47	68	2024-02-17 16:10:18.758702
132	2	24	47	71	2024-02-17 15:56:12.045447
133	2	25	47	75	2024-02-17 15:52:27.080124
134	2	26	47	78	2024-02-17 15:55:52.670436
135	2	27	47	79	2024-02-17 16:23:23.343616
136	2	23	54	68	2024-02-17 16:24:52.927833
137	2	24	54	71	2024-02-17 15:57:02.432971
138	2	25	54	75	2024-02-17 15:42:19.400117
139	2	26	54	78	2024-02-17 16:09:11.126488
140	2	27	54	79	2024-02-17 15:57:27.105394
141	2	23	59	68	2024-02-20 17:21:15.096975
142	2	24	59	71	2024-02-20 17:24:56.037178
143	2	25	59	75	2024-02-20 17:27:07.586514
144	2	26	59	78	2024-02-20 16:49:27.408127
145	2	27	59	79	2024-02-20 16:52:46.475993
146	2	23	60	68	2024-02-20 16:48:01.147723
147	2	24	60	71	2024-02-20 17:20:50.502765
148	2	25	60	75	2024-02-20 17:24:04.667488
149	2	26	60	78	2024-02-20 17:17:41.773783
150	2	27	60	79	2024-02-20 17:22:39.836559
151	2	23	57	68	2024-02-21 18:15:32.580847
152	2	24	57	71	2024-02-21 18:07:46.985216
153	2	25	57	75	2024-02-21 17:51:37.055869
154	2	26	57	78	2024-02-21 17:49:20.854445
156	2	23	48	68	2024-02-22 18:05:48.927173
157	2	24	48	71	2024-02-22 18:40:46.031324
158	2	25	48	75	2024-02-22 18:21:23.260096
159	2	26	48	78	2024-02-22 18:21:13.719345
160	2	27	48	79	2024-02-22 17:52:55.200705
161	2	23	56	68	2024-02-23 18:33:34.103113
162	2	24	56	71	2024-02-23 18:43:31.355051
163	2	25	56	75	2024-02-23 17:50:31.532166
164	2	26	56	78	2024-02-23 18:34:24.380925
165	2	27	56	79	2024-02-23 17:59:09.636704
166	2	23	44	68	2024-02-26 19:59:39.817616
167	2	24	44	71	2024-02-26 20:10:29.955886
168	2	25	44	75	2024-02-26 20:28:27.960898
169	2	26	44	78	2024-02-26 19:59:47.702576
170	2	27	44	79	2024-02-26 20:03:49.76002
171	3	28	48	82	2024-03-04 09:33:59.705656
172	3	29	48	86	2024-03-04 09:09:45.577949
173	3	30	48	88	2024-03-04 09:19:15.961351
174	3	31	48	92	2024-03-04 09:34:22.121812
175	3	32	48	95	2024-03-04 09:38:10.221017
176	3	33	48	99	2024-03-04 09:38:26.614025
178	3	28	60	82	2024-03-04 09:31:25.258364
179	3	29	60	86	2024-03-04 09:31:44.07128
180	3	30	60	88	2024-03-04 09:18:13.568386
181	3	31	60	92	2024-03-04 09:43:26.437216
182	3	32	60	95	2024-03-04 09:17:25.368561
183	3	33	60	99	2024-03-04 09:21:01.187512
185	3	28	51	82	2024-03-05 10:34:34.066724
186	3	29	51	86	2024-03-05 10:52:49.732188
187	3	30	51	88	2024-03-05 10:15:09.367636
188	3	31	51	92	2024-03-05 10:22:29.266906
189	3	32	51	95	2024-03-05 10:39:40.896557
190	3	33	51	99	2024-03-05 10:40:02.362675
192	3	28	53	82	2024-03-07 10:19:17.715519
193	3	29	53	86	2024-03-07 10:34:36.916069
194	3	30	53	88	2024-03-07 10:49:17.131613
195	3	31	53	92	2024-03-07 10:45:43.443335
196	3	32	53	95	2024-03-07 11:01:00.385735
197	3	33	53	99	2024-03-07 11:07:19.222836
199	3	28	46	82	2024-03-08 11:30:40.721411
200	3	29	46	86	2024-03-08 11:30:48.543062
201	3	30	46	88	2024-03-08 12:05:03.393521
202	3	31	46	92	2024-03-08 11:55:44.905587
203	3	32	46	95	2024-03-08 11:52:13.212565
204	3	33	46	99	2024-03-08 11:39:51.496143
206	3	28	57	82	2024-03-08 11:31:49.91326
207	3	29	57	86	2024-03-08 11:25:45.986439
208	3	30	57	88	2024-03-08 12:02:14.60934
209	3	31	57	92	2024-03-08 11:14:53.797089
210	3	32	57	95	2024-03-08 11:38:44.906755
211	3	33	57	99	2024-03-08 11:52:33.755407
213	3	28	49	82	2024-03-12 12:34:14.869467
214	3	29	49	86	2024-03-12 12:54:50.696291
215	3	30	49	88	2024-03-12 12:52:21.130142
216	3	31	49	92	2024-03-12 12:51:16.253691
217	3	32	49	95	2024-03-12 12:53:02.972306
218	3	33	49	99	2024-03-12 13:12:32.574946
220	3	28	59	82	2024-03-12 13:07:46.983868
221	3	29	59	86	2024-03-12 12:54:14.550783
222	3	30	59	88	2024-03-12 12:43:41.653726
223	3	31	59	92	2024-03-12 12:37:46.896496
224	3	32	59	95	2024-03-12 13:07:23.207893
225	3	33	59	99	2024-03-12 13:11:25.938333
227	3	28	50	82	2024-03-12 12:52:36.222646
228	3	29	50	86	2024-03-12 12:42:10.985
229	3	30	50	88	2024-03-12 12:52:02.416446
230	3	31	50	92	2024-03-12 12:34:15.051136
231	3	32	50	95	2024-03-12 12:47:43.993477
232	3	33	50	99	2024-03-12 13:12:34.774169
234	3	28	54	82	2024-03-13 13:31:28.115126
235	3	29	54	86	2024-03-13 13:33:11.354953
236	3	30	54	88	2024-03-13 14:09:14.096139
237	3	31	54	92	2024-03-13 14:20:50.026882
238	3	32	54	95	2024-03-13 14:06:03.56261
239	3	33	54	99	2024-03-13 14:20:13.019827
241	3	28	41	82	2024-03-14 14:24:23.353583
242	3	29	41	86	2024-03-14 14:23:51.370262
243	3	30	41	88	2024-03-14 13:56:39.65629
244	3	31	41	92	2024-03-14 13:37:55.54309
245	3	32	41	95	2024-03-14 13:56:18.466082
246	3	33	41	99	2024-03-14 13:48:40.869342
248	3	28	44	82	2024-03-16 14:45:51.897247
249	3	29	44	86	2024-03-16 14:29:39.20121
250	3	30	44	88	2024-03-16 14:33:48.374754
251	3	31	44	92	2024-03-16 14:46:43.42639
252	3	32	44	95	2024-03-16 14:41:57.858022
253	3	33	44	99	2024-03-16 15:01:05.069169
255	3	28	55	82	2024-03-19 16:24:49.33396
256	3	29	55	86	2024-03-19 16:07:46.704669
257	3	30	55	88	2024-03-19 15:51:43.13128
258	3	31	55	92	2024-03-19 15:54:48.935857
259	3	32	55	95	2024-03-19 16:07:57.984117
260	3	33	55	99	2024-03-19 16:28:08.897333
262	3	28	43	82	2024-03-22 16:51:32.622927
263	3	29	43	86	2024-03-22 16:42:51.443237
264	3	30	43	88	2024-03-22 16:57:49.377897
265	3	31	43	92	2024-03-22 17:32:51.120352
266	3	32	43	95	2024-03-22 17:16:09.698076
267	3	33	43	99	2024-03-22 16:53:44.443041
269	3	28	42	82	2024-03-23 18:00:39.03651
270	3	29	42	86	2024-03-23 18:00:21.021407
271	3	30	42	88	2024-03-23 18:02:35.640984
272	3	31	42	92	2024-03-23 17:50:44.809015
155	2	27	57	80	2026-01-18 22:27:19.472089
273	3	32	42	95	2024-03-23 18:40:45.57884
274	3	33	42	99	2024-03-23 17:58:40.981156
\.


--
-- TOC entry 4903 (class 0 OID 24914)
-- Dependencies: 217
-- Data for Name: pol; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pol (id_pola, naimenovanie) FROM stdin;
1	Мужской
2	Женский
3	Другое
\.


--
-- TOC entry 4904 (class 0 OID 24921)
-- Dependencies: 218
-- Data for Name: region; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.region (id_regiona, naimenovanie) FROM stdin;
1	Москва
2	Санкт-Петербург
3	Новосибирск
4	Екатеринбург
5	Казань
6	Краснодар
7	Ростов-на-Дону
8	Воронеж
9	Самара
10	Нижний Новгород
\.


--
-- TOC entry 4909 (class 0 OID 24975)
-- Dependencies: 223
-- Data for Name: respondent; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.respondent (id_respondenta, familiya, imya, otchestvo, data_rozhdeniya, id_pola, id_regiona, id_urovnya) FROM stdin;
41	Иванов	Иван	Иванович	1990-05-15	1	1	3
42	Петрова	Мария	Сергеевна	1985-08-22	2	2	3
43	Сидоров	Петр	Александрович	1995-03-10	1	3	1
44	Козлова	Анна	Дмитриевна	1988-11-30	2	4	3
45	Морозов	Дмитрий	Викторович	1992-07-18	1	1	1
46	Волкова	Елена	Павловна	1987-01-25	2	5	3
47	Новиков	Сергей	Олегович	1998-09-12	1	2	1
48	Лебедева	Ольга	Игоревна	1983-04-05	2	1	3
49	Соколов	Андрей	Николаевич	1991-12-20	1	6	1
50	Федорова	Татьяна	Владимировна	1986-06-14	2	1	3
51	Михайлов	Алексей	Борисович	1993-02-28	1	2	3
53	Алексеев	Владимир	Петрович	1996-08-03	1	1	1
54	Николаева	Ирина	Анатольевна	1984-05-17	2	2	3
55	Орлов	Максим	Сергеевич	1994-11-22	1	8	3
56	Романова	Юлия	Дмитриевна	1997-07-09	2	1	1
57	Семенов	Игорь	Викторович	1990-03-31	1	9	3
58	Титова	Наталья	Олеговна	1985-09-16	2	2	3
59	Ушаков	Роман	Александрович	1992-01-27	1	1	1
60	Яковлева	Екатерина	Павловна	1988-12-11	2	10	3
52	Павлова	Светлана	Юрьевна	1989-10-08	2	8	1
\.


--
-- TOC entry 4910 (class 0 OID 24995)
-- Dependencies: 224
-- Data for Name: uchastie; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.uchastie (id_uchastiya, id_oprosa, id_respondenta, data_uchastiya) FROM stdin;
1	1	54	2024-01-04 09:06:00
2	1	48	2024-01-07 10:12:00
3	1	47	2024-01-12 13:23:00
4	1	49	2024-01-13 13:24:00
5	1	43	2024-01-15 13:27:00
6	1	60	2024-01-16 14:29:00
7	1	51	2024-01-16 14:30:00
8	1	41	2024-01-16 14:31:00
9	1	58	2024-01-16 14:31:00
10	1	59	2024-01-17 14:32:00
11	1	55	2024-01-18 15:33:00
12	1	56	2024-01-19 15:37:00
13	1	45	2024-01-20 16:38:00
14	1	50	2024-01-21 16:40:00
15	1	42	2024-01-22 17:43:00
16	1	57	2024-01-24 17:46:00
17	1	44	2024-01-24 17:46:00
18	1	46	2024-01-26 18:50:00
19	2	53	2024-02-01 08:00:00
20	2	58	2024-02-04 09:05:00
21	2	42	2024-02-07 11:13:00
22	2	41	2024-02-10 12:19:00
23	2	45	2024-02-11 12:21:00
24	2	52	2024-02-12 13:23:00
25	2	43	2024-02-13 13:26:00
26	2	46	2024-02-14 14:29:00
27	2	47	2024-02-17 15:34:00
28	2	54	2024-02-17 15:35:00
29	2	59	2024-02-20 16:40:00
30	2	60	2024-02-20 16:41:00
31	2	57	2024-02-21 17:43:00
32	2	48	2024-02-22 17:45:00
33	2	56	2024-02-23 17:47:00
34	2	44	2024-02-26 19:53:00
35	3	48	2024-03-04 09:06:00
36	3	60	2024-03-04 09:06:00
37	3	51	2024-03-05 10:08:00
38	3	53	2024-03-07 10:11:00
39	3	46	2024-03-08 11:13:00
40	3	57	2024-03-08 11:14:00
41	3	49	2024-03-12 12:21:00
42	3	59	2024-03-12 12:21:00
43	3	50	2024-03-12 12:22:00
44	3	54	2024-03-13 13:23:00
45	3	41	2024-03-14 13:25:00
46	3	44	2024-03-16 14:28:00
47	3	55	2024-03-19 15:34:00
48	3	43	2024-03-22 16:40:00
49	3	42	2024-03-23 17:43:00
\.


--
-- TOC entry 4905 (class 0 OID 24928)
-- Dependencies: 219
-- Data for Name: uroven_obrazovaniya; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.uroven_obrazovaniya (id_urovnya, naimenovanie) FROM stdin;
1	Среднее
2	Среднее специальное
3	Высшее
4	Неоконченное высшее
\.


--
-- TOC entry 4908 (class 0 OID 24961)
-- Dependencies: 222
-- Data for Name: variant_otveta; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.variant_otveta (id_varianta, id_voprosa, tekst_varianta, poryadok, priznak_polozh) FROM stdin;
52	18	Да	1	1
53	18	Нет	2	0
54	18	Затрудняюсь ответить	3	0
55	19	Да	1	1
56	19	Нет	2	0
57	19	Затрудняюсь ответить	3	0
58	20	Да	1	1
59	20	Нет	2	0
60	20	Затрудняюсь ответить	3	0
61	21	Да	1	1
62	21	Нет	2	0
63	21	Затрудняюсь ответить	3	0
64	22	Да	1	1
65	22	Нет	2	0
66	22	Затрудняюсь ответить	3	0
67	23	Да	1	1
68	23	Нет	2	0
69	23	Затрудняюсь ответить	3	0
70	24	Да	1	1
71	24	Нет	2	0
72	24	Затрудняюсь ответить	3	0
73	25	Да	1	1
74	25	Нет	2	0
75	25	Затрудняюсь ответить	3	0
76	26	Да	1	1
77	26	Нет	2	0
78	26	Затрудняюсь ответить	3	0
79	27	Да	1	1
80	27	Нет	2	0
81	27	Затрудняюсь ответить	3	0
82	28	Да	1	1
83	28	Нет	2	0
84	28	Затрудняюсь ответить	3	0
85	29	Да	1	1
86	29	Нет	2	0
87	29	Затрудняюсь ответить	3	0
88	30	Да	1	1
89	30	Нет	2	0
90	30	Затрудняюсь ответить	3	0
91	31	Да	1	1
92	31	Нет	2	0
93	31	Затрудняюсь ответить	3	0
94	32	Да	1	1
95	32	Нет	2	0
96	32	Затрудняюсь ответить	3	0
97	33	Да	1	1
98	33	Нет	2	0
99	33	Затрудняюсь ответить	3	0
103	24	Не знаю	5	1
\.


--
-- TOC entry 4907 (class 0 OID 24945)
-- Dependencies: 221
-- Data for Name: vopros; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.vopros (id_voprosa, id_oprosa, tekst_voprosa, poryadok, tip_voprosa) FROM stdin;
18	1	Считаете ли вы, что цифровизация улучшает качество жизни?	1	single_choice
19	1	Готовы ли вы полностью перейти на цифровые услуги?	2	single_choice
20	1	Обеспокоены ли вы проблемами кибербезопасности?	3	single_choice
21	1	Поддерживаете ли вы внедрение цифровых технологий в образование?	4	single_choice
22	1	Считаете ли вы, что цифровизация создаёт новые рабочие места?	5	single_choice
23	2	Считаете ли вы, что цифровизация улучшает качество жизни?	1	single_choice
24	2	Готовы ли вы полностью перейти на цифровые услуги?	2	single_choice
25	2	Обеспокоены ли вы проблемами кибербезопасности?	3	single_choice
26	2	Поддерживаете ли вы внедрение цифровых технологий в образование?	4	single_choice
27	2	Считаете ли вы, что цифровизация создаёт новые рабочие места?	5	single_choice
28	3	Сортируете ли вы мусор?	1	single_choice
29	3	Готовы ли вы платить больше за экологически чистые продукты?	2	single_choice
30	3	Используете ли вы общественный транспорт вместо личного автомобиля?	3	single_choice
32	3	Считаете ли вы проблему изменения климата критической?	5	single_choice
33	3	Участвуете ли вы в экологических акциях?	6	single_choice
31	3	Поддерживаете ли вы развитие возобновляемых источников энергии?	4	single_choice
40	3	Кто?	7	single_choice
\.


--
-- TOC entry 4953 (class 0 OID 0)
-- Dependencies: 229
-- Name: opros_id_oprosa_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.opros_id_oprosa_seq', 4, true);


--
-- TOC entry 4954 (class 0 OID 0)
-- Dependencies: 234
-- Name: otvet_id_otveta_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.otvet_id_otveta_seq', 275, true);


--
-- TOC entry 4955 (class 0 OID 0)
-- Dependencies: 226
-- Name: pol_id_pola_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pol_id_pola_seq', 3, true);


--
-- TOC entry 4956 (class 0 OID 0)
-- Dependencies: 227
-- Name: region_id_regiona_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.region_id_regiona_seq', 10, true);


--
-- TOC entry 4957 (class 0 OID 0)
-- Dependencies: 232
-- Name: respondent_id_respondenta_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.respondent_id_respondenta_seq', 62, true);


--
-- TOC entry 4958 (class 0 OID 0)
-- Dependencies: 233
-- Name: uchastie_id_uchastiya_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.uchastie_id_uchastiya_seq', 50, true);


--
-- TOC entry 4959 (class 0 OID 0)
-- Dependencies: 228
-- Name: uroven_obrazovaniya_id_urovnya_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.uroven_obrazovaniya_id_urovnya_seq', 4, true);


--
-- TOC entry 4960 (class 0 OID 0)
-- Dependencies: 231
-- Name: variant_otveta_id_varianta_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.variant_otveta_id_varianta_seq', 103, true);


--
-- TOC entry 4961 (class 0 OID 0)
-- Dependencies: 230
-- Name: vopros_id_voprosa_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.vopros_id_voprosa_seq', 40, true);


--
-- TOC entry 4714 (class 2606 OID 24944)
-- Name: opros opros_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.opros
    ADD CONSTRAINT opros_pk PRIMARY KEY (id_oprosa);


--
-- TOC entry 4743 (class 2606 OID 25020)
-- Name: otvet otvet_opros_vopros_respondent_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.otvet
    ADD CONSTRAINT otvet_opros_vopros_respondent_unique UNIQUE (id_oprosa, id_voprosa, id_respondenta);


--
-- TOC entry 4745 (class 2606 OID 25018)
-- Name: otvet otvet_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.otvet
    ADD CONSTRAINT otvet_pk PRIMARY KEY (id_otveta);


--
-- TOC entry 4702 (class 2606 OID 24920)
-- Name: pol pol_naimenovanie_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pol
    ADD CONSTRAINT pol_naimenovanie_unique UNIQUE (naimenovanie);


--
-- TOC entry 4704 (class 2606 OID 24918)
-- Name: pol pol_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pol
    ADD CONSTRAINT pol_pk PRIMARY KEY (id_pola);


--
-- TOC entry 4706 (class 2606 OID 24927)
-- Name: region region_naimenovanie_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.region
    ADD CONSTRAINT region_naimenovanie_unique UNIQUE (naimenovanie);


--
-- TOC entry 4708 (class 2606 OID 24925)
-- Name: region region_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.region
    ADD CONSTRAINT region_pk PRIMARY KEY (id_regiona);


--
-- TOC entry 4730 (class 2606 OID 24979)
-- Name: respondent respondent_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.respondent
    ADD CONSTRAINT respondent_pk PRIMARY KEY (id_respondenta);


--
-- TOC entry 4735 (class 2606 OID 25002)
-- Name: uchastie uchastie_opros_respondent_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.uchastie
    ADD CONSTRAINT uchastie_opros_respondent_unique UNIQUE (id_oprosa, id_respondenta);


--
-- TOC entry 4737 (class 2606 OID 25000)
-- Name: uchastie uchastie_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.uchastie
    ADD CONSTRAINT uchastie_pk PRIMARY KEY (id_uchastiya);


--
-- TOC entry 4710 (class 2606 OID 24934)
-- Name: uroven_obrazovaniya uroven_obrazovaniya_naimenovanie_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.uroven_obrazovaniya
    ADD CONSTRAINT uroven_obrazovaniya_naimenovanie_unique UNIQUE (naimenovanie);


--
-- TOC entry 4712 (class 2606 OID 24932)
-- Name: uroven_obrazovaniya uroven_obrazovaniya_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.uroven_obrazovaniya
    ADD CONSTRAINT uroven_obrazovaniya_pk PRIMARY KEY (id_urovnya);


--
-- TOC entry 4722 (class 2606 OID 24967)
-- Name: variant_otveta variant_otveta_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.variant_otveta
    ADD CONSTRAINT variant_otveta_pk PRIMARY KEY (id_varianta);


--
-- TOC entry 4724 (class 2606 OID 24969)
-- Name: variant_otveta variant_otveta_vopros_poryadok_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.variant_otveta
    ADD CONSTRAINT variant_otveta_vopros_poryadok_unique UNIQUE (id_voprosa, poryadok);


--
-- TOC entry 4717 (class 2606 OID 24955)
-- Name: vopros vopros_opros_poryadok_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vopros
    ADD CONSTRAINT vopros_opros_poryadok_unique UNIQUE (id_oprosa, poryadok);


--
-- TOC entry 4719 (class 2606 OID 24953)
-- Name: vopros vopros_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vopros
    ADD CONSTRAINT vopros_pk PRIMARY KEY (id_voprosa);


--
-- TOC entry 4738 (class 1259 OID 25049)
-- Name: idx_otvet_data; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_otvet_data ON public.otvet USING btree (data_otveta);


--
-- TOC entry 4739 (class 1259 OID 25046)
-- Name: idx_otvet_opros_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_otvet_opros_id ON public.otvet USING btree (id_oprosa);


--
-- TOC entry 4740 (class 1259 OID 25048)
-- Name: idx_otvet_respondent_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_otvet_respondent_id ON public.otvet USING btree (id_respondenta);


--
-- TOC entry 4741 (class 1259 OID 25047)
-- Name: idx_otvet_vopros_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_otvet_vopros_id ON public.otvet USING btree (id_voprosa);


--
-- TOC entry 4725 (class 1259 OID 25050)
-- Name: idx_respondent_data_rozhdeniya; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_respondent_data_rozhdeniya ON public.respondent USING btree (data_rozhdeniya);


--
-- TOC entry 4726 (class 1259 OID 25051)
-- Name: idx_respondent_pol; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_respondent_pol ON public.respondent USING btree (id_pola);


--
-- TOC entry 4727 (class 1259 OID 25052)
-- Name: idx_respondent_region; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_respondent_region ON public.respondent USING btree (id_regiona);


--
-- TOC entry 4728 (class 1259 OID 25053)
-- Name: idx_respondent_uroven; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_respondent_uroven ON public.respondent USING btree (id_urovnya);


--
-- TOC entry 4731 (class 1259 OID 25045)
-- Name: idx_uchastie_data; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_uchastie_data ON public.uchastie USING btree (data_uchastiya);


--
-- TOC entry 4732 (class 1259 OID 25043)
-- Name: idx_uchastie_opros_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_uchastie_opros_id ON public.uchastie USING btree (id_oprosa);


--
-- TOC entry 4733 (class 1259 OID 25044)
-- Name: idx_uchastie_respondent_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_uchastie_respondent_id ON public.uchastie USING btree (id_respondenta);


--
-- TOC entry 4720 (class 1259 OID 25042)
-- Name: idx_variant_otveta_vopros_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_variant_otveta_vopros_id ON public.variant_otveta USING btree (id_voprosa);


--
-- TOC entry 4715 (class 1259 OID 25041)
-- Name: idx_vopros_opros_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vopros_opros_id ON public.vopros USING btree (id_oprosa);


--
-- TOC entry 4757 (class 2620 OID 25074)
-- Name: opros trigger_prodlenie_oprosa_pri_zakrytii; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_prodlenie_oprosa_pri_zakrytii BEFORE UPDATE OF status ON public.opros FOR EACH ROW WHEN ((((new.status)::text = 'closed'::text) AND ((old.status)::text <> 'closed'::text))) EXECUTE FUNCTION public.prodlenie_oprosa_esli_nekhvataet();


--
-- TOC entry 4962 (class 0 OID 0)
-- Dependencies: 4757
-- Name: TRIGGER trigger_prodlenie_oprosa_pri_zakrytii ON opros; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TRIGGER trigger_prodlenie_oprosa_pri_zakrytii ON public.opros IS 'Триггер продления опроса. Срабатывает при попытке перевести статус в "closed".
Если участников недостаточно (считается по UCHASTIE), опрос автоматически продлевается и остаётся активным.';


--
-- TOC entry 4753 (class 2606 OID 25021)
-- Name: otvet otvet_opros_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.otvet
    ADD CONSTRAINT otvet_opros_fk FOREIGN KEY (id_oprosa) REFERENCES public.opros(id_oprosa) ON DELETE CASCADE;


--
-- TOC entry 4754 (class 2606 OID 25031)
-- Name: otvet otvet_respondent_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.otvet
    ADD CONSTRAINT otvet_respondent_fk FOREIGN KEY (id_respondenta) REFERENCES public.respondent(id_respondenta) ON DELETE CASCADE;


--
-- TOC entry 4755 (class 2606 OID 25036)
-- Name: otvet otvet_variant_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.otvet
    ADD CONSTRAINT otvet_variant_fk FOREIGN KEY (id_varianta) REFERENCES public.variant_otveta(id_varianta) ON DELETE CASCADE;


--
-- TOC entry 4756 (class 2606 OID 25026)
-- Name: otvet otvet_vopros_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.otvet
    ADD CONSTRAINT otvet_vopros_fk FOREIGN KEY (id_voprosa) REFERENCES public.vopros(id_voprosa) ON DELETE CASCADE;


--
-- TOC entry 4748 (class 2606 OID 24980)
-- Name: respondent respondent_pol_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.respondent
    ADD CONSTRAINT respondent_pol_fk FOREIGN KEY (id_pola) REFERENCES public.pol(id_pola);


--
-- TOC entry 4749 (class 2606 OID 24985)
-- Name: respondent respondent_region_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.respondent
    ADD CONSTRAINT respondent_region_fk FOREIGN KEY (id_regiona) REFERENCES public.region(id_regiona);


--
-- TOC entry 4750 (class 2606 OID 24990)
-- Name: respondent respondent_uroven_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.respondent
    ADD CONSTRAINT respondent_uroven_fk FOREIGN KEY (id_urovnya) REFERENCES public.uroven_obrazovaniya(id_urovnya);


--
-- TOC entry 4751 (class 2606 OID 25003)
-- Name: uchastie uchastie_opros_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.uchastie
    ADD CONSTRAINT uchastie_opros_fk FOREIGN KEY (id_oprosa) REFERENCES public.opros(id_oprosa) ON DELETE CASCADE;


--
-- TOC entry 4752 (class 2606 OID 25008)
-- Name: uchastie uchastie_respondent_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.uchastie
    ADD CONSTRAINT uchastie_respondent_fk FOREIGN KEY (id_respondenta) REFERENCES public.respondent(id_respondenta) ON DELETE CASCADE;


--
-- TOC entry 4747 (class 2606 OID 24970)
-- Name: variant_otveta variant_otveta_vopros_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.variant_otveta
    ADD CONSTRAINT variant_otveta_vopros_fk FOREIGN KEY (id_voprosa) REFERENCES public.vopros(id_voprosa) ON DELETE CASCADE;


--
-- TOC entry 4746 (class 2606 OID 24956)
-- Name: vopros vopros_opros_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vopros
    ADD CONSTRAINT vopros_opros_fk FOREIGN KEY (id_oprosa) REFERENCES public.opros(id_oprosa) ON DELETE CASCADE;


-- Completed on 2026-01-20 06:23:11

--
-- PostgreSQL database dump complete
--

