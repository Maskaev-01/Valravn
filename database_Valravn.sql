--
-- PostgreSQL database dump
--

-- Dumped from database version 15.1
-- Dumped by pg_dump version 17.0

-- Started on 2025-06-23 18:41:18

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
-- TOC entry 3370 (class 1262 OID 54556)
-- Name: Valravn; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE "Valravn" WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'Russian_Russia.1251';


ALTER DATABASE "Valravn" OWNER TO postgres;

\connect "Valravn"

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
-- TOC entry 4 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: pg_database_owner
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO pg_database_owner;

--
-- TOC entry 3371 (class 0 OID 0)
-- Dependencies: 4
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: pg_database_owner
--

COMMENT ON SCHEMA public IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 214 (class 1259 OID 54557)
-- Name: budget; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.budget (
    id integer NOT NULL,
    price double precision,
    description character varying,
    data date,
    type character varying
);


ALTER TABLE public.budget OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 54589)
-- Name: categories_query; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.categories_query (
    string_agg text
);


ALTER TABLE public.categories_query OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 54638)
-- Name: column_definitions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.column_definitions (
    string_agg text
);


ALTER TABLE public.column_definitions OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 54630)
-- Name: inventory; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.inventory (
    id integer NOT NULL,
    owner text NOT NULL,
    item_name text NOT NULL,
    item_type text,
    subtype text,
    material text,
    color text,
    size text,
    find_type text,
    region text,
    place text,
    burial_number text,
    notes text
);


ALTER TABLE public.inventory OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 54629)
-- Name: inventory_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.inventory_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.inventory_id_seq OWNER TO postgres;

--
-- TOC entry 3372 (class 0 OID 0)
-- Dependencies: 220
-- Name: inventory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.inventory_id_seq OWNED BY public.inventory.id;


--
-- TOC entry 216 (class 1259 OID 54570)
-- Name: results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.results (
    income_nit double precision,
    expenses_nit double precision,
    debt_nit double precision,
    remains_now double precision,
    result_now double precision
);


ALTER TABLE public.results OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 54643)
-- Name: Имущество сводная; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public."Имущество сводная" AS
 SELECT inventory.owner,
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Ботинки'::text) THEN true
            ELSE false
        END) AS "Ботинки",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Бусы'::text) THEN true
            ELSE false
        END) AS "Бусы",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Бытовой нож'::text) THEN true
            ELSE false
        END) AS "Бытовой нож",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Игольница'::text) THEN true
            ELSE false
        END) AS "Игольница",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Кафтан'::text) THEN true
            ELSE false
        END) AS "Кафтан",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Кофта'::text) THEN true
            ELSE false
        END) AS "Кофта",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Кулон молот Тора'::text) THEN true
            ELSE false
        END) AS "Кулон молот Тора",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Меч'::text) THEN true
            ELSE false
        END) AS "Меч",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Молоточек (железо)'::text) THEN true
            ELSE false
        END) AS "Молоточек (железо)",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Ноговицы'::text) THEN true
            ELSE false
        END) AS "Ноговицы",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Нож'::text) THEN true
            ELSE false
        END) AS "Нож",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Носки'::text) THEN true
            ELSE false
        END) AS "Носки",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Обмотки'::text) THEN true
            ELSE false
        END) AS "Обмотки",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Обувь'::text) THEN true
            ELSE false
        END) AS "Обувь",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Платок'::text) THEN true
            ELSE false
        END) AS "Платок",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Платье'::text) THEN true
            ELSE false
        END) AS "Платье",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Плащ'::text) THEN true
            ELSE false
        END) AS "Плащ",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Плащевая игла'::text) THEN true
            ELSE false
        END) AS "Плащевая игла",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Подвески'::text) THEN true
            ELSE false
        END) AS "Подвески",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Подшлемник'::text) THEN true
            ELSE false
        END) AS "Подшлемник",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Пояс'::text) THEN true
            ELSE false
        END) AS "Пояс",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Пояс тканый на дощечках'::text) THEN true
            ELSE false
        END) AS "Пояс тканый на дощечках",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Ремень'::text) THEN true
            ELSE false
        END) AS "Ремень",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Рубаха'::text) THEN true
            ELSE false
        END) AS "Рубаха",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Серьга салтовская'::text) THEN true
            ELSE false
        END) AS "Серьга салтовская",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Сумка'::text) THEN true
            ELSE false
        END) AS "Сумка",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Сухарка'::text) THEN true
            ELSE false
        END) AS "Сухарка",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Топор'::text) THEN true
            ELSE false
        END) AS "Топор",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Фибула'::text) THEN true
            ELSE false
        END) AS "Фибула",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Фибула плащевая'::text) THEN true
            ELSE false
        END) AS "Фибула плащевая",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Фибулы парные'::text) THEN true
            ELSE false
        END) AS "Фибулы парные",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Хангерок'::text) THEN true
            ELSE false
        END) AS "Хангерок",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Худ'::text) THEN true
            ELSE false
        END) AS "Худ",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Чепец'::text) THEN true
            ELSE false
        END) AS "Чепец",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Череп'::text) THEN true
            ELSE false
        END) AS "Череп",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Черепушка'::text) THEN true
            ELSE false
        END) AS "Черепушка",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Шапка'::text) THEN true
            ELSE false
        END) AS "Шапка",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Шлем Гьёрмундбю с бармицей'::text) THEN true
            ELSE false
        END) AS "Шлем Гьёрмундбю с бармицей",
    bool_or(
        CASE
            WHEN (inventory.item_name = 'Штаны'::text) THEN true
            ELSE false
        END) AS "Штаны"
   FROM public.inventory
  GROUP BY inventory.owner
  ORDER BY inventory.owner;


ALTER VIEW public."Имущество сводная" OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 54573)
-- Name: Итог; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public."Итог" AS
 SELECT 'Общий расход(за всё время)'::text AS resault,
    sum(budget.price) AS sum
   FROM public.budget
  WHERE ((budget.price < (0)::double precision) AND ((budget.type)::text <> 'Долг'::text))
UNION ALL
 SELECT 'Общий доход(за всё время)'::text AS resault,
    sum(budget.price) AS sum
   FROM public.budget
  WHERE ((budget.price > (0)::double precision) AND ((budget.type)::text <> 'Погашение Долга'::text))
UNION ALL
 SELECT 'Долг'::text AS resault,
    sum(budget.price) AS sum
   FROM public.budget
  WHERE ((budget.type)::text = ANY ((ARRAY['Погашение Долга'::character varying, 'Долг'::character varying])::text[]))
UNION ALL
 SELECT 'Остаток фактический(на данный момент)'::text AS resault,
    sum(budget.price) AS sum
   FROM public.budget
  WHERE (((budget.price < (0)::double precision) AND ((budget.type)::text <> 'Долг'::text)) OR ((budget.price > (0)::double precision) AND ((budget.type)::text <> 'Погашение Долга'::text)))
UNION ALL
 SELECT 'Итог(за всё время)'::text AS resault,
    sum(budget.price) AS sum
   FROM public.budget
  WHERE (((budget.price < (0)::double precision) AND ((budget.type)::text <> 'Долг'::text)) OR ((budget.price > (0)::double precision) AND ((budget.type)::text <> 'Погашение Долга'::text)) OR ((budget.type)::text = ANY ((ARRAY['Погашение Долга'::character varying, 'Долг'::character varying])::text[])));


ALTER VIEW public."Итог" OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 54664)
-- Name: Сводная поимённо; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public."Сводная поимённо" AS
 SELECT budget.description,
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2024_08'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2024_08",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2024_09'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2024_09",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2024_10'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2024_10",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2024_11'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2024_11",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2024_12'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2024_12",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2025_01'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2025_01",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2025_02'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2025_02",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2025_03'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2025_03",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2025_04'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2025_04",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2025_05'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2025_05",
    sum(budget.price) AS "Итог"
   FROM public.budget
  WHERE ((budget.type)::text = 'Взнос'::text)
  GROUP BY budget.description
UNION ALL
 SELECT 'Итог'::character varying AS description,
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2024_08'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2024_08",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2024_09'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2024_09",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2024_10'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2024_10",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2024_11'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2024_11",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2024_12'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2024_12",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2025_01'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2025_01",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2025_02'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2025_02",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2025_03'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2025_03",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2025_04'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2025_04",
    sum(
        CASE
            WHEN ((((date_part('year'::text, budget.data))::text || '_'::text) || to_char(EXTRACT(month FROM budget.data), 'FM00'::text)) = '2025_05'::text) THEN budget.price
            ELSE (0)::double precision
        END) AS "2025_05",
    sum(budget.price) AS "Итог"
   FROM public.budget
  WHERE ((budget.type)::text = 'Взнос'::text);


ALTER VIEW public."Сводная поимённо" OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 54578)
-- Name: Сумма помесячно; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public."Сумма помесячно" AS
 SELECT a.year AS "год",
    a.month AS "месяц",
    COALESCE(a."Доход", (0)::double precision) AS "Доход",
    COALESCE(b."Расход", (0)::double precision) AS "Расход",
    COALESCE(c."Долг", (0)::double precision) AS "Долг",
    COALESCE(d."Итог", (0)::double precision) AS "Итог"
   FROM (((( SELECT date_part('year'::text, budget.data) AS year,
            date_part('month'::text, budget.data) AS month,
            sum(budget.price) AS "Доход"
           FROM public.budget
          WHERE ((budget.price > (0)::double precision) AND ((budget.type)::text <> 'Погашение Долга'::text))
          GROUP BY (date_part('year'::text, budget.data)), (date_part('month'::text, budget.data))
          ORDER BY (date_part('year'::text, budget.data)), (date_part('month'::text, budget.data))) a
     LEFT JOIN ( SELECT date_part('year'::text, budget.data) AS year,
            date_part('month'::text, budget.data) AS month,
            sum(budget.price) AS "Расход"
           FROM public.budget
          WHERE ((budget.price < (0)::double precision) AND ((budget.type)::text <> 'Долг'::text))
          GROUP BY (date_part('year'::text, budget.data)), (date_part('month'::text, budget.data))
          ORDER BY (date_part('year'::text, budget.data)), (date_part('month'::text, budget.data))) b ON (((a.year = b.year) AND (a.month = b.month))))
     LEFT JOIN ( SELECT date_part('year'::text, budget.data) AS year,
            date_part('month'::text, budget.data) AS month,
            sum(budget.price) AS "Долг"
           FROM public.budget
          WHERE ((budget.price < (0)::double precision) AND ((budget.type)::text = 'Долг'::text))
          GROUP BY (date_part('year'::text, budget.data)), (date_part('month'::text, budget.data))
          ORDER BY (date_part('year'::text, budget.data)), (date_part('month'::text, budget.data))) c ON (((a.year = c.year) AND (a.month = c.month))))
     LEFT JOIN ( SELECT date_part('year'::text, budget.data) AS year,
            date_part('month'::text, budget.data) AS month,
            sum(budget.price) AS "Итог"
           FROM public.budget
          GROUP BY (date_part('year'::text, budget.data)), (date_part('month'::text, budget.data))
          ORDER BY (date_part('year'::text, budget.data)), (date_part('month'::text, budget.data))) d ON (((a.year = d.year) AND (a.month = d.month))));


ALTER VIEW public."Сумма помесячно" OWNER TO postgres;

--
-- TOC entry 215 (class 1259 OID 54560)
-- Name: бюджет_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."бюджет_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."бюджет_id_seq" OWNER TO postgres;

--
-- TOC entry 3373 (class 0 OID 0)
-- Dependencies: 215
-- Name: бюджет_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."бюджет_id_seq" OWNED BY public.budget.id;


--
-- TOC entry 3206 (class 2604 OID 54561)
-- Name: budget id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.budget ALTER COLUMN id SET DEFAULT nextval('public."бюджет_id_seq"'::regclass);


--
-- TOC entry 3207 (class 2604 OID 54633)
-- Name: inventory id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory ALTER COLUMN id SET DEFAULT nextval('public.inventory_id_seq'::regclass);


--
-- TOC entry 3358 (class 0 OID 54557)
-- Dependencies: 214
-- Data for Name: budget; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.budget (id, price, description, data, type) FROM stdin;
1	1000	Владимир 	2024-08-01	Взнос
2	1000	Алексей	2024-08-03	Взнос
3	-10000	На ремонт машины (Алексей)	2024-08-01	Долг
4	-8000	На ремонт машины (Илья)	2024-09-16	Долг
5	1000	Магдалена	2024-08-11	Взнос
6	1000	Илья	2024-08-11	Взнос
7	1000	Настя	2024-08-18	Взнос
8	1000	Даниил	2024-08-18	Взнос
9	1000	Александр	2024-08-19	Взнос
10	1000	Роман	2024-08-27	Взнос
11	1000	Магдалена	2024-09-01	Взнос
12	1000	Алексей	2024-09-01	Взнос
13	1000	Владимир 	2024-09-02	Взнос
14	45.36	Капитализация	2024-09-03	Капитализация
15	1000	Александр	2024-09-05	Взнос
16	1000	Сергей	2024-09-05	Взнос
17	-6000	Древки копий	2024-09-12	Траты
18	1000	Даниил	2024-09-16	Взнос
19	1000	Настя	2024-09-16	Взнос
20	1000	Илья	2024-09-17	Взнос
21	-5000	Топоры	2024-09-22	Траты
22	1000	Владимир 	2024-10-01	Взнос
23	1000	Магдалена	2024-10-01	Взнос
24	1000	Алексей	2024-10-01	Взнос
25	70.05	Капитализация	2024-10-03	Капитализация
26	1000	Илья	2024-10-12	Взнос
27	1000	Александр	2024-10-14	Взнос
28	1000	Никита	2024-10-16	Взнос
30	10000	На ремонт машины (Алексей)	2024-11-01	Погашение Долга
31	1000	Даниил	2024-10-31	Взнос
32	1000	Настя	2024-10-31	Взнос
33	1000	Никита	2024-11-01	Взнос
34	1000	Владимир 	2024-11-02	Взнос
35	1000	Алексей	2024-11-02	Взнос
36	1000	Илья	2024-11-06	Взнос
37	87.32	Капитализация	2024-11-03	Капитализация
38	1000	Сергей	2024-10-30	Взнос
39	1000	Сергей	2024-11-15	Взнос
40	1000	Магдалена	2024-11-11	Взнос
41	1000	Алексей	2024-12-03	Взнос
42	1000	Никита	2024-12-10	Взнос
43	154.13	Капитализация	2024-12-03	Капитализация
44	1000	Владимир 	2024-12-10	Взнос
45	1000	Магдалена	2024-12-11	Взнос
46	1000	Илья	2024-12-21	Взнос
47	1000	Сергей	2024-12-27	Взнос
48	1000	Магдалена	2025-01-01	Взнос
49	1000	Алексей	2025-01-01	Взнос
50	1000	Роман Э	2025-01-01	Взнос
51	1000	Катя	2025-01-01	Взнос
52	1000	Владимир 	2025-01-01	Взнос
75	1000	Никита	2025-04-03	Взнос
29	8000	На ремонт машины (Илья)	2024-11-01	Погашение Долга
54	1000	Никита	2025-01-03	Взнос
55	1000	Никита	2025-02-01	Взнос
56	1000	Алексей	2025-02-01	Взнос
57	1000	Катя	2025-02-01	Взнос
58	1000	Александр	2024-11-30	Взнос
59	1000	Александр	2024-12-30	Взнос
53	203.91	Капитализация	2025-01-03	Капитализация
60	513.81	Капитализация	2025-02-03	Капитализация
62	1000	Настя	2024-11-30	Взнос
61	1000	Даниил	2024-11-30	Взнос
63	1	тест	1999-01-01	тест
64	1000	Александр	2025-01-30	Взнос
65	1000	Александр	2025-02-14	Взнос
66	1000	Магдалена	2025-02-04	Взнос
67	1000	Сергей	2025-01-30	Взнос
68	1000	Сергей	2025-02-02	Взнос
69	1000	Алексей	2025-03-05	Взнос
70	1000	Роман Э	2025-02-28	Взнос
71	1000	Владимир 	2025-03-05	Взнос
72	1000	Владимир 	2025-02-05	Взнос
73	549.62	Капитализация	2025-03-03	Капитализация
74	522.71	Капитализация	2025-04-03	Капитализация
77	-10500	Шатры	2025-03-19	Траты
76	-10000	Снаряжение	2025-03-25	Траты
78	1000	Александр	2025-03-30	Взнос
80	-8000	Расходы Русборг	2025-05-13	Траты
81	-13900	Расходы Русборг	2025-05-07	Траты
82	-5400	Расходы	2025-04-12	Траты
83	-2500	Расходы	2025-04-28	Траты
84	-3200	Расходы	2025-05-02	Траты
86	528.11	Капитализация	2025-05-03	Капитализация
87	1000	Владимир 	2025-05-06	Взнос
85	1000	Никита	2025-05-02	Взнос
79	1000	Александр	2025-05-30	Взнос
88	1000	Катя	2025-05-28	Взнос
89	1000	Катя	2025-03-28	Взнос
\.


--
-- TOC entry 3361 (class 0 OID 54589)
-- Dependencies: 219
-- Data for Name: categories_query; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.categories_query (string_agg) FROM stdin;
SUM(CASE WHEN CAST(DATE_PART('year', "data") AS TEXT) || CAST(DATE_PART('month', "data") AS TEXT) = '20249' THEN price ELSE 0 END) AS "20249", SUM(CASE WHEN CAST(DATE_PART('year', "data") AS TEXT) || CAST(DATE_PART('month', "data") AS TEXT) = '20251' THEN price ELSE 0 END) AS "20251", SUM(CASE WHEN CAST(DATE_PART('year', "data") AS TEXT) || CAST(DATE_PART('month', "data") AS TEXT) = '202410' THEN price ELSE 0 END) AS "202410", SUM(CASE WHEN CAST(DATE_PART('year', "data") AS TEXT) || CAST(DATE_PART('month', "data") AS TEXT) = '20248' THEN price ELSE 0 END) AS "20248", SUM(CASE WHEN CAST(DATE_PART('year', "data") AS TEXT) || CAST(DATE_PART('month', "data") AS TEXT) = '202411' THEN price ELSE 0 END) AS "202411", SUM(CASE WHEN CAST(DATE_PART('year', "data") AS TEXT) || CAST(DATE_PART('month', "data") AS TEXT) = '202412' THEN price ELSE 0 END) AS "202412"
\.


--
-- TOC entry 3364 (class 0 OID 54638)
-- Dependencies: 222
-- Data for Name: column_definitions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.column_definitions (string_agg) FROM stdin;
CASE WHEN item_name = 'Топор' THEN TRUE ELSE FALSE END AS "Топор", CASE WHEN item_name = 'Плащ' THEN TRUE ELSE FALSE END AS "Плащ", CASE WHEN item_name = 'Обувь' THEN TRUE ELSE FALSE END AS "Обувь", CASE WHEN item_name = 'Пояс' THEN TRUE ELSE FALSE END AS "Пояс", CASE WHEN item_name = 'Носки' THEN TRUE ELSE FALSE END AS "Носки", CASE WHEN item_name = 'Ремень' THEN TRUE ELSE FALSE END AS "Ремень", CASE WHEN item_name = 'Молоточек (железо)' THEN TRUE ELSE FALSE END AS "Молоточек (железо)", CASE WHEN item_name = 'Фибула' THEN TRUE ELSE FALSE END AS "Фибула", CASE WHEN item_name = 'Меч' THEN TRUE ELSE FALSE END AS "Меч", CASE WHEN item_name = 'Бытовой нож' THEN TRUE ELSE FALSE END AS "Бытовой нож", CASE WHEN item_name = 'Сухарка' THEN TRUE ELSE FALSE END AS "Сухарка", CASE WHEN item_name = 'Череп' THEN TRUE ELSE FALSE END AS "Череп", CASE WHEN item_name = 'Сумка' THEN TRUE ELSE FALSE END AS "Сумка", CASE WHEN item_name = 'Подвески' THEN TRUE ELSE FALSE END AS "Подвески", CASE WHEN item_name = 'Штаны' THEN TRUE ELSE FALSE END AS "Штаны", CASE WHEN item_name = 'Фибулы парные' THEN TRUE ELSE FALSE END AS "Фибулы парные", CASE WHEN item_name = 'Платок' THEN TRUE ELSE FALSE END AS "Платок", CASE WHEN item_name = 'Рубаха' THEN TRUE ELSE FALSE END AS "Рубаха", CASE WHEN item_name = 'Пояс тканый на дощечках' THEN TRUE ELSE FALSE END AS "Пояс тканый на дощечках", CASE WHEN item_name = 'Чепец' THEN TRUE ELSE FALSE END AS "Чепец", CASE WHEN item_name = 'Черепушка' THEN TRUE ELSE FALSE END AS "Черепушка", CASE WHEN item_name = 'Плащевая игла' THEN TRUE ELSE FALSE END AS "Плащевая игла", CASE WHEN item_name = 'Шапка' THEN TRUE ELSE FALSE END AS "Шапка", CASE WHEN item_name = 'Ботинки' THEN TRUE ELSE FALSE END AS "Ботинки", CASE WHEN item_name = 'Нож' THEN TRUE ELSE FALSE END AS "Нож", CASE WHEN item_name = 'Игольница' THEN TRUE ELSE FALSE END AS "Игольница", CASE WHEN item_name = 'Подшлемник' THEN TRUE ELSE FALSE END AS "Подшлемник", CASE WHEN item_name = 'Кафтан' THEN TRUE ELSE FALSE END AS "Кафтан", CASE WHEN item_name = 'Бусы' THEN TRUE ELSE FALSE END AS "Бусы", CASE WHEN item_name = 'Фибула плащевая' THEN TRUE ELSE FALSE END AS "Фибула плащевая", CASE WHEN item_name = 'Платье' THEN TRUE ELSE FALSE END AS "Платье", CASE WHEN item_name = 'Кофта' THEN TRUE ELSE FALSE END AS "Кофта", CASE WHEN item_name = 'Кулон молот Тора' THEN TRUE ELSE FALSE END AS "Кулон молот Тора", CASE WHEN item_name = 'Обмотки' THEN TRUE ELSE FALSE END AS "Обмотки", CASE WHEN item_name = 'Ноговицы' THEN TRUE ELSE FALSE END AS "Ноговицы", CASE WHEN item_name = 'Худ' THEN TRUE ELSE FALSE END AS "Худ", CASE WHEN item_name = 'Шлем Гьёрмундбю с бармицей' THEN TRUE ELSE FALSE END AS "Шлем Гьёрмундбю с бармицей", CASE WHEN item_name = 'Хангерок' THEN TRUE ELSE FALSE END AS "Хангерок", CASE WHEN item_name = 'Серьга салтовская' THEN TRUE ELSE FALSE END AS "Серьга салтовская"
\.


--
-- TOC entry 3363 (class 0 OID 54630)
-- Dependencies: 221
-- Data for Name: inventory; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inventory (id, owner, item_name, item_type, subtype, material, color, size, find_type, region, place, burial_number, notes) FROM stdin;
47	Ромэо	Нож	оружие	нож	железо	\N	\N	\N	\N	\N	\N	\N
50	Ромэо	Носки	одежда	носки	шерсть	\N	\N	\N	\N	\N	\N	\N
57	Ромэо	Подшлемник	аксессуары	подшлемник	\N	\N	\N	\N	\N	\N	\N	современный
54	Ромэо	Серьга салтовская	украшения	серьга	металл	\N	\N	\N	\N	\N	\N	салтовская
32	Настя	Чепец	одежда	чепец	лён	\N	\N	\N	\N	\N	\N	\N
63	Никита	Обмотки	одежда	обмотки	\N	\N	\N	\N	\N	\N	\N	\N
66	Никита	Бытовой нож	оружие	нож	железо	\N	\N	\N	\N	\N	\N	\N
37	Настя	Бусы	украшения	бусы	стекло/янтарь	\N	\N	\N	\N	\N	\N	\N
58	Ромэо	Топор	оружие	топор	железо	\N	\N	тип 4	\N	\N	\N	не посажен
29	Настя	Платье	одежда	платье	лён	некрашеный	\N	\N	\N	\N	\N	\N
44	Ромэо	Рубаха	одежда	рубаха	лён	\N	\N	\N	\N	\N	\N	\N
3	Мэг	Кафтан	одежда	кафтан	лён	\N	\N	\N	\N	\N	\N	\N
4	Мэг	Обувь	обувь	ботинки	кожа	\N	\N	\N	\N	\N	\N	\N
5	Мэг	Пояс	аксессуары	ремень	кожа	\N	\N	\N	\N	\N	\N	\N
6	Мэг	Нож	оружие	нож	железо	\N	\N	\N	\N	\N	\N	\N
7	Мэг	Бусы	украшения	бусы	стекло/янтарь	\N	\N	\N	\N	\N	\N	\N
8	Мэг	Платок	аксессуары	платок	лён	\N	\N	\N	\N	\N	\N	\N
9	Мэг	Чепец	одежда	чепец	лён	\N	\N	\N	\N	\N	\N	\N
10	Мэг	Игольница	инструменты	игольница	дерево	\N	\N	\N	\N	\N	\N	\N
11	Мэг	Подвески	украшения	подвеска	металл	\N	\N	\N	\N	\N	\N	\N
12	Мэг	Кулон молот Тора	украшения	кулон	металл	\N	\N	\N	\N	\N	\N	\N
14	Мэг	Фибула	украшения	фибула	металл	\N	\N	\N	\N	\N	\N	на кафтан
39	Настя	Фибула	украшения	фибула	металл	\N	\N	\N	\N	\N	\N	плащевая
45	Ромэо	Штаны	одежда	штаны	лён	\N	\N	\N	Торсберг	\N	\N	
16	Даня	Кофта	одежда	кофта	\N	\N	\N	\N	\N	\N	\N	\N
17	Даня	Кофта	одежда	кофта	\N	\N	\N	\N	\N	\N	\N	\N
18	Даня	Ремень	аксессуары	ремень	кожа	\N	\N	\N	\N	\N	\N	\N
19	Даня	Ремень	аксессуары	ремень	кожа	\N	\N	\N	\N	\N	\N	\N
20	Даня	Плащ	одежда	плащ	\N	\N	\N	\N	\N	\N	\N	\N
21	Даня	Худ	аксессуары	худ	\N	\N	\N	\N	\N	\N	\N	\N
22	Даня	Шапка	одежда	шапка	\N	\N	\N	\N	\N	\N	\N	\N
23	Даня	Штаны	одежда	штаны	\N	\N	\N	\N	\N	\N	\N	\N
2	Мэг	Платье	одежда	платье	лён	\N	\N	\N	\N	\N	\N	верхнее
25	Даня	Ноговицы	одежда	ноговицы	\N	\N	\N	\N	\N	\N	\N	\N
26	Даня	Обувь	обувь	ботинки	кожа	\N	\N	\N	\N	\N	\N	\N
27	Даня	Нож	оружие	нож	железо	\N	\N	\N	\N	\N	\N	\N
28	Даня	Череп	артефакты	череп	кость	\N	\N	\N	\N	\N	\N	\N
30	Настя	Платье	одежда	платье	лён	цветной	\N	\N	\N	\N	\N	\N
60	Никита	Рубаха	одежда	рубаха	лён	\N	\N	\N	\N	\N	\N	\N
31	Настя	Хангерок	одежда	хангерок	лён	\N	\N	\N	\N	\N	\N	\N
53	Ромэо	Плащевая игла	инструменты	плащевая игла	металл	\N	\N	\N	Бирка	\N	\N	бирка
33	Настя	Носки	одежда	носки	шерсть	\N	\N	\N	\N	\N	\N	\N
34	Настя	Пояс	аксессуары	ремень	кожа	\N	\N	\N	\N	\N	\N	\N
35	Настя	Нож	оружие	нож	железо	\N	\N	\N	\N	\N	\N	\N
15	Мэг	Сумка	аксессуары	сумка	дерево/кожа	\N	\N	\N	\N	\N	\N	 с деревянными плашками
38	Настя	Фибулы парные	украшения	фибула	металл	\N	\N	\N	\N	\N	\N	парные
59	Никита	Рубаха	одежда	рубаха	шерсть	\N	\N	\N	\N	\N	\N	\N
13	Мэг	Фибула	украшения	фибула	металл	\N	\N	\N	\N	\N	\N	на камизу
41	Настя	Плащ	одежда	плащ	\N	\N	\N	\N	\N	\N	\N	\N
42	Настя	Черепушка	артефакты	череп	кость	\N	\N	\N	\N	\N	\N	\N
36	Настя	Сумка	аксессуары	сумка	лён	\N	\N	\N	Гогстед	\N	\N	гогстед
43	Ромэо	Рубаха	одежда	рубаха	шерсть	\N	\N	\N	\N	\N	\N	\N
40	Настя	Фибула	украшения	фибула	металл	\N	\N	\N	\N	\N	\N	на ворот
48	Ромэо	Обмотки	одежда	обмотки	\N	\N	\N	\N	\N	\N	\N	\N
51	Ромэо	Плащ	одежда	плащ	\N	\N	\N	\N	\N	\N	\N	\N
62	Никита	Худ	аксессуары	худ	\N	\N	\N	\N	Скьёльдехамн	\N	\N	
56	Ромэо	Шлем Гьёрмундбю с бармицей	оружие	шлем	металл	\N	\N	\N	\N	\N	\N	гьёрмундбю с бармицей
1	Мэг	Рубаха	одежда	рубаха	лён	\N	\N	\N	\N	\N	\N	нижнее
52	Ромэо	Худ	аксессуары	худ	\N	\N	\N	\N	Хедебю	\N	\N	Хедебю
64	Никита	Ботинки	обувь	ботинки	кожа	\N	\N	тип 3	Хедебю	\N	\N	
61	Никита	Штаны	одежда	штаны	лён	\N	\N	\N	Торсберг	\N	\N	
68	Никита	Меч	оружие	меч	сталь	\N	\N	тип Y	\N	\N	\N	каролинг
46	Ромэо	Пояс	аксессуары	ремень	кожа	\N	\N	\N	\N	\N	bj 750	
24	Даня	Рубаха	одежда	рубаха	\N	\N	\N	\N	\N	\N	\N	нижнее
55	Ромэо	Молоточек (железо)	украшения	молоточек	железо	\N	\N	\N	\N	\N	\N	\N
93	Ромзес	Нож	оружие	нож	железо	\N	\N	\N	\N	\N	\N	\N
87	Света	Пояс тканый на дощечках	аксессуары	ремень	ткань	\N	\N	\N	\N	\N	\N	тканый на дощечках
88	Света	Нож	оружие	нож	железо	\N	\N	\N	\N	\N	\N	\N
84	Света	Ботинки	обувь	ботинки	кожа	\N	\N	тип 3	Хедебю	\N	\N	
73	Катя	Фибула плащевая	украшения	фибула	металл	\N	\N	\N	\N	\N	\N	плащевая
74	Катя	Фибула плащевая	украшения	фибула	металл	\N	\N	\N	\N	\N	\N	плащевая
92	Ромзес	Пояс	аксессуары	ремень	кожа	\N	\N	\N	Готланд	\N	\N	
75	Катя	Нож	оружие	нож	железо	\N	\N	\N	\N	\N	\N	\N
76	Катя	Бусы	украшения	бусы	стекло/янтарь	\N	\N	\N	\N	\N	\N	\N
78	Катя	Плащ	одежда	плащ	\N	\N	\N	\N	\N	\N	\N	\N
79	Катя	Ботинки	обувь	ботинки	кожа	\N	38-39	\N	\N	\N	\N	\N
85	Света	Платок	аксессуары	платок	лён	\N	\N	\N	\N	\N	\N	\N
71	Катя	Пояс	аксессуары	ремень	кожа	\N	\N	\N	Бирка	\N	\N	
72	Катя	Пояс	аксессуары	ремень	кожа	\N	\N	\N	Бирка	\N	\N	
65	Никита	Пояс	аксессуары	ремень	кожа	\N	\N	\N	Бирка	\N	\N	
67	Никита	Топор	оружие	топор	железо	\N	\N	тип 4	\N	\N	\N	тип по Кирпичникову
80	Катя	Носки	одежда	носки	шерсть	\N	\N	\N	\N	\N	\N	\N
91	Ромзес	Обмотки	одежда	обмотки	шерсть	оливковые	\N	\N	\N	\N	\N	\N
82	Света	Платье	одежда	платье	лён	\N	\N	\N	\N	\N	\N	 верхнее
69	Катя	Платье	одежда	платье	лён	\N	\N	\N	\N	\N	\N	\N
81	Света	Платье	одежда	платье	лён	\N	\N	\N	\N	\N	\N	 нижнее
70	Катя	Платье	одежда	платье	шерсть	\N	\N	\N	\N	\N	\N	\N
89	Ромзес	Рубаха	одежда	рубаха	лён	ненатурально белённая	\N	\N	\N	\N	\N	\N
77	Катя	Сумка	аксессуары	сумка	дерево/кожа	\N	\N	\N	\N	\N	\N	 на планках
86	Света	Сухарка	аксессуары	сумка	лён	\N	\N	\N	\N	\N	\N	\N
90	Ромзес	Штаны	одежда	штаны	лён	ненатурально белённая	\N	\N	\N	\N	\N	рваная
83	Света	Фибула	украшения	фибула	металл	\N	\N	\N	Хедебю	\N	\N	на платье
49	Ромэо	Ботинки	обувь	ботинки	кожа	\N	44-45	тип 3	\N	\N	\N	
\.


--
-- TOC entry 3360 (class 0 OID 54570)
-- Dependencies: 216
-- Data for Name: results; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.results (income_nit, expenses_nit, debt_nit, remains_now, result_now) FROM stdin;
\.


--
-- TOC entry 3374 (class 0 OID 0)
-- Dependencies: 220
-- Name: inventory_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.inventory_id_seq', 93, true);


--
-- TOC entry 3375 (class 0 OID 0)
-- Dependencies: 215
-- Name: бюджет_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."бюджет_id_seq"', 89, true);


--
-- TOC entry 3211 (class 2606 OID 54637)
-- Name: inventory inventory_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory
    ADD CONSTRAINT inventory_pkey PRIMARY KEY (id);


--
-- TOC entry 3209 (class 2606 OID 54563)
-- Name: budget бюджет_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.budget
    ADD CONSTRAINT "бюджет_pkey" PRIMARY KEY (id);


-- Completed on 2025-06-23 18:41:19

--
-- PostgreSQL database dump complete
--

