--
-- PostgreSQL database dump
--

\restrict O58z81XQDnROhSkDDJqIGDTRMAXoriubZiqn09kdKXUnO2E9rVLAWOJXvRoM67X

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

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

ALTER TABLE IF EXISTS ONLY public.use_case_runs DROP CONSTRAINT IF EXISTS use_case_runs_use_case_id_fkey;
ALTER TABLE IF EXISTS ONLY public.metadata_rules DROP CONSTRAINT IF EXISTS metadata_rules_use_case_id_fkey;
ALTER TABLE IF EXISTS ONLY public.metadata_rules DROP CONSTRAINT IF EXISTS metadata_rules_node_id_fkey;
ALTER TABLE IF EXISTS ONLY public.history_snapshots DROP CONSTRAINT IF EXISTS history_snapshots_use_case_id_fkey;
ALTER TABLE IF EXISTS ONLY public.hierarchy_bridge DROP CONSTRAINT IF EXISTS hierarchy_bridge_parent_node_id_fkey;
ALTER TABLE IF EXISTS ONLY public.hierarchy_bridge DROP CONSTRAINT IF EXISTS hierarchy_bridge_leaf_node_id_fkey;
ALTER TABLE IF EXISTS ONLY public.fact_pnl_entries DROP CONSTRAINT IF EXISTS fact_pnl_entries_use_case_id_fkey;
ALTER TABLE IF EXISTS ONLY public.fact_calculated_results DROP CONSTRAINT IF EXISTS fact_calculated_results_run_id_fkey;
ALTER TABLE IF EXISTS ONLY public.fact_calculated_results DROP CONSTRAINT IF EXISTS fact_calculated_results_node_id_fkey;
ALTER TABLE IF EXISTS ONLY public.fact_calculated_results DROP CONSTRAINT IF EXISTS fact_calculated_results_calculation_run_id_fkey;
ALTER TABLE IF EXISTS ONLY public.dim_hierarchy DROP CONSTRAINT IF EXISTS dim_hierarchy_parent_node_id_fkey;
ALTER TABLE IF EXISTS ONLY public.calculation_runs DROP CONSTRAINT IF EXISTS calculation_runs_use_case_id_fkey;
DROP INDEX IF EXISTS public.ix_fact_pnl_entries_use_case_id;
DROP INDEX IF EXISTS public.ix_fact_pnl_entries_scenario;
DROP INDEX IF EXISTS public.ix_fact_pnl_entries_pnl_date;
DROP INDEX IF EXISTS public.ix_fact_calculated_results_calc_run_id;
DROP INDEX IF EXISTS public.ix_dim_dictionary_tech_id;
DROP INDEX IF EXISTS public.ix_dim_dictionary_category;
DROP INDEX IF EXISTS public.ix_calculation_runs_use_case_id;
DROP INDEX IF EXISTS public.ix_calculation_runs_pnl_date;
DROP INDEX IF EXISTS public.ix_calculation_runs_date_use_case;
ALTER TABLE IF EXISTS ONLY public.use_cases DROP CONSTRAINT IF EXISTS use_cases_pkey;
ALTER TABLE IF EXISTS ONLY public.use_case_runs DROP CONSTRAINT IF EXISTS use_case_runs_pkey;
ALTER TABLE IF EXISTS ONLY public.metadata_rules DROP CONSTRAINT IF EXISTS uq_use_case_node;
ALTER TABLE IF EXISTS ONLY public.dim_dictionary DROP CONSTRAINT IF EXISTS uq_category_tech_id;
ALTER TABLE IF EXISTS ONLY public.report_registrations DROP CONSTRAINT IF EXISTS report_registrations_pkey;
ALTER TABLE IF EXISTS ONLY public.metadata_rules DROP CONSTRAINT IF EXISTS metadata_rules_pkey;
ALTER TABLE IF EXISTS ONLY public.history_snapshots DROP CONSTRAINT IF EXISTS history_snapshots_pkey;
ALTER TABLE IF EXISTS ONLY public.hierarchy_bridge DROP CONSTRAINT IF EXISTS hierarchy_bridge_pkey;
ALTER TABLE IF EXISTS ONLY public.fact_pnl_gold DROP CONSTRAINT IF EXISTS fact_pnl_gold_pkey;
ALTER TABLE IF EXISTS ONLY public.fact_pnl_entries DROP CONSTRAINT IF EXISTS fact_pnl_entries_pkey;
ALTER TABLE IF EXISTS ONLY public.fact_calculated_results DROP CONSTRAINT IF EXISTS fact_calculated_results_pkey;
ALTER TABLE IF EXISTS ONLY public.dim_hierarchy DROP CONSTRAINT IF EXISTS dim_hierarchy_pkey;
ALTER TABLE IF EXISTS ONLY public.dim_dictionary DROP CONSTRAINT IF EXISTS dim_dictionary_pkey;
ALTER TABLE IF EXISTS ONLY public.calculation_runs DROP CONSTRAINT IF EXISTS calculation_runs_pkey;
ALTER TABLE IF EXISTS ONLY public.alembic_version DROP CONSTRAINT IF EXISTS alembic_version_pkc;
ALTER TABLE IF EXISTS public.metadata_rules ALTER COLUMN rule_id DROP DEFAULT;
DROP TABLE IF EXISTS public.use_cases;
DROP TABLE IF EXISTS public.use_case_runs;
DROP TABLE IF EXISTS public.report_registrations;
DROP SEQUENCE IF EXISTS public.metadata_rules_rule_id_seq;
DROP TABLE IF EXISTS public.metadata_rules;
DROP TABLE IF EXISTS public.history_snapshots;
DROP TABLE IF EXISTS public.hierarchy_bridge;
DROP TABLE IF EXISTS public.fact_pnl_gold;
DROP TABLE IF EXISTS public.fact_pnl_entries;
DROP TABLE IF EXISTS public.fact_calculated_results;
DROP TABLE IF EXISTS public.dim_hierarchy;
DROP TABLE IF EXISTS public.dim_dictionary;
DROP TABLE IF EXISTS public.calculation_runs;
DROP TABLE IF EXISTS public.alembic_version;
DROP TYPE IF EXISTS public.usecasestatus;
DROP TYPE IF EXISTS public.runstatus;
--
-- Name: runstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.runstatus AS ENUM (
    'IN_PROGRESS',
    'COMPLETED',
    'FAILED'
);


--
-- Name: usecasestatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.usecasestatus AS ENUM (
    'DRAFT',
    'ACTIVE',
    'ARCHIVED'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: calculation_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.calculation_runs (
    id uuid NOT NULL,
    pnl_date date NOT NULL,
    use_case_id uuid NOT NULL,
    run_name character varying(200) NOT NULL,
    executed_at timestamp without time zone DEFAULT now() NOT NULL,
    status character varying(20) DEFAULT 'IN_PROGRESS'::character varying NOT NULL,
    triggered_by character varying(100) NOT NULL,
    calculation_duration_ms integer
);


--
-- Name: dim_dictionary; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dim_dictionary (
    id uuid NOT NULL,
    category character varying(50) NOT NULL,
    tech_id character varying(100) NOT NULL,
    display_name character varying(200) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: dim_hierarchy; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dim_hierarchy (
    node_id character varying(200) NOT NULL,
    parent_node_id character varying(200),
    node_name character varying NOT NULL,
    depth integer NOT NULL,
    is_leaf boolean NOT NULL,
    atlas_source character varying
);


--
-- Name: fact_calculated_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fact_calculated_results (
    result_id uuid NOT NULL,
    run_id uuid NOT NULL,
    node_id character varying(200) NOT NULL,
    measure_vector jsonb NOT NULL,
    plug_vector jsonb,
    is_override boolean NOT NULL,
    is_reconciled boolean NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    calculation_run_id uuid
);


--
-- Name: fact_pnl_entries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fact_pnl_entries (
    id uuid NOT NULL,
    use_case_id uuid NOT NULL,
    pnl_date date NOT NULL,
    category_code character varying(50) NOT NULL,
    amount numeric(18,2) NOT NULL,
    scenario character varying(20) NOT NULL,
    audit_metadata jsonb,
    daily_amount numeric(18,2) NOT NULL,
    wtd_amount numeric(18,2) NOT NULL,
    ytd_amount numeric(18,2) NOT NULL
);


--
-- Name: fact_pnl_gold; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fact_pnl_gold (
    fact_id uuid NOT NULL,
    account_id character varying(50) NOT NULL,
    cc_id character varying(200) NOT NULL,
    book_id character varying(50) NOT NULL,
    strategy_id character varying(50) NOT NULL,
    trade_date date NOT NULL,
    daily_pnl numeric(18,2) NOT NULL,
    mtd_pnl numeric(18,2) NOT NULL,
    ytd_pnl numeric(18,2) NOT NULL,
    pytd_pnl numeric(18,2) NOT NULL
);


--
-- Name: hierarchy_bridge; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hierarchy_bridge (
    bridge_id uuid NOT NULL,
    parent_node_id character varying(200) NOT NULL,
    leaf_node_id character varying(200) NOT NULL,
    structure_id character varying NOT NULL,
    path_length integer NOT NULL
);


--
-- Name: TABLE hierarchy_bridge; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.hierarchy_bridge IS 'Flattened parent-to-leaf mappings for fast aggregation';


--
-- Name: history_snapshots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.history_snapshots (
    snapshot_id uuid NOT NULL,
    use_case_id uuid NOT NULL,
    snapshot_name character varying(200) NOT NULL,
    snapshot_date timestamp with time zone DEFAULT now() NOT NULL,
    created_by character varying(100) NOT NULL,
    rules_snapshot jsonb,
    results_snapshot jsonb,
    notes text,
    version_tag character varying(50)
);


--
-- Name: metadata_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metadata_rules (
    rule_id integer NOT NULL,
    use_case_id uuid NOT NULL,
    node_id character varying(200) NOT NULL,
    predicate_json jsonb,
    sql_where text NOT NULL,
    logic_en text,
    last_modified_by character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    last_modified_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: metadata_rules_rule_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.metadata_rules_rule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: metadata_rules_rule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.metadata_rules_rule_id_seq OWNED BY public.metadata_rules.rule_id;


--
-- Name: report_registrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.report_registrations (
    report_id uuid NOT NULL,
    report_name character varying(200) NOT NULL,
    atlas_structure_id character varying(200) NOT NULL,
    selected_measures jsonb NOT NULL,
    selected_dimensions jsonb,
    owner_id character varying(100) DEFAULT 'default_user'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    measure_scopes jsonb,
    dimension_scopes jsonb
);


--
-- Name: use_case_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.use_case_runs (
    run_id uuid NOT NULL,
    use_case_id uuid NOT NULL,
    version_tag character varying NOT NULL,
    run_timestamp timestamp without time zone DEFAULT now() NOT NULL,
    parameters_snapshot jsonb,
    status public.runstatus NOT NULL,
    triggered_by character varying NOT NULL,
    calculation_duration_ms integer
);


--
-- Name: use_cases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.use_cases (
    use_case_id uuid NOT NULL,
    name character varying NOT NULL,
    description text,
    owner_id character varying NOT NULL,
    atlas_structure_id character varying NOT NULL,
    status public.usecasestatus NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: metadata_rules rule_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metadata_rules ALTER COLUMN rule_id SET DEFAULT nextval('public.metadata_rules_rule_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
aa275d79876c
\.


--
-- Data for Name: calculation_runs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.calculation_runs (id, pnl_date, use_case_id, run_name, executed_at, status, triggered_by, calculation_duration_ms) FROM stdin;
\.


--
-- Data for Name: dim_dictionary; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dim_dictionary (id, category, tech_id, display_name, created_at) FROM stdin;
0e6957d7-6a6c-4573-9081-34917ad95fac	BOOK	EQ_CORE_NYC	Core Equities - New York	2025-12-24 02:36:28.790357
6b7c68a9-137f-4d8d-a764-6ec989ee9a8b	BOOK	EQ_CORE_LDN	Core Equities - London	2025-12-24 02:36:28.790357
a5c33905-8d7f-4a89-a8f3-fe1749ab5eb6	BOOK	FX_SPOT_NYC	FX Spot Trading - New York	2025-12-24 02:36:28.790357
136e1af1-6c0a-4baf-afce-38e28d9f50b0	BOOK	FX_SPOT_LDN	FX Spot Trading - London	2025-12-24 02:36:28.790357
2aa8a80a-9e57-4caa-bcf0-ccef0512728b	BOOK	FI_GOVT_US	Fixed Income - Government US	2025-12-24 02:36:28.790357
5cc94ddf-5b8b-494d-843a-6639a90b2a8f	STRATEGY	STRAT_MARKET_MAKING	Market Making Strategy	2025-12-24 02:36:28.790357
05bb115b-2846-4ea2-aa4d-bca87e2d7647	STRATEGY	STRAT_ARBITRAGE	Arbitrage Strategy	2025-12-24 02:36:28.790357
05e3864e-b952-45bc-be18-4646ffe1f935	STRATEGY	STRAT_PROP_TRADING	Proprietary Trading Strategy	2025-12-24 02:36:28.790357
5c039661-98df-4749-ac56-104354bb4f87	STRATEGY	STRAT_HEDGE	Hedging Strategy	2025-12-24 02:36:28.790357
384e943b-886b-49b1-9b13-04252b6b8560	PRODUCT_TYPE	PROD_EQUITY	Equity Products	2025-12-24 02:36:28.790357
bdec2423-adfd-454c-88d9-bd49ed2de901	PRODUCT_TYPE	PROD_FX	Foreign Exchange Products	2025-12-24 02:36:28.790357
608fac4e-5adc-4a85-b3bc-cb735aa44043	PRODUCT_TYPE	PROD_FIXED_INCOME	Fixed Income Products	2025-12-24 02:36:28.790357
fb4d5bac-ba18-456d-9f48-3442da80b986	PRODUCT_TYPE	PROD_DERIVATIVES	Derivatives Products	2025-12-24 02:36:28.790357
c5f7c142-1e75-4e59-b008-8452dad1f480	LEGAL_ENTITY	ENTITY_US_HOLDINGS	US Holdings Inc.	2025-12-24 02:36:28.790357
0a7f0a5e-c359-4c0f-af05-5cd03182bcae	LEGAL_ENTITY	ENTITY_UK_LTD	UK Trading Limited	2025-12-24 02:36:28.790357
ecda15f4-7bb9-483a-8abe-26362aec91b0	LEGAL_ENTITY	ENTITY_SG_PTE	Singapore Private Limited	2025-12-24 02:36:28.790357
e5dc0205-79a6-4471-9494-288325e39845	RISK_OFFICER	RO_NYC_001	Risk Officer - New York Region	2025-12-24 02:36:28.790357
5f6ca475-deec-4a9e-af24-f204c2e97673	RISK_OFFICER	RO_LDN_001	Risk Officer - London Region	2025-12-24 02:36:28.790357
e41add0f-6e7a-4192-bca0-3fde4c699836	RISK_OFFICER	RO_SG_001	Risk Officer - Singapore Region	2025-12-24 02:36:28.790357
\.


--
-- Data for Name: dim_hierarchy; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dim_hierarchy (node_id, parent_node_id, node_name, depth, is_leaf, atlas_source) FROM stdin;
STERLING_TRADE_001	\N	TRADE_001	0	t	STERLING
STERLING_TRADE_002	\N	TRADE_002	0	t	STERLING
STERLING_TRADE_003	\N	TRADE_003	0	t	STERLING
STERLING_TRADE_004	\N	TRADE_004	0	t	STERLING
STERLING_TRADE_005	\N	TRADE_005	0	t	STERLING
STERLING_TRADE_006	\N	TRADE_006	0	t	STERLING
STERLING_TRADE_007	\N	TRADE_007	0	t	STERLING
STERLING_TRADE_008	\N	TRADE_008	0	t	STERLING
STERLING_TRADE_009	\N	TRADE_009	0	t	STERLING
STERLING_TRADE_010	\N	TRADE_010	0	t	STERLING
STERLING_TRADE_011	\N	TRADE_011	0	t	STERLING
STERLING_TRADE_012	\N	TRADE_012	0	t	STERLING
STERLING_TRADE_013	\N	TRADE_013	0	t	STERLING
STERLING_TRADE_014	\N	TRADE_014	0	t	STERLING
STERLING_TRADE_015	\N	TRADE_015	0	t	STERLING
STERLING_TRADE_016	\N	TRADE_016	0	t	STERLING
STERLING_TRADE_017	\N	TRADE_017	0	t	STERLING
STERLING_TRADE_018	\N	TRADE_018	0	t	STERLING
STERLING_TRADE_019	\N	TRADE_019	0	t	STERLING
STERLING_TRADE_020	\N	TRADE_020	0	t	STERLING
STERLING_TRADE_021	\N	TRADE_021	0	t	STERLING
STERLING_TRADE_022	\N	TRADE_022	0	t	STERLING
STERLING_TRADE_023	\N	TRADE_023	0	t	STERLING
STERLING_TRADE_024	\N	TRADE_024	0	t	STERLING
STERLING_TRADE_025	\N	TRADE_025	0	t	STERLING
STERLING_TRADE_026	\N	TRADE_026	0	t	STERLING
STERLING_TRADE_027	\N	TRADE_027	0	t	STERLING
STERLING_TRADE_028	\N	TRADE_028	0	t	STERLING
STERLING_TRADE_029	\N	TRADE_029	0	t	STERLING
STERLING_TRADE_030	\N	TRADE_030	0	t	STERLING
TRADE_011	ROOT	TRADE_011	1	t	Mock Atlas Structure v1
TRADE_015	ROOT	TRADE_015	1	t	Mock Atlas Structure v1
TRADE_003	ROOT	TRADE_003	1	t	Mock Atlas Structure v1
TRADE_006	ROOT	TRADE_006	1	t	Mock Atlas Structure v1
TRADE_008	ROOT	TRADE_008	1	t	Mock Atlas Structure v1
TRADE_022	ROOT	TRADE_022	1	t	Mock Atlas Structure v1
TRADE_024	ROOT	TRADE_024	1	t	Mock Atlas Structure v1
TRADE_004	ROOT	TRADE_004	1	t	Mock Atlas Structure v1
TRADE_021	ROOT	TRADE_021	1	t	Mock Atlas Structure v1
TRADE_027	ROOT	TRADE_027	1	t	Mock Atlas Structure v1
TRADE_001	ROOT	TRADE_001	1	t	Mock Atlas Structure v1
TRADE_028	ROOT	TRADE_028	1	t	Mock Atlas Structure v1
TRADE_016	ROOT	TRADE_016	1	t	Mock Atlas Structure v1
TRADE_020	ROOT	TRADE_020	1	t	Mock Atlas Structure v1
TRADE_005	ROOT	TRADE_005	1	t	Mock Atlas Structure v1
TRADE_026	ROOT	TRADE_026	1	t	Mock Atlas Structure v1
TRADE_013	ROOT	TRADE_013	1	t	Mock Atlas Structure v1
TRADE_017	ROOT	TRADE_017	1	t	Mock Atlas Structure v1
TRADE_030	ROOT	TRADE_030	1	t	Mock Atlas Structure v1
TRADE_002	ROOT	TRADE_002	1	t	Mock Atlas Structure v1
TRADE_025	ROOT	TRADE_025	1	t	Mock Atlas Structure v1
TRADE_018	ROOT	TRADE_018	1	t	Mock Atlas Structure v1
TRADE_023	ROOT	TRADE_023	1	t	Mock Atlas Structure v1
TRADE_009	ROOT	TRADE_009	1	t	Mock Atlas Structure v1
TRADE_012	ROOT	TRADE_012	1	t	Mock Atlas Structure v1
TRADE_019	ROOT	TRADE_019	1	t	Mock Atlas Structure v1
TRADE_014	ROOT	TRADE_014	1	t	Mock Atlas Structure v1
TRADE_010	ROOT	TRADE_010	1	t	Mock Atlas Structure v1
TRADE_029	ROOT	TRADE_029	1	t	Mock Atlas Structure v1
TRADE_007	ROOT	TRADE_007	1	t	Mock Atlas Structure v1
ENTITY_UK_LTD_EMEA	ENTITY_UK_LTD	EMEA	2	f	Mock Atlas Structure v1
ENTITY_UK_LTD_AMER_MARKET_MAKING	ENTITY_UK_LTD_AMER	Market Making	3	f	Mock Atlas Structure v1
ENTITY_UK_LTD_AMER_ALGO_BOOK_001	ENTITY_UK_LTD_AMER_ALGO	Book 001	4	t	Mock Atlas Structure v1
ENTITY_UK_LTD_AMER_ALGO_BOOK_002	ENTITY_UK_LTD_AMER_ALGO	Book 002	4	t	Mock Atlas Structure v1
ENTITY_UK_LTD_AMER_ALGO_BOOK_003	ENTITY_UK_LTD_AMER_ALGO	Book 003	4	t	Mock Atlas Structure v1
ENTITY_UK_LTD	ROOT	UK Limited	1	f	Mock Atlas Structure v1
ENTITY_UK_LTD_AMER	ENTITY_UK_LTD	Americas	2	f	Mock Atlas Structure v1
ENTITY_UK_LTD_AMER_ALGO	ENTITY_UK_LTD_AMER	Algorithmic Trading	3	f	Mock Atlas Structure v1
ENTITY_UK_LTD_AMER_VOL	ENTITY_UK_LTD_AMER	Volatility Trading	3	f	Mock Atlas Structure v1
ENTITY_US_HOLDINGS	ROOT	US Holdings	1	f	Mock Atlas Structure v1
STERLING_RULE_002	\N	Sterling Rule 2 (Fact-Level)	0	t	Mock Atlas Structure v1
STERLING_RULE_003	\N	Sterling Rule 3 (Fact-Level)	0	t	Mock Atlas Structure v1
STERLING_RULE_004	\N	Sterling Rule 4 (Fact-Level)	0	t	Mock Atlas Structure v1
STERLING_RULE_005	\N	Sterling Rule 5 (Fact-Level)	0	t	Mock Atlas Structure v1
STERLING_RULE_006	\N	Sterling Rule 6 (Fact-Level)	0	t	Mock Atlas Structure v1
STERLING_RULE_007	\N	Sterling Rule 7 (Fact-Level)	0	t	Mock Atlas Structure v1
STERLING_RULE_008	\N	Sterling Rule 8 (Fact-Level)	0	t	Mock Atlas Structure v1
STERLING_RULE_009	\N	Sterling Rule 9 (Fact-Level)	0	t	Mock Atlas Structure v1
STERLING_RULE_010	\N	Sterling Rule 10 (Fact-Level)	0	t	Mock Atlas Structure v1
STERLING_RULE_001	\N	Global Trading P&L	0	t	Mock Atlas Structure v1
ROOT	\N	Global Trading P&L	0	f	MOCK_ATLAS_v1
AMER	ROOT	Americas	1	f	MOCK_ATLAS_v1
AMER_CASH_EQUITIES	AMER	Cash Equities	2	f	MOCK_ATLAS_v1
AMER_CASH_EQUITIES_HIGH_TOUCH	AMER_CASH_EQUITIES	High Touch Trading	3	f	MOCK_ATLAS_v1
AMER_CASH_NY	AMER_CASH_EQUITIES_HIGH_TOUCH	Americas Cash NY	4	f	MOCK_ATLAS_v1
CC_AMER_CASH_NY_001	AMER_CASH_NY	Cost Center 001 - Americas Cash NY	5	t	MOCK_ATLAS_v1
CC_AMER_CASH_NY_002	AMER_CASH_NY	Cost Center 002 - Americas Cash NY	5	t	MOCK_ATLAS_v1
CC_AMER_CASH_NY_003	AMER_CASH_NY	Cost Center 003 - Americas Cash NY	5	t	MOCK_ATLAS_v1
CC_AMER_CASH_NY_004	AMER_CASH_NY	Cost Center 004 - Americas Cash NY	5	t	MOCK_ATLAS_v1
AMER_PROG_TRADING	AMER_CASH_EQUITIES_HIGH_TOUCH	Americas Program Trading	4	f	MOCK_ATLAS_v1
CC_AMER_PROG_TRADING_005	AMER_PROG_TRADING	Cost Center 005 - Americas Program Trading	5	t	MOCK_ATLAS_v1
CC_AMER_PROG_TRADING_006	AMER_PROG_TRADING	Cost Center 006 - Americas Program Trading	5	t	MOCK_ATLAS_v1
CC_AMER_PROG_TRADING_007	AMER_PROG_TRADING	Cost Center 007 - Americas Program Trading	5	t	MOCK_ATLAS_v1
EMEA_INDEX_ARB	AMER_CASH_EQUITIES_HIGH_TOUCH	EMEA Index Arbitrage	4	f	MOCK_ATLAS_v1
CC_EMEA_INDEX_ARB_008	EMEA_INDEX_ARB	Cost Center 008 - EMEA Index Arbitrage	5	t	MOCK_ATLAS_v1
CC_EMEA_INDEX_ARB_009	EMEA_INDEX_ARB	Cost Center 009 - EMEA Index Arbitrage	5	t	MOCK_ATLAS_v1
CC_EMEA_INDEX_ARB_010	EMEA_INDEX_ARB	Cost Center 010 - EMEA Index Arbitrage	5	t	MOCK_ATLAS_v1
APAC_ALGO_G1	AMER_CASH_EQUITIES_HIGH_TOUCH	APAC Algorithmic G1	4	f	MOCK_ATLAS_v1
CC_APAC_ALGO_G1_011	APAC_ALGO_G1	Cost Center 011 - APAC Algorithmic G1	5	t	MOCK_ATLAS_v1
CC_APAC_ALGO_G1_012	APAC_ALGO_G1	Cost Center 012 - APAC Algorithmic G1	5	t	MOCK_ATLAS_v1
CC_APAC_ALGO_G1_013	APAC_ALGO_G1	Cost Center 013 - APAC Algorithmic G1	5	t	MOCK_ATLAS_v1
\.


--
-- Data for Name: fact_calculated_results; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.fact_calculated_results (result_id, run_id, node_id, measure_vector, plug_vector, is_override, is_reconciled, created_at, calculation_run_id) FROM stdin;
8e954530-6376-48cb-91d0-816937bae9f8	18047c5f-c015-4e8e-8487-f871b296366e	ROOT	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:29:47.661668	\N
cfded3dc-e3f0-4da5-8587-53057790cf81	18047c5f-c015-4e8e-8487-f871b296366e	AMER	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:29:47.661668	\N
11e10f64-70bc-4021-813c-3aa4efff2dab	18047c5f-c015-4e8e-8487-f871b296366e	AMER_CASH_EQUITIES	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:29:47.661668	\N
7d07b5d9-1aed-4b94-8863-e50b57d9405c	18047c5f-c015-4e8e-8487-f871b296366e	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	f	f	2025-12-24 18:29:47.661668	\N
b07e4a45-c1df-44f1-a25c-d6d023298249	18047c5f-c015-4e8e-8487-f871b296366e	AMER_CASH_NY	{"mtd": 8274402.06, "ytd": -19397564.36, "pytd": -4207920.78, "daily": 5391532.48}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:29:47.661668	\N
6d3ec5e3-6196-48e9-a8ee-29729572de7b	18047c5f-c015-4e8e-8487-f871b296366e	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
22a0ceeb-70ae-4fb8-8601-a3eac32878ca	18047c5f-c015-4e8e-8487-f871b296366e	CC_AMER_CASH_NY_002	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:29:47.661668	\N
a5d213c0-2042-49c2-9e5e-37d36243c10e	18047c5f-c015-4e8e-8487-f871b296366e	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
67b925d7-74d6-45ac-940f-d992674d5867	18047c5f-c015-4e8e-8487-f871b296366e	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
fb168df9-7385-4146-abdf-c181c1efad88	18047c5f-c015-4e8e-8487-f871b296366e	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
7701ac5e-0a64-4dc2-b497-853b5578265f	18047c5f-c015-4e8e-8487-f871b296366e	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
a40effc9-c48c-4e8d-a5a1-d6ed5e9c1f25	18047c5f-c015-4e8e-8487-f871b296366e	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
0e3a8fdc-7cb0-4774-aa8f-ca6f7f8280ad	18047c5f-c015-4e8e-8487-f871b296366e	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
19db3dcf-cd0e-469e-9ba4-74b5cf1d38f6	18047c5f-c015-4e8e-8487-f871b296366e	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
d66e4f62-ee51-4836-a258-f302cad27ae5	18047c5f-c015-4e8e-8487-f871b296366e	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
a3d77095-c79b-4bfc-92d8-6ef6a604a85c	18047c5f-c015-4e8e-8487-f871b296366e	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
9721f54f-b89a-49cd-a102-9739a9490de8	18047c5f-c015-4e8e-8487-f871b296366e	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
b3df21d2-f159-4184-9e9c-5db6dc88aec5	18047c5f-c015-4e8e-8487-f871b296366e	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
8a915866-cec5-48af-96ae-99d2b5c84d2d	18047c5f-c015-4e8e-8487-f871b296366e	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
d5a5aa30-0b17-4c76-9c17-213d3a301830	18047c5f-c015-4e8e-8487-f871b296366e	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
db7e689f-10b0-4185-851d-e8d50ca266fb	18047c5f-c015-4e8e-8487-f871b296366e	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:29:47.661668	\N
7a0a2af8-f792-4ba8-9bb5-bef0a75f7069	194cc4ec-45a0-4b96-80cb-be4122661b18	ROOT	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:35:20.10089	\N
fbde61b4-b142-422c-88fe-215384d92e4b	194cc4ec-45a0-4b96-80cb-be4122661b18	AMER	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:35:20.10089	\N
300994a7-6ced-4609-8bf9-8eb5d0fcb59a	194cc4ec-45a0-4b96-80cb-be4122661b18	AMER_CASH_EQUITIES	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:35:20.10089	\N
3b41fb14-a112-4f0b-ad40-aa7ec92e7ee3	194cc4ec-45a0-4b96-80cb-be4122661b18	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	f	f	2025-12-24 18:35:20.10089	\N
50974fd3-f568-4d6c-ad02-563c458a107c	194cc4ec-45a0-4b96-80cb-be4122661b18	AMER_CASH_NY	{"mtd": 8274402.06, "ytd": -19397564.36, "pytd": -4207920.78, "daily": 5391532.48}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:35:20.10089	\N
99bfa018-5d70-4737-b04a-ac2f079f4acf	194cc4ec-45a0-4b96-80cb-be4122661b18	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
53da7dc9-9521-4a9b-9d1f-bc9072d6f46a	194cc4ec-45a0-4b96-80cb-be4122661b18	CC_AMER_CASH_NY_002	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:35:20.10089	\N
eb4e7794-4f5f-4135-8e36-010ae6077f05	194cc4ec-45a0-4b96-80cb-be4122661b18	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
0a652b19-f856-4547-8a11-cc742d663bb7	194cc4ec-45a0-4b96-80cb-be4122661b18	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
cd9ff1b2-bee2-48f2-b118-0f282d1ba75c	194cc4ec-45a0-4b96-80cb-be4122661b18	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
054134fd-f3df-449c-a3d7-59dd45cd1c9c	194cc4ec-45a0-4b96-80cb-be4122661b18	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
9437d576-f5a3-45b6-a190-d80b98a41eb4	194cc4ec-45a0-4b96-80cb-be4122661b18	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
b12aa13f-94d1-437c-8c40-88c20f93ef0b	194cc4ec-45a0-4b96-80cb-be4122661b18	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
c5f5c9e1-059b-412a-aa76-669d81c99017	194cc4ec-45a0-4b96-80cb-be4122661b18	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
2b2db89a-0ecf-43f3-ba50-efb3c75f034f	194cc4ec-45a0-4b96-80cb-be4122661b18	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
24701dcd-338f-4e13-bd5a-3cb7afa5e4c0	194cc4ec-45a0-4b96-80cb-be4122661b18	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
cfd97320-34c1-4a53-87f4-465db8b91bb7	194cc4ec-45a0-4b96-80cb-be4122661b18	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
f2765499-def8-4bd0-8aa3-532fd45e13a5	194cc4ec-45a0-4b96-80cb-be4122661b18	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
2753ea71-73e3-4a9d-af8a-a90ce13a390d	194cc4ec-45a0-4b96-80cb-be4122661b18	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
5e0d7e12-9533-41a0-88c0-763fef184bf8	194cc4ec-45a0-4b96-80cb-be4122661b18	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
470778df-e7d2-4278-8d15-d49c3a46e1e5	194cc4ec-45a0-4b96-80cb-be4122661b18	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:35:20.10089	\N
c6dd3a88-0cd9-4ac4-94f5-c9ef77409551	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	ROOT	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:59:52.481345	\N
99141e7a-7bb0-44d6-9236-67574273a8f5	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	AMER	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:59:52.481345	\N
3dcf023f-fcbd-478f-80f4-4cfd2d45218d	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	AMER_CASH_EQUITIES	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:59:52.481345	\N
6d7da14c-4b42-4a64-8921-aed06af87ccf	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	f	f	2025-12-24 18:59:52.481345	\N
7a463dc6-75c2-4fb2-bfc3-bf183f674760	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	AMER_CASH_NY	{"mtd": 8274402.06, "ytd": -19397564.36, "pytd": -4207920.78, "daily": 5391532.48}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:59:52.481345	\N
d5237380-40d0-45a5-b20e-c78933e30c61	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
e2f6dd22-fb7a-4778-b3fc-1d4d4ac5a2d4	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	CC_AMER_CASH_NY_002	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 18:59:52.481345	\N
7c9a51b1-3d02-4539-8e1f-d7e2426280cf	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
bb6d5da1-f3f4-4e8c-89a8-bed5e800f9b9	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
5352defc-fbb2-4926-a126-bdc67c07263d	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
c7f9a4dc-f46e-4342-9d39-1282b5e2d42f	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
5e87c35e-9bb8-4c85-98a2-94c7cdde6a7f	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
694a30c4-ff6b-463b-88bc-f5a8158c13b1	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
41091d43-3701-4d6d-821f-75bf9eee738e	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
f76cf3a0-fdf1-4e35-8088-2e4c5f458b44	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
8450faa3-1c24-44f2-aca1-e44bde9376fe	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
eca17f04-fe43-4eba-8f97-4ad0edb32246	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
bb0d89d6-486b-4b06-b569-636e6a2f8484	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
2641ca7f-d3c5-4f98-9021-e12224c08dd1	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
09021ffe-e5b8-40cf-82a8-4eb62d259cd6	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
8e394bd5-358b-4892-8431-d9a8d93d94c8	ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 18:59:52.481345	\N
0b82bed2-5776-43ce-8cb8-f65321d2b0ad	d62f6fb4-667d-411d-ad62-2e919f70f697	ROOT	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 19:56:53.972223	\N
bf76fc86-44f3-4424-9b01-a6d538d68ca0	d62f6fb4-667d-411d-ad62-2e919f70f697	AMER	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 19:56:53.972223	\N
5de6dbc6-36ea-494d-ba59-b2ef53a65bec	d62f6fb4-667d-411d-ad62-2e919f70f697	AMER_CASH_EQUITIES	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 19:56:53.972223	\N
97d99996-94db-40e2-891e-b8f6e5a367f5	d62f6fb4-667d-411d-ad62-2e919f70f697	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	f	f	2025-12-24 19:56:53.972223	\N
099a217f-78e0-439f-8c0f-3d29a0c38d63	d62f6fb4-667d-411d-ad62-2e919f70f697	AMER_CASH_NY	{"mtd": 8274402.06, "ytd": -19397564.36, "pytd": -4207920.78, "daily": 5391532.48}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 19:56:53.972223	\N
9a68b3ab-4c2f-4972-8b69-f992ea734595	d62f6fb4-667d-411d-ad62-2e919f70f697	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
cde52d36-8bb9-412d-a804-7c6d41b30a1b	d62f6fb4-667d-411d-ad62-2e919f70f697	CC_AMER_CASH_NY_002	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 19:56:53.972223	\N
5400e420-ca3c-4c28-880a-0da679f7bc08	d62f6fb4-667d-411d-ad62-2e919f70f697	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
16e0b092-8f13-4497-bead-f77e1644b0de	d62f6fb4-667d-411d-ad62-2e919f70f697	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
9457e7ac-e549-48ab-b6ad-743397606ae8	d62f6fb4-667d-411d-ad62-2e919f70f697	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
28cb4b74-1137-4bc9-b047-e99dae1de3b5	d62f6fb4-667d-411d-ad62-2e919f70f697	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
11d68f46-9099-46b7-be76-34516cd91399	d62f6fb4-667d-411d-ad62-2e919f70f697	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
11c91b00-050a-4d9f-b7e7-6bd134ce2cc4	d62f6fb4-667d-411d-ad62-2e919f70f697	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
22786202-aa39-447e-a5b7-278b2c4bffd0	d62f6fb4-667d-411d-ad62-2e919f70f697	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
7d1c6e66-e0a6-4c04-b7f2-b0a20641619c	d62f6fb4-667d-411d-ad62-2e919f70f697	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
1862b22d-e55b-4ae4-8610-848c7e82e2b4	d62f6fb4-667d-411d-ad62-2e919f70f697	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
a1b349d9-c6e8-46a8-9c75-b3b6b5ea1ced	d62f6fb4-667d-411d-ad62-2e919f70f697	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
2159a7d2-a554-4130-8c4c-1c13987fb49e	d62f6fb4-667d-411d-ad62-2e919f70f697	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
3bd4c9d3-a419-4c67-a82a-46d5327513f5	d62f6fb4-667d-411d-ad62-2e919f70f697	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
33ad1875-666e-4fe3-b0ff-f909a78b5ea4	d62f6fb4-667d-411d-ad62-2e919f70f697	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
8277dc90-58fa-4f9e-bed5-b5f6afcbb1ee	d62f6fb4-667d-411d-ad62-2e919f70f697	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:56:53.972223	\N
1797ae01-beb1-40e6-9950-47ab22c8e093	25eab13c-742b-4266-8965-cd65ed5a0d02	ROOT	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 19:58:33.911465	\N
73824d5c-fc2f-49c0-8dd4-a1aa24b1252f	25eab13c-742b-4266-8965-cd65ed5a0d02	AMER	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 19:58:33.911465	\N
a5afe106-ee25-4eab-850b-d414a91ef7ab	25eab13c-742b-4266-8965-cd65ed5a0d02	AMER_CASH_EQUITIES	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 19:58:33.911465	\N
28b8414b-7c36-4d49-9c5b-ca7d72e65395	25eab13c-742b-4266-8965-cd65ed5a0d02	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	f	f	2025-12-24 19:58:33.911465	\N
c2f462ee-ed7c-408d-bc38-d69094caba3b	25eab13c-742b-4266-8965-cd65ed5a0d02	AMER_CASH_NY	{"mtd": 8274402.06, "ytd": -19397564.36, "pytd": -4207920.78, "daily": 5391532.48}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 19:58:33.911465	\N
2d5aeb89-314c-4769-8e03-67f1fcebd72b	25eab13c-742b-4266-8965-cd65ed5a0d02	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
0e46434d-e6d7-4bdf-aa06-6533cb5c2f48	25eab13c-742b-4266-8965-cd65ed5a0d02	CC_AMER_CASH_NY_002	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 19:58:33.911465	\N
0bd87940-e84e-44e6-b42c-54791093bc33	25eab13c-742b-4266-8965-cd65ed5a0d02	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
f8cac30d-07a1-46e3-8d15-c83ef260d6e9	25eab13c-742b-4266-8965-cd65ed5a0d02	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
a5b26998-57fd-45f8-b96a-2d09433867cf	25eab13c-742b-4266-8965-cd65ed5a0d02	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
3e5c9228-09a4-4e0b-869b-d6c3020cdf16	25eab13c-742b-4266-8965-cd65ed5a0d02	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
7a790be2-8a14-4b2d-bcb7-0464042408d1	25eab13c-742b-4266-8965-cd65ed5a0d02	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
5b73b36e-b2aa-4c9f-a0d3-2948a6a92100	25eab13c-742b-4266-8965-cd65ed5a0d02	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
62374faf-548a-42e8-878c-c87ebec95a21	25eab13c-742b-4266-8965-cd65ed5a0d02	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
a0d956d8-d5a5-40ca-b4e0-903d1c0b7e86	25eab13c-742b-4266-8965-cd65ed5a0d02	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
bcf8885a-9f02-4ea2-ad76-9ea762f2be17	25eab13c-742b-4266-8965-cd65ed5a0d02	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
97bd077c-11c7-49cf-b184-eaf7389002d0	25eab13c-742b-4266-8965-cd65ed5a0d02	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
988d303f-d92b-49da-a1e4-f52907a23e13	25eab13c-742b-4266-8965-cd65ed5a0d02	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
13a86611-2748-4c4a-9700-912a1d3ddfe9	25eab13c-742b-4266-8965-cd65ed5a0d02	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
30f09403-6981-4a90-8e45-7bdb33e8ea54	25eab13c-742b-4266-8965-cd65ed5a0d02	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
0599995f-fbc6-4196-ade8-2dd9ac5ff625	25eab13c-742b-4266-8965-cd65ed5a0d02	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 19:58:33.911465	\N
a0aa7319-b6df-497b-992a-2c33732308b5	39052ce2-304e-44fb-bba2-8487161de67a	ROOT	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
837e3caa-0291-4145-b28a-9b31539b02a7	39052ce2-304e-44fb-bba2-8487161de67a	AMER	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
f154149a-5146-4a97-bd72-793897e19eb9	39052ce2-304e-44fb-bba2-8487161de67a	AMER_CASH_EQUITIES	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
38ff9713-b898-462a-afc1-17fbd3c180ee	39052ce2-304e-44fb-bba2-8487161de67a	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
fb00d3e5-4d3c-4062-a36b-d4966e8b1af8	39052ce2-304e-44fb-bba2-8487161de67a	AMER_CASH_NY	{"mtd": 6875660.29, "ytd": -33798171.76, "pytd": -2900039.46, "daily": 2196515.25}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
b2454728-98b7-4905-a20f-372c1d31ea15	39052ce2-304e-44fb-bba2-8487161de67a	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
72963c74-cfe8-4c81-8a58-98c3cb26283f	39052ce2-304e-44fb-bba2-8487161de67a	CC_AMER_CASH_NY_002	{"mtd": 2491857.33, "ytd": -11853524.95, "pytd": -285367.5, "daily": 287619.9}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
ea1bce74-04b8-4c57-a2c3-910461b4098e	39052ce2-304e-44fb-bba2-8487161de67a	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
352072d3-805e-40a9-ac59-c70ba5849d18	39052ce2-304e-44fb-bba2-8487161de67a	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
f7ff0e0e-cc2c-46f9-b40f-0a5cf21b0cbc	39052ce2-304e-44fb-bba2-8487161de67a	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
5e0901a7-ae86-4075-88a1-ae845546df98	39052ce2-304e-44fb-bba2-8487161de67a	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
c2530087-820f-47f3-9551-22ee1a72c610	39052ce2-304e-44fb-bba2-8487161de67a	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
022c54c7-d0e8-450b-a50b-f39f7501762a	39052ce2-304e-44fb-bba2-8487161de67a	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
9bf3f081-564a-463f-8c83-38fea5a47fa6	39052ce2-304e-44fb-bba2-8487161de67a	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
aed92f4b-9259-41dc-82fe-ae502a1c8c60	39052ce2-304e-44fb-bba2-8487161de67a	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
cc36f60d-3c39-4310-ad3d-7a54ad8690fd	39052ce2-304e-44fb-bba2-8487161de67a	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
69b09eaf-780d-4cbe-869a-b64088dc87e3	39052ce2-304e-44fb-bba2-8487161de67a	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
a025d785-fc0a-493f-8ad1-f251f17a0b9e	39052ce2-304e-44fb-bba2-8487161de67a	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
5218550b-2f1d-44af-a809-06d8f7b778ff	39052ce2-304e-44fb-bba2-8487161de67a	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
be6bc64e-81a9-4f51-a3fb-2f84bb52ec84	39052ce2-304e-44fb-bba2-8487161de67a	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
5298093f-73c0-4151-a06b-fa209942c8e0	39052ce2-304e-44fb-bba2-8487161de67a	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 20:06:13.461083	\N
e604f863-2025-4b6f-9471-c403431784bf	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	ROOT	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
f22ab3b4-5992-4d9c-bd03-c25f58f8b509	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	AMER	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
a65f0582-55af-4690-adf9-369a35a94994	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	AMER_CASH_EQUITIES	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
89bd6565-def0-4820-a866-3f74c29ceb0e	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
bd6168a2-efd4-4222-b03f-632036f729c6	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	AMER_CASH_NY	{"mtd": 6875660.29, "ytd": -33798171.76, "pytd": -2900039.46, "daily": 2196515.25}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
2d92f5b2-1b2c-4086-99c5-e36c538e79a5	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
d3e2fcaa-4c0b-4f6e-8da2-d6a4273e50b3	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	CC_AMER_CASH_NY_002	{"mtd": 2491857.33, "ytd": -11853524.95, "pytd": -285367.5, "daily": 287619.9}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
0810880d-3716-4b69-8748-6bfccbad87f9	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
d010ee6d-2c71-40a6-b784-355961280525	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
ca867626-bcd8-4688-9997-8ea45a78d048	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
7fde8706-daf8-4dea-8840-5828573103b3	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
441c45d4-2d5e-4646-92ee-943020293945	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
278d1070-21d7-43cd-80eb-7e2f4539a0b2	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
b5c29db2-17d1-44fb-a4cd-caaa5cfb3cac	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
c29e3bab-eca5-4e9a-b141-6881dcae925a	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
1786a7f4-1b78-4616-bb6f-380bd8b52887	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
6c4a120c-6d2d-4600-b219-e62f485c0cdc	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
51ce7b30-e181-4df6-824e-b302ac404d41	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
0624904f-73a0-4295-8813-e29067301eb5	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
241dc3b5-2d61-42ba-8108-61e5c2f4fac5	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
776f6fc3-7b5a-46e2-9772-b09ca6f67f84	6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:43.965403	\N
abf66656-7270-4453-95be-2efdfd25d8f5	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	ROOT	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 21:36:50.207268	\N
f48f899d-fd53-4ad2-8224-f27b3e39d35a	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	AMER	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 21:36:50.207268	\N
b09e79f8-9cbc-4f2e-b016-e7f87027780e	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	AMER_CASH_EQUITIES	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 21:36:50.207268	\N
0c7c8e9b-2abf-4e3a-a468-f717e135564a	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	f	f	2025-12-24 21:36:50.207268	\N
d867bca4-ae76-4631-806d-d10821c58c58	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	AMER_CASH_NY	{"mtd": 8274402.06, "ytd": -19397564.36, "pytd": -4207920.78, "daily": 5391532.48}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 21:36:50.207268	\N
79c91f30-0212-42d3-a89f-d00a4c953f38	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
e982dfc5-98a5-4f66-8a27-609cf35fa3eb	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	CC_AMER_CASH_NY_002	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-24 21:36:50.207268	\N
c66e50c6-59bb-44c0-8fda-51249002bc46	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
4576cb68-21d4-4dd8-b098-185181226c8a	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
dbc4c880-13ff-4f65-8dc4-a4e5b5d1b53b	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
5b1de4cf-7429-4ccb-a521-f27363340848	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
ff8a3da3-c892-485b-b5db-ea80698afe55	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
410a2cd4-817c-4c5a-bb83-e6cdfdb00d5e	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
eba4b03f-c022-4f5e-8173-e9a57def8751	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
caea3810-217f-451f-90e8-72a666608db8	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
e22f3192-72aa-49e3-85dc-4b3b7743311d	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
0e8dcb8d-26be-4463-8be6-a6be13d2555f	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
9b20bbfc-7360-4f0a-8ab0-3bca88ba29af	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
b04ec6e7-fbb6-424a-9ade-9319fc3ec17f	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
23ec4eb2-6270-49f5-82d6-361887ef2b49	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
eaf0fd90-15e0-4b5c-9782-ab451228d747	cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-24 21:36:50.207268	\N
f9b9db9f-1773-47d9-9b8a-addaa9d1f74c	3b484679-d759-444d-b9fc-bf58d7ee4802	ROOT	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
db5be475-aaf0-4086-bcc6-ad8ff465f3f9	3b484679-d759-444d-b9fc-bf58d7ee4802	AMER	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
53e2baa3-fb5c-4831-872b-5381c921e65d	3b484679-d759-444d-b9fc-bf58d7ee4802	AMER_CASH_EQUITIES	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
c04a53b8-b97e-4966-86c8-fc2bc5c7c39e	3b484679-d759-444d-b9fc-bf58d7ee4802	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
e28c11f8-fa50-4e2d-a94c-28ab4ba28809	3b484679-d759-444d-b9fc-bf58d7ee4802	AMER_CASH_NY	{"mtd": 6875660.29, "ytd": -33798171.76, "pytd": -2900039.46, "daily": 2196515.25}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
745e289c-5059-416f-a0c4-ebbf2c15b62e	3b484679-d759-444d-b9fc-bf58d7ee4802	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
1d2659f0-92f0-4613-9bed-87c187dee4a0	3b484679-d759-444d-b9fc-bf58d7ee4802	CC_AMER_CASH_NY_002	{"mtd": 2491857.33, "ytd": -11853524.95, "pytd": -285367.5, "daily": 287619.9}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
9dbc087b-39ea-44e5-a7bd-aa2e567e740c	3b484679-d759-444d-b9fc-bf58d7ee4802	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
34088d0b-941a-40dc-a0df-075610405cea	3b484679-d759-444d-b9fc-bf58d7ee4802	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
1b3affe9-897c-4021-bd7b-0994d45892fa	3b484679-d759-444d-b9fc-bf58d7ee4802	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
954a6c56-cec0-4efa-b92b-9dafdaa964a9	3b484679-d759-444d-b9fc-bf58d7ee4802	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
347d22da-4d21-40c7-9ee1-64ac5bf22c59	3b484679-d759-444d-b9fc-bf58d7ee4802	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
d9ad853c-a95d-44c3-a82e-7a514e9c7cdf	3b484679-d759-444d-b9fc-bf58d7ee4802	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
11083708-2dd5-426a-a188-c47e1aa13a5f	3b484679-d759-444d-b9fc-bf58d7ee4802	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
6ba7be8f-a78c-436b-b89a-0fffa29d60e4	3b484679-d759-444d-b9fc-bf58d7ee4802	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
f01f5c7d-2c03-49b0-9d45-a56f03eb042b	3b484679-d759-444d-b9fc-bf58d7ee4802	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
60ff659b-029c-4cff-b985-386c9b912b61	3b484679-d759-444d-b9fc-bf58d7ee4802	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
2435bc8a-0f95-4908-904b-0edb1a87ef29	3b484679-d759-444d-b9fc-bf58d7ee4802	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
d156f0dd-425c-460c-8863-491ffda4ee32	3b484679-d759-444d-b9fc-bf58d7ee4802	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
4cfe35e3-ea3c-4213-bbee-43b80573ee12	3b484679-d759-444d-b9fc-bf58d7ee4802	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
04f4828b-e9d6-4a0d-9e7a-79734d40378d	3b484679-d759-444d-b9fc-bf58d7ee4802	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:21.737296	\N
252b78a0-3d19-44cf-b650-7de0b26cedaf	0989025d-a103-45a6-8e1e-12939ac26bfc	ROOT	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 21:35:34.108737	\N
257e9629-4116-49b9-ab04-f921c91566ec	0989025d-a103-45a6-8e1e-12939ac26bfc	AMER	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 21:35:34.108737	\N
4f9b2a71-79b9-4207-848c-0e72281d101a	0989025d-a103-45a6-8e1e-12939ac26bfc	AMER_CASH_EQUITIES	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 21:35:34.108737	\N
f8615837-16b3-43e3-810f-a1aaa9a09b76	0989025d-a103-45a6-8e1e-12939ac26bfc	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	f	f	2025-12-26 21:35:34.108737	\N
dbecc310-829b-4909-be66-390c0d0dfbc6	0989025d-a103-45a6-8e1e-12939ac26bfc	AMER_CASH_NY	{"mtd": 8274402.06, "ytd": -19397564.36, "pytd": -4207920.78, "daily": 5391532.48}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 21:35:34.108737	\N
f198027f-2560-4972-bfb2-a9aca06bd9cc	0989025d-a103-45a6-8e1e-12939ac26bfc	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
0ca15a40-622c-49c4-a58b-e9930a00112c	0989025d-a103-45a6-8e1e-12939ac26bfc	CC_AMER_CASH_NY_002	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 21:35:34.108737	\N
a0991c7f-4604-4d1d-9f79-af2befe6bd8a	0989025d-a103-45a6-8e1e-12939ac26bfc	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
a74e0125-1321-4bdd-adc1-c6c8a89b32f2	0989025d-a103-45a6-8e1e-12939ac26bfc	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
5d2f96c5-7fda-41ac-abe2-612f47bb9633	0989025d-a103-45a6-8e1e-12939ac26bfc	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
d1fa0f86-44bd-47dd-8cde-8538d414a71f	0989025d-a103-45a6-8e1e-12939ac26bfc	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
ce0b65cb-3e2e-4077-9bb0-71157708c9d8	0989025d-a103-45a6-8e1e-12939ac26bfc	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
e22b8fa6-e13d-4aac-b60f-1dfa90bbb2d0	0989025d-a103-45a6-8e1e-12939ac26bfc	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
592306e5-3ccb-4927-83e8-bb5648ec57ef	0989025d-a103-45a6-8e1e-12939ac26bfc	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
898cbe78-079c-4349-af78-c54c7f1ad3c8	0989025d-a103-45a6-8e1e-12939ac26bfc	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
00c14b86-2149-4fce-a462-5008393c6ac7	0989025d-a103-45a6-8e1e-12939ac26bfc	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
94a239f4-034a-4449-849a-3e747d28beed	0989025d-a103-45a6-8e1e-12939ac26bfc	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
4c889fe5-12ce-4227-a96d-8912570ae594	0989025d-a103-45a6-8e1e-12939ac26bfc	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
c9e87242-ec67-43f6-8415-a2345dd37c93	0989025d-a103-45a6-8e1e-12939ac26bfc	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
e66facf9-70c3-4882-9d1b-828e42b13e96	0989025d-a103-45a6-8e1e-12939ac26bfc	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
c9fcf710-e892-4847-9cd0-225fe44a7df4	0989025d-a103-45a6-8e1e-12939ac26bfc	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:35:34.108737	\N
dc71c326-731e-48e7-bfb4-ea0ea010be13	a03e7003-b41b-4587-994e-75b790fb7667	ROOT	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
740b384f-bd60-4ba8-b634-b833ec174bc7	a03e7003-b41b-4587-994e-75b790fb7667	AMER	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
d9fd7394-b2f4-47de-99da-e2ddfd518407	a03e7003-b41b-4587-994e-75b790fb7667	AMER_CASH_EQUITIES	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
06b1cd14-cd52-44dd-80e2-cc710c9b502a	a03e7003-b41b-4587-994e-75b790fb7667	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
f42ccaae-5720-45e7-9066-8ffbca7f7611	a03e7003-b41b-4587-994e-75b790fb7667	AMER_CASH_NY	{"mtd": 6875660.29, "ytd": -33798171.76, "pytd": -2900039.46, "daily": 2196515.25}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
05f81f2d-e05b-4ce6-8e66-f99db477ffef	a03e7003-b41b-4587-994e-75b790fb7667	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
1123361c-bb19-4820-945d-86b77e83ac12	a03e7003-b41b-4587-994e-75b790fb7667	CC_AMER_CASH_NY_002	{"mtd": 2491857.33, "ytd": -11853524.95, "pytd": -285367.5, "daily": 287619.9}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
c1157301-c9d8-4cf3-93bd-72f513cdbd3f	a03e7003-b41b-4587-994e-75b790fb7667	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
1e6d887c-6fb4-4daf-b403-d359ef68ddf8	a03e7003-b41b-4587-994e-75b790fb7667	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
a7eb962e-6f3c-41c1-af5d-cdfb58453738	a03e7003-b41b-4587-994e-75b790fb7667	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
7eac4a3d-2abc-4786-ac27-35203202315b	a03e7003-b41b-4587-994e-75b790fb7667	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
a208443a-6616-416f-a726-8b1beb8bbecf	a03e7003-b41b-4587-994e-75b790fb7667	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
52866574-6afe-44f3-9afb-fa6a0d4242b8	a03e7003-b41b-4587-994e-75b790fb7667	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
8b34fe7c-e26c-4b0d-a40f-c33cea894aec	a03e7003-b41b-4587-994e-75b790fb7667	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
4641967f-766b-498e-9141-3140f3425afe	a03e7003-b41b-4587-994e-75b790fb7667	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
f4b82953-2240-45dd-85e7-dbc4584d230c	a03e7003-b41b-4587-994e-75b790fb7667	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
debb55fd-f841-440c-85aa-8c87910ff260	a03e7003-b41b-4587-994e-75b790fb7667	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
fd5ff86d-d4d4-4b0e-88c9-4cec5e409253	a03e7003-b41b-4587-994e-75b790fb7667	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
2f6094d0-b4fc-407c-8b39-4cee9c63d2f7	a03e7003-b41b-4587-994e-75b790fb7667	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
63ba6927-607c-417b-a259-4be1ad1afa68	a03e7003-b41b-4587-994e-75b790fb7667	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
e9ca9931-1a68-401f-8a79-691952eaec3e	a03e7003-b41b-4587-994e-75b790fb7667	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:41:22.378297	\N
b57bf71c-c348-4acf-b1ce-3aac142fa46c	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	ROOT	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
8f58a9df-d0b9-45a0-b070-2e823f6d8ec4	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	AMER	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
af3093e2-f8a2-43d2-9811-9ae41bfed96b	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	AMER_CASH_EQUITIES	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
a057be4c-7fae-44b8-9d99-c8baea524982	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
e5f76ce2-650c-4848-b9aa-085986ea097a	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	AMER_CASH_NY	{"mtd": 6875660.29, "ytd": -33798171.76, "pytd": -2900039.46, "daily": 2196515.25}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
cd5c4e59-e573-48cf-a88d-cd85e2ce5092	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
bf4cd31d-96c7-4496-ab1c-c68505c89097	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	CC_AMER_CASH_NY_002	{"mtd": 2491857.33, "ytd": -11853524.95, "pytd": -285367.5, "daily": 287619.9}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
61dd0f0f-c778-4e54-b342-14da0849ce92	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
63292596-ad68-4cb6-a4d4-792828c2965c	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
b9d8c4e6-7993-4092-aeba-e91f4f985391	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
3a6c4411-4566-43b1-b3ee-e6c99d7907c7	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
ac7f725e-56e1-4b6c-a659-1cf714ee71db	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
88f4f54c-ca71-4ddd-9afb-38786e649f13	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
9bc108dc-99f0-4942-a94d-7c42a284590c	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
8aadc8a8-f2c9-4c6b-b6ae-d37c42ac6c1d	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
5a32f1bf-a64f-4aad-807c-fa1345072fba	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
0e8fae1f-d3ed-4f1c-b953-9f419c236f9d	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
48ac9200-f210-4a86-b976-b586d18ecf90	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
346408dc-1b95-4d8c-8938-7553c6347f00	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
0ca925a6-e95b-4d8c-920a-87b97fc1aa4a	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
f7cbd51e-ede6-42ee-9d0c-fba33cd8c2aa	e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 21:58:45.284267	\N
14dce813-1d47-4afa-8307-5d06010f8d0e	1bafc99d-ef4c-4644-86f7-5b67b57f2045	ROOT	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
e96ba633-5fb9-49fe-925a-4c75be4bf33f	1bafc99d-ef4c-4644-86f7-5b67b57f2045	AMER	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
0c835eeb-78eb-423e-a7e3-95612c275da6	1bafc99d-ef4c-4644-86f7-5b67b57f2045	AMER_CASH_EQUITIES	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
eef9f5c1-1f90-4d8f-b7d6-bca9100e036f	1bafc99d-ef4c-4644-86f7-5b67b57f2045	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
4cc7237d-1c1b-4bf4-9b8d-59cd18f6cbd7	1bafc99d-ef4c-4644-86f7-5b67b57f2045	AMER_CASH_NY	{"mtd": 6875660.29, "ytd": -33798171.76, "pytd": -2900039.46, "daily": 2196515.25}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
aa71a218-671e-4dd7-96e2-9781616039e5	1bafc99d-ef4c-4644-86f7-5b67b57f2045	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
fa2299fc-e93d-4a3d-98dd-5c5484471218	1bafc99d-ef4c-4644-86f7-5b67b57f2045	CC_AMER_CASH_NY_002	{"mtd": 2491857.33, "ytd": -11853524.95, "pytd": -285367.5, "daily": 287619.9}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
f3a1e93c-659b-4d43-85c2-fb7983874401	1bafc99d-ef4c-4644-86f7-5b67b57f2045	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
6e0f32de-4d18-4cab-bed3-b79c674b8649	1bafc99d-ef4c-4644-86f7-5b67b57f2045	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
c04ddb00-20fe-4d3a-b5fc-08e6241d7ac3	1bafc99d-ef4c-4644-86f7-5b67b57f2045	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
36369f1c-b785-4067-8c0d-a08d05bab172	1bafc99d-ef4c-4644-86f7-5b67b57f2045	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
99731575-16d1-46a4-abc2-3ca486736145	1bafc99d-ef4c-4644-86f7-5b67b57f2045	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
f717486e-9e89-4f95-bc7f-684cd0a1fff7	1bafc99d-ef4c-4644-86f7-5b67b57f2045	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
c47d84a8-962c-44a8-bb2f-c8585b857a04	1bafc99d-ef4c-4644-86f7-5b67b57f2045	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
a9120225-04be-4965-9736-3869c215999e	1bafc99d-ef4c-4644-86f7-5b67b57f2045	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
2dcadbe9-092e-4b8e-959d-1c7cdfb0bcfa	1bafc99d-ef4c-4644-86f7-5b67b57f2045	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
63fa8814-1d7d-4af7-98b7-2550cacfe136	1bafc99d-ef4c-4644-86f7-5b67b57f2045	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
a1581ff2-77f6-421d-a420-311e6ed1b249	1bafc99d-ef4c-4644-86f7-5b67b57f2045	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
c772d787-e99d-424a-809c-85e20f59071f	1bafc99d-ef4c-4644-86f7-5b67b57f2045	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
dcaa99ec-ec50-4881-ba34-71885313984d	1bafc99d-ef4c-4644-86f7-5b67b57f2045	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
24b7d15b-2abc-4be6-87b7-2df66bc26da9	1bafc99d-ef4c-4644-86f7-5b67b57f2045	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:00:11.557514	\N
bfbba2ef-657d-48bb-873f-2d9bc47f4697	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	ROOT	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
0380b159-438f-42f9-ae70-2fc18fe8908c	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	AMER	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
59e08747-360a-483f-baeb-3e57ab8d89c1	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	AMER_CASH_EQUITIES	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
61b38db4-5679-4b82-a7cd-f977674eea33	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
94b3d6d9-5356-43ce-a03d-63cda80c2965	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	AMER_CASH_NY	{"mtd": 6875660.29, "ytd": -33798171.76, "pytd": -2900039.46, "daily": 2196515.25}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
dec1cc88-df20-45dd-95c3-f9bc7cca1a24	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
d1bcb815-7ed5-498d-95e8-70d3964899b4	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	CC_AMER_CASH_NY_002	{"mtd": 2491857.33, "ytd": -11853524.95, "pytd": -285367.5, "daily": 287619.9}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
e9dd01e5-d77b-49b1-a34c-fcf1ecf7ae37	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
351ed663-5cec-4b6a-9e4b-74b2de14cb74	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
9c30bc59-8f77-4efd-a85c-68166946f5ff	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
08b7e243-85ab-411b-9157-7bce6fbe2a6a	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
a377f5f8-dc02-44e4-a00a-95f34ad0028a	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
0e88cc18-7c28-488a-b13c-43d0a4db354f	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
30ab9bc2-44c7-43fe-bd27-eef2c3efeb07	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
7a9778fc-fd72-4ee6-8db7-8a4dfff3682e	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
5a05d041-1dda-426f-a94b-38efd69e820e	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
6b12a4ed-ea60-44b3-9aeb-a0e557e6ceb6	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
6d3c48cc-11b5-4d81-bfe5-4521ae3258bd	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
3a29e942-22a3-4c51-a9e0-55be52716e1a	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
9eb3bd00-eb00-4c6d-bc5c-7a7a5bed0f6b	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
c6b8f778-c7c1-4d37-9ee2-59ab8d36f033	469f8f88-c7d8-4d32-9a0b-4264aad6ba03	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:14:50.519649	\N
548c7475-5240-4ecc-b6db-9899f300455d	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	ROOT	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:28:25.381613	\N
87015fbc-3cc3-444f-898d-ff47803bf742	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	AMER	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:28:25.381613	\N
4d119330-ecd9-413a-9fe0-4abc3921a629	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	AMER_CASH_EQUITIES	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:28:25.381613	\N
ecbbd817-3655-4b03-8dbb-a23a7f695bd6	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	f	f	2025-12-26 22:28:25.381613	\N
2964289d-f67a-412b-9040-3288ca72f44a	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	AMER_CASH_NY	{"mtd": 8274402.06, "ytd": -19397564.36, "pytd": -4207920.78, "daily": 5391532.48}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:28:25.381613	\N
817f5118-8389-428a-aedd-209f66019f82	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
2b130102-17b2-43a8-b0a1-44118df7797d	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	CC_AMER_CASH_NY_002	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:28:25.381613	\N
9a110416-31e4-4a08-a181-f0aa8ef30e86	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
77cf6928-d1f0-4b19-b49b-5010a659ff57	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
119bcf9b-5dae-407d-a586-21394b74e401	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
73afcb7a-c1ff-438e-a8eb-05d2848cfa9c	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
1af9ba81-4cb2-4cd9-8ac9-0b4620b213d2	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
8073c8ed-a5be-43ad-a303-32ebe2586f4e	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
26f422a7-7b40-4f38-a42c-7f57c8fcc1f7	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
e6b8ad58-0aae-47c0-b816-dceef344067b	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
c64af00f-4c39-4088-8e07-71bad0fd7c3e	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
2ee93519-75eb-46ca-9782-8878d0ecd2e5	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
fde4dadd-12be-4684-b240-33405ea33697	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
37016cff-2191-4491-9a57-c5797f78cf2c	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
c3b1ffd8-92ea-4114-afde-3e731af6b76b	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
e63683fc-9cf9-469c-9788-d0d9ca2ae106	7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:28:25.381613	\N
e9838029-3ba9-42da-9aa7-980bd2dff45f	e1a1364c-00ce-403c-8f2e-01423af9c471	ROOT	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:29:43.878796	\N
d117fe34-c84e-4987-9a95-41cad1d2dc77	e1a1364c-00ce-403c-8f2e-01423af9c471	AMER	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:29:43.878796	\N
002d5b7c-5105-4685-b907-d19143ec9e23	e1a1364c-00ce-403c-8f2e-01423af9c471	AMER_CASH_EQUITIES	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:29:43.878796	\N
d7e2d80a-d7a8-48d8-a25d-afa456c5c7f9	e1a1364c-00ce-403c-8f2e-01423af9c471	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	f	f	2025-12-26 22:29:43.878796	\N
655a26e9-daf2-475a-a5e1-76126dfde163	e1a1364c-00ce-403c-8f2e-01423af9c471	AMER_CASH_NY	{"mtd": 8274402.06, "ytd": -19397564.36, "pytd": -4207920.78, "daily": 5391532.48}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:29:43.878796	\N
aebfb38e-f317-4492-9ed8-4424951f6af2	e1a1364c-00ce-403c-8f2e-01423af9c471	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
68493ecd-3073-4c1f-9e69-f950ecef2da9	e1a1364c-00ce-403c-8f2e-01423af9c471	CC_AMER_CASH_NY_002	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:29:43.878796	\N
9fd3f2a5-a1bd-43b1-85b3-d80aa952436d	e1a1364c-00ce-403c-8f2e-01423af9c471	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
286c2030-e4bf-4f45-a25a-952ba67953ed	e1a1364c-00ce-403c-8f2e-01423af9c471	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
9151f0a7-1c5c-4338-9196-7cd89edb2279	e1a1364c-00ce-403c-8f2e-01423af9c471	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
eb89e5b8-f28a-4235-87b1-35a5a138d0b6	e1a1364c-00ce-403c-8f2e-01423af9c471	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
271f63cb-1495-4455-9a71-6f07507332eb	e1a1364c-00ce-403c-8f2e-01423af9c471	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
39306254-5e32-4cad-b28c-a698356d406d	e1a1364c-00ce-403c-8f2e-01423af9c471	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
f9f53180-d7b4-4218-951b-168eaf58bc40	e1a1364c-00ce-403c-8f2e-01423af9c471	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
fb05a7d3-3a7d-41ff-93e3-b3fbe923420d	e1a1364c-00ce-403c-8f2e-01423af9c471	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
dc569518-09c5-4487-91fd-710751383587	e1a1364c-00ce-403c-8f2e-01423af9c471	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
a3ed3f40-53ed-46fc-8c02-3d80d4bc7687	e1a1364c-00ce-403c-8f2e-01423af9c471	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
30a0fbca-5a17-474a-bd53-81751bec8c51	e1a1364c-00ce-403c-8f2e-01423af9c471	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
873b12f8-5cd3-42dd-8d94-60cf581af585	e1a1364c-00ce-403c-8f2e-01423af9c471	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
3e000d2c-3352-4ce0-bfa9-d2b1a96e0df0	e1a1364c-00ce-403c-8f2e-01423af9c471	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
ef209a0d-f0a2-4d7d-86ae-4d2db4e07bef	e1a1364c-00ce-403c-8f2e-01423af9c471	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:29:43.878796	\N
4e758a6a-2b8b-4a71-83eb-4c590bf3a59c	e8581cc4-7b61-418a-a31c-5e57846e42ee	ROOT	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:49:33.89092	\N
c5f6a535-ac13-45ea-a9d8-3c758157ead9	e8581cc4-7b61-418a-a31c-5e57846e42ee	AMER	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:49:33.89092	\N
c5b0d977-2b88-4586-b1db-744ac2cb3117	e8581cc4-7b61-418a-a31c-5e57846e42ee	AMER_CASH_EQUITIES	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:49:33.89092	\N
4321a334-b8bb-4bad-8bcf-91330c1ad89a	e8581cc4-7b61-418a-a31c-5e57846e42ee	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	f	f	2025-12-26 22:49:33.89092	\N
fe09763b-c66f-4d80-80c6-e548f159a422	e8581cc4-7b61-418a-a31c-5e57846e42ee	AMER_CASH_NY	{"mtd": 8274402.06, "ytd": -19397564.36, "pytd": -4207920.78, "daily": 5391532.48}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:49:33.89092	\N
8bcd680d-0e83-4c6a-82c9-a6e5db3da25f	e8581cc4-7b61-418a-a31c-5e57846e42ee	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
6d1794fe-355d-441a-bc13-3829acd721b7	e8581cc4-7b61-418a-a31c-5e57846e42ee	CC_AMER_CASH_NY_002	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:49:33.89092	\N
e3005666-ee66-43fc-85fa-cc767ac5bc5a	e8581cc4-7b61-418a-a31c-5e57846e42ee	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
1fc4475d-e858-459a-b586-680d8899613f	e8581cc4-7b61-418a-a31c-5e57846e42ee	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
a438f990-7699-44c3-97b1-f4b5202aee49	e8581cc4-7b61-418a-a31c-5e57846e42ee	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
e845ba80-7cf6-4f04-bc86-1847717e3540	e8581cc4-7b61-418a-a31c-5e57846e42ee	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
d38adfaf-9728-4ba4-b3bf-9aa242806e6c	e8581cc4-7b61-418a-a31c-5e57846e42ee	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
ce3f2929-53fc-4915-b462-ccef9b5a06f8	e8581cc4-7b61-418a-a31c-5e57846e42ee	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
f5923987-7497-4933-9c0e-9a52256f7edc	e8581cc4-7b61-418a-a31c-5e57846e42ee	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
d6a17b40-5b12-4c74-983d-6cf558e75a60	e8581cc4-7b61-418a-a31c-5e57846e42ee	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
a5591dbb-aecd-4695-8e8a-617dd3ab428f	e8581cc4-7b61-418a-a31c-5e57846e42ee	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
04287cfa-e873-49a3-a03c-d7848e5548d3	e8581cc4-7b61-418a-a31c-5e57846e42ee	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
04450c2c-3490-4990-ba34-f0242daf839a	e8581cc4-7b61-418a-a31c-5e57846e42ee	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
922d8e78-594b-44cc-96f2-3b328d224518	e8581cc4-7b61-418a-a31c-5e57846e42ee	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
8f69f29c-2a1e-4c21-b5f5-5144fc4070c4	e8581cc4-7b61-418a-a31c-5e57846e42ee	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
bb882663-f4be-43bb-ad7f-9a3788e7e98d	e8581cc4-7b61-418a-a31c-5e57846e42ee	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:49:33.89092	\N
71ac9d00-118b-4287-a6c3-ef38c4436298	9ad67223-cd8e-4e8d-8dd2-94e624953806	ROOT	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:52:02.460417	\N
4d531d68-5dad-4c11-be41-791ca70a46c2	9ad67223-cd8e-4e8d-8dd2-94e624953806	AMER	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:52:02.460417	\N
6982bc4c-e631-4854-857c-fc27b95580b3	9ad67223-cd8e-4e8d-8dd2-94e624953806	AMER_CASH_EQUITIES	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:52:02.460417	\N
7f7eb536-3237-4773-91db-3f3f5d6dcfe4	9ad67223-cd8e-4e8d-8dd2-94e624953806	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 5289340.87, "ytd": 16947689.85, "pytd": -2901130.14, "daily": 6677654.36}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	f	f	2025-12-26 22:52:02.460417	\N
9bafafd9-7d5a-4b8b-9398-27d0d8d0251e	9ad67223-cd8e-4e8d-8dd2-94e624953806	AMER_CASH_NY	{"mtd": 8274402.06, "ytd": -19397564.36, "pytd": -4207920.78, "daily": 5391532.48}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:52:02.460417	\N
3fd8127d-0fea-46b1-9e56-3d2435ec12cb	9ad67223-cd8e-4e8d-8dd2-94e624953806	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
a48f7c7b-f34e-45e8-8b74-40524f1a3a82	9ad67223-cd8e-4e8d-8dd2-94e624953806	CC_AMER_CASH_NY_002	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:52:02.460417	\N
e4628998-a067-46d6-b1e7-74681e63d155	9ad67223-cd8e-4e8d-8dd2-94e624953806	CC_AMER_CASH_NY_003	{"mtd": -2290373.3, "ytd": -214130.75, "pytd": -5119318.49, "daily": 1012729.92}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
988a81cb-11b0-4fa2-bd89-e13b356c476e	9ad67223-cd8e-4e8d-8dd2-94e624953806	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
a23f5102-bb10-4a7e-8971-a12a693dea72	9ad67223-cd8e-4e8d-8dd2-94e624953806	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
29ef530e-b2ce-47b4-9687-3571947917a8	9ad67223-cd8e-4e8d-8dd2-94e624953806	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
c80ebd46-a6cb-4813-a8c4-71a409ef66e7	9ad67223-cd8e-4e8d-8dd2-94e624953806	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
bb966328-bed2-433d-a029-038c8cd0dd54	9ad67223-cd8e-4e8d-8dd2-94e624953806	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
54991187-9c95-4813-bae8-3634d5019b32	9ad67223-cd8e-4e8d-8dd2-94e624953806	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
7848b740-8755-4f66-a9a6-c4993a792ad3	9ad67223-cd8e-4e8d-8dd2-94e624953806	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
417c4d5f-036e-4bc8-af18-44362538c712	9ad67223-cd8e-4e8d-8dd2-94e624953806	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
b3c42dd9-2c83-4c28-b464-b9f1286d3557	9ad67223-cd8e-4e8d-8dd2-94e624953806	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
86d048a4-6baa-44f6-9386-a2847e2696c4	9ad67223-cd8e-4e8d-8dd2-94e624953806	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
9281cde4-708b-4e8f-8b97-e6280fe58038	9ad67223-cd8e-4e8d-8dd2-94e624953806	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
f4873e13-b548-4880-96e9-64427d4ebde1	9ad67223-cd8e-4e8d-8dd2-94e624953806	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
9c514dc3-279b-4b8f-84e7-24a6841f5c87	9ad67223-cd8e-4e8d-8dd2-94e624953806	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:52:02.460417	\N
682c5ee0-a433-4c3f-b5ec-17bc8ec21cc9	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	ROOT	{"mtd": 11470313.27, "ytd": 19708903.05, "pytd": 624939.53, "daily": 9147561.57}	{"mtd": -7579714.17, "ytd": -17161820.6, "pytd": -2218188.35, "daily": -5664924.44}	t	f	2025-12-26 22:56:56.587762	\N
780bce50-e4ae-42b7-936f-c2e73fb7aae6	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	AMER	{"mtd": 11470313.27, "ytd": 19708903.05, "pytd": 624939.53, "daily": 9147561.57}	{"mtd": -7579714.17, "ytd": -17161820.6, "pytd": -2218188.35, "daily": -5664924.44}	t	f	2025-12-26 22:56:56.587762	\N
30e13433-7e76-4d3d-9a75-98f361fc043a	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	AMER_CASH_EQUITIES	{"mtd": 11470313.27, "ytd": 19708903.05, "pytd": 624939.53, "daily": 9147561.57}	{"mtd": -7579714.17, "ytd": -17161820.6, "pytd": -2218188.35, "daily": -5664924.44}	t	f	2025-12-26 22:56:56.587762	\N
8610b851-0880-4678-b264-6b71a71e53d2	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 11470313.27, "ytd": 19708903.05, "pytd": 624939.53, "daily": 9147561.57}	{"mtd": -7579714.17, "ytd": -17161820.6, "pytd": -2218188.35, "daily": -5664924.44}	f	f	2025-12-26 22:56:56.587762	\N
612fcfa1-f2c0-4289-a84e-3dc3049d4b72	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	AMER_CASH_NY	{"mtd": 14455374.46, "ytd": -16636351.16, "pytd": -681851.11, "daily": 7861439.69}	{"mtd": -7579714.17, "ytd": -17161820.6, "pytd": -2218188.35, "daily": -5664924.44}	t	f	2025-12-26 22:56:56.587762	\N
8db5d5c4-8f04-428e-ba8c-ed9d852627d3	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:56:56.587762	\N
7fa1942a-af89-4d76-89f5-05c5bb20d722	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	CC_AMER_CASH_NY_002	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:56:56.587762	\N
db6f76c1-367d-441c-b277-99dca6ea82a5	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	CC_AMER_CASH_NY_003	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -6180972.4, "ytd": -2761213.2, "pytd": -3526069.67, "daily": -2469907.21}	t	f	2025-12-26 22:56:56.587762	\N
836f33fb-49cb-424f-b1a0-7c733f03fd8e	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:56:56.587762	\N
355b6a70-53a3-4307-9be3-3ea95039a5f6	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	t	t	2025-12-26 22:56:56.587762	\N
4e742607-f9c4-48b2-a43d-eea4f3d8f1b1	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:56:56.587762	\N
f7da1a34-487d-41aa-92c1-f8731f27d6ec	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:56:56.587762	\N
f1eef698-a8c2-4576-b5d4-d21f926b32fa	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:56:56.587762	\N
b3aca36c-31a7-49bb-8fb9-2ae25e26dcfa	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:56:56.587762	\N
60d5bff9-13e1-4a38-a7d1-af89b940e456	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:56:56.587762	\N
d91aa3e7-9558-4d76-90d5-a963a6a386ea	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:56:56.587762	\N
b055bb40-b9b0-4369-bbe2-0fa9074d12ab	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:56:56.587762	\N
8e13ac23-0b64-4033-ba30-f5efadbee889	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:56:56.587762	\N
bcb6fc75-4c16-4e50-9edc-d4fc612afc67	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:56:56.587762	\N
245e157c-c1b1-45d6-a641-3ab68cfd1453	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:56:56.587762	\N
4cc072b1-d7fd-40b4-8b15-9955ffbcb307	6a44256b-45b2-4e3c-b555-e93ccf2b1f00	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:56:56.587762	\N
18827c70-dc5b-4e56-a8b6-abc245a177c3	80d4d457-c260-47eb-8186-4eeb20ce7e2c	ROOT	{"mtd": 11470313.27, "ytd": 19708903.05, "pytd": 624939.53, "daily": 9147561.57}	{"mtd": -7579714.17, "ytd": -17161820.6, "pytd": -2218188.35, "daily": -5664924.44}	t	f	2025-12-26 22:57:16.357415	\N
6c13f217-fe77-4461-ba14-63732f415e28	80d4d457-c260-47eb-8186-4eeb20ce7e2c	AMER	{"mtd": 11470313.27, "ytd": 19708903.05, "pytd": 624939.53, "daily": 9147561.57}	{"mtd": -7579714.17, "ytd": -17161820.6, "pytd": -2218188.35, "daily": -5664924.44}	t	f	2025-12-26 22:57:16.357415	\N
c8c5d63d-733c-45b7-b41d-135eba85dd04	80d4d457-c260-47eb-8186-4eeb20ce7e2c	AMER_CASH_EQUITIES	{"mtd": 11470313.27, "ytd": 19708903.05, "pytd": 624939.53, "daily": 9147561.57}	{"mtd": -7579714.17, "ytd": -17161820.6, "pytd": -2218188.35, "daily": -5664924.44}	t	f	2025-12-26 22:57:16.357415	\N
132f46ec-da93-41b7-96b3-011a2588dcc7	80d4d457-c260-47eb-8186-4eeb20ce7e2c	AMER_CASH_EQUITIES_HIGH_TOUCH	{"mtd": 11470313.27, "ytd": 19708903.05, "pytd": 624939.53, "daily": 9147561.57}	{"mtd": -7579714.17, "ytd": -17161820.6, "pytd": -2218188.35, "daily": -5664924.44}	f	f	2025-12-26 22:57:16.357415	\N
8faa8694-db2f-478a-a269-71f8eb691ec7	80d4d457-c260-47eb-8186-4eeb20ce7e2c	AMER_CASH_NY	{"mtd": 14455374.46, "ytd": -16636351.16, "pytd": -681851.11, "daily": 7861439.69}	{"mtd": -7579714.17, "ytd": -17161820.6, "pytd": -2218188.35, "daily": -5664924.44}	t	f	2025-12-26 22:57:16.357415	\N
71227487-3605-440f-a941-9fa7643bcabf	80d4d457-c260-47eb-8186-4eeb20ce7e2c	CC_AMER_CASH_NY_001	{"mtd": 4900577.95, "ytd": -3442379.22, "pytd": 4821994.46, "daily": 647412.44}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:57:16.357415	\N
bef322e9-041b-4616-92b6-60cf11a75d0d	80d4d457-c260-47eb-8186-4eeb20ce7e2c	CC_AMER_CASH_NY_002	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -1398741.77, "ytd": -14400607.4, "pytd": 1307881.32, "daily": -3195017.23}	t	f	2025-12-26 22:57:16.357415	\N
22dabb3f-47b6-4dcd-b4c2-3a6176aaf946	80d4d457-c260-47eb-8186-4eeb20ce7e2c	CC_AMER_CASH_NY_003	{"mtd": 3890599.1, "ytd": 2547082.45, "pytd": -1593248.82, "daily": 3482637.13}	{"mtd": -6180972.4, "ytd": -2761213.2, "pytd": -3526069.67, "daily": -2469907.21}	t	f	2025-12-26 22:57:16.357415	\N
1cbb91f4-ffde-46e4-92a9-13948117a5ee	80d4d457-c260-47eb-8186-4eeb20ce7e2c	CC_AMER_CASH_NY_004	{"mtd": 1773598.31, "ytd": -18288136.84, "pytd": -2317347.93, "daily": 248752.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:57:16.357415	\N
2a8b2c06-7b93-4bf9-81b2-26b993b473b6	80d4d457-c260-47eb-8186-4eeb20ce7e2c	AMER_PROG_TRADING	{"mtd": -2699401.64, "ytd": 11676838.21, "pytd": 3315881.06, "daily": 883258.6}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	t	t	2025-12-26 22:57:16.357415	\N
bead27be-b745-460a-9e39-0fe6d50ab432	80d4d457-c260-47eb-8186-4eeb20ce7e2c	CC_AMER_PROG_TRADING_005	{"mtd": 75625.17, "ytd": 657728.41, "pytd": -12632603.7, "daily": 640136.96}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:57:16.357415	\N
07d581b6-d937-4d3c-82f7-948191756d12	80d4d457-c260-47eb-8186-4eeb20ce7e2c	CC_AMER_PROG_TRADING_006	{"mtd": -2285521.33, "ytd": 5045130.61, "pytd": 3409536.06, "daily": 46819.29}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:57:16.357415	\N
71a5d407-92f9-4bf3-b819-3747f06a1caa	80d4d457-c260-47eb-8186-4eeb20ce7e2c	CC_AMER_PROG_TRADING_007	{"mtd": -489505.48, "ytd": 5973979.19, "pytd": 12538948.7, "daily": 196302.35}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:57:16.357415	\N
7eb540d2-0b13-4fd4-a912-ddd75616d3cb	80d4d457-c260-47eb-8186-4eeb20ce7e2c	EMEA_INDEX_ARB	{"mtd": 4546486.64, "ytd": 12253940.34, "pytd": -30441485.45, "daily": -31501.85}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:57:16.357415	\N
abab3fe4-fd12-4be1-a99d-edcf6cad9483	80d4d457-c260-47eb-8186-4eeb20ce7e2c	CC_EMEA_INDEX_ARB_008	{"mtd": 2113486.85, "ytd": 10858650.5, "pytd": -2092918.75, "daily": 509611.2}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:57:16.357415	\N
a6e88e94-170a-4a8a-ab17-bb7a075e5b72	80d4d457-c260-47eb-8186-4eeb20ce7e2c	CC_EMEA_INDEX_ARB_009	{"mtd": 17861.63, "ytd": -961200.21, "pytd": -13655639.04, "daily": -1058036.04}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:57:16.357415	\N
a7de749e-5732-42b9-93b0-5da7e7b88a3e	80d4d457-c260-47eb-8186-4eeb20ce7e2c	CC_EMEA_INDEX_ARB_010	{"mtd": 2415138.16, "ytd": 2356490.05, "pytd": -14692927.66, "daily": 516922.99}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:57:16.357415	\N
46c8c700-6531-4403-a215-d3afc9df2120	80d4d457-c260-47eb-8186-4eeb20ce7e2c	APAC_ALGO_G1	{"mtd": -4832146.19, "ytd": 12414475.66, "pytd": 28432395.03, "daily": 434365.13}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:57:16.357415	\N
ade9aaf7-6cee-44ed-9720-271c11f5a036	80d4d457-c260-47eb-8186-4eeb20ce7e2c	CC_APAC_ALGO_G1_011	{"mtd": 1259260.66, "ytd": 1651792.47, "pytd": 20041118.46, "daily": -234800.54}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:57:16.357415	\N
b6b4b5ea-5666-4e73-80a4-141b1505c761	80d4d457-c260-47eb-8186-4eeb20ce7e2c	CC_APAC_ALGO_G1_012	{"mtd": -1692990.1, "ytd": 22236754.82, "pytd": 8525596.78, "daily": 287950.27}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:57:16.357415	\N
152c38a7-b4b9-40fb-b2ec-29784ee881b1	80d4d457-c260-47eb-8186-4eeb20ce7e2c	CC_APAC_ALGO_G1_013	{"mtd": -4398416.75, "ytd": -11474071.63, "pytd": -134320.21, "daily": 381215.4}	{"mtd": 0.0, "ytd": 0.0, "pytd": 0.0, "daily": 0.0}	f	t	2025-12-26 22:57:16.357415	\N
\.


--
-- Data for Name: fact_pnl_entries; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.fact_pnl_entries (id, use_case_id, pnl_date, category_code, amount, scenario, audit_metadata, daily_amount, wtd_amount, ytd_amount) FROM stdin;
895553c4-cbc7-4698-a8d4-7b746796b157	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_007	73000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	19203.43	134424.03	1920343.34
403aa09a-6135-4967-9d56-c33c5daadaa5	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_008	185000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	48666.24	340663.65	4866623.54
38dca0ff-935e-463a-8351-9e1b8e8c312b	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_009	97000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	25516.89	178618.24	2551689.10
6e2f340e-a0ef-4dd2-9c78-7b9a441a8b71	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_010	215000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	56558.06	395906.40	5655805.73
9d6fe094-d6de-4376-b432-36cb7b78c65b	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_011	63000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	16572.83	116009.78	1657282.61
1b0bc6cb-cdcf-4495-a318-0f3a8a9f1c5b	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_012	270000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	71026.40	497184.78	7102639.76
453fdc7c-b2a8-4d48-b49d-c05e00cb0022	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_013	108000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	28410.56	198873.91	2841055.90
fa52738b-0c48-41a8-94d4-abac741d4621	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_014	195000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	51296.84	359077.90	5129684.27
3e027e32-259c-4dd9-aa36-9c6ad26b61ce	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_015	87000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	22886.28	160203.99	2288628.37
cd343f75-f2f8-40f0-ad3e-40b025b18ceb	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_016	315000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	82864.13	580048.91	8286413.05
41c3dc94-4463-4ac4-b892-76cf058fd04b	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_017	68000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	17888.13	125216.91	1788812.98
2bf8970f-55c3-4354-a885-f70b922a186b	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_018	235000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	61819.27	432734.90	6181927.20
342a8cab-80c4-4a10-96ff-e048518a6df4	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_019	128000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	33671.77	235702.42	3367177.37
97005b2c-d197-4348-924c-b94f2c81be63	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_020	205000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	53927.45	377492.15	5392745.00
22f9b9fa-6a16-4cde-9940-70c4c54a0f07	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_021	0.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	0.00	0.00	0.00
4e5db393-bd71-40d0-81cd-3facfa77c11c	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_022	0.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	0.00	894406.49	1262691.51
c9938a0b-8363-4b8c-9a83-d1720d8cb42f	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_029	58000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	15257.52	106802.66	1525752.24
0830b59e-6793-479f-bda6-6f642f3fc993	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_030	208000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	54716.63	383016.43	5471663.22
23199ffd-549f-49e9-8dc4-205a9bce9524	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_021	450000.00	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	225337.61	1577363.26	22533760.95
5734f975-1675-4a1c-8f5a-b8439d7c4ae2	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_022	0.00	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	0.00	1752625.85	2503751.22
10f5312e-a6e1-4f97-8ff0-73faa9e09447	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_029	60000.00	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	30045.01	210315.11	3004501.46
a4ad980d-e174-4077-8c97-273b788ad325	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_030	210000.25	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	105157.68	736102.94	10515755.36
2101a4db-f2da-4d04-b6cf-c424ac78fdab	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_027	90000.25	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	45067.64	315472.73	4506752.45
3596a191-2ce8-4841-b746-94cdc1cc7fa4	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_028	290000.50	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	145217.81	1016523.17	14521757.44
348b3d87-a12e-4515-bc53-110ac37769dd	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_001	125000.50	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	125000.50	875000.25	12500000.75
9485ef7f-a0ca-46d3-97e5-2c5b6c19c353	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_001	120000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	120000.00	850000.00	12000000.00
bac3088f-5e1c-4263-a468-cfb6abca92f7	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_002	87500.75	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	87500.75	612500.50	8750000.25
2860c2f8-70c3-4687-b581-b9a750acefb5	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_002	90000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	90000.00	630000.00	9000000.00
1cd0424f-0e23-4fc8-8b58-c41e66ce6ec0	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_014	190000.00	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	190000.00	1330000.00	19000000.00
39e7a888-300a-4960-abbe-5ab08604e78f	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_003	250000.00	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	250000.00	1750000.00	25000000.00
bf1bfd95-27d7-4bcf-91d4-7e06fd0c8f2e	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_003	245000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	245000.00	1715000.00	24500000.00
ee7c2e0c-fd28-484f-95ca-855019d404b9	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_004	150000.25	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	150000.25	1050000.15	15000000.50
f460879f-8b64-4081-8e86-7fac44fa8215	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_004	155000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	155000.00	1085000.00	15500000.00
373354b1-651c-4f9b-8e5d-69128c5208c5	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_005	50000.00	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	50000.00	350000.00	5000000.00
438fd425-7aa1-41d4-8e0d-13ef3bbad62c	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_005	48000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	48000.00	336000.00	4800000.00
23f22942-48d0-44ad-9dd2-c991fd0c958a	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_006	300000.50	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	300000.50	2100000.35	30000000.75
a373ba68-73c8-4a69-a5bc-5f1e309eb78d	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_006	295000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	295000.00	2065000.00	29500000.00
613a7abc-22b2-4649-be15-a318667d0579	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_007	75000.25	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	75000.25	525000.15	7500000.50
8eae09ce-e05f-44db-ac57-8443a35b5f83	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_007	73000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	73000.00	511000.00	7300000.00
02153b2b-2e54-40f8-8845-f292eb09aeb1	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_008	180000.00	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	180000.00	1260000.00	18000000.00
099439fe-819d-4da9-977e-121e93d53fe8	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_008	185000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	185000.00	1295000.00	18500000.00
945a207a-013c-486a-aef5-1a7388028226	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_009	95000.75	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	95000.75	665000.50	9500000.25
28fcf65e-6208-4835-a1c7-1421bd3a23fe	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_009	97000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	97000.00	679000.00	9700000.00
cd58a888-c509-4da5-93c7-5cfe61d2cc1d	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_010	220000.50	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	220000.50	1540000.35	22000000.75
05d19536-b266-4caf-9499-a638bfcc9c9c	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_010	215000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	215000.00	1505000.00	21500000.00
b9fd09e2-e3bf-47e1-aaaa-e9017b8e3b81	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_011	65000.00	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	65000.00	455000.00	6500000.00
07cd08a0-df84-4772-9f6e-982c9a1e315b	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_011	63000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	63000.00	441000.00	6300000.00
d31f2a79-0809-4c8e-abc8-f658c55e1782	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_012	275000.25	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	275000.25	1925000.15	27500000.50
6b7e7c37-a6d5-4635-a302-5b368db0f23f	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_012	270000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	270000.00	1890000.00	27000000.00
ea169a1c-142e-48b1-98eb-38f444c939e2	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_013	110000.75	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	110000.75	770000.50	11000000.25
38ccb2f9-89ba-4bb9-b356-bec236bc910f	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_013	108000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	108000.00	756000.00	10800000.00
640023b7-a719-49e8-b048-a0149175038a	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_014	195000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	195000.00	1365000.00	19500000.00
9a400e30-f35f-464c-ab29-36e95d0d5624	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_015	85000.25	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	85000.25	595000.15	8500000.50
9be4ccd3-aa8a-40fd-8091-b78d3bba1128	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_015	87000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	87000.00	609000.00	8700000.00
fecec8f7-892c-4aaa-b8b8-822bbcfa15ec	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_016	320000.50	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	320000.50	2240000.35	32000000.75
a10e2ba9-8adb-4686-ab2f-5b19f10abaf4	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_016	315000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	315000.00	2205000.00	31500000.00
53923cda-bb93-4821-bfba-aedcd90c61aa	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_017	70000.00	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	70000.00	490000.00	7000000.00
4d4f5591-6cdd-496f-a6a2-ea337daefe7f	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_017	68000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	68000.00	476000.00	6800000.00
4a1a9670-11d9-4598-8ce7-fecefce347a8	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_018	240000.25	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	240000.25	1680000.15	24000000.50
28f91f4e-e5d7-4b76-bbc6-eb9c76fdc419	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_018	235000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	235000.00	1645000.00	23500000.00
0c95ccfa-4771-4196-a26e-05a45589bd99	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_019	130000.75	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	130000.75	910000.50	13000000.25
dc1b8951-235d-4f35-a36e-f7cc542d8315	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_019	128000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	128000.00	896000.00	12800000.00
6dcda134-8428-4cea-9185-18b9a4114d69	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_020	200000.00	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	200000.00	1400000.00	20000000.00
9707cf12-915b-4f78-ab59-aaf909d79669	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_020	205000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	205000.00	1435000.00	20500000.00
85bd4af7-9be1-45ad-9fc7-eb157918a941	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_021	450000.00	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	450000.00	3150000.00	45000000.00
535a6701-f109-4f4a-85e8-17bbf660cb55	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_021	0.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	0.00	0.00	0.00
61713c3f-c89d-429b-9528-fb5c23ba8651	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_022	0.00	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	0.00	3500000.00	5000000.00
d6c32e9f-d4ee-466e-af3b-436eb0a615cd	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_022	0.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	0.00	3400000.00	4800000.00
3da19863-3113-42ba-b540-40b0956942d7	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_023	105000.25	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	105000.25	735000.15	10500000.50
deadcc10-d9ea-4491-a732-3e90b5ce45f9	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_023	103000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	103000.00	721000.00	10300000.00
f943cee8-7bbb-4cce-9cd1-4605a100259c	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_024	260000.50	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	260000.50	1820000.35	26000000.75
e018efc4-6cf9-4edb-845a-1f3ac6cb19fa	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_024	255000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	255000.00	1785000.00	25500000.00
d1dbe001-1d20-400d-a06c-8050e8672941	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_025	140000.75	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	140000.75	980000.50	14000000.25
4de1caeb-906f-47a6-bec1-16eee4822937	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_025	138000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	138000.00	966000.00	13800000.00
c1b0afe7-0c81-4428-9603-4786913285ac	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_026	170000.00	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	170000.00	1190000.00	17000000.00
a1c6312e-817f-49d5-9917-83176e1db912	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_026	175000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	175000.00	1225000.00	17500000.00
3381b939-2709-4a41-8082-423c0cdfc645	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_027	90000.25	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	90000.25	630000.15	9000000.50
a6faf427-7a64-41e7-8537-c8ff4d3bfcb9	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_001	120000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	31567.29	223601.62	3156728.78
0280a33a-6152-4a90-b2e5-5677df474d8b	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_002	90000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	23675.47	165728.26	2367546.59
485a708c-b7e7-4d64-9262-78aee6e6c639	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_003	245000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	64449.88	451149.15	6444987.93
efcbc1df-319a-4e32-a041-080f0891b162	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_004	155000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	40774.41	285420.89	4077441.34
71ba095b-a93c-458b-9688-c7893e4dc6ca	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_005	48000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	12626.92	88388.41	1262691.51
fd3089b0-0e28-4cd1-9b5d-67d77aeb3399	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_006	295000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	77602.92	543220.41	7760291.59
7d1e0624-183f-475a-9229-7dc1276e23fc	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_027	92000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	92000.00	644000.00	9200000.00
26bb7623-273a-422d-914b-2f6fee6c3d5c	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_028	290000.50	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	290000.50	2030000.35	29000000.75
13607690-cbd9-4ced-a74e-e2acbf8869f8	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_028	285000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	285000.00	1995000.00	28500000.00
71b4db82-b723-494e-b614-4758ec197061	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_029	60000.00	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	60000.00	420000.00	6000000.00
f5e54c98-3e99-4ef2-bf71-6b67bc87143c	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_029	58000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	58000.00	406000.00	5800000.00
2564e208-decb-427d-8079-e78544f5fbc0	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_030	210000.25	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	210000.25	1470000.15	21000000.50
0d746b47-52ef-4d06-bfbd-1aed1057d463	a26121d8-9e01-4e70-9761-588b1854fe06	2025-12-24	TRADE_030	208000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	208000.00	1456000.00	20800000.00
4b06e6f8-4d96-4467-9c37-ac8a73060f24	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_007	75000.25	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	37556.39	262893.97	3755627.08
6c275e04-097a-47b8-aa56-4cfac7d85b94	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_008	180000.00	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	90135.04	630945.30	9013504.38
6b582525-4c88-4d82-85a5-958e18c58953	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_009	95000.75	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	47571.65	332999.17	4757127.44
679aca58-dd7d-4853-8dc7-5eb828ad780e	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_010	220000.50	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	110165.30	771155.55	11016505.74
cccc0b34-a4c5-45b7-80b6-606d11841e50	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_011	65000.00	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	32548.77	227841.36	3254876.59
d7a5e8d8-6c8b-472c-bbdf-107f6c41ffb8	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_012	275000.25	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	137706.45	963944.30	13770631.93
9e5a8854-13cf-40ad-bc62-af44ebb06dcb	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_013	110000.75	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	55082.91	385577.93	5508252.81
ec65b43a-6459-44cd-a7d8-630dd46e5899	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_014	190000.00	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	95142.55	665997.82	9514254.62
aa60c1b6-4fb1-4b31-b4af-20bce010e37a	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_015	85000.25	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	42563.90	297946.48	4256377.32
f7e4e84b-457e-4e17-9067-52bf39bff24b	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_023	103000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	27095.26	189666.79	2709525.54
d5c1c062-c19f-4783-920c-57255dabe00b	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_024	255000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	67080.49	469563.41	6708048.66
a9e4f8ce-71ea-4fef-a21e-00b8bd7c4bc7	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_025	138000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	36302.38	254116.67	3630238.10
f5bacadd-6876-4cf7-b34a-9278cf281ca4	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_026	175000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	46035.63	322249.40	4603562.81
bd20c953-e701-4530-98e2-b2d1a4a1cc82	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_027	92000.00	PRIOR	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	24201.59	169411.11	2420158.73
0a49e4c5-b5ba-4f37-925e-c74372b462b2	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_028	285000.00	PRIOR	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	74972.31	524806.16	7497230.85
bd793c5b-4c05-443a-a305-76676fbe7919	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_016	320000.50	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	160240.34	1121680.72	16024008.18
850ad0ad-7db6-4405-bd3b-e94506077c83	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_017	70000.00	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	35052.51	245367.62	3505251.70
2f5e6d05-128f-40cc-acf5-1dde8c48e0c9	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_018	240000.25	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	120180.18	841260.49	12018006.08
118a7643-9bd2-4e8e-854f-aceb442efd79	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_019	130000.75	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	65097.92	455682.98	6509753.29
e0aed379-6de6-4a85-a420-7f6f104ad63e	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_020	200000.00	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	100150.06	701050.33	10015004.86
6db45ec4-1632-4eb4-843f-a82d775b168b	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_001	125000.50	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	62594.03	438156.60	6259378.43
f1057004-3f3a-4444-9e09-4c175762f082	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_002	87500.75	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	43816.02	306709.77	4381564.76
b5dddc17-4fc9-40aa-acb8-e13cf3f40ae3	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_003	250000.00	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	125187.56	876312.92	12518756.08
a81446f1-3b9e-46e6-9783-5c92a0805c5b	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_004	150000.25	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	75112.67	525787.83	7511253.90
3942e283-2d73-4ea6-887c-067d4b60e805	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_005	50000.00	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	25037.52	175262.59	2503751.22
fe94685b-0a95-4fc2-8eb9-e44691109a89	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_006	300000.50	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	150225.32	1051575.69	15022507.68
a40df032-cea6-4098-931f-26cf700d1bf1	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_023	105000.25	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	52578.91	368051.51	5257877.80
ba22dac9-be68-4516-a67e-2e41092d0ac1	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_024	260000.50	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "MARKET_MAKING", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	130195.31	911365.63	13019506.70
e2022d70-ed09-4a1f-af4c-08f8dec91628	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_025	140000.75	ACTUAL	{"region": "AMER", "source": "sterling_facts.csv", "strategy": "ALGO", "legal_entity": "US_HOLDINGS", "risk_officer": "NYC_001", "import_timestamp": "2025-12-24"}	70105.41	490735.49	7010503.53
b749e1fa-a283-45ca-bd7d-fad4efde2600	b90f1708-4087-4117-9820-9226ed1115bb	2025-12-24	TRADE_026	170000.00	ACTUAL	{"region": "EMEA", "source": "sterling_facts.csv", "strategy": "VOL", "legal_entity": "UK_LTD", "risk_officer": "LDN_001", "import_timestamp": "2025-12-24"}	85127.53	595892.79	8512754.14
\.


--
-- Data for Name: fact_pnl_gold; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.fact_pnl_gold (fact_id, account_id, cc_id, book_id, strategy_id, trade_date, daily_pnl, mtd_pnl, ytd_pnl, pytd_pnl) FROM stdin;
c2363260-cba7-4bb7-bf62-0c90553df63b	ACC_007	CC_EMEA_INDEX_ARB_010	BOOK_08	STRAT_03	2024-04-09	-65712.76	-283627.94	892230.26	-1007814.41
1730188d-8d3e-44c0-8eb9-863499f8cd18	ACC_003	CC_APAC_ALGO_G1_012	BOOK_06	STRAT_05	2024-05-15	-43905.22	49297.78	765907.72	-255206.01
9ae38e93-ebf0-478d-8101-0f917c84bf97	ACC_009	CC_APAC_ALGO_G1_013	BOOK_09	STRAT_05	2024-01-04	-47780.00	17650.76	1533096.16	1006479.62
04c5642c-1beb-4ea2-ab95-107b83ed3b4a	ACC_001	CC_APAC_ALGO_G1_012	BOOK_06	STRAT_02	2024-01-05	58510.19	-109526.44	993979.01	1698024.89
0850049c-7ccc-4263-b6bd-95a0a0af9491	ACC_004	CC_AMER_PROG_TRADING_005	BOOK_03	STRAT_04	2024-06-05	-57792.29	138788.86	-205609.42	415444.17
0b1d3621-42ef-49d4-b88f-c5863f24c1d9	ACC_005	CC_EMEA_INDEX_ARB_009	BOOK_04	STRAT_02	2024-12-11	-26496.19	428267.37	216839.46	-343986.76
8316ebf6-86a2-4ec7-b38f-8ffedd0933fe	ACC_010	CC_EMEA_INDEX_ARB_010	BOOK_06	STRAT_05	2024-01-08	90552.81	97162.22	-522521.15	-707490.45
48cae679-2655-43c5-8fa8-9afd23a765b5	ACC_002	CC_AMER_PROG_TRADING_005	BOOK_04	STRAT_03	2024-12-20	-18330.91	-416810.95	1289067.37	-1670239.31
72f21518-9e04-4b3c-8855-b20c038dbaeb	ACC_006	CC_APAC_ALGO_G1_013	BOOK_03	STRAT_04	2024-07-21	23965.53	-425493.72	-732977.95	1528376.95
ef1f24f5-d6fb-43e6-b15b-c51fc2ca0c95	ACC_002	CC_AMER_CASH_NY_002	BOOK_04	STRAT_03	2024-04-26	-59441.77	227334.41	1290672.40	-1640820.30
ea511207-4ef5-4e15-8d18-eeffd5e3b7cd	ACC_001	CC_AMER_CASH_NY_001	BOOK_03	STRAT_01	2024-05-09	-38719.46	223888.57	-341069.79	1128742.65
b5b00eb6-d954-4b79-9a34-55280e3b48da	ACC_010	CC_AMER_CASH_NY_002	BOOK_07	STRAT_03	2024-10-17	95725.78	-335802.60	-1910068.63	1452649.55
e40d908a-42b0-4ae9-9ea5-1b33db7ba077	ACC_001	CC_EMEA_INDEX_ARB_008	BOOK_06	STRAT_05	2024-11-05	97435.36	52180.54	-1087355.83	-1495850.04
a897d1e7-6a0a-4c49-a57d-4221c8882cf9	ACC_010	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_03	2024-04-24	60638.49	43279.38	-147218.01	256581.56
e5ce504f-04fb-4924-bc52-642bccd78f4c	ACC_008	CC_AMER_CASH_NY_001	BOOK_09	STRAT_05	2024-05-15	-47035.00	400219.27	62613.92	-1676944.01
39eb5aec-d56c-4f84-a27c-163117b2fef9	ACC_002	CC_EMEA_INDEX_ARB_010	BOOK_06	STRAT_04	2024-12-26	74027.47	-175230.27	1621292.35	-1426194.84
33163382-72ce-42b8-9b41-9d7a10ac30d9	ACC_004	CC_EMEA_INDEX_ARB_010	BOOK_09	STRAT_01	2024-03-15	62040.02	195042.40	22421.07	1536959.94
a44db2f7-7e2a-436d-86fa-fb8006160747	ACC_008	CC_APAC_ALGO_G1_011	BOOK_07	STRAT_01	2024-08-12	-67390.52	-420771.17	1406188.80	-1321409.04
5ae4e51d-5416-4e46-a6c8-f89d742473b6	ACC_010	CC_APAC_ALGO_G1_012	BOOK_01	STRAT_02	2024-07-24	91432.35	-117103.56	1906488.93	1504381.59
131fbcff-c1bf-4c9a-8224-d5f1e552bedd	ACC_009	CC_AMER_CASH_NY_002	BOOK_01	STRAT_03	2024-03-08	95955.56	-84453.59	-1619737.40	-1522116.79
72ad9303-b550-4550-ad8c-f999025b8948	ACC_006	CC_AMER_PROG_TRADING_006	BOOK_04	STRAT_01	2024-06-11	-14210.16	-327014.34	-1242925.48	1113391.13
053d9844-fae1-4017-a82b-5a35e1f9f0ae	ACC_004	CC_APAC_ALGO_G1_011	BOOK_04	STRAT_01	2024-08-08	87567.86	-297007.29	-623943.82	-1093456.44
502fdb4d-3392-4f8a-b588-875dd5bd0f42	ACC_006	CC_AMER_PROG_TRADING_005	BOOK_09	STRAT_02	2024-08-02	6775.16	59832.54	-1971665.06	-313413.50
e6335641-aca9-4bc3-aa22-2f4f0a8fc5ca	ACC_009	CC_APAC_ALGO_G1_013	BOOK_04	STRAT_05	2024-09-06	73786.08	469199.08	-604422.69	-1794381.52
25eb9247-e695-4924-9961-c8b6965e0e7e	ACC_009	CC_EMEA_INDEX_ARB_008	BOOK_02	STRAT_02	2024-08-10	96514.15	366241.92	-348830.78	1335502.59
315b6a2a-13a3-46d1-aed8-351421b0693a	ACC_001	CC_APAC_ALGO_G1_012	BOOK_01	STRAT_02	2024-01-28	83660.55	-107026.96	606589.17	-298725.24
6a809e4a-3e01-41b3-bc14-abe879949c8f	ACC_004	CC_AMER_CASH_NY_004	BOOK_06	STRAT_04	2024-03-20	70425.86	427322.10	-275215.56	-1795939.01
37edf6ac-cfe6-4531-b9b5-3188437858b3	ACC_009	CC_AMER_CASH_NY_004	BOOK_08	STRAT_01	2024-06-22	-66434.40	-281190.07	-692253.73	-1047823.51
6e689830-6d74-4ceb-8e4d-53a264a00884	ACC_008	CC_AMER_CASH_NY_002	BOOK_07	STRAT_02	2024-11-08	-5656.78	430232.11	641104.02	359427.00
9b29db3c-066a-49b8-9317-b9e1a6951412	ACC_003	CC_AMER_CASH_NY_003	BOOK_06	STRAT_01	2024-07-15	-92704.65	233255.95	-1547609.39	-1355892.85
99a3c0d4-1ef3-4ef4-9d14-6e5da94cf0a5	ACC_001	CC_AMER_CASH_NY_002	BOOK_07	STRAT_04	2024-06-19	98527.10	-32838.34	1210299.95	1623979.68
845c86cb-5331-4c1b-a4cc-ef272a564a43	ACC_006	CC_AMER_CASH_NY_001	BOOK_04	STRAT_05	2024-12-03	-77137.43	-30533.50	159896.20	-1484876.93
6d1f9810-ec8b-4364-9170-a2e125be3445	ACC_005	CC_AMER_PROG_TRADING_007	BOOK_06	STRAT_03	2024-12-13	-38931.11	84630.51	-1104142.06	1598605.33
14e8892b-998b-4351-814a-dd01618948c6	ACC_003	CC_AMER_CASH_NY_002	BOOK_03	STRAT_04	2024-10-07	8065.49	455240.96	1255296.85	60188.77
43c6a0c5-4123-4657-9211-ef5cdc28a5fd	ACC_008	CC_AMER_CASH_NY_004	BOOK_01	STRAT_02	2024-12-09	-62261.17	-56538.23	-682504.15	1357581.39
3e46393f-3c5e-4058-a046-7453335600f1	ACC_010	CC_APAC_ALGO_G1_013	BOOK_09	STRAT_05	2024-11-03	75536.69	111336.50	1153518.87	-1678164.32
0190f665-3b84-48d2-9283-811a568d5aa9	ACC_002	CC_EMEA_INDEX_ARB_008	BOOK_06	STRAT_03	2024-11-23	22681.85	-73470.51	-116165.09	-449797.99
a528d7b8-b5e5-4840-b2fb-1fef7644523e	ACC_002	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_04	2024-07-17	-94304.40	-499352.42	1600108.08	-1421162.76
35eae44c-6a31-4c0e-96cb-74d2fe73f618	ACC_001	CC_AMER_PROG_TRADING_006	BOOK_06	STRAT_01	2024-08-03	-97544.74	-101061.14	1418081.87	750997.21
da16eefc-04e6-47e2-9618-e8f34d2c96c0	ACC_009	CC_AMER_CASH_NY_002	BOOK_09	STRAT_01	2024-05-14	-11936.01	-186427.42	281655.88	-541339.23
1bfbb182-21d9-462e-9281-ba19ce9d5ee6	ACC_010	CC_EMEA_INDEX_ARB_010	BOOK_03	STRAT_02	2024-06-26	74198.76	171774.89	-1673920.52	-7114.73
651d77dc-28df-4068-b91b-52666e053370	ACC_008	CC_AMER_CASH_NY_002	BOOK_01	STRAT_03	2024-06-27	84565.28	-314618.37	-1783198.98	-894831.34
d0147572-9756-485d-b3b7-4ef615928d3a	ACC_004	CC_AMER_CASH_NY_002	BOOK_05	STRAT_05	2024-07-29	30596.56	-385059.78	364101.03	1605504.95
800473dd-02b4-4840-bbcf-bbe8e2028c9e	ACC_007	CC_AMER_CASH_NY_003	BOOK_09	STRAT_03	2024-02-25	-16645.07	141301.96	423372.40	1219833.82
9fa6228e-0346-4845-97ba-ff023cb0888d	ACC_005	CC_AMER_PROG_TRADING_006	BOOK_07	STRAT_03	2024-01-13	-96365.64	209723.03	935120.78	906434.24
3bf4500a-5e1d-4aa9-9ef9-32f673d2e9f6	ACC_009	CC_EMEA_INDEX_ARB_009	BOOK_02	STRAT_03	2024-08-22	92435.13	-134020.30	190687.99	233538.10
4fc7ec73-85aa-4c7d-b346-af351855c719	ACC_007	CC_APAC_ALGO_G1_012	BOOK_06	STRAT_03	2024-04-07	-88282.42	-436610.94	1746857.22	911865.68
a8b0f1d9-b562-4dee-bc0f-8cf6fd58f956	ACC_010	CC_APAC_ALGO_G1_013	BOOK_09	STRAT_03	2024-03-02	-78067.38	-418725.99	-1130384.29	581655.98
229f4ac9-c557-41fa-b065-539481dcbade	ACC_004	CC_AMER_PROG_TRADING_006	BOOK_02	STRAT_01	2024-10-18	9185.61	258278.19	-138426.83	723706.02
632476b2-567f-4967-85cc-37328737b650	ACC_003	CC_EMEA_INDEX_ARB_009	BOOK_04	STRAT_01	2024-01-11	-18392.85	316539.43	-896919.23	791311.57
046b9041-0692-4bd8-8c18-146e2cb5198d	ACC_006	CC_APAC_ALGO_G1_013	BOOK_02	STRAT_04	2024-10-02	-34822.31	-460125.64	589943.72	1582333.00
74c95a17-9983-4fc4-a1d2-465dff9b406a	ACC_002	CC_AMER_CASH_NY_002	BOOK_10	STRAT_03	2024-05-14	-93851.84	-257498.72	-1034266.14	624200.69
5eddb679-15dd-4d6e-97ae-4d31d8ebe0ed	ACC_001	CC_AMER_CASH_NY_004	BOOK_02	STRAT_05	2024-12-14	-52405.29	216470.37	-1160637.27	807414.85
0fde8a16-67dc-40d6-9da4-847022e12c59	ACC_003	CC_AMER_PROG_TRADING_006	BOOK_07	STRAT_01	2024-02-28	-55542.06	475922.31	1088907.95	120016.69
4da4667d-db43-4ed2-bac2-f7bc22ea6e81	ACC_007	CC_APAC_ALGO_G1_013	BOOK_10	STRAT_04	2024-06-29	90090.17	299135.09	635873.29	1199511.10
c739414b-7516-4932-91bf-f667d1a685aa	ACC_006	CC_AMER_PROG_TRADING_006	BOOK_10	STRAT_03	2024-10-19	19521.19	-350851.97	1728750.50	1087093.41
1ce3ad58-dd08-4f6c-91a2-19ac2844ad3f	ACC_005	CC_AMER_CASH_NY_001	BOOK_01	STRAT_01	2024-03-22	95394.32	374785.98	-1406734.00	109788.38
c72be197-aa25-4d66-83e4-48fa01fe19d4	ACC_007	CC_AMER_PROG_TRADING_005	BOOK_03	STRAT_04	2024-07-29	-23509.08	475203.20	960445.22	-314114.82
126b2bf4-cf1d-44db-9938-3db416769c55	ACC_007	CC_APAC_ALGO_G1_012	BOOK_02	STRAT_05	2024-12-11	9362.07	463998.28	-564027.40	52871.86
63cc8318-930c-4d5e-b390-7ff95f1f69e1	ACC_009	CC_APAC_ALGO_G1_013	BOOK_01	STRAT_03	2024-03-01	-5382.07	194753.22	1568636.21	-695439.40
b00a5422-18a0-4b12-8bc0-83253c889de5	ACC_001	CC_APAC_ALGO_G1_013	BOOK_02	STRAT_04	2024-04-07	46723.39	-78130.62	459472.16	-1382636.89
71a4c679-f3f9-482b-afb7-c79b50580ae4	ACC_010	CC_AMER_PROG_TRADING_005	BOOK_10	STRAT_05	2024-09-09	15242.77	-263474.39	-588208.37	-1032534.46
8cab3812-2a52-4117-9d11-f6c8ed8497d6	ACC_004	CC_AMER_PROG_TRADING_005	BOOK_06	STRAT_04	2024-03-21	-58906.65	495849.41	-1880278.38	-1413249.94
a3754766-2007-48bd-9dc9-810b04caadaf	ACC_001	CC_APAC_ALGO_G1_011	BOOK_09	STRAT_04	2024-07-18	41624.60	13613.13	-897849.94	-387398.08
68163ad9-0b1b-458d-854d-91a02f0659fb	ACC_004	CC_AMER_PROG_TRADING_006	BOOK_07	STRAT_01	2024-09-22	-70987.60	-112632.30	1457195.02	1589964.61
98b7f43a-4f26-499b-be23-d58f80754d9b	ACC_002	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_05	2024-01-29	51627.99	-217340.76	-1086865.25	-16258.17
2ded2b73-2038-47b5-bc36-fe614bfd61cc	ACC_003	CC_APAC_ALGO_G1_012	BOOK_01	STRAT_03	2024-09-22	84876.23	291016.57	-1723192.67	1703426.31
9543e622-3199-4e15-9d04-200e3536d821	ACC_008	CC_APAC_ALGO_G1_012	BOOK_04	STRAT_02	2024-12-23	-53226.05	-37872.74	-189177.63	10561.13
fb46c8d5-35bf-4151-b7b6-266ec069607e	ACC_002	CC_APAC_ALGO_G1_011	BOOK_06	STRAT_04	2024-05-06	54099.24	22611.86	-706161.94	1459858.93
9b277bb6-e727-493d-9237-038bc6425c9e	ACC_007	CC_APAC_ALGO_G1_013	BOOK_01	STRAT_05	2024-12-29	72857.89	236022.26	-675070.62	1264598.39
5124ed7f-96da-4869-8bcd-6907b6325d6e	ACC_007	CC_AMER_CASH_NY_004	BOOK_02	STRAT_02	2024-09-24	14133.66	-203625.20	-1413067.16	1302748.99
27371867-10f4-45d4-bbc1-8e4128908a2a	ACC_010	CC_EMEA_INDEX_ARB_010	BOOK_08	STRAT_04	2024-08-04	-27227.75	-18083.86	1541183.04	1492839.94
24d46793-6d76-44a6-b2ad-ba18ee1639a2	ACC_007	CC_AMER_PROG_TRADING_007	BOOK_01	STRAT_05	2024-08-17	-98289.17	-171822.85	556293.90	1635542.45
3aeb67a1-4a3b-4db7-9c34-a7ed20ceecf6	ACC_005	CC_AMER_CASH_NY_004	BOOK_10	STRAT_01	2024-02-11	38698.59	426007.52	1993551.94	-1440016.88
d6c3e81c-636f-4833-bc88-a1c2e2da1050	ACC_010	CC_EMEA_INDEX_ARB_008	BOOK_08	STRAT_05	2024-08-05	31862.26	-470574.97	-1016221.76	-1257718.39
7aae3078-1e72-417b-88dc-51d24db05069	ACC_009	CC_APAC_ALGO_G1_011	BOOK_02	STRAT_05	2024-03-11	59706.43	168290.65	-1563288.60	105189.13
f5da4dce-aeb0-4706-ae6b-61a8ba6e63cf	ACC_010	CC_AMER_CASH_NY_001	BOOK_10	STRAT_01	2024-10-03	-55707.37	-486321.79	1359234.16	-1274134.43
0b219f95-5f85-4f6e-a96a-c317142abd2d	ACC_005	CC_APAC_ALGO_G1_011	BOOK_06	STRAT_03	2024-02-29	-84617.28	212818.11	-449499.31	213844.03
f9ac5a20-d165-49d9-8388-6c7a3f59bdbc	ACC_004	CC_EMEA_INDEX_ARB_009	BOOK_08	STRAT_02	2024-09-29	-95470.37	383257.69	-1646587.88	1348561.97
a59ddb7f-6b6e-413f-b6af-f07c17a0ddc9	ACC_006	CC_AMER_CASH_NY_001	BOOK_03	STRAT_03	2024-11-24	-71382.90	-377678.00	1911161.15	747192.30
9a7ce572-5899-4b89-8d17-b47dd05497c5	ACC_009	CC_EMEA_INDEX_ARB_010	BOOK_01	STRAT_05	2024-09-04	-54625.57	34353.46	902640.80	-743565.16
818467e8-4056-4cde-b622-873f15380071	ACC_001	CC_APAC_ALGO_G1_011	BOOK_03	STRAT_03	2024-10-24	-58869.57	-112680.87	-747663.41	-1701219.22
e1eb2087-87b3-4ed0-84ec-bcede19b1f23	ACC_010	CC_EMEA_INDEX_ARB_008	BOOK_05	STRAT_04	2024-01-30	82975.73	-46677.84	1235439.47	834642.09
9f7b5486-a84e-4c6d-a60f-528f03857914	ACC_001	CC_AMER_CASH_NY_001	BOOK_10	STRAT_01	2024-08-25	31130.39	407444.07	243307.51	34916.45
0727858a-3af0-46c8-9d34-e37bbd6795c3	ACC_008	CC_AMER_PROG_TRADING_007	BOOK_04	STRAT_04	2024-02-03	-78079.37	297302.91	300016.07	342553.15
ef76f793-ec41-4731-a13b-b3bc6f6be5be	ACC_003	CC_EMEA_INDEX_ARB_009	BOOK_03	STRAT_01	2024-07-04	-32689.09	355886.84	638823.30	-517924.91
3a27d3a4-2c50-4025-9421-985f76602bfa	ACC_003	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_05	2024-12-19	35390.62	391933.52	-527218.11	-132280.90
4b3badba-ee79-41f6-ba4b-904f2bda06cb	ACC_004	CC_AMER_PROG_TRADING_006	BOOK_01	STRAT_04	2024-01-16	18043.88	345849.31	1130623.96	1783983.85
837d9bc7-8ac7-4b11-a71e-d23989d1c343	ACC_007	CC_AMER_PROG_TRADING_005	BOOK_01	STRAT_05	2024-12-15	-38357.28	-242982.84	1411214.93	-445425.63
1496b89b-8230-43a8-abc0-203bc98b098f	ACC_009	CC_APAC_ALGO_G1_011	BOOK_07	STRAT_02	2024-09-08	80386.16	-371678.85	-1462693.89	1144568.64
13d9ae25-975b-4847-9466-6e7e28f63970	ACC_002	CC_EMEA_INDEX_ARB_008	BOOK_02	STRAT_03	2024-01-24	86035.44	-144323.75	-1797132.59	574504.89
8784d175-efac-42df-addc-b69d27a70ad5	ACC_004	CC_APAC_ALGO_G1_011	BOOK_06	STRAT_04	2024-06-07	14884.95	-246291.66	1873435.49	1694808.64
dbd48338-0597-404a-b02b-6d39637b68e6	ACC_008	CC_AMER_PROG_TRADING_007	BOOK_09	STRAT_05	2024-12-08	14713.13	-164778.01	-1673025.81	52435.14
14d2f27c-7064-4bb6-bfb2-0c25a5d030d4	ACC_004	CC_AMER_CASH_NY_002	BOOK_06	STRAT_02	2024-08-06	-98282.97	-292099.40	-1504375.49	-1627528.58
5cfcb9db-a2b9-4b05-94b8-1f6213ce0ee1	ACC_002	CC_EMEA_INDEX_ARB_010	BOOK_08	STRAT_01	2024-09-12	82574.51	268836.10	-774533.49	179181.47
2f1d30ed-cb85-47d2-8701-4c260f50d7f1	ACC_004	CC_APAC_ALGO_G1_013	BOOK_01	STRAT_02	2024-03-19	-45013.53	61834.65	1682418.35	-849485.67
8e255981-4210-499f-87cd-aa0f2ef93c73	ACC_001	CC_APAC_ALGO_G1_012	BOOK_04	STRAT_05	2024-02-28	17017.92	390523.28	-1793498.65	1070759.08
180def99-53f6-43cb-af95-341871305689	ACC_006	CC_AMER_CASH_NY_004	BOOK_06	STRAT_01	2024-09-18	-54969.98	-230481.25	-1647705.57	1445452.95
a5a668a4-617a-4b9c-8852-9b06931bd8c8	ACC_009	CC_AMER_PROG_TRADING_006	BOOK_10	STRAT_04	2024-09-16	-76154.71	453407.13	-949076.93	951675.42
1f9fae1a-b4d3-4f05-b2d5-d7125c2c600a	ACC_004	CC_EMEA_INDEX_ARB_010	BOOK_04	STRAT_05	2024-12-03	-75467.12	299474.37	1600833.84	-407125.28
9f1e8bb6-7e5b-4315-9e9f-4a98b919d233	ACC_001	CC_AMER_CASH_NY_003	BOOK_01	STRAT_05	2024-05-20	45395.19	-315121.24	-1286190.90	-1081265.59
f5529eca-5291-47fd-95a7-189116a4070c	ACC_003	CC_APAC_ALGO_G1_013	BOOK_09	STRAT_04	2024-03-04	2283.52	374561.00	-1493424.89	1542604.50
b9114291-d4c6-436c-a841-1686dd1efc48	ACC_006	CC_AMER_CASH_NY_003	BOOK_04	STRAT_01	2024-04-10	-38497.41	-401016.42	-986832.46	-833072.05
b4643ab7-19c5-493b-83fe-12144a6f34d9	ACC_009	CC_AMER_PROG_TRADING_006	BOOK_07	STRAT_05	2024-06-04	85976.71	182656.22	1488463.76	-911132.61
26953561-daac-4aee-8283-4e362c92f9f1	ACC_002	CC_EMEA_INDEX_ARB_008	BOOK_09	STRAT_05	2024-06-13	-34907.60	-227076.48	-627464.89	-782400.85
fe2c43da-59e2-45f4-8e67-943cf54490cb	ACC_009	CC_APAC_ALGO_G1_011	BOOK_01	STRAT_04	2024-04-17	77625.34	36089.33	310992.30	-90272.66
4f7b9ac6-2a6b-421d-936e-2ba6e1bd7d8e	ACC_009	CC_AMER_PROG_TRADING_007	BOOK_07	STRAT_03	2024-11-19	-95649.47	395751.85	-600011.49	1717574.06
a6cea3aa-9fb6-4926-b61b-3ff83e1ddf87	ACC_003	CC_AMER_CASH_NY_002	BOOK_03	STRAT_03	2024-06-18	59287.74	445961.82	950080.24	375465.55
7c5b381d-761b-4c9f-a126-aa6b154094ba	ACC_006	CC_EMEA_INDEX_ARB_008	BOOK_05	STRAT_02	2024-08-24	85604.93	-316671.87	1689240.55	-856256.66
2167e786-388c-43ac-8499-842985a9ea0b	ACC_008	CC_AMER_PROG_TRADING_007	BOOK_03	STRAT_05	2024-03-25	-38281.92	391713.34	623680.52	-938340.86
cad682e0-d334-495a-a68f-10534225258e	ACC_005	CC_APAC_ALGO_G1_011	BOOK_10	STRAT_01	2024-04-04	-52203.91	353787.23	-720163.32	-87245.48
5c2a09bd-8f1a-4ce7-8392-96c3f1af7e11	ACC_003	CC_EMEA_INDEX_ARB_008	BOOK_07	STRAT_02	2024-12-29	-14597.21	312038.18	-285201.96	-1216590.06
e15595b4-1b34-43bd-86fd-a79e21610b00	ACC_005	CC_AMER_PROG_TRADING_006	BOOK_09	STRAT_03	2024-12-13	-97720.21	-145915.91	-1695270.07	-406445.61
7fcfd616-6616-4460-b726-269b541e7467	ACC_003	CC_APAC_ALGO_G1_013	BOOK_08	STRAT_05	2024-01-13	52294.65	-489174.23	-262556.65	871310.69
f41be112-e3e1-4485-8143-b680fd0cc671	ACC_005	CC_AMER_CASH_NY_004	BOOK_10	STRAT_05	2024-06-08	52335.79	74041.60	4928.49	-404626.15
19b49b0f-d4fc-4218-83e9-c4460e925ccc	ACC_007	CC_AMER_PROG_TRADING_007	BOOK_04	STRAT_03	2024-10-02	84855.25	440961.94	1682687.35	500789.68
26233436-c69f-4a2f-8f59-452df6939590	ACC_005	CC_EMEA_INDEX_ARB_010	BOOK_07	STRAT_02	2024-07-30	9002.09	-218424.47	1060650.59	-1471320.12
04185a90-9149-4c95-a2e1-7858c6b2a2cb	ACC_003	CC_APAC_ALGO_G1_011	BOOK_03	STRAT_02	2024-02-26	19707.38	-257331.58	-1865453.78	1393557.56
ab352c4f-c22a-47dc-bf89-90e9f5b42530	ACC_007	CC_AMER_CASH_NY_002	BOOK_09	STRAT_03	2024-01-17	69093.92	357369.90	1497051.02	1348899.53
447bbc63-1ddb-44fd-8cc0-84a84bfd15cd	ACC_008	CC_APAC_ALGO_G1_013	BOOK_10	STRAT_02	2024-09-26	67703.21	354460.06	-1916406.58	-1692822.25
c8832620-c712-43e1-afc0-86c8ec4cd9b2	ACC_008	CC_AMER_CASH_NY_003	BOOK_09	STRAT_05	2024-11-13	41496.90	347579.05	-956659.94	-384418.73
c908972c-0f3f-4f67-b094-0ab0f89641b8	ACC_009	CC_EMEA_INDEX_ARB_009	BOOK_07	STRAT_01	2024-11-28	58826.68	-491598.83	-1507525.93	-47232.31
cdb009ad-5a42-42fe-9960-538e4244b80a	ACC_005	CC_AMER_PROG_TRADING_006	BOOK_03	STRAT_04	2024-04-26	-2217.62	-122270.87	213366.45	553754.90
334d348d-563d-4f32-ad32-d102a2a7fbb6	ACC_007	CC_APAC_ALGO_G1_012	BOOK_05	STRAT_03	2024-08-04	-16499.64	475669.83	-973329.69	1351698.80
313c15a4-dfec-4847-82d1-21cde898739a	ACC_003	CC_APAC_ALGO_G1_012	BOOK_10	STRAT_04	2024-02-14	90536.87	101602.20	-1341915.63	-850810.17
ad4a4591-a302-42a7-8188-787da0ecc077	ACC_008	CC_APAC_ALGO_G1_013	BOOK_03	STRAT_05	2024-10-19	76756.71	-318144.59	1664609.49	1459872.77
bb8debc3-df69-4d34-9e39-064232eab1c5	ACC_002	CC_AMER_CASH_NY_002	BOOK_01	STRAT_01	2024-09-19	-5172.53	406432.56	908314.29	-1403080.87
b19e9004-2e7c-4f90-92b1-28266938ec84	ACC_009	CC_APAC_ALGO_G1_013	BOOK_03	STRAT_01	2024-11-15	-47542.57	-190102.30	-1469065.80	1674554.00
7e169409-2791-459b-a6ef-313873323c1b	ACC_004	CC_AMER_CASH_NY_002	BOOK_06	STRAT_01	2024-11-28	-10250.71	-104051.63	-404331.39	-895948.90
34097e2d-bab7-422b-94e4-8d262a4e7156	ACC_010	CC_EMEA_INDEX_ARB_009	BOOK_09	STRAT_01	2024-04-20	23114.03	185442.69	-1619328.16	370741.39
eed7068d-7115-42cb-ac52-9aab51458e70	ACC_002	CC_AMER_CASH_NY_003	BOOK_08	STRAT_04	2024-05-24	39341.71	-289739.65	-1797424.25	-770302.98
6bad1809-6545-4b2c-b9b7-8b39c479d210	ACC_010	CC_APAC_ALGO_G1_013	BOOK_09	STRAT_05	2024-11-23	-58736.29	-3754.17	-1158855.67	1558054.45
5c3d2f48-6022-4f25-b760-96e60a9f8d51	ACC_003	CC_AMER_CASH_NY_003	BOOK_07	STRAT_04	2024-08-18	22431.58	-256678.11	1084293.70	1665364.40
21a73c21-23c8-4349-8ab7-4707b3d4f5fb	ACC_007	CC_AMER_CASH_NY_003	BOOK_09	STRAT_03	2024-10-02	47885.04	252157.66	1563590.96	925911.08
2df22cf3-715b-4cb5-9775-3846b5e473a6	ACC_001	CC_AMER_PROG_TRADING_007	BOOK_01	STRAT_01	2024-07-15	-82771.47	-67266.17	-700458.82	-710704.20
b29aef63-c18f-48b1-b87b-add5f3a9c2a2	ACC_002	CC_AMER_PROG_TRADING_005	BOOK_03	STRAT_04	2024-10-13	69677.73	111661.30	490475.18	1356203.87
f63bb946-2592-4b01-b5a6-24673448483c	ACC_007	CC_EMEA_INDEX_ARB_008	BOOK_02	STRAT_01	2024-01-22	-86057.60	-358121.90	-275897.13	213816.31
f87678b1-5ce8-440c-99e4-fe7178215dc6	ACC_010	CC_AMER_CASH_NY_003	BOOK_01	STRAT_01	2024-11-13	-84055.90	445272.39	1182864.37	-349168.28
45eb8122-0f4a-40e8-8e23-d2dc10adf541	ACC_005	CC_EMEA_INDEX_ARB_008	BOOK_10	STRAT_04	2024-12-04	-5071.98	478069.77	-1187122.78	117102.12
28596587-ba3d-4c16-9593-5838008e1304	ACC_010	CC_AMER_PROG_TRADING_006	BOOK_08	STRAT_01	2024-04-16	21145.99	-164038.78	-1045002.18	-1683226.53
dae1dfa6-39d7-4f39-a85d-8d1ade06d969	ACC_008	CC_AMER_CASH_NY_004	BOOK_04	STRAT_03	2024-06-18	98768.55	381758.74	554331.11	-1790930.14
69593808-17ca-45fb-9d80-44f074dbfd86	ACC_004	CC_APAC_ALGO_G1_012	BOOK_09	STRAT_04	2024-02-08	7638.31	6172.80	659699.89	1350235.08
e24ba026-1831-4e62-be0d-735fdca4399b	ACC_005	CC_EMEA_INDEX_ARB_010	BOOK_10	STRAT_05	2024-02-07	33258.53	-95432.66	1861363.40	94265.74
77981cd7-0946-4af6-ba3f-d5355a7978b3	ACC_005	CC_EMEA_INDEX_ARB_009	BOOK_02	STRAT_02	2024-04-05	-18473.98	-251815.66	-1580177.58	1406447.71
f2edb9ea-a072-40ca-81d1-d9e6902b6824	ACC_002	CC_AMER_PROG_TRADING_007	BOOK_05	STRAT_01	2024-06-22	98357.01	-182881.76	-856530.04	-389700.64
0b1dd1c5-c078-40d9-af4c-348fb3b43b83	ACC_001	CC_EMEA_INDEX_ARB_009	BOOK_04	STRAT_03	2024-01-12	-14827.40	-7065.91	912403.60	248457.22
8b24193c-cdd9-41a6-a97d-95911826d16e	ACC_006	CC_AMER_PROG_TRADING_005	BOOK_07	STRAT_02	2024-04-06	-98060.63	303262.16	1372151.99	-30520.66
9784d072-fcc1-419a-abaa-3b291f7cc4d4	ACC_009	CC_EMEA_INDEX_ARB_008	BOOK_07	STRAT_02	2024-02-22	-88577.66	437642.92	-1159563.73	1253296.08
921c2511-5d91-4102-8b63-f34f476e5c13	ACC_004	CC_AMER_CASH_NY_001	BOOK_05	STRAT_01	2024-11-01	-99271.33	22569.64	1357769.52	-396505.20
a1e34403-32d0-4474-a1c6-b2a1e1378fa3	ACC_006	CC_APAC_ALGO_G1_012	BOOK_10	STRAT_02	2024-10-04	22126.08	326613.61	343030.83	849398.39
cdc7e7e3-fb15-4ff3-86e2-b006b766429d	ACC_010	CC_APAC_ALGO_G1_011	BOOK_02	STRAT_05	2024-08-24	37965.45	403147.10	-176949.52	-1095021.42
1cfed441-57eb-4897-a010-0c945191dadb	ACC_008	CC_AMER_PROG_TRADING_005	BOOK_05	STRAT_05	2024-08-28	-99414.48	183598.93	-1462435.73	414577.05
cd88e6a6-a5ec-4132-b55f-fd3ca799bfb0	ACC_009	CC_EMEA_INDEX_ARB_009	BOOK_03	STRAT_03	2024-03-12	-13594.67	262332.66	1631183.44	-937851.95
23a4ce78-08d5-445f-85c4-1d8fa2e9b8cb	ACC_004	CC_APAC_ALGO_G1_011	BOOK_06	STRAT_04	2024-02-19	75232.61	183740.92	702547.50	93302.77
aab8e535-cdb5-4cb9-a4ab-af61f1f97f81	ACC_004	CC_EMEA_INDEX_ARB_010	BOOK_06	STRAT_05	2024-04-07	27880.99	445923.09	-457070.47	109908.24
3f00e523-a567-486a-a607-14d1f8359ac5	ACC_002	CC_AMER_CASH_NY_002	BOOK_05	STRAT_01	2024-10-17	10656.09	-181469.41	296814.07	-1013222.49
2c243454-e63d-4625-ad20-c4f8bd781bdd	ACC_006	CC_AMER_PROG_TRADING_005	BOOK_08	STRAT_03	2024-06-20	61231.14	197560.51	1915275.05	719276.17
4eb942a9-fd57-4744-b027-df9dbbd2aa0e	ACC_010	CC_AMER_CASH_NY_004	BOOK_06	STRAT_04	2024-11-27	-76902.57	-408289.09	59360.25	77234.15
9f23a0a4-76bb-4230-8af0-a98b0d2f7456	ACC_005	CC_AMER_PROG_TRADING_006	BOOK_04	STRAT_05	2024-10-19	21026.93	-296826.39	928123.14	916850.69
95e32d3b-7fb5-417a-b786-e44d5d71a880	ACC_010	CC_AMER_PROG_TRADING_007	BOOK_09	STRAT_04	2024-07-09	-794.42	180756.75	1236771.25	1038804.26
84aa3a2c-f2e0-4788-9853-5377beb4583c	ACC_010	CC_AMER_CASH_NY_004	BOOK_01	STRAT_05	2024-12-31	50357.83	-448837.12	-1612750.29	-1308230.16
ea04e622-eb87-4705-b310-1632d0fdebac	ACC_008	CC_AMER_CASH_NY_004	BOOK_07	STRAT_03	2024-03-24	-30073.14	88735.75	1899721.14	-1061038.28
e4065356-1dcd-477c-846c-a3f3e0937830	ACC_002	CC_APAC_ALGO_G1_013	BOOK_01	STRAT_02	2024-05-06	5319.41	85740.92	1008326.82	1174495.32
d6fed590-e0bf-4479-8c49-11ac927c6d62	ACC_008	CC_EMEA_INDEX_ARB_008	BOOK_04	STRAT_05	2024-01-20	12398.08	-322563.60	1402769.54	1394015.03
1bef0d98-6d61-479b-b3c6-9d7246b55447	ACC_004	CC_AMER_CASH_NY_002	BOOK_05	STRAT_03	2024-05-16	33105.11	113738.72	792291.02	874069.99
df3a5839-1379-4837-b71b-5d6982ebadf0	ACC_008	CC_EMEA_INDEX_ARB_010	BOOK_08	STRAT_03	2024-11-09	54242.43	418785.72	1287226.43	1149468.83
9e78d95b-d76d-4f39-ac02-b10037099d9d	ACC_002	CC_AMER_PROG_TRADING_005	BOOK_01	STRAT_04	2024-12-21	16450.95	354379.10	-823668.09	-1474296.58
5cefd962-b9d9-474d-9ba6-c51f2d774d93	ACC_009	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_05	2024-05-11	-62245.56	-119867.90	-964642.80	-956729.91
e27aebfb-3f6c-41f8-88fe-adcb7ee42ebd	ACC_007	CC_EMEA_INDEX_ARB_010	BOOK_10	STRAT_02	2024-10-06	-21537.69	124439.66	1657077.05	333495.39
048bf004-41c7-45f4-9edd-9703a9ef5300	ACC_008	CC_APAC_ALGO_G1_013	BOOK_04	STRAT_01	2024-05-12	36839.07	206006.10	-984011.09	-1034919.88
bdca5f73-535f-4d32-bb33-98362b1e6a6a	ACC_001	CC_AMER_CASH_NY_004	BOOK_01	STRAT_02	2024-02-19	-620.20	322003.87	398195.42	-1687888.62
68e82e27-c1ff-4315-a58e-3b639204ba01	ACC_010	CC_AMER_PROG_TRADING_005	BOOK_07	STRAT_03	2024-12-01	54451.33	-195050.68	1539339.16	-1639712.12
20a437e2-74c6-4a97-a0e9-c3dde3a33a6e	ACC_001	CC_EMEA_INDEX_ARB_008	BOOK_05	STRAT_03	2024-02-25	33209.86	-173251.41	504810.46	-1465559.54
1dc18b5c-c8e4-4352-8f34-28154822e79e	ACC_007	CC_AMER_PROG_TRADING_005	BOOK_01	STRAT_03	2024-05-11	63348.06	-265419.85	1402091.00	318321.28
d72634df-6700-46b4-aa0f-18125d87179d	ACC_001	CC_EMEA_INDEX_ARB_010	BOOK_10	STRAT_02	2024-06-26	68679.91	-432928.76	-555369.91	211940.37
9edd856d-c2e6-468f-8072-3d124c70f66c	ACC_009	CC_AMER_CASH_NY_003	BOOK_02	STRAT_03	2024-12-13	96756.63	347761.76	-1121416.79	-235960.17
91b6de8a-f975-4acb-94ce-335400dac2e7	ACC_009	CC_AMER_PROG_TRADING_005	BOOK_03	STRAT_01	2024-05-17	-27588.12	-334992.88	1842996.24	977599.34
84fce39c-52e6-4484-86d8-aded4b8f46dd	ACC_003	CC_APAC_ALGO_G1_013	BOOK_08	STRAT_04	2024-12-27	91797.05	-242601.71	645763.60	-1116080.81
f782789f-02c6-47b0-a1f9-e70ab8ff6e8b	ACC_001	CC_APAC_ALGO_G1_013	BOOK_05	STRAT_02	2024-07-29	-90655.23	279448.56	1020592.04	-678834.64
4f9547cc-2f12-4b30-8c31-06eb0e5f39cc	ACC_008	CC_AMER_CASH_NY_003	BOOK_07	STRAT_03	2024-12-12	28625.83	349022.93	-1767505.96	479848.70
77d76eb9-7c0a-464c-a7ef-ad9cdb42a96a	ACC_009	CC_AMER_PROG_TRADING_007	BOOK_01	STRAT_02	2024-01-19	24094.80	55361.23	1331792.12	-1356756.29
ec46fcbc-286a-4fb3-9bb1-695ae50309ba	ACC_005	CC_EMEA_INDEX_ARB_009	BOOK_09	STRAT_02	2024-08-06	70853.66	-300829.04	946219.94	-1247144.68
6d85b239-c5f0-4b6a-bd4d-7f55bb2720d6	ACC_002	CC_EMEA_INDEX_ARB_008	BOOK_10	STRAT_04	2024-06-13	87234.44	369259.46	-1022245.36	1356517.23
4eb59672-a4af-4ff6-9694-42ea2565f905	ACC_001	CC_AMER_PROG_TRADING_005	BOOK_03	STRAT_03	2024-10-27	90965.79	377585.59	578581.12	-1773684.35
1f0ea3da-cc58-40d2-a549-e7498485fd32	ACC_003	CC_EMEA_INDEX_ARB_010	BOOK_03	STRAT_03	2024-10-08	-80979.18	-312911.90	-1112994.61	-1728829.36
3c406bd1-8d98-4610-ad67-3877f65f7a96	ACC_008	CC_APAC_ALGO_G1_012	BOOK_10	STRAT_05	2024-10-08	51621.99	-242088.02	-1920057.58	1263191.32
83c51e4c-6755-4c70-81d8-e41fae0e3fad	ACC_005	CC_AMER_PROG_TRADING_005	BOOK_10	STRAT_01	2024-11-26	83894.36	147591.21	549373.84	-1149008.46
9a107778-4bc7-41e6-a50f-55e9c206d443	ACC_001	CC_AMER_PROG_TRADING_005	BOOK_10	STRAT_05	2024-03-13	-71334.94	343066.40	-814073.25	-1738728.25
ea55daf1-a6bf-4b6e-a5dc-d1d4feb0cd2f	ACC_008	CC_APAC_ALGO_G1_011	BOOK_07	STRAT_04	2024-07-22	-96701.29	-44028.60	-1081012.65	634344.16
b904f48a-94ad-4a31-885f-b8e976b422fa	ACC_009	CC_EMEA_INDEX_ARB_010	BOOK_06	STRAT_03	2024-10-25	48744.79	232125.34	-256222.69	-439804.73
eb1333fd-d379-4705-8981-9912089677d5	ACC_004	CC_EMEA_INDEX_ARB_008	BOOK_06	STRAT_03	2024-05-06	-49107.61	73699.01	-1544600.63	-1309021.03
2678adbf-1954-4eba-9f0f-2646188b5e41	ACC_009	CC_AMER_CASH_NY_003	BOOK_06	STRAT_05	2024-12-05	35970.49	-68126.60	-534101.01	1605759.95
bca9e19c-d780-4510-9657-e6133581bb02	ACC_004	CC_AMER_CASH_NY_003	BOOK_10	STRAT_04	2024-07-25	35821.79	-22217.88	811702.74	-1397431.93
7f33eaa1-1385-4c12-a5fb-4a3d0c3b08ec	ACC_008	CC_APAC_ALGO_G1_011	BOOK_08	STRAT_01	2024-08-12	7789.60	-303043.08	773364.56	1637005.31
21c3cf13-72c9-4413-bb3f-5b73b15ba03a	ACC_002	CC_AMER_PROG_TRADING_006	BOOK_03	STRAT_01	2024-01-05	35302.28	115329.71	895850.19	-1169216.29
5a6510e7-d6ec-4882-8af8-a1314e7d86ea	ACC_008	CC_AMER_CASH_NY_003	BOOK_02	STRAT_01	2024-10-19	39397.64	-162890.34	-1460611.52	1357246.49
2633431a-f4ba-422e-9543-769637c6e578	ACC_005	CC_AMER_PROG_TRADING_006	BOOK_10	STRAT_02	2024-07-14	-12483.84	-401299.70	-1287027.93	-203778.13
920750c7-288a-4f54-9ee8-2abda5e67ae8	ACC_007	CC_AMER_PROG_TRADING_005	BOOK_01	STRAT_04	2024-10-02	33251.52	-127373.33	-1989394.04	-1300528.69
0b950789-34be-4727-b8f2-46964b78a1e1	ACC_004	CC_AMER_CASH_NY_003	BOOK_09	STRAT_04	2024-10-21	-961.80	54853.07	111673.34	-1591900.96
3c9ade7e-f56c-402b-af35-205c7d7b8c59	ACC_003	CC_AMER_PROG_TRADING_006	BOOK_04	STRAT_02	2024-01-27	19348.32	41461.92	-1148941.77	413582.15
609d9053-bfcf-4bec-8c4e-8da7f226fbb2	ACC_005	CC_AMER_PROG_TRADING_007	BOOK_08	STRAT_04	2024-08-11	29147.53	-417079.40	510734.21	918753.51
c7e3d663-373e-4fa0-b5ff-aa53f3fad367	ACC_007	CC_AMER_PROG_TRADING_006	BOOK_07	STRAT_04	2024-09-03	-14904.46	-449486.14	-678975.30	-166268.91
272de4ed-2a07-4e39-9765-e401b6b537e2	ACC_002	CC_AMER_CASH_NY_002	BOOK_04	STRAT_04	2024-01-26	-65926.10	132814.87	1385601.30	1182338.21
9187512c-95f7-41c0-b1d5-2874a9227f12	ACC_005	CC_APAC_ALGO_G1_013	BOOK_05	STRAT_03	2024-06-30	-94058.51	-347930.35	-1274453.63	585784.29
d55046e7-1977-413b-9b2b-c9c1c90946a8	ACC_002	CC_APAC_ALGO_G1_013	BOOK_03	STRAT_04	2024-02-10	75671.58	-137213.97	428103.50	1328950.84
fd9b32cd-1e86-42c3-a20b-b1f95e740f50	ACC_001	CC_EMEA_INDEX_ARB_009	BOOK_10	STRAT_04	2024-10-16	40816.60	-204676.54	613763.21	1447386.24
f8b5420d-f672-4104-9864-31d274b02f1c	ACC_010	CC_EMEA_INDEX_ARB_008	BOOK_03	STRAT_03	2024-11-01	40676.05	-443026.55	-1294759.02	1616953.30
6a707569-5698-4ac8-9ad9-e2a36ca20062	ACC_005	CC_EMEA_INDEX_ARB_010	BOOK_09	STRAT_05	2024-10-03	-26232.25	347398.89	-243492.31	-498540.10
5259ed0d-354c-46c9-8fef-1a861f4e40a2	ACC_004	CC_EMEA_INDEX_ARB_009	BOOK_10	STRAT_04	2024-06-06	3155.01	110659.93	970220.88	-218520.79
04b0dcd8-c206-454d-b69f-fd71b7dce51f	ACC_008	CC_APAC_ALGO_G1_013	BOOK_10	STRAT_01	2024-04-08	13763.51	223373.43	663009.16	284651.08
88ff0b06-40b8-488b-94ec-df508394fb48	ACC_008	CC_APAC_ALGO_G1_013	BOOK_02	STRAT_01	2024-09-29	-81271.86	68849.93	-830539.62	414281.47
dc77a347-081d-45ac-81e2-fca6050ff4b2	ACC_007	CC_APAC_ALGO_G1_011	BOOK_05	STRAT_04	2024-09-23	-95389.68	-453808.16	1887319.57	206999.13
06195df6-ed79-4a28-a43f-f1890f6e0e53	ACC_002	CC_EMEA_INDEX_ARB_008	BOOK_01	STRAT_01	2024-08-25	17705.33	312295.35	-598174.69	-967873.96
f1ba2796-997c-49b8-89b1-3b022c0902db	ACC_005	CC_APAC_ALGO_G1_013	BOOK_09	STRAT_02	2024-03-24	-1888.33	-46829.54	-321201.85	-1271423.20
f3bda790-cd50-44c6-9c31-5a1dfdef565b	ACC_006	CC_AMER_CASH_NY_003	BOOK_02	STRAT_04	2024-04-05	-96236.54	-379644.18	1265420.31	464278.12
55e5b6cf-2a39-4f12-a4db-3fa962e22ff4	ACC_005	CC_APAC_ALGO_G1_012	BOOK_04	STRAT_03	2024-04-25	29477.03	-146913.80	1683444.83	-1561757.50
c6a2719e-e757-4c63-9cfa-0c2c14230cc1	ACC_008	CC_AMER_PROG_TRADING_006	BOOK_04	STRAT_01	2024-12-20	-79024.61	-477426.26	1486222.99	-833315.50
72db43eb-f8f6-4f63-8fe3-94338267936e	ACC_007	CC_APAC_ALGO_G1_011	BOOK_07	STRAT_03	2024-08-23	22100.49	24747.00	-1109556.66	1385153.95
ff48b932-7c7e-46d9-8bce-fb7a787166df	ACC_003	CC_AMER_CASH_NY_003	BOOK_05	STRAT_05	2024-05-09	10150.51	-316939.77	281772.77	941588.65
948bffd2-ba8b-44d6-9575-256a47364086	ACC_003	CC_EMEA_INDEX_ARB_009	BOOK_10	STRAT_05	2024-12-18	-98870.57	-484588.79	-1798842.15	-284641.77
183d8c01-7e85-475b-bed5-c29907bc8c94	ACC_001	CC_AMER_PROG_TRADING_005	BOOK_08	STRAT_02	2024-08-11	97015.18	-78503.24	-416863.34	3858.77
d9cb17f6-5e67-465c-bb2c-8b235487f1cd	ACC_010	CC_AMER_PROG_TRADING_007	BOOK_10	STRAT_01	2024-09-30	1483.48	168722.81	-889434.76	1505360.46
13a1e9a6-172f-45b3-a0b7-6724f2f8648b	ACC_007	CC_AMER_CASH_NY_002	BOOK_05	STRAT_03	2024-08-24	-457.36	-175495.05	-1316198.47	1578711.27
0c4f8ef2-ca8c-4599-a43c-795c10ba7136	ACC_006	CC_AMER_PROG_TRADING_007	BOOK_04	STRAT_04	2024-08-17	-23551.54	308576.55	1584410.82	-1506569.51
9e3663a9-7ae4-4d6b-839a-01e702efce14	ACC_003	CC_AMER_PROG_TRADING_005	BOOK_02	STRAT_05	2024-02-07	-17248.32	91025.05	-588236.68	426716.26
c4eefdd8-4449-445c-9977-7fb1b1356f6b	ACC_001	CC_AMER_PROG_TRADING_005	BOOK_06	STRAT_03	2024-08-27	58085.46	353589.93	1711340.20	1445604.10
cac4d12a-c58d-4c8e-9026-1bf41145c12d	ACC_009	CC_AMER_CASH_NY_002	BOOK_10	STRAT_03	2024-02-22	3229.79	46968.74	628703.13	1506464.04
0ca4f7e2-ea6e-4644-b720-10f98ad6990c	ACC_001	CC_APAC_ALGO_G1_013	BOOK_09	STRAT_04	2024-01-18	-31347.81	-390719.77	-1532949.36	191347.42
3b3e129c-a0ec-4b85-b651-15449f6898ce	ACC_010	CC_AMER_PROG_TRADING_005	BOOK_01	STRAT_03	2024-03-24	40078.91	422387.72	1052174.36	-342563.31
36512450-dabe-403d-bde8-c95595f366b1	ACC_006	CC_AMER_PROG_TRADING_007	BOOK_04	STRAT_05	2024-08-09	78818.85	143261.28	-231684.32	-806933.45
0ed7d5c5-d56f-439c-89fe-0910dc269dcc	ACC_010	CC_AMER_PROG_TRADING_005	BOOK_03	STRAT_04	2024-09-24	78758.20	-199332.06	1172940.62	1282598.50
946a8de7-c535-48ba-884e-18c01f7acedb	ACC_010	CC_AMER_CASH_NY_003	BOOK_02	STRAT_01	2024-02-17	22860.88	290243.13	2836.17	411047.72
59c424da-8664-4e1a-be2b-3596a5bcefd6	ACC_007	CC_EMEA_INDEX_ARB_010	BOOK_01	STRAT_01	2024-07-06	55862.02	263805.95	201214.32	-1597615.21
ae5a484b-c1ff-470e-b9bb-77d1a5eaeb72	ACC_002	CC_EMEA_INDEX_ARB_010	BOOK_03	STRAT_04	2024-12-16	-66098.15	481136.01	-943275.16	-630886.49
448a2afe-368d-4675-bf29-81858a483ca1	ACC_002	CC_AMER_PROG_TRADING_007	BOOK_10	STRAT_05	2024-03-31	811.35	183776.13	-408851.25	319021.76
275f3e7f-8468-4f15-a351-5aba59391c29	ACC_008	CC_APAC_ALGO_G1_013	BOOK_02	STRAT_03	2024-01-18	-68582.45	-419196.21	411592.61	-593519.61
179e0758-c5eb-43e0-9603-456a18ecb757	ACC_003	CC_AMER_CASH_NY_004	BOOK_05	STRAT_03	2024-05-08	60294.36	-73701.45	674008.73	987218.74
a7b760e6-bb29-4141-9f10-0a556e381f90	ACC_005	CC_AMER_CASH_NY_004	BOOK_03	STRAT_02	2024-11-15	-64334.94	-253533.03	-1839086.30	-826823.42
2099f703-c9bb-4022-b6ae-8639d17678a3	ACC_005	CC_AMER_CASH_NY_002	BOOK_05	STRAT_04	2024-10-27	-32711.63	310708.01	-730687.34	-387414.09
9e7684d6-cec8-4b84-96e1-a52e581a6c82	ACC_009	CC_APAC_ALGO_G1_011	BOOK_10	STRAT_01	2024-06-19	-12104.32	-499432.10	1731013.03	783553.24
83b8496c-23a4-46ff-ba6e-383d08ccebc8	ACC_007	CC_APAC_ALGO_G1_012	BOOK_09	STRAT_05	2024-02-07	95624.80	-90536.46	-1989008.39	109006.76
ca708b44-6d6b-4ee7-bee1-cb70bc2803de	ACC_001	CC_AMER_CASH_NY_003	BOOK_10	STRAT_02	2024-11-29	1113.53	145224.13	-799122.68	-1536840.15
6e304769-16cf-44be-a415-2e99a942eb78	ACC_002	CC_AMER_CASH_NY_001	BOOK_08	STRAT_05	2024-05-08	92086.83	62394.49	-1811044.27	-133727.62
d3b48801-988b-46aa-b185-030d66dafabc	ACC_007	CC_AMER_CASH_NY_003	BOOK_02	STRAT_05	2024-02-24	94261.93	-460430.44	-1606496.82	-1297580.17
00afe4bd-fd17-43bb-9ef6-f6a9bad3aee6	ACC_004	CC_AMER_CASH_NY_004	BOOK_07	STRAT_01	2024-05-01	-61331.74	-263156.24	330978.15	-808082.72
da8abf14-e754-446b-a48d-af37409a0126	ACC_004	CC_AMER_CASH_NY_001	BOOK_02	STRAT_05	2024-12-09	-70519.13	64719.48	1849812.85	89417.91
df585a8a-b16e-4df6-a700-da278fb36c8f	ACC_003	CC_APAC_ALGO_G1_012	BOOK_09	STRAT_01	2024-06-20	-20094.46	-189063.60	850935.14	-1709982.25
ba2cb877-8fd7-41f8-a6f7-72160ef726e1	ACC_006	CC_APAC_ALGO_G1_013	BOOK_05	STRAT_02	2024-06-22	-27.73	-64126.16	-988743.78	-1152251.33
af5ba6f8-dd2f-4239-91e5-e2b9a38fa306	ACC_006	CC_AMER_PROG_TRADING_005	BOOK_04	STRAT_02	2024-01-10	3437.03	-399334.37	-1277042.93	1291493.38
33c3b9fb-613f-49cf-898d-f6beb2258dff	ACC_008	CC_APAC_ALGO_G1_011	BOOK_01	STRAT_01	2024-01-11	-1744.34	428724.86	982022.36	-914484.21
5af661ae-4ac6-489a-99a1-4c725d0364c8	ACC_001	CC_APAC_ALGO_G1_011	BOOK_10	STRAT_02	2024-12-19	-23064.03	113265.72	202950.05	254671.22
2ce5d61e-d9a4-439e-b4c5-995da5a24bae	ACC_002	CC_EMEA_INDEX_ARB_010	BOOK_09	STRAT_01	2024-09-05	32575.27	-332823.77	483389.70	-1066368.47
eb04baf6-659f-4419-b9eb-cd164e669ec3	ACC_007	CC_AMER_CASH_NY_001	BOOK_06	STRAT_03	2024-11-01	51034.61	431048.05	-1981973.08	-1602464.10
6b9cf52c-57f2-4964-9b86-ab60000840fb	ACC_003	CC_APAC_ALGO_G1_011	BOOK_05	STRAT_01	2024-11-25	29285.24	-144328.65	1787056.08	826151.33
b6aed0e9-f076-4574-bf1b-0610a8a0e5f5	ACC_001	CC_AMER_CASH_NY_004	BOOK_09	STRAT_04	2024-10-21	-20617.23	161920.98	1900859.46	600589.38
6390e549-25ab-474d-be75-7a5e068f5864	ACC_003	CC_AMER_CASH_NY_001	BOOK_10	STRAT_01	2024-01-07	-23302.95	-77693.04	-1138179.35	-150957.38
c13a924f-9e75-4471-892e-c8ae9e79d884	ACC_001	CC_AMER_CASH_NY_002	BOOK_01	STRAT_05	2024-05-24	31188.55	439572.73	899391.85	-237352.92
def57beb-3e4f-46c6-854e-48907652b51f	ACC_010	CC_APAC_ALGO_G1_013	BOOK_05	STRAT_01	2024-05-17	-38433.89	-446165.67	-1696606.19	-1067097.42
82e95c54-f6cb-4e62-9df6-90d6048abce2	ACC_001	CC_EMEA_INDEX_ARB_008	BOOK_04	STRAT_01	2024-02-09	-243.03	-24699.01	773021.07	409728.04
2fe47540-8b8e-42d8-9f07-a182ede29ec9	ACC_007	CC_APAC_ALGO_G1_011	BOOK_06	STRAT_05	2024-08-13	46486.49	-341182.85	-1443850.37	-203662.08
d42ad1cb-8931-4d48-80d7-03139221c2b7	ACC_004	CC_EMEA_INDEX_ARB_008	BOOK_05	STRAT_02	2024-01-10	-52099.24	-422876.87	1964057.58	972195.84
7fea0208-8c77-46d5-b137-3f98fae23910	ACC_002	CC_EMEA_INDEX_ARB_009	BOOK_01	STRAT_04	2024-09-28	-81447.05	447433.58	-15149.51	1222866.02
c6c8f657-af75-4546-b6f0-13daaba0ae24	ACC_007	CC_AMER_CASH_NY_002	BOOK_07	STRAT_02	2024-02-13	-72210.98	-106849.19	1501651.38	-445911.67
00c2e653-3de6-48e5-8675-ef15ce915d1b	ACC_004	CC_AMER_CASH_NY_002	BOOK_09	STRAT_02	2024-03-18	56619.81	423093.66	-516875.17	-1577113.72
4e0b0071-a12c-4a80-908e-e8a716789ad4	ACC_006	CC_APAC_ALGO_G1_011	BOOK_08	STRAT_03	2024-04-05	-75855.01	-432272.02	270284.07	-494973.18
a9967779-26a6-4526-b530-1e5c0ee1803a	ACC_005	CC_AMER_CASH_NY_002	BOOK_03	STRAT_01	2024-05-21	58727.59	-180191.82	1708511.76	95595.10
478d7d0b-c738-4af4-9b7b-4580dec5c515	ACC_001	CC_AMER_CASH_NY_001	BOOK_05	STRAT_01	2024-08-10	89935.66	-240710.76	-263385.32	-1394433.39
6d5f7d17-1ed1-4a61-8c4c-1a9981dbdc8b	ACC_005	CC_EMEA_INDEX_ARB_008	BOOK_09	STRAT_04	2024-08-30	-21362.17	238135.11	294044.19	-41838.07
22840e35-7a3c-4d87-91ab-890a2bb48daa	ACC_007	CC_APAC_ALGO_G1_011	BOOK_03	STRAT_03	2024-02-11	95218.51	-220390.10	-1375466.54	-58509.22
1d5967a8-e937-4157-9b54-611e50437130	ACC_008	CC_APAC_ALGO_G1_012	BOOK_01	STRAT_03	2024-01-30	-25784.31	385652.60	-543773.58	520439.36
bb7d6c81-0981-4624-9cdf-098535aa390b	ACC_005	CC_AMER_CASH_NY_004	BOOK_06	STRAT_02	2024-12-27	-39772.69	139563.57	-1638772.89	-608837.67
e1dbf751-aef8-474d-bd29-82684f5dddea	ACC_002	CC_APAC_ALGO_G1_011	BOOK_07	STRAT_05	2024-07-04	-16816.51	237950.47	-929111.14	1675074.80
1e28803f-5fda-4dcc-948d-53182fe8f1bb	ACC_002	CC_APAC_ALGO_G1_011	BOOK_06	STRAT_03	2024-09-17	35097.97	244602.12	403724.12	905195.92
39993556-9ede-4e7b-af5a-7eae4798b635	ACC_003	CC_AMER_PROG_TRADING_007	BOOK_01	STRAT_02	2024-04-24	65931.66	-413732.89	-422145.37	-1631944.60
c391af81-0ed3-4ce7-bee1-728c9333642a	ACC_009	CC_AMER_CASH_NY_004	BOOK_03	STRAT_02	2024-07-09	74578.56	403605.77	1400224.75	657495.20
0ca34113-2f7b-4ef6-883c-9ebd8964d040	ACC_002	CC_AMER_PROG_TRADING_005	BOOK_08	STRAT_04	2024-04-18	-48301.98	400370.33	-1096295.55	-677447.52
ce23c573-f4cc-4143-a75f-8931c0a624e2	ACC_005	CC_AMER_CASH_NY_004	BOOK_08	STRAT_02	2024-06-11	-92915.84	62539.83	-995951.31	-1402799.28
5b070d2b-3230-4357-b288-4090c2960fa0	ACC_006	CC_AMER_PROG_TRADING_005	BOOK_07	STRAT_01	2024-10-29	34453.55	-224428.31	432206.21	1274752.27
9127afd0-c1c2-48d1-abc3-77ec847d04e0	ACC_009	CC_AMER_CASH_NY_003	BOOK_09	STRAT_04	2024-02-21	55735.48	270297.54	-1427464.20	777807.28
6be8a5f9-e701-4f7f-806e-c595f77614e9	ACC_003	CC_AMER_CASH_NY_002	BOOK_07	STRAT_01	2024-08-26	-67642.85	-380715.25	-597670.07	-485476.20
b1c27957-4902-4305-8675-f39029c061bd	ACC_006	CC_EMEA_INDEX_ARB_009	BOOK_04	STRAT_05	2024-07-16	-3519.43	385008.19	-1910475.97	-263747.99
226c4591-658f-475a-8f65-cd49cad3c18b	ACC_004	CC_APAC_ALGO_G1_011	BOOK_05	STRAT_01	2024-09-12	12814.60	-411744.76	1813938.76	190736.13
cb889d5c-ccb9-4dbe-9c07-6614afeafd93	ACC_005	CC_EMEA_INDEX_ARB_010	BOOK_07	STRAT_02	2024-07-27	-12607.13	245856.96	379782.87	1782536.31
a8e1bb1f-dbcd-4f47-9df3-72ca25c5c652	ACC_007	CC_AMER_PROG_TRADING_005	BOOK_02	STRAT_02	2024-07-18	83170.48	-36550.59	-71643.10	-1562938.66
b2df896e-cb17-4082-a8cf-a5035cd59703	ACC_003	CC_AMER_PROG_TRADING_007	BOOK_06	STRAT_05	2024-04-20	-84108.94	258241.02	124805.75	-953307.32
badae79c-fb50-492c-a3a7-8d8514150f2f	ACC_005	CC_AMER_CASH_NY_004	BOOK_09	STRAT_01	2024-12-21	64723.18	-218366.93	-1581690.52	1254215.17
476fa894-f273-400b-8214-7444102b4b64	ACC_001	CC_EMEA_INDEX_ARB_010	BOOK_07	STRAT_01	2024-07-01	84543.11	-20142.46	-1075493.88	-996002.38
9335c4a7-1288-4787-949c-a47af3ba83ff	ACC_005	CC_APAC_ALGO_G1_011	BOOK_09	STRAT_01	2024-08-28	-11211.30	241039.86	-583546.98	912687.46
91f97dcc-2142-4f33-af6a-4fa04f3585af	ACC_003	CC_EMEA_INDEX_ARB_010	BOOK_06	STRAT_05	2024-04-13	52258.82	-374417.28	1355199.33	62761.80
72d584e3-8e40-47db-8d7a-3c5b6517c33a	ACC_007	CC_APAC_ALGO_G1_013	BOOK_04	STRAT_02	2024-11-15	-13307.94	272557.14	-1979132.21	-1024296.62
04eda09a-01c3-45a8-ba73-f1dacdfa2ff8	ACC_001	CC_AMER_PROG_TRADING_007	BOOK_05	STRAT_05	2024-05-07	41382.77	-334261.75	892365.31	-286318.16
254563c4-acf2-4ec2-b4e6-d1bdcd0408b6	ACC_008	CC_AMER_PROG_TRADING_007	BOOK_01	STRAT_05	2024-12-12	31379.67	482733.36	725131.85	-710988.76
13234db4-e963-4101-a289-ba30f265c8ac	ACC_001	CC_AMER_CASH_NY_004	BOOK_04	STRAT_02	2024-08-04	-56962.02	287217.85	-700671.32	-434706.58
84d927e3-9108-44e7-afb1-e5736788a2e2	ACC_007	CC_APAC_ALGO_G1_011	BOOK_09	STRAT_03	2024-02-10	25262.76	1376.17	-782582.94	-792430.52
fc1e53b2-5e34-40f8-a73a-359dfcd311b4	ACC_001	CC_AMER_CASH_NY_004	BOOK_04	STRAT_03	2024-05-17	-46477.05	495879.06	-419244.28	587888.51
f099ba92-ec1c-4669-bded-1cbfd7421e80	ACC_001	CC_AMER_CASH_NY_004	BOOK_07	STRAT_03	2024-12-03	73262.66	-156416.31	939780.18	-251343.82
b6f61e39-5b27-48e9-9f93-0ba3d3b7a37e	ACC_003	CC_APAC_ALGO_G1_012	BOOK_02	STRAT_05	2024-08-10	-43301.18	-334014.15	197403.06	-1016105.52
585b047d-9620-45aa-8167-d57eb9655757	ACC_003	CC_AMER_PROG_TRADING_005	BOOK_03	STRAT_05	2024-01-05	89826.90	166412.74	1664542.37	-1089349.65
ec2a37a2-dc76-47a9-af8c-a3e53880e3e9	ACC_010	CC_APAC_ALGO_G1_011	BOOK_05	STRAT_02	2024-07-30	-23098.87	94391.95	1358760.88	347108.93
8f2f8d39-ba20-4a1f-b13f-38e806868fea	ACC_007	CC_APAC_ALGO_G1_011	BOOK_02	STRAT_05	2024-03-08	-69367.59	-324630.13	1880142.41	-1685489.41
66151655-a1b0-41b1-88df-a3758317f01e	ACC_003	CC_AMER_PROG_TRADING_005	BOOK_03	STRAT_01	2024-06-11	74909.05	-313654.99	1685268.92	-703290.32
705d773c-9bbe-44cb-a18d-1ab71c5af8a5	ACC_004	CC_AMER_PROG_TRADING_007	BOOK_04	STRAT_02	2024-09-29	82129.57	308749.12	-1780457.03	-431255.38
ad6acff9-7a5a-42a3-8a52-6de6c392f9e1	ACC_001	CC_AMER_CASH_NY_002	BOOK_05	STRAT_02	2024-06-14	-27958.25	210545.47	-232892.97	1172978.09
3fe836de-e8fe-42f1-b151-4e5806cf955d	ACC_010	CC_EMEA_INDEX_ARB_009	BOOK_02	STRAT_02	2024-02-26	20789.14	-235880.19	-1295021.10	-145003.22
320eac2d-d27c-4baa-a3a4-64093de45777	ACC_006	CC_APAC_ALGO_G1_012	BOOK_02	STRAT_03	2024-12-05	10834.87	311100.27	1747402.07	1607338.51
fde84d6d-f17c-4e0a-afbb-19b8b35cc4bb	ACC_004	CC_AMER_PROG_TRADING_006	BOOK_09	STRAT_01	2024-03-06	-4898.45	-368882.71	-1057969.07	-870286.12
e41689f1-5f53-49b4-b0f5-c2d425aec6fc	ACC_005	CC_APAC_ALGO_G1_013	BOOK_10	STRAT_01	2024-08-09	97634.44	-452515.56	-998495.68	-570309.04
d63ceb2f-5742-42f1-a237-7d733096b791	ACC_004	CC_AMER_PROG_TRADING_005	BOOK_01	STRAT_03	2024-11-04	-68086.58	-440529.69	1844545.20	-1798374.97
045b1d2a-3ec7-4ee7-9d56-60345cf275ac	ACC_006	CC_APAC_ALGO_G1_011	BOOK_10	STRAT_05	2024-08-12	-42877.53	-6511.92	-240065.53	289481.47
bbd94caf-67a1-46f9-9945-3dd47c5cd229	ACC_008	CC_AMER_CASH_NY_004	BOOK_02	STRAT_02	2024-01-18	-94820.91	359858.52	-1783798.95	735522.90
7ae75868-a6ee-4075-b906-d5b2ff04ad83	ACC_010	CC_APAC_ALGO_G1_011	BOOK_04	STRAT_01	2024-05-03	35224.22	85425.31	602811.19	1383433.49
30536850-0e70-4106-afa5-d6c329cf0e1d	ACC_003	CC_AMER_CASH_NY_003	BOOK_01	STRAT_02	2024-05-13	58372.05	-466782.41	1289821.87	-920644.91
8feef8e0-7d9d-4be2-a9bb-4c328b7707fe	ACC_009	CC_AMER_CASH_NY_004	BOOK_04	STRAT_01	2024-12-19	5220.88	472681.41	255900.38	-1547839.68
c383bc7b-dade-4f2f-a292-be6008a112e0	ACC_006	CC_AMER_CASH_NY_002	BOOK_02	STRAT_01	2024-02-03	-10152.20	301517.57	1604800.96	-793046.67
1bb01d36-9042-4c0a-8b98-5a883d2f5476	ACC_001	CC_AMER_CASH_NY_003	BOOK_08	STRAT_03	2024-12-17	-24013.17	298585.36	374392.91	-1503840.31
684c7f68-c10f-444d-9a64-303f99269806	ACC_003	CC_EMEA_INDEX_ARB_010	BOOK_01	STRAT_03	2024-09-04	-28968.60	-33858.70	-1684475.52	233796.23
8f9b9bba-a184-4eaf-9569-640d185271f9	ACC_010	CC_EMEA_INDEX_ARB_008	BOOK_10	STRAT_04	2024-08-08	-97949.71	-123756.43	1056621.02	-1207326.95
74365ed6-070d-45d5-9761-5e3475dbea39	ACC_007	CC_AMER_PROG_TRADING_007	BOOK_07	STRAT_05	2024-01-25	78799.56	-327623.15	1508172.49	-494897.51
4e53489a-a55e-4693-8d60-8b39fa9bc636	ACC_002	CC_APAC_ALGO_G1_011	BOOK_10	STRAT_02	2024-07-18	24474.05	351929.16	1069436.76	153331.53
4a9f2a94-aab4-45a3-ae28-21626d670c91	ACC_006	CC_EMEA_INDEX_ARB_009	BOOK_06	STRAT_04	2024-07-08	-16132.64	-22141.38	-651866.64	-141517.41
4fc83051-3ac0-477b-ad85-61fd21544f9c	ACC_002	CC_APAC_ALGO_G1_011	BOOK_08	STRAT_03	2024-08-29	-10436.21	307554.29	-1096514.09	1742500.01
076b939a-deb3-4e05-a875-324ed426d8c8	ACC_003	CC_AMER_CASH_NY_003	BOOK_06	STRAT_01	2024-04-06	8127.14	307673.10	-682135.90	1225128.74
e915e1e1-6429-49ce-a029-80c4c1c6b526	ACC_001	CC_AMER_PROG_TRADING_007	BOOK_06	STRAT_05	2024-03-30	7031.55	202375.18	-1191278.32	467303.57
45d2a40d-14cf-4a4f-baea-a792d90640e1	ACC_004	CC_APAC_ALGO_G1_012	BOOK_06	STRAT_05	2024-02-18	-98723.00	424279.63	1796038.85	-668352.02
3e0063b2-cf2c-45ae-8eef-a0465f1684e4	ACC_003	CC_AMER_PROG_TRADING_006	BOOK_09	STRAT_05	2024-01-07	78750.48	61373.86	-1671060.32	1589633.37
e783299b-1e39-43e7-94a2-3a57817f2756	ACC_008	CC_EMEA_INDEX_ARB_010	BOOK_02	STRAT_04	2024-09-27	24609.32	330875.57	721861.39	-1748799.31
e43f8cd2-3165-4f51-b980-8afb09d78e13	ACC_010	CC_AMER_CASH_NY_002	BOOK_08	STRAT_05	2024-10-02	-30324.82	487878.43	-834729.23	-1364920.13
e427c59c-ca26-49fa-8267-24c8fa1ef73f	ACC_001	CC_APAC_ALGO_G1_012	BOOK_07	STRAT_01	2024-07-23	-5674.14	212453.22	221977.92	145860.47
3e0ea309-ae2d-413b-bd1b-71565c355009	ACC_006	CC_APAC_ALGO_G1_011	BOOK_05	STRAT_02	2024-03-03	-30717.45	364438.83	-706925.58	-876951.33
0434f5c0-e933-4ef1-9836-529a39267ef9	ACC_006	CC_EMEA_INDEX_ARB_010	BOOK_07	STRAT_03	2024-09-26	-89020.65	200244.35	10453.19	-1504392.41
254d81d9-9a58-46c7-9faf-598292bcc89b	ACC_010	CC_EMEA_INDEX_ARB_008	BOOK_07	STRAT_03	2024-07-15	-47702.69	-325071.98	-537762.08	-416195.70
2528c935-be58-4d05-9164-01c0d8685074	ACC_010	CC_AMER_PROG_TRADING_007	BOOK_06	STRAT_01	2024-06-02	47220.37	-261331.15	79918.40	-1331974.04
f6fb528b-c6af-4ada-814a-77eaa0061c26	ACC_008	CC_EMEA_INDEX_ARB_008	BOOK_01	STRAT_02	2024-08-17	-10636.07	-71080.44	-66431.19	796286.04
d3949595-951b-46ed-880e-bb322fad4e49	ACC_007	CC_AMER_PROG_TRADING_006	BOOK_05	STRAT_03	2024-07-29	-35240.90	345133.47	1708964.62	-157965.78
6789fffe-a6f2-4f4c-9aae-38017606aac1	ACC_005	CC_EMEA_INDEX_ARB_009	BOOK_06	STRAT_04	2024-03-21	72695.10	135318.49	-524128.08	-418674.37
d71c4ebc-df7d-41ce-893d-d0baab1344c6	ACC_007	CC_AMER_CASH_NY_001	BOOK_07	STRAT_02	2024-10-22	72542.91	469063.41	-1229207.14	-1510164.83
d21e7bd7-2204-4822-af01-9c3925b4a297	ACC_008	CC_AMER_PROG_TRADING_006	BOOK_09	STRAT_04	2024-07-04	56605.21	-415140.82	508212.45	-510932.83
1f713b9c-ca71-4761-8ce2-bf7f8c8c9f11	ACC_009	CC_AMER_CASH_NY_001	BOOK_05	STRAT_02	2024-07-28	66307.35	-94515.43	-1925074.55	-1329712.93
af4c10c9-4253-4ece-966f-be10ef968dec	ACC_007	CC_EMEA_INDEX_ARB_009	BOOK_06	STRAT_01	2024-08-10	-69199.98	-406345.45	-1507569.36	-471533.70
f16a9cbf-0fd2-43c7-b231-c4dafd8cb352	ACC_008	CC_EMEA_INDEX_ARB_010	BOOK_02	STRAT_02	2024-03-09	-25780.50	-387883.09	83377.22	-700805.55
fbd37a18-4035-4e3f-98bf-6b0c2a63d265	ACC_003	CC_AMER_CASH_NY_004	BOOK_05	STRAT_05	2024-05-11	16888.46	448594.26	645614.32	-491524.14
8aff4202-466a-4c98-a007-00092b7c9338	ACC_008	CC_APAC_ALGO_G1_011	BOOK_05	STRAT_02	2024-10-30	16424.41	290361.87	1152962.51	1060281.42
409f35b2-1695-4272-8f2c-3b7991ae2960	ACC_005	CC_AMER_CASH_NY_001	BOOK_06	STRAT_03	2024-09-21	8559.47	-11555.90	811869.87	-1525366.43
1d211402-4aea-42a2-9a97-1b1ffa60f91e	ACC_002	CC_AMER_CASH_NY_003	BOOK_06	STRAT_05	2024-06-08	79534.28	451511.84	1175200.60	1358380.47
975de309-2427-42e5-b858-9d444990608f	ACC_004	CC_APAC_ALGO_G1_012	BOOK_06	STRAT_02	2024-07-09	24157.78	153430.41	1214978.89	-1321995.67
2ec9328b-9066-49e1-b946-353e14d6ef89	ACC_002	CC_AMER_PROG_TRADING_005	BOOK_03	STRAT_02	2024-12-21	78823.85	292198.90	-1978100.98	-1253247.01
f615929d-a648-445d-b6aa-382c0ace244d	ACC_003	CC_APAC_ALGO_G1_013	BOOK_10	STRAT_02	2024-07-20	-79201.04	-470559.28	1605326.19	1375286.06
04085089-8dd6-40f5-8e09-408adccce615	ACC_003	CC_APAC_ALGO_G1_013	BOOK_02	STRAT_05	2024-08-13	-22134.97	-303863.75	-1038984.01	-981349.82
5f2300e1-3872-48fc-ae78-615f51fa0bff	ACC_004	CC_EMEA_INDEX_ARB_008	BOOK_10	STRAT_02	2024-10-23	-326.02	368229.22	1873157.88	-1103965.75
73986daa-41a5-4e14-bbce-d1f53fd175b1	ACC_002	CC_AMER_CASH_NY_004	BOOK_01	STRAT_05	2024-08-12	-25552.65	-342292.72	-1391055.80	-980642.29
17153a52-0d73-433b-b12b-7688f895a84a	ACC_005	CC_AMER_CASH_NY_002	BOOK_03	STRAT_02	2024-03-16	75345.17	-69726.50	-35310.42	1624722.44
3f571eb4-5991-4ea6-b227-2f115186d2be	ACC_007	CC_APAC_ALGO_G1_013	BOOK_02	STRAT_01	2024-07-28	22329.63	-252868.16	-322433.72	-882777.10
6ad2878d-1890-4074-9316-72e4a8dc97fb	ACC_005	CC_AMER_CASH_NY_003	BOOK_10	STRAT_05	2024-10-12	73182.23	465434.53	1795436.30	-1110817.15
6fc61aef-ea85-45a3-8af1-9b8ae2ae4dd1	ACC_005	CC_APAC_ALGO_G1_012	BOOK_04	STRAT_01	2024-05-10	-87202.73	208288.81	745323.75	-1053777.73
e3e2e679-7aa7-4100-b100-ac8606650735	ACC_006	CC_EMEA_INDEX_ARB_009	BOOK_04	STRAT_04	2024-04-25	46965.94	-93917.97	645844.85	375937.77
76ff6b25-50c0-44d4-81c1-a3606ce30d92	ACC_007	CC_AMER_PROG_TRADING_006	BOOK_05	STRAT_03	2024-06-29	-83816.62	-72640.29	714240.04	1010713.88
ff45f158-6e54-4cf9-b670-3e0ebadfa2d9	ACC_003	CC_EMEA_INDEX_ARB_008	BOOK_06	STRAT_01	2024-11-09	-15105.36	-57509.41	-1689393.48	-424182.53
5fdbacde-f22f-418f-9861-efd1ed5452ad	ACC_002	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_03	2024-01-25	-87272.97	-225806.30	-1400576.13	-500437.37
9ed5fabf-ee29-47cb-8984-b55c9d874e34	ACC_001	CC_AMER_CASH_NY_001	BOOK_10	STRAT_02	2024-01-10	36262.39	-267595.18	1177940.55	313267.31
d5d24cf4-e185-47a1-9c58-fd2aa030eb53	ACC_009	CC_AMER_PROG_TRADING_007	BOOK_08	STRAT_05	2024-03-02	-24863.69	-140602.64	1602509.48	1558830.03
b5a9995e-8854-47bc-8de2-13f931780508	ACC_001	CC_AMER_PROG_TRADING_005	BOOK_07	STRAT_05	2024-04-14	-22046.29	298133.24	241993.64	675441.56
b1a5f92c-e88a-4449-888d-26ef1ae34939	ACC_005	CC_EMEA_INDEX_ARB_010	BOOK_09	STRAT_05	2024-07-04	45033.66	407623.08	-1363415.33	275228.21
33bfa236-7cb6-4306-89d0-1e8b524d0027	ACC_009	CC_AMER_CASH_NY_003	BOOK_08	STRAT_04	2024-12-04	23793.27	-303025.30	1435496.83	-767052.97
1ddae9f2-ae96-4327-85f5-09701d177759	ACC_007	CC_EMEA_INDEX_ARB_008	BOOK_04	STRAT_05	2024-05-12	19688.16	264547.32	189197.26	-1788863.24
02c6b555-6c27-4732-8b70-0f678d6d0fd8	ACC_003	CC_APAC_ALGO_G1_012	BOOK_05	STRAT_02	2024-09-21	-83643.18	-27115.76	-599110.34	1169774.46
3908405f-2318-4642-af06-ac3865f22fb0	ACC_010	CC_APAC_ALGO_G1_013	BOOK_02	STRAT_05	2024-04-15	44340.91	-312429.93	-1482111.03	1697648.97
71831398-01a2-4fc0-85a5-dcdede34dbaf	ACC_003	CC_AMER_PROG_TRADING_006	BOOK_04	STRAT_05	2024-04-29	-31351.61	-50718.07	1518635.11	1564629.32
6e4f7b4a-91ab-4a59-90b1-685fabec41e0	ACC_003	CC_AMER_PROG_TRADING_006	BOOK_04	STRAT_04	2024-02-26	59272.14	-297127.95	262870.30	453705.17
7d6b161b-443c-4037-9413-1cfb727bc693	ACC_009	CC_AMER_CASH_NY_003	BOOK_06	STRAT_02	2024-11-11	96653.50	-342893.81	832238.68	-1217001.44
f14bc829-0ca5-4282-b0eb-95318a8a32b9	ACC_009	CC_AMER_CASH_NY_002	BOOK_01	STRAT_04	2024-12-19	7682.56	-187588.71	-1196436.33	-1471620.54
14ea7ef2-c651-4c3e-b3a7-b5583b8f46b8	ACC_004	CC_AMER_PROG_TRADING_007	BOOK_08	STRAT_01	2024-07-22	-56925.29	-277440.70	1690836.92	1128058.01
5eba48c8-258e-4304-850f-4eb82d427c2c	ACC_006	CC_AMER_CASH_NY_001	BOOK_04	STRAT_02	2024-04-18	14660.84	92352.44	-1307430.69	1026400.69
ac316926-cf84-4b44-bc4a-822c97855557	ACC_006	CC_AMER_CASH_NY_003	BOOK_08	STRAT_05	2024-08-05	-84980.28	-264280.82	1187831.77	385444.25
cc5eb710-e3d6-4d7e-92cd-139a257f350b	ACC_001	CC_AMER_CASH_NY_004	BOOK_08	STRAT_02	2024-08-15	99265.64	-414502.24	-480143.01	1698822.10
86d389b9-d823-4bb7-a535-9545f1f8fe79	ACC_006	CC_AMER_PROG_TRADING_007	BOOK_01	STRAT_01	2024-10-06	2337.02	-198354.23	457573.00	-734505.88
fdc19d54-9f14-4fe4-bfd3-0089a184177c	ACC_009	CC_AMER_CASH_NY_003	BOOK_05	STRAT_04	2024-08-12	18772.39	408021.34	-1573503.29	-1362869.81
979babaf-ef94-4208-b0b1-51f57c77a13c	ACC_002	CC_EMEA_INDEX_ARB_008	BOOK_05	STRAT_05	2024-10-20	67.00	-24959.39	1632379.43	-1077729.02
1238c0db-7f25-42e8-887c-6408511c926b	ACC_006	CC_AMER_PROG_TRADING_006	BOOK_01	STRAT_01	2024-11-13	-1143.34	311124.75	-541718.33	346982.49
7d758a3d-b6eb-4694-9af6-f3befb0be2d7	ACC_002	CC_APAC_ALGO_G1_013	BOOK_02	STRAT_05	2024-07-20	51844.07	280613.71	-504852.98	1151311.64
e8b02a0d-2e6a-4b08-a69f-a9dad53b13e0	ACC_004	CC_AMER_PROG_TRADING_005	BOOK_10	STRAT_05	2024-03-18	-79405.29	-128794.94	1345085.42	-920449.99
e2528aa3-8de0-4b71-b2f4-6970d6b80bc5	ACC_006	CC_AMER_CASH_NY_001	BOOK_03	STRAT_01	2024-04-28	-15366.40	-393433.44	-457738.65	1626219.99
66f50eff-52d0-406a-a1dd-e77eabd1604d	ACC_003	CC_APAC_ALGO_G1_012	BOOK_08	STRAT_04	2024-06-05	29318.94	-464590.68	1387380.65	-71899.20
8da274cb-6e90-4575-a2aa-dd072e4dfbe4	ACC_009	CC_EMEA_INDEX_ARB_009	BOOK_06	STRAT_02	2024-02-18	-74785.13	19316.45	500606.68	-721307.31
89c3f603-3332-4ccf-b163-89767b7d9336	ACC_003	CC_AMER_CASH_NY_004	BOOK_03	STRAT_02	2024-07-08	-80888.49	-91152.93	-1546668.31	1550210.67
4be19e84-5824-4d6a-85ee-97c3a0b8c355	ACC_005	CC_AMER_PROG_TRADING_007	BOOK_01	STRAT_01	2024-10-27	10752.12	-367107.18	-1888777.37	1646223.49
bb8ace04-dbe4-4451-97c7-eac59210bed3	ACC_001	CC_EMEA_INDEX_ARB_010	BOOK_02	STRAT_03	2024-04-22	75834.22	-472451.36	1539829.94	-276862.16
b85b15f3-d51b-482f-a4ed-22c53fb9c4e9	ACC_003	CC_APAC_ALGO_G1_012	BOOK_09	STRAT_05	2024-01-28	84511.73	-217064.46	1878311.02	1558208.82
a953d0f3-83d8-4e4a-8dd4-8e5f5eeaef66	ACC_006	CC_AMER_CASH_NY_002	BOOK_01	STRAT_05	2024-02-24	10069.98	-281423.60	1820927.21	-1471406.28
e25f4f38-2842-4a01-b5cc-9ff9cb8107ec	ACC_008	CC_EMEA_INDEX_ARB_008	BOOK_10	STRAT_04	2024-10-09	-32396.48	-178418.80	742008.49	402918.18
5ed0bee1-ea46-492d-998f-95b745171e37	ACC_004	CC_AMER_PROG_TRADING_007	BOOK_06	STRAT_01	2024-04-13	-27189.41	-352440.34	1502504.87	-395645.44
a91d1520-5a6e-4d0c-9b47-121f9f9da472	ACC_005	CC_APAC_ALGO_G1_012	BOOK_09	STRAT_03	2024-03-24	-29043.73	145319.61	-381715.30	-631665.61
09083c29-6d83-4419-8baa-b7a3fee8ba0b	ACC_007	CC_AMER_CASH_NY_001	BOOK_08	STRAT_02	2024-07-09	8408.78	121285.77	-722238.10	-1514328.04
e8c2ae31-474e-4b19-addb-6b4e9a7dcf7d	ACC_004	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_03	2024-09-01	-87529.30	-269709.59	-1731046.13	1148128.00
21ef604b-fe1e-4840-ad50-ca2343972792	ACC_005	CC_AMER_CASH_NY_002	BOOK_09	STRAT_04	2024-05-29	-2558.93	459373.25	275203.21	-719864.63
005177ef-41b9-4922-847d-d36545d35743	ACC_004	CC_AMER_CASH_NY_004	BOOK_05	STRAT_02	2024-05-25	18250.65	89472.83	-687634.13	1016831.79
abc0b57e-fe25-4f64-9753-5438775c3dcb	ACC_006	CC_AMER_CASH_NY_003	BOOK_06	STRAT_02	2024-11-16	3902.47	153807.21	1971074.88	1362370.77
842415a0-733c-49b6-89e9-bed2a4e93c3b	ACC_006	CC_AMER_PROG_TRADING_007	BOOK_09	STRAT_03	2024-12-22	-89747.43	-146142.09	-659023.89	1133731.43
ad6f7f39-8f94-465a-87c7-57149e896e9c	ACC_009	CC_EMEA_INDEX_ARB_009	BOOK_07	STRAT_02	2024-06-01	31648.35	-176779.44	1498353.44	-1603175.87
4ba59144-ebfd-44d5-8bde-532061124905	ACC_009	CC_APAC_ALGO_G1_012	BOOK_04	STRAT_04	2024-01-19	-69332.18	-172093.21	-1130972.14	-1571960.28
7f6709c6-bd35-4a94-9733-43c4009ff558	ACC_010	CC_AMER_PROG_TRADING_006	BOOK_08	STRAT_02	2024-06-05	56019.94	-165788.74	-1336793.04	1004276.50
0d54e92a-c8e7-49fe-ad18-c22c38e9a9f7	ACC_004	CC_AMER_PROG_TRADING_007	BOOK_10	STRAT_02	2024-07-13	-55369.40	-407925.30	-1049842.46	-392727.39
c3e20127-5335-4dc5-945d-e3afefb4bc1f	ACC_007	CC_APAC_ALGO_G1_013	BOOK_04	STRAT_04	2024-09-22	31756.02	-224520.27	49289.42	1599076.55
364db3ac-595a-48bf-bc1a-6ea5add7a4de	ACC_001	CC_AMER_CASH_NY_002	BOOK_09	STRAT_01	2024-08-24	39040.80	-238802.93	-785206.37	-492583.20
24758a7c-af9d-41be-8252-cc93c745e577	ACC_005	CC_AMER_CASH_NY_004	BOOK_05	STRAT_01	2024-12-22	-78989.89	163265.30	-1651453.89	-1419260.79
df699463-cea2-4d58-9024-a1c981202bb4	ACC_007	CC_AMER_PROG_TRADING_006	BOOK_03	STRAT_02	2024-07-21	-51495.24	424624.62	1784516.87	-1795289.06
f7e1de69-05f9-41f9-8845-4e74bc71ff0d	ACC_005	CC_AMER_PROG_TRADING_006	BOOK_07	STRAT_02	2024-11-27	15508.13	378909.46	-1419254.66	528333.43
e040cde3-213d-49d4-ac34-0edba1ca300f	ACC_003	CC_AMER_CASH_NY_004	BOOK_02	STRAT_04	2024-01-28	-35001.49	-327155.61	-147575.62	1553384.57
678b1b60-4ebb-4181-84eb-9912a5b08c01	ACC_002	CC_AMER_CASH_NY_003	BOOK_01	STRAT_05	2024-07-16	82890.38	-208004.31	-1732914.06	-809041.05
2fe285c2-cbc5-4c20-8852-53b8b952aaf6	ACC_010	CC_EMEA_INDEX_ARB_009	BOOK_04	STRAT_01	2024-08-22	-85808.97	124148.09	998531.61	619578.58
8ba95dc9-1e2c-4e4f-863c-23cf8375ca0f	ACC_007	CC_APAC_ALGO_G1_013	BOOK_09	STRAT_05	2024-04-27	-62281.83	-294765.56	-704698.72	478790.18
1db66fec-67aa-44ea-a5e3-9351d258da42	ACC_004	CC_AMER_PROG_TRADING_006	BOOK_05	STRAT_04	2024-04-07	16398.36	100775.40	-1266587.58	-58293.34
2c3931a2-9b74-4c64-8155-e803e22c0018	ACC_008	CC_AMER_CASH_NY_004	BOOK_02	STRAT_02	2024-02-02	18640.62	-10250.08	846727.91	-616634.56
989f44c0-8590-4e45-899a-7e2f9bc67555	ACC_009	CC_EMEA_INDEX_ARB_008	BOOK_01	STRAT_03	2024-09-30	29764.47	-398252.41	828763.06	-1502911.46
80191bff-7339-4406-8f84-426e80ae92e7	ACC_007	CC_APAC_ALGO_G1_012	BOOK_05	STRAT_05	2024-08-02	-30613.55	-499443.14	1622574.34	1429370.46
db1e3846-c522-4c89-8c31-5d2c6e89b1d6	ACC_006	CC_AMER_CASH_NY_003	BOOK_02	STRAT_01	2024-04-20	29128.41	77387.61	-1832411.98	-1236701.55
51720e42-eb13-4bd4-aa22-2b329311c1ea	ACC_007	CC_APAC_ALGO_G1_012	BOOK_04	STRAT_05	2024-11-05	52176.02	67736.53	1666314.92	536383.40
a55f7e59-fb06-40a3-91dd-ba19ccdaacbc	ACC_010	CC_AMER_CASH_NY_002	BOOK_01	STRAT_03	2024-06-04	74195.95	-156515.84	-1975236.81	1624696.34
53e706d6-1e6a-4faf-ba9e-5492b473f94c	ACC_009	CC_AMER_CASH_NY_002	BOOK_04	STRAT_02	2024-10-19	5703.66	235065.93	-744473.45	3970.41
4c5c7380-0a13-4078-a8fd-8883dcd4bc94	ACC_001	CC_AMER_PROG_TRADING_006	BOOK_10	STRAT_03	2024-07-01	-62376.69	-94978.03	1524834.63	-1697571.12
ed8020af-4251-4d3e-8c2b-b74e0d34cd73	ACC_007	CC_AMER_PROG_TRADING_007	BOOK_02	STRAT_01	2024-07-24	-41147.52	-231578.23	1381593.22	-1579156.15
914425fe-01f8-409c-b4c0-40892b0aca19	ACC_001	CC_APAC_ALGO_G1_012	BOOK_07	STRAT_04	2024-01-09	-25830.49	489671.10	378069.10	1214641.26
096ee9b3-35a2-41c9-b6e8-a26729ac8d02	ACC_008	CC_APAC_ALGO_G1_013	BOOK_08	STRAT_02	2024-02-13	-24872.11	-3653.18	-974486.67	-1453941.86
00966d26-d571-44ab-9272-55ce4fd41ee4	ACC_007	CC_APAC_ALGO_G1_011	BOOK_01	STRAT_04	2024-01-25	-54374.70	266884.29	-845453.05	-1329810.42
fc30f939-8dc1-4a9b-b24d-c26247b9dd70	ACC_004	CC_AMER_PROG_TRADING_005	BOOK_04	STRAT_04	2024-07-30	27958.84	2779.91	-318496.85	-471889.05
72c8178d-7f79-471a-8bf3-df8d2fe4f2b3	ACC_004	CC_AMER_PROG_TRADING_007	BOOK_09	STRAT_04	2024-07-10	60967.99	96733.50	566634.86	527171.96
a820bd68-8f2c-4aa1-922b-6ed81936028e	ACC_010	CC_EMEA_INDEX_ARB_008	BOOK_10	STRAT_04	2024-05-25	43832.07	7122.27	-1671521.14	1423907.97
75492d29-91fa-4101-8c47-907815984823	ACC_006	CC_AMER_PROG_TRADING_007	BOOK_08	STRAT_03	2024-05-02	-69820.60	-236387.97	-1920014.52	-443282.36
6f25c399-57a5-4bb6-ad3a-da7dc25004df	ACC_004	CC_AMER_PROG_TRADING_007	BOOK_08	STRAT_01	2024-07-12	2702.43	183198.33	1241816.58	1537047.88
c60a12d3-76a5-408d-bb85-1f9966643b84	ACC_007	CC_EMEA_INDEX_ARB_010	BOOK_02	STRAT_03	2024-06-15	23920.63	-207179.64	680590.05	-749257.92
4ed62b42-19ac-4690-ae45-f6ade422525f	ACC_007	CC_AMER_PROG_TRADING_007	BOOK_10	STRAT_01	2024-05-01	34995.14	102996.33	-1333372.59	-705157.16
b414a405-ffc5-48cf-921e-e439adbd2089	ACC_008	CC_AMER_CASH_NY_001	BOOK_10	STRAT_04	2024-03-14	32420.64	-307107.43	-1763631.49	1331349.78
5ef5be1d-8794-4b6b-aa5f-ed6645187f3b	ACC_004	CC_AMER_PROG_TRADING_006	BOOK_09	STRAT_04	2024-03-03	9111.18	-254003.25	1169626.58	-698757.21
b550675d-1de4-448a-90b2-fec0beb101e8	ACC_001	CC_AMER_CASH_NY_001	BOOK_02	STRAT_02	2024-07-17	-89090.02	369931.66	1810812.54	1486338.29
c24c4adb-f165-478a-99e9-bc26d6babcf2	ACC_002	CC_AMER_CASH_NY_002	BOOK_05	STRAT_03	2024-09-23	-66760.31	-140312.58	-394045.46	78786.19
678b23c8-c866-4b31-af65-bf2ab46cbde0	ACC_002	CC_AMER_CASH_NY_002	BOOK_09	STRAT_01	2024-06-10	-97970.49	393872.42	-291221.66	-24271.35
60ba2d4b-2921-40c5-a70b-aaa1de8ff436	ACC_002	CC_APAC_ALGO_G1_012	BOOK_01	STRAT_03	2024-07-17	10437.59	-122661.56	643351.37	100551.49
2eb03009-0bb2-4d2a-b419-a9e2844fc02e	ACC_001	CC_APAC_ALGO_G1_013	BOOK_07	STRAT_04	2024-04-11	-75493.64	260992.45	1716426.43	121212.98
56d028e6-9062-4a3c-86ff-e4a3c6e706c3	ACC_008	CC_EMEA_INDEX_ARB_009	BOOK_10	STRAT_04	2024-05-14	-12223.35	13287.24	1315103.37	-1481856.17
d53eef7c-b769-4fb4-bee7-bc3a2048594f	ACC_008	CC_APAC_ALGO_G1_011	BOOK_05	STRAT_05	2024-08-31	30417.65	-194891.86	-117004.28	709781.85
3461c821-17b5-4e07-8245-5592778dba98	ACC_008	CC_AMER_CASH_NY_001	BOOK_06	STRAT_05	2024-04-25	47152.68	-488272.96	1233225.45	1151732.03
4d9be2ab-b5d9-4505-97e8-5d0dd0f2ce85	ACC_010	CC_AMER_CASH_NY_002	BOOK_05	STRAT_01	2024-06-15	56517.92	249832.48	945603.77	-1678264.41
9779dadd-4865-49a2-9bd0-a756c7882817	ACC_002	CC_APAC_ALGO_G1_013	BOOK_07	STRAT_03	2024-04-17	-12769.53	-421682.39	-272642.71	518913.69
076fe877-54ba-4804-b0f5-b8b8c8173ab0	ACC_004	CC_AMER_PROG_TRADING_005	BOOK_07	STRAT_02	2024-04-07	-14937.24	-493183.32	-181633.24	-1565423.53
437da403-eda8-4827-964e-cffdff3ba2a9	ACC_004	CC_AMER_CASH_NY_004	BOOK_08	STRAT_01	2024-02-07	59269.45	-150635.43	-46393.41	162230.90
306b225c-3623-40f8-8369-9b3d7ba630cf	ACC_005	CC_APAC_ALGO_G1_011	BOOK_08	STRAT_03	2024-07-06	98779.09	134595.41	299263.60	-718687.62
e88cf806-d9f0-4f2a-8253-42ea0dc54b3d	ACC_002	CC_AMER_CASH_NY_002	BOOK_05	STRAT_05	2024-02-01	79079.70	-449761.41	-543420.60	824869.25
274db64c-0eef-440f-a09a-60e44877d3be	ACC_004	CC_AMER_CASH_NY_003	BOOK_10	STRAT_01	2024-09-09	-14585.46	297402.67	-473676.90	123671.23
4b5e5e88-d03c-402e-8fa4-c279a305f797	ACC_006	CC_AMER_CASH_NY_001	BOOK_05	STRAT_01	2024-06-11	-94200.35	128662.30	-1841796.04	-1540853.06
93c864da-2ab2-4b28-b5aa-ada0b7967d47	ACC_006	CC_AMER_PROG_TRADING_007	BOOK_09	STRAT_03	2024-03-22	31596.90	421537.60	849756.68	1035447.22
0e9a3f6a-0b4f-4ea1-8918-41b05ed88a94	ACC_010	CC_AMER_PROG_TRADING_007	BOOK_09	STRAT_03	2024-02-01	-976.09	170808.26	-133154.50	-97908.21
cedfab95-65b4-4d90-9bef-481bc5131882	ACC_003	CC_APAC_ALGO_G1_012	BOOK_03	STRAT_03	2024-09-01	18890.54	-279434.66	-739588.55	1422404.27
18a7a5a7-b4c5-4ec2-a880-33f1307b5d4e	ACC_009	CC_AMER_PROG_TRADING_005	BOOK_09	STRAT_01	2024-07-02	-65245.70	-390063.97	-1961286.03	1633003.39
e85875de-cac4-4079-8f62-a81bbaebbfff	ACC_009	CC_AMER_CASH_NY_002	BOOK_04	STRAT_04	2024-04-19	-34374.35	465581.68	641441.16	391262.13
5fed0e76-7b2f-4421-83e7-eabea13dac2f	ACC_003	CC_APAC_ALGO_G1_013	BOOK_10	STRAT_04	2024-07-30	70151.08	-454153.11	-1963880.96	-1166375.33
d4912c8f-6060-4fee-868f-31c6d33d7d9e	ACC_007	CC_AMER_PROG_TRADING_007	BOOK_08	STRAT_04	2024-12-14	-11248.43	176996.49	545894.66	512445.63
fa14351b-eec8-442d-a8b2-4248a264b91f	ACC_008	CC_EMEA_INDEX_ARB_010	BOOK_06	STRAT_02	2024-01-20	-22787.51	67381.70	1116895.77	953729.20
31e0156c-cfeb-4e35-80a5-9a755d3f8147	ACC_005	CC_EMEA_INDEX_ARB_010	BOOK_06	STRAT_03	2024-05-24	58753.63	-12814.37	-1528992.49	5589.32
259dad9f-97e0-4f1a-b7d3-e14a7ebe3764	ACC_006	CC_EMEA_INDEX_ARB_008	BOOK_08	STRAT_04	2024-10-04	-52039.01	426711.95	1102563.89	-1357781.68
e32a36cc-ee5a-4976-af26-7694d213459a	ACC_008	CC_AMER_PROG_TRADING_006	BOOK_08	STRAT_01	2024-04-22	97102.74	-342325.77	20692.25	-1204528.34
12e4cf59-1ed8-4685-95d0-6f59e258082c	ACC_001	CC_AMER_CASH_NY_004	BOOK_03	STRAT_02	2024-03-02	97611.62	420693.31	-926305.80	-459313.53
ad815f18-d505-4aa6-b2d8-3b7b079a6919	ACC_008	CC_EMEA_INDEX_ARB_010	BOOK_03	STRAT_01	2024-04-09	-98544.42	-39052.20	1009958.13	648088.82
1dd43d2a-c826-420f-a01b-8aedb96fd683	ACC_007	CC_AMER_PROG_TRADING_005	BOOK_09	STRAT_03	2024-06-02	87358.33	324786.32	-355861.26	-1188482.95
5b862879-fb02-493b-ad01-2e637fac2d0c	ACC_004	CC_EMEA_INDEX_ARB_009	BOOK_01	STRAT_01	2024-10-07	-98961.22	-429002.94	1012923.62	338940.60
d766634b-a01a-4804-b4d6-626d5a1ac1cf	ACC_006	CC_APAC_ALGO_G1_012	BOOK_06	STRAT_05	2024-11-16	1884.94	-329220.73	1239322.55	1496972.70
89d8daa3-8598-419d-bab8-5a22caf2a525	ACC_007	CC_AMER_PROG_TRADING_007	BOOK_09	STRAT_03	2024-09-15	-59704.32	432326.38	-1709357.99	-1766259.05
8f1308f9-be13-4080-8a5c-244647b6d50c	ACC_005	CC_AMER_PROG_TRADING_006	BOOK_07	STRAT_01	2024-03-20	-83205.85	133522.69	-935385.17	1231025.82
512670c7-e31c-4040-9648-2cdb6faa799f	ACC_007	CC_AMER_CASH_NY_002	BOOK_05	STRAT_01	2024-06-17	-32552.44	94615.96	-1414059.92	-615743.70
3cc5dda5-b7bf-45ff-a601-e5c62e8d1b8f	ACC_005	CC_EMEA_INDEX_ARB_008	BOOK_06	STRAT_03	2024-10-08	-35342.11	107406.68	528437.54	-151178.80
298151b7-e164-4050-8371-278dd0c80a37	ACC_006	CC_AMER_CASH_NY_001	BOOK_06	STRAT_03	2024-06-01	-468.64	-334292.04	-1134219.03	501422.81
14493c18-78c5-482d-a9d3-e702d8d4000e	ACC_003	CC_AMER_PROG_TRADING_005	BOOK_08	STRAT_02	2024-01-20	-41855.43	-165399.97	1737613.65	335499.71
0534dc1f-b12f-4545-bc33-3548b533e57e	ACC_006	CC_AMER_CASH_NY_001	BOOK_02	STRAT_03	2024-10-24	96516.73	302645.16	1423979.74	835604.98
35d61b9b-1c47-41be-bfa0-41a490972513	ACC_004	CC_APAC_ALGO_G1_012	BOOK_07	STRAT_03	2024-03-12	69200.53	-403783.89	-807679.56	467042.29
abfba03d-7a11-4a0d-b353-7ad166525a1f	ACC_009	CC_APAC_ALGO_G1_013	BOOK_06	STRAT_05	2024-08-26	-43368.32	456600.13	-1771272.87	-61390.01
51fde7c9-5a65-437f-b1f5-1b82c565b688	ACC_005	CC_AMER_CASH_NY_002	BOOK_10	STRAT_03	2024-12-29	66086.24	490228.41	1407413.03	-581550.17
a07d0e31-6595-47a1-8e70-00b75cda735e	ACC_005	CC_APAC_ALGO_G1_012	BOOK_08	STRAT_02	2024-09-30	-20452.78	-448382.56	1365300.57	-1559057.22
bd2f901d-507a-4e92-aef1-cad7e40f8467	ACC_003	CC_AMER_CASH_NY_002	BOOK_10	STRAT_01	2024-01-12	45361.33	175409.15	-1183003.68	-559082.68
96d03ce2-dc7b-4553-8072-24ada55120c4	ACC_009	CC_AMER_CASH_NY_004	BOOK_07	STRAT_05	2024-06-24	36880.31	-155043.66	-1199390.37	-1213236.41
c85e519f-6702-42b9-bfb8-9ac5d7e548a5	ACC_001	CC_EMEA_INDEX_ARB_010	BOOK_02	STRAT_01	2024-10-13	35597.32	279749.92	106342.23	-386820.16
5ef16284-8b5b-42f9-a460-6a957588cd16	ACC_009	CC_EMEA_INDEX_ARB_008	BOOK_08	STRAT_04	2024-02-25	11288.21	212166.95	1486644.86	-421530.14
39df4695-7a08-4560-9971-8b0852f1d5a9	ACC_009	CC_AMER_PROG_TRADING_006	BOOK_04	STRAT_01	2024-01-27	15171.58	28537.13	-634905.00	1261099.98
f2a901bb-f144-47ec-8a39-6c79926f4ad8	ACC_008	CC_AMER_CASH_NY_001	BOOK_04	STRAT_03	2024-12-07	33255.22	-203922.05	1733613.18	-1736005.01
828e25e4-2637-4d55-81d4-ff902b732f81	ACC_001	CC_AMER_CASH_NY_003	BOOK_06	STRAT_05	2024-12-04	5125.42	-94438.79	1686429.63	1747183.51
eaeab4eb-4757-4562-a11a-5caa8747a62b	ACC_007	CC_APAC_ALGO_G1_012	BOOK_08	STRAT_04	2024-03-20	-77570.54	304901.28	1835517.41	-1649722.98
0ac58bd9-8b4c-4ad5-ae98-a22008628ab0	ACC_008	CC_AMER_CASH_NY_002	BOOK_10	STRAT_01	2024-03-27	45724.26	484879.04	1135321.31	1201284.59
0bbea8ef-ea92-486a-bce4-23b19b181460	ACC_007	CC_AMER_PROG_TRADING_007	BOOK_10	STRAT_03	2024-11-10	-72369.33	-348113.75	442293.54	315360.63
7708b4ca-e837-425b-8d62-8213b3db01d1	ACC_002	CC_APAC_ALGO_G1_012	BOOK_03	STRAT_05	2024-01-10	-59577.89	-298103.31	1673979.24	-1768594.69
1c4d7d64-5e48-4cbc-bf9e-6bed0038e6d7	ACC_009	CC_EMEA_INDEX_ARB_008	BOOK_08	STRAT_03	2024-07-22	-38296.17	475328.24	1765056.86	1766688.95
f82746a3-f973-458f-a4b8-1d5ed4cf8e99	ACC_006	CC_AMER_PROG_TRADING_006	BOOK_06	STRAT_05	2024-11-21	99166.20	-244959.49	1696281.07	-1621080.67
e3d48fa2-d7cd-44eb-8d5d-03626464fb5e	ACC_008	CC_AMER_PROG_TRADING_007	BOOK_05	STRAT_03	2024-06-26	54414.53	80581.07	-1710186.63	980908.45
7bab0ebe-34cd-459b-8717-67d40cb7252b	ACC_003	CC_AMER_PROG_TRADING_007	BOOK_08	STRAT_03	2024-05-18	69812.59	-85364.43	-238579.37	-886083.61
727bc590-6a34-4f9c-815a-73cc3d8ba73f	ACC_008	CC_AMER_PROG_TRADING_007	BOOK_02	STRAT_02	2024-09-30	-72423.35	279855.57	-281833.29	-1688485.63
00dfc2af-e868-4430-af42-3b0007604dda	ACC_005	CC_EMEA_INDEX_ARB_009	BOOK_03	STRAT_01	2024-09-04	-81671.18	-120718.69	299202.53	-287360.33
a8cc4609-a920-4215-aa50-eb2fdfcb973a	ACC_006	CC_APAC_ALGO_G1_013	BOOK_06	STRAT_01	2024-09-29	21083.24	-494744.41	285897.34	-387862.14
dc014905-8510-4eec-8b9f-bc2d7686eb57	ACC_006	CC_AMER_CASH_NY_003	BOOK_09	STRAT_05	2024-07-30	62455.84	93017.59	1074914.72	1038500.96
8bb8e878-386a-45d9-9270-bd2a5fb8ab14	ACC_004	CC_APAC_ALGO_G1_012	BOOK_01	STRAT_03	2024-10-24	-55754.86	-297953.08	508454.76	-675139.69
d7e154a5-1934-424a-9a0d-83e70fab1137	ACC_005	CC_AMER_PROG_TRADING_006	BOOK_02	STRAT_03	2024-01-30	-49182.38	274697.86	-639900.24	828492.88
6725befa-4c6c-47eb-8f32-6e9c5d51e8ed	ACC_003	CC_EMEA_INDEX_ARB_010	BOOK_02	STRAT_03	2024-04-14	82594.69	-172533.88	1607346.28	-571930.90
ad0cc9cd-7206-4986-8b91-57f9abe28507	ACC_007	CC_AMER_CASH_NY_002	BOOK_03	STRAT_01	2024-05-16	-53808.47	353914.22	-1206461.61	-10275.88
9a8f8cfe-9df4-4913-b9ef-edde0a65cb45	ACC_005	CC_EMEA_INDEX_ARB_009	BOOK_08	STRAT_03	2024-05-05	99422.67	-376826.35	-258552.70	-197654.67
c49a7e13-4a9e-4815-90c2-e09779cfeb60	ACC_004	CC_APAC_ALGO_G1_011	BOOK_06	STRAT_03	2024-05-16	13071.18	-79762.80	1449400.50	1408648.76
bf2cc883-c3ab-40fa-955b-5d6edb48d2bd	ACC_009	CC_EMEA_INDEX_ARB_008	BOOK_04	STRAT_05	2024-01-04	-6071.32	-76573.69	-490751.09	-228986.42
3b2096f5-e6e5-4c6a-afc2-130f45321d4f	ACC_010	CC_AMER_CASH_NY_004	BOOK_02	STRAT_01	2024-07-15	-63063.03	-5431.02	-1713867.61	297987.09
5229f4f5-f9dd-409c-b634-bde589fbf178	ACC_008	CC_AMER_CASH_NY_003	BOOK_10	STRAT_02	2024-12-28	33458.01	-322290.21	188914.37	1338657.56
4f154192-d010-4d51-b0fb-23cab83c7e01	ACC_010	CC_APAC_ALGO_G1_012	BOOK_04	STRAT_01	2024-01-15	6686.03	399475.97	-1277662.81	-263601.66
54f4ddc9-6f8f-4328-909d-a99e82c16e4a	ACC_007	CC_AMER_CASH_NY_004	BOOK_02	STRAT_03	2024-04-02	91113.18	318562.99	-1568746.39	-783814.42
35ce3e0c-ff14-48e6-b97d-943691c368c2	ACC_004	CC_AMER_CASH_NY_003	BOOK_05	STRAT_05	2024-07-19	76746.05	205166.40	-878093.96	579535.22
4e716eb9-2506-4db9-a5fa-138f40922a24	ACC_007	CC_APAC_ALGO_G1_011	BOOK_10	STRAT_04	2024-06-30	-52889.28	302817.37	-1179402.57	1580943.62
07ca3611-0895-4eac-9c43-02f6a8e79d59	ACC_003	CC_AMER_CASH_NY_003	BOOK_01	STRAT_01	2024-12-16	-48028.49	-280591.80	1490133.11	-1205889.78
72cab537-1236-41fa-a599-4d2de91bd9bc	ACC_006	CC_AMER_CASH_NY_001	BOOK_01	STRAT_04	2024-07-31	64744.95	-6632.80	-449917.74	-1082525.53
14045f97-2e9c-4860-8b42-0b1eff565b54	ACC_006	CC_APAC_ALGO_G1_012	BOOK_09	STRAT_05	2024-10-05	1747.60	-433668.82	858360.09	-1459276.34
2d255ae4-e7f3-473a-89d4-b61ce2040f56	ACC_003	CC_APAC_ALGO_G1_011	BOOK_03	STRAT_02	2024-08-10	-86033.01	473686.48	1323968.35	1090087.22
60fa6846-36d2-42d3-9836-db8633a8849a	ACC_005	CC_EMEA_INDEX_ARB_010	BOOK_10	STRAT_01	2024-12-19	-41028.74	229388.23	-1105333.18	1020193.59
2c89bda4-4d64-4339-89e8-f41963e8bb55	ACC_006	CC_AMER_PROG_TRADING_007	BOOK_03	STRAT_05	2024-07-15	76435.07	301012.66	-173359.78	-78522.71
1296ba13-8bb1-4d69-b583-96dc5a71ef86	ACC_004	CC_APAC_ALGO_G1_012	BOOK_02	STRAT_01	2024-01-18	58965.58	352985.04	646346.75	1562502.20
c442210a-4e15-4114-91c4-0d9781568740	ACC_004	CC_AMER_CASH_NY_001	BOOK_03	STRAT_03	2024-06-17	-56173.98	-475900.19	-768738.47	1077702.77
bfd23094-3c63-49f7-8fc1-0779b2de2fe0	ACC_008	CC_AMER_CASH_NY_001	BOOK_09	STRAT_05	2024-05-19	-90523.37	495152.80	-1405775.78	798086.26
44903b4b-1c7e-4e74-9c57-7d8816e31387	ACC_007	CC_APAC_ALGO_G1_011	BOOK_09	STRAT_04	2024-11-19	32014.30	327299.16	728308.02	-98633.02
007ff696-e98d-49d4-8253-a7de96fd4ce6	ACC_001	CC_APAC_ALGO_G1_013	BOOK_04	STRAT_05	2024-03-22	-96368.99	427598.80	368224.33	-1399745.48
c009db46-fb6d-42bd-bc89-40852698149e	ACC_006	CC_AMER_CASH_NY_003	BOOK_09	STRAT_03	2024-01-16	58421.95	-431934.15	1806708.34	947542.82
40c293a4-6023-4bc4-8846-ad522eed03e3	ACC_009	CC_EMEA_INDEX_ARB_010	BOOK_09	STRAT_02	2024-08-13	52338.43	-368.81	-737118.62	-1534435.63
fb081dfb-7895-41c7-9611-3761acd4f6d5	ACC_001	CC_AMER_CASH_NY_001	BOOK_07	STRAT_05	2024-10-08	-20997.33	63194.20	1137196.26	-1689760.14
f4cbd819-304b-45ab-82dd-f2850eb8367d	ACC_006	CC_EMEA_INDEX_ARB_010	BOOK_04	STRAT_02	2024-11-20	-91784.83	22279.21	925082.66	752378.34
67817b71-5160-40bf-9f93-6e605b9efa18	ACC_006	CC_AMER_PROG_TRADING_005	BOOK_04	STRAT_04	2024-02-18	3400.22	-184381.99	-1801888.68	1552995.82
a25edc1c-9a83-4264-a5be-23e6de1eae6b	ACC_006	CC_EMEA_INDEX_ARB_008	BOOK_01	STRAT_05	2024-07-03	62533.68	415091.89	1247335.39	216952.80
24aa4acb-1824-45e9-9d25-f15dd86a3671	ACC_006	CC_APAC_ALGO_G1_011	BOOK_01	STRAT_05	2024-10-23	71096.02	371576.01	-360960.18	-1544594.13
11aa07b0-9d0a-448b-98dc-065a605edb26	ACC_004	CC_AMER_CASH_NY_003	BOOK_08	STRAT_03	2024-06-15	3529.73	-187064.04	469296.87	-1179243.16
9736ede6-7343-4154-afae-bec34d31bc26	ACC_005	CC_AMER_PROG_TRADING_007	BOOK_10	STRAT_03	2024-04-01	43609.71	124129.83	309839.39	-1360384.23
376ba482-e466-40fd-8744-7e81b798b103	ACC_002	CC_AMER_CASH_NY_003	BOOK_03	STRAT_01	2024-06-19	18919.91	-424902.30	-41924.94	588914.90
2e4cc69e-2c17-45ff-8fa0-2a614b15cc19	ACC_001	CC_APAC_ALGO_G1_011	BOOK_05	STRAT_01	2024-09-27	-98357.04	379781.44	1109509.09	1688818.83
8826bc6e-0745-4284-8ae6-7304a52d5e96	ACC_002	CC_APAC_ALGO_G1_013	BOOK_05	STRAT_05	2024-06-01	-1308.76	-171846.37	-1056824.39	-1792548.38
da6d5f32-d514-4557-bbad-d8b7c52491ed	ACC_002	CC_AMER_PROG_TRADING_006	BOOK_01	STRAT_04	2024-10-04	-53346.29	-46703.53	-324351.50	456376.91
7223e5d0-7eb1-4691-9313-082f0d640a45	ACC_004	CC_AMER_CASH_NY_003	BOOK_05	STRAT_01	2024-07-26	-94692.05	-311609.83	-1585982.90	668874.47
7772cf6a-80de-40bf-ab77-5cdc2e89717e	ACC_007	CC_AMER_CASH_NY_003	BOOK_10	STRAT_05	2024-04-26	-75757.71	-38043.55	-1619125.55	454603.85
5c47954d-3966-4cf5-96f6-e2a0f533ddeb	ACC_002	CC_EMEA_INDEX_ARB_009	BOOK_08	STRAT_05	2024-10-21	-6732.54	282306.21	767237.52	-1683787.33
744af0e9-a266-43ad-8fb7-02938c3908a7	ACC_003	CC_AMER_PROG_TRADING_005	BOOK_01	STRAT_02	2024-12-04	-68396.84	-88087.89	1331345.26	1065064.78
9599c9cf-d0c9-44f8-863c-555719e6901c	ACC_001	CC_APAC_ALGO_G1_011	BOOK_07	STRAT_02	2024-08-14	96650.33	-220329.52	-1947221.97	1734890.09
30316e65-59db-4f5d-996a-da86ed846ce0	ACC_005	CC_AMER_CASH_NY_003	BOOK_10	STRAT_01	2024-01-01	63466.70	-145904.54	-172587.26	-183861.17
cd0f0247-d1e9-4dec-af08-88c4af0ffe2d	ACC_006	CC_AMER_CASH_NY_001	BOOK_01	STRAT_04	2024-09-26	-12132.37	220360.27	512724.76	-19607.03
a85e2dd1-262b-47c7-94c1-109bd7e40da0	ACC_008	CC_AMER_CASH_NY_003	BOOK_08	STRAT_04	2024-04-11	-62140.55	-274361.05	-1300461.17	491220.13
ae302bdf-00e3-4351-b86e-cc37e0958c86	ACC_003	CC_APAC_ALGO_G1_011	BOOK_05	STRAT_01	2024-01-06	-50089.78	280818.03	-249035.55	-1453897.90
3c8e2f1f-5a34-4c16-88bb-75124335de04	ACC_005	CC_APAC_ALGO_G1_012	BOOK_02	STRAT_04	2024-07-29	-13154.63	437038.16	-1525846.50	1262485.69
a62a8abd-2a73-44d2-b4f3-e3428587ae2b	ACC_003	CC_AMER_CASH_NY_003	BOOK_08	STRAT_02	2024-01-31	92538.83	-68100.99	-1289817.71	-1386762.62
9e890258-c46e-43c2-835f-5fd791f6496b	ACC_003	CC_AMER_CASH_NY_003	BOOK_05	STRAT_03	2024-04-13	30773.64	164188.21	192799.43	-1682215.49
1c754a2a-6e69-4800-b85e-ac61be7f77f2	ACC_004	CC_AMER_CASH_NY_004	BOOK_05	STRAT_04	2024-02-26	-948.07	-175130.36	286985.08	-1011116.37
30c54d64-3ad2-432f-b18c-c55a2f4dfaeb	ACC_005	CC_EMEA_INDEX_ARB_009	BOOK_04	STRAT_01	2024-03-20	76607.45	329416.93	797770.71	440791.09
110da0ea-3d6f-44e0-a472-84ff3963b60b	ACC_008	CC_AMER_CASH_NY_002	BOOK_09	STRAT_01	2024-02-21	-57531.59	-7892.10	1200945.08	-1527783.83
347dd852-1fc1-47d6-a62d-11e9fc47ab89	ACC_007	CC_AMER_PROG_TRADING_005	BOOK_09	STRAT_05	2024-03-18	3687.62	-87062.84	-888268.69	-1658393.32
cadf8856-1d15-4b88-8caf-e867b975b9a4	ACC_002	CC_AMER_CASH_NY_003	BOOK_06	STRAT_03	2024-02-06	40134.86	169343.61	-1284106.26	-1253199.56
18544237-5ce8-4bb4-92e7-3e28d5523caa	ACC_010	CC_APAC_ALGO_G1_013	BOOK_07	STRAT_04	2024-11-15	50805.24	-256517.34	1648154.96	-1125093.72
a7a976a8-84bf-4385-8972-c9672241192c	ACC_007	CC_EMEA_INDEX_ARB_008	BOOK_02	STRAT_05	2024-03-10	-58153.49	-27652.19	-394797.44	-1628039.84
348bdc2e-eca7-4f2a-8a9d-f3f6ce440a8e	ACC_004	CC_APAC_ALGO_G1_012	BOOK_06	STRAT_02	2024-12-07	59858.63	-340212.01	-1914263.91	-618576.00
46c6242b-5097-441e-9886-23693a028635	ACC_006	CC_EMEA_INDEX_ARB_008	BOOK_02	STRAT_05	2024-03-11	-2898.34	-452346.00	1865819.40	395365.71
bd89c115-313c-45c7-becb-0777c7ddcdc3	ACC_010	CC_EMEA_INDEX_ARB_010	BOOK_04	STRAT_01	2024-04-08	-14268.96	316771.97	-27613.45	1419986.14
c450f0b2-ef91-4c68-8e48-228bd417b4f2	ACC_008	CC_AMER_PROG_TRADING_006	BOOK_06	STRAT_05	2024-02-01	3906.65	-107337.46	1656240.51	1061019.44
79c2ce84-df8b-4e17-a04a-c8e8c8de4efe	ACC_008	CC_APAC_ALGO_G1_011	BOOK_02	STRAT_01	2024-07-18	68065.07	414336.36	-476558.51	899148.32
42dcb499-a195-4aaa-a907-3415d1634577	ACC_001	CC_EMEA_INDEX_ARB_010	BOOK_09	STRAT_03	2024-12-21	73293.46	486999.22	1406835.74	-425933.99
688ef121-70d5-401f-81e1-87ab5be50134	ACC_006	CC_EMEA_INDEX_ARB_009	BOOK_07	STRAT_04	2024-05-03	-99319.14	352245.08	1743780.16	-1425910.85
c58a6732-8518-48da-b9d0-d40122f6aa3a	ACC_006	CC_EMEA_INDEX_ARB_009	BOOK_09	STRAT_04	2024-03-23	77441.31	357977.89	355885.02	1681640.14
e964771b-714f-4868-bc04-b2cdbba9d9c8	ACC_004	CC_AMER_PROG_TRADING_005	BOOK_07	STRAT_03	2024-09-12	21633.79	12612.58	1866308.59	-367277.35
7f4e5b40-3ba6-4929-ac4a-a62aee6658ed	ACC_010	CC_AMER_CASH_NY_002	BOOK_03	STRAT_05	2024-05-30	35460.04	23118.98	612394.46	241737.38
11bd3c07-8cb7-45ba-8b7a-8eb1f1551c22	ACC_005	CC_AMER_CASH_NY_004	BOOK_02	STRAT_05	2024-01-07	-93178.60	-322222.77	-685811.14	122355.34
0c228c18-e1e0-42d9-abc7-10a81243469e	ACC_007	CC_AMER_PROG_TRADING_006	BOOK_08	STRAT_03	2024-05-13	-40079.24	48929.02	-1017716.66	-576666.84
496c7468-b17b-4dd4-8c33-e2ca63aa0f76	ACC_003	CC_EMEA_INDEX_ARB_008	BOOK_07	STRAT_02	2024-08-23	-30272.55	470624.15	1182661.07	-97378.90
78dee2ca-1ee3-489e-8a51-52f4b00ecae7	ACC_001	CC_AMER_CASH_NY_002	BOOK_03	STRAT_02	2024-07-25	-85157.90	-50374.30	110152.76	1432202.66
1d1f479a-65a4-4d76-9efb-fce0fb5a596f	ACC_006	CC_EMEA_INDEX_ARB_009	BOOK_02	STRAT_02	2024-09-25	-74678.24	242389.06	-65260.91	-184199.25
4906be11-3848-45e3-9f4c-4e5575f8bf6f	ACC_009	CC_AMER_PROG_TRADING_006	BOOK_05	STRAT_04	2024-05-13	-33362.98	52151.67	-946.63	72446.17
2038ae2a-5b12-49fc-869a-e14ac5cd3324	ACC_007	CC_APAC_ALGO_G1_011	BOOK_05	STRAT_02	2024-02-18	57405.46	380261.33	-1414567.21	-1625307.99
0b668195-7e4b-44d7-bc4e-5b18930035a1	ACC_003	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_03	2024-11-29	-97124.41	-374772.34	-171632.71	-176654.04
f36a33f7-003c-4cc4-8835-16464737a248	ACC_005	CC_AMER_PROG_TRADING_005	BOOK_08	STRAT_02	2024-04-06	19309.92	367902.64	-1897577.17	-1035494.26
49c38328-3c8e-4697-b690-925aecebe33c	ACC_006	CC_APAC_ALGO_G1_013	BOOK_07	STRAT_01	2024-11-21	-3460.61	-37601.05	-922049.38	753240.36
a41ace26-7c6d-4900-9a39-e4cf8570456c	ACC_005	CC_AMER_CASH_NY_002	BOOK_03	STRAT_03	2024-08-21	2193.31	-114892.95	850146.43	-1051150.07
b063a416-b34a-4d85-8f19-20ebe7be8202	ACC_003	CC_AMER_CASH_NY_001	BOOK_10	STRAT_02	2024-11-23	36102.66	-100123.61	816225.33	1192241.16
c546d5da-0faf-4e31-a4a2-3490d0a215d5	ACC_005	CC_AMER_CASH_NY_001	BOOK_09	STRAT_02	2024-04-29	-39609.94	-451594.61	-1247901.52	-124161.78
e197edb7-5c10-4167-9acd-31d7dd8a79e0	ACC_010	CC_AMER_PROG_TRADING_005	BOOK_01	STRAT_01	2024-05-05	-44504.82	-384792.81	-877221.70	-1656315.42
aab32b2f-e5a3-4b22-92dd-fb993a9c6875	ACC_009	CC_AMER_CASH_NY_003	BOOK_07	STRAT_02	2024-03-04	27230.73	361655.91	-849281.99	530222.75
35f494ca-53d0-417f-b00b-91c7b79eddda	ACC_008	CC_EMEA_INDEX_ARB_009	BOOK_08	STRAT_05	2024-12-29	34147.58	-104079.15	-794311.70	556572.94
13832769-567c-46b3-a57a-d2d35cbd75f5	ACC_001	CC_AMER_PROG_TRADING_007	BOOK_03	STRAT_02	2024-03-05	45579.42	-468780.79	-1697697.08	-1677430.75
256fdc60-2a32-40a2-81f6-48291cd9cd8a	ACC_001	CC_EMEA_INDEX_ARB_008	BOOK_09	STRAT_04	2024-04-11	-32358.71	-335303.56	1439074.73	965048.54
e570b7c4-7687-4f85-880d-9366c2b35acc	ACC_010	CC_AMER_CASH_NY_003	BOOK_01	STRAT_03	2024-01-04	87171.60	-476927.73	-1317676.39	986157.43
190bc80b-fe2e-4072-9c5b-a779fa6f5666	ACC_008	CC_AMER_PROG_TRADING_007	BOOK_05	STRAT_05	2024-03-17	-48440.15	-365951.81	-384017.06	1245578.74
a4139b8c-e5ae-4f1e-9b03-04bb8fc9de41	ACC_007	CC_AMER_PROG_TRADING_006	BOOK_02	STRAT_01	2024-05-19	62284.20	-177097.45	1606185.99	-77574.44
66082b56-4a90-4518-bbc8-f9548c2f808f	ACC_006	CC_EMEA_INDEX_ARB_010	BOOK_06	STRAT_05	2024-08-14	10718.17	-215667.60	-1945677.94	-496794.76
55ad092a-9a2c-48cf-b322-adf1c6431c51	ACC_001	CC_AMER_CASH_NY_002	BOOK_01	STRAT_05	2024-05-19	92006.27	139643.07	-1286633.15	268354.17
ad4f0e05-b9d9-446e-9545-8983d4fbf9a8	ACC_009	CC_APAC_ALGO_G1_012	BOOK_02	STRAT_04	2024-12-06	-74351.25	7239.83	868036.71	1546818.08
a32f68c7-04e7-4b7f-a558-4dbc9fecd5fd	ACC_005	CC_AMER_PROG_TRADING_005	BOOK_05	STRAT_03	2024-08-31	38052.66	92358.53	-1873790.65	-1259303.70
a57d8344-36dc-430f-b49b-10a03103dc5c	ACC_010	CC_EMEA_INDEX_ARB_010	BOOK_06	STRAT_05	2024-11-20	-61985.28	308048.79	-1752563.95	-812625.27
8fbcb161-dbed-4765-8714-a75da10bcfd7	ACC_001	CC_APAC_ALGO_G1_011	BOOK_10	STRAT_02	2024-02-23	26725.35	-414706.65	354094.52	-889864.81
2627786c-03ca-4f21-964a-cad866386a37	ACC_004	CC_AMER_PROG_TRADING_006	BOOK_03	STRAT_02	2024-08-08	-94828.64	-244638.05	-898023.49	686302.42
f92a6eaa-bd90-4f93-9c6a-199cf5463e4a	ACC_009	CC_AMER_PROG_TRADING_007	BOOK_09	STRAT_04	2024-09-13	46378.39	260709.38	1379825.84	1516488.28
fb9b009a-661c-4dd3-9932-f0e6d4824831	ACC_002	CC_EMEA_INDEX_ARB_009	BOOK_03	STRAT_01	2024-10-12	-61306.60	-58982.19	1559258.77	88543.59
f5494cdc-8306-4cd9-aa7a-93dc80328546	ACC_003	CC_AMER_CASH_NY_001	BOOK_03	STRAT_05	2024-05-04	84223.43	-236817.51	-1288861.34	-1399099.02
f5b0a62a-8820-4a66-80cf-6bd29204b69c	ACC_010	CC_APAC_ALGO_G1_013	BOOK_08	STRAT_01	2024-09-02	91197.06	275849.66	1616891.98	-1332713.09
d7cfce8d-ef7b-4886-aed2-239268b7dc6f	ACC_008	CC_EMEA_INDEX_ARB_008	BOOK_09	STRAT_05	2024-08-15	-50105.43	203385.68	-661199.72	8720.19
ae75cf18-aa9e-4b0d-a463-5acfd123615d	ACC_002	CC_AMER_CASH_NY_001	BOOK_02	STRAT_03	2024-10-03	25741.17	-267492.04	1919952.31	1396191.37
390696f2-0ad0-4dc2-bc95-cab2d1aec7f6	ACC_007	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_01	2024-01-11	-50375.48	-151360.33	-463798.64	-469601.03
21add2ea-472f-4384-877a-f573262dc282	ACC_004	CC_AMER_CASH_NY_002	BOOK_01	STRAT_01	2024-11-13	-6586.71	-287597.71	-1907548.77	-28006.79
7f9d1e21-a821-427e-af21-db5701dbc6e1	ACC_006	CC_APAC_ALGO_G1_012	BOOK_01	STRAT_03	2024-05-24	-76074.95	-140527.55	1471022.25	950985.15
8bbe5e20-0db5-4fd4-846e-7d93d594d737	ACC_002	CC_EMEA_INDEX_ARB_009	BOOK_02	STRAT_05	2024-05-03	75043.99	-312023.10	221218.03	-1128365.20
a4f71ef7-dc4d-45ef-ae64-8f26f91f8f18	ACC_007	CC_AMER_PROG_TRADING_007	BOOK_02	STRAT_01	2024-03-26	28869.36	56508.26	1938390.52	908432.79
7f6868b7-c8dc-4a74-a454-e687d9ef9e27	ACC_003	CC_APAC_ALGO_G1_012	BOOK_03	STRAT_03	2024-11-13	10241.60	493630.53	730738.17	1082774.18
b7d8473b-c206-4474-8daa-33b1c2a7c729	ACC_005	CC_APAC_ALGO_G1_011	BOOK_07	STRAT_04	2024-03-01	-13865.07	-146360.24	1029312.69	-918691.63
af795224-13c2-4d24-8434-1dd88eeedb74	ACC_008	CC_EMEA_INDEX_ARB_010	BOOK_02	STRAT_02	2024-01-30	-48189.65	-67123.38	-1309998.58	-1186354.25
fcc5a25e-d131-4888-a577-73f07877e90c	ACC_009	CC_EMEA_INDEX_ARB_008	BOOK_04	STRAT_03	2024-03-21	49993.57	48403.54	725.27	658605.64
46479fc1-179c-4751-a000-ac88bb0f453f	ACC_007	CC_APAC_ALGO_G1_012	BOOK_02	STRAT_02	2024-06-22	35607.96	5150.39	614786.57	1064416.94
849d42f0-8cdb-4bf6-9548-aa1def8d5a3f	ACC_009	CC_AMER_CASH_NY_003	BOOK_02	STRAT_04	2024-04-15	-66368.46	22395.97	1188544.11	-671640.28
eff935f7-f751-436c-9365-1a31cb6b593f	ACC_006	CC_AMER_CASH_NY_001	BOOK_02	STRAT_02	2024-03-22	-22755.39	-198630.14	452515.52	-68861.09
bc16666b-e69a-42e5-893f-0e174a84c43c	ACC_001	CC_APAC_ALGO_G1_011	BOOK_02	STRAT_04	2024-04-24	50811.94	-280863.73	-447502.11	-1118830.04
90d90ae8-b96d-446f-a842-be1ea5b06c87	ACC_003	CC_EMEA_INDEX_ARB_008	BOOK_05	STRAT_01	2024-06-04	56456.07	349928.86	-9827.60	-1158932.87
8faa8ab4-f3fd-42d2-a13a-279d180b8525	ACC_005	CC_AMER_CASH_NY_003	BOOK_03	STRAT_02	2024-07-18	28509.04	410226.99	652673.33	1474226.58
975036f1-69d1-4684-aa1f-f41f67e23654	ACC_008	CC_EMEA_INDEX_ARB_008	BOOK_10	STRAT_04	2024-06-19	69183.72	335798.95	1097946.14	325208.99
b9eb0437-8740-4426-9993-7dc10044e3dd	ACC_006	CC_EMEA_INDEX_ARB_010	BOOK_01	STRAT_04	2024-01-17	47479.19	-352155.50	-958035.72	-558831.59
4334d045-5fa9-4ef2-ab88-ba78abd13d74	ACC_001	CC_AMER_CASH_NY_001	BOOK_02	STRAT_03	2024-04-17	13206.29	450460.00	-969878.63	1062649.61
f8ba8f88-833a-46d0-becf-5df9682e521d	ACC_002	CC_EMEA_INDEX_ARB_010	BOOK_10	STRAT_04	2024-08-17	-79743.08	103857.64	-1897701.19	-382394.43
722ad464-f160-48b5-bb99-3783b1257378	ACC_002	CC_APAC_ALGO_G1_011	BOOK_02	STRAT_03	2024-09-25	30126.47	333849.82	1699191.36	1157199.02
d5a7f0a6-9afd-4862-be3f-6fbb63c3a989	ACC_003	CC_AMER_CASH_NY_002	BOOK_03	STRAT_05	2024-01-23	-78989.60	-235402.42	1056860.51	-277498.52
83578e2a-0aa0-4d37-bdd8-33c08cfc3e6e	ACC_007	CC_EMEA_INDEX_ARB_010	BOOK_06	STRAT_03	2024-08-05	-69485.46	334377.42	-937554.04	-1673079.96
b5103a28-3a82-4564-b2ac-43d08b73a6e4	ACC_002	CC_APAC_ALGO_G1_012	BOOK_09	STRAT_04	2024-07-19	97221.50	-30554.39	894357.77	-730968.66
c5b3e669-97ac-40e6-bf5c-a60a812f85d4	ACC_004	CC_AMER_PROG_TRADING_006	BOOK_01	STRAT_04	2024-03-15	85770.31	271374.90	-1127494.82	-1732329.63
f86350ff-51f3-46f2-b637-c63bee96f12e	ACC_009	CC_APAC_ALGO_G1_011	BOOK_03	STRAT_02	2024-01-27	-30387.07	430865.11	-883395.14	1543589.07
b37c1549-21cf-4032-a14f-8b41098af337	ACC_003	CC_APAC_ALGO_G1_011	BOOK_03	STRAT_03	2024-02-21	24643.79	-78568.67	719818.59	-396954.79
8293c4eb-5914-4e34-a0f5-83d46a857363	ACC_008	CC_AMER_CASH_NY_004	BOOK_01	STRAT_03	2024-06-23	-18306.09	383695.97	62238.43	905664.74
edcdeab6-4bb3-4ec1-8e6b-1ffbb5a800ae	ACC_006	CC_EMEA_INDEX_ARB_008	BOOK_03	STRAT_05	2024-02-04	-93584.68	136843.30	-1688516.89	1458664.10
a30a6376-0ebe-4d21-b7ea-a4a265f55279	ACC_002	CC_AMER_CASH_NY_003	BOOK_02	STRAT_04	2024-12-29	-74284.95	-49249.85	-1879878.94	778727.11
35ac5b6f-3cd2-44b2-bf41-bd7789426a82	ACC_002	CC_AMER_PROG_TRADING_005	BOOK_07	STRAT_03	2024-05-19	7083.95	-395418.30	1141566.93	-1161425.29
d5aa57b8-d1f9-4f9e-8fa3-0f93b1bff931	ACC_010	CC_AMER_PROG_TRADING_005	BOOK_05	STRAT_04	2024-03-12	-49103.92	-377408.84	387601.99	914741.37
dbe21d8f-44a8-467a-8f24-c65d7053c910	ACC_005	CC_APAC_ALGO_G1_012	BOOK_01	STRAT_04	2024-03-10	-84336.43	-168279.31	1349201.24	15396.91
3e590473-b8ba-4769-93d1-5af289c67975	ACC_006	CC_EMEA_INDEX_ARB_009	BOOK_07	STRAT_05	2024-08-16	-43530.58	438560.10	480405.96	-1037180.46
daa870be-7537-4b38-948a-5728fb786e8a	ACC_009	CC_EMEA_INDEX_ARB_008	BOOK_01	STRAT_02	2024-07-18	48399.44	413205.09	573044.81	742852.60
c3c5c5f7-7396-4ddf-899f-97647daa4c9a	ACC_001	CC_EMEA_INDEX_ARB_010	BOOK_05	STRAT_02	2024-10-11	-25665.77	-165143.68	1522123.75	59338.11
76ca264c-a17f-4f55-9c71-b02d164da896	ACC_001	CC_APAC_ALGO_G1_011	BOOK_02	STRAT_01	2024-03-01	57510.83	210315.07	992437.54	-1105480.35
bf562707-3859-4a2f-92c3-019b162bb8c0	ACC_006	CC_AMER_PROG_TRADING_005	BOOK_05	STRAT_02	2024-07-29	40058.84	-336544.39	-1957928.34	1612415.12
825474b1-615f-4d0d-9d28-4ff94c11e788	ACC_007	CC_AMER_CASH_NY_001	BOOK_04	STRAT_05	2024-09-27	17586.16	64770.69	-8883.09	-777757.98
ede24e64-1c7b-4696-9f74-93674fcf82dc	ACC_008	CC_APAC_ALGO_G1_013	BOOK_06	STRAT_01	2024-05-01	76225.05	-85112.41	-1586096.01	-443861.23
99328a41-4bbe-40e5-82d6-830bfe48cd77	ACC_010	CC_APAC_ALGO_G1_012	BOOK_10	STRAT_04	2024-05-07	34448.78	-131892.33	-1678118.96	-1233754.20
4b6bee15-4bd0-48bd-902f-cd034fd542fc	ACC_004	CC_AMER_PROG_TRADING_005	BOOK_01	STRAT_03	2024-06-01	-51805.36	444989.79	-1424708.33	-629214.86
46dc7347-ef4d-4baf-9a98-299de2724167	ACC_010	CC_AMER_CASH_NY_004	BOOK_01	STRAT_02	2024-05-18	55122.14	308907.62	-710739.84	-325009.98
d8dadd4e-1ecb-4655-aa7f-6689c2ca5572	ACC_002	CC_APAC_ALGO_G1_012	BOOK_03	STRAT_02	2024-01-09	9128.90	-1875.72	956147.48	-555631.64
bae59e60-9a35-4a89-9cec-892a9a7f5135	ACC_008	CC_APAC_ALGO_G1_011	BOOK_04	STRAT_04	2024-06-01	-60025.34	391532.13	-912877.89	917072.34
ec15a07a-c1b3-4f2f-b5b3-05b2c65b2431	ACC_010	CC_AMER_CASH_NY_004	BOOK_06	STRAT_02	2024-07-31	-78415.71	-26865.44	1136653.39	-141522.31
6b8e7f9a-3fb1-4473-abf5-425ba83d0e8f	ACC_002	CC_EMEA_INDEX_ARB_008	BOOK_02	STRAT_02	2024-09-04	1278.62	-75242.09	732628.26	-1434345.11
080ab990-c2af-4459-83d0-a91d309adf62	ACC_008	CC_AMER_CASH_NY_002	BOOK_05	STRAT_01	2024-03-10	35812.42	301064.97	303163.31	716862.31
e4fab00c-4f70-4264-b7c6-cf4520900e7a	ACC_006	CC_AMER_CASH_NY_001	BOOK_02	STRAT_02	2024-01-15	-14474.40	353857.96	922496.15	-1228618.62
b587edbd-0004-4cdc-8922-94dfa670f3ac	ACC_001	CC_APAC_ALGO_G1_011	BOOK_03	STRAT_01	2024-07-09	-3797.81	-277993.73	820535.84	-488142.92
0dcb944d-a089-4678-9a98-9efbfc5fcf9f	ACC_002	CC_EMEA_INDEX_ARB_010	BOOK_10	STRAT_02	2024-03-17	-40539.68	485804.27	-1961790.33	1536450.32
dc99226d-9a53-45a3-8098-933eba129c32	ACC_006	CC_AMER_PROG_TRADING_005	BOOK_09	STRAT_01	2024-11-05	85025.39	25715.41	-1167269.43	-880467.44
d3364c81-42d7-472c-8091-80d6aa11bcc6	ACC_003	CC_EMEA_INDEX_ARB_009	BOOK_10	STRAT_04	2024-02-21	-79697.15	-264457.20	-1675746.94	880713.57
368834a8-173e-4e9b-b5fe-2d928b9c1cbe	ACC_004	CC_AMER_CASH_NY_001	BOOK_08	STRAT_05	2024-10-03	-30228.11	333933.10	-1570676.43	1648885.39
70572f21-483a-4ee6-914b-d58f502c5f99	ACC_010	CC_EMEA_INDEX_ARB_010	BOOK_09	STRAT_03	2024-11-28	-55040.27	362164.74	1135298.78	1284442.57
f9a21abc-8a5b-4e65-9cd2-b0fa1c1e8b84	ACC_004	CC_EMEA_INDEX_ARB_008	BOOK_07	STRAT_04	2024-07-07	66323.49	-84.81	1561069.16	124166.39
09da4b93-4d24-400f-b365-c46d3a672205	ACC_009	CC_AMER_CASH_NY_002	BOOK_09	STRAT_01	2024-04-18	-48064.78	172935.52	-1513833.58	-1102155.74
178d2888-1e1e-46e4-81dd-db876e2760d2	ACC_005	CC_APAC_ALGO_G1_012	BOOK_01	STRAT_03	2024-02-27	-34590.72	182051.73	-362199.22	-494927.00
73f1048a-3f9f-425a-ae02-f5ceadbadc3e	ACC_005	CC_AMER_CASH_NY_002	BOOK_06	STRAT_02	2024-12-18	-15764.21	324602.51	-657850.02	732397.68
e815ace1-468c-4951-ac28-a9913548d52c	ACC_005	CC_AMER_CASH_NY_003	BOOK_05	STRAT_04	2024-03-01	95427.48	-234088.47	719821.18	-1044599.21
1129d279-764a-45e3-8f32-fe35af67b5fe	ACC_007	CC_AMER_CASH_NY_002	BOOK_06	STRAT_02	2024-04-28	73422.04	-385762.32	-1255981.96	-829031.72
0404efdb-0b05-4e36-922d-b4eb97944d4c	ACC_002	CC_AMER_CASH_NY_003	BOOK_01	STRAT_02	2024-07-05	5827.33	133855.09	1770961.30	-471032.36
6f86d784-362d-44c8-a862-dde42dfdf573	ACC_001	CC_EMEA_INDEX_ARB_008	BOOK_08	STRAT_02	2024-09-07	14612.62	299778.89	254040.56	760009.29
daedda6c-ef6a-46c9-baf9-4ab590f3f580	ACC_003	CC_APAC_ALGO_G1_013	BOOK_01	STRAT_05	2024-05-06	49099.55	58062.55	981799.05	-308616.66
2a9f61ac-0e30-4870-95c0-d1f5ec304ced	ACC_006	CC_EMEA_INDEX_ARB_010	BOOK_05	STRAT_02	2024-05-01	57335.56	-16143.07	1320379.69	-1383653.85
4c568509-7dbb-4f09-86d8-990c1d34ba24	ACC_007	CC_AMER_CASH_NY_004	BOOK_09	STRAT_01	2024-02-09	-8943.01	360115.07	84596.47	1344480.79
f9a034e4-2be9-4e54-b4c3-529962d86247	ACC_001	CC_EMEA_INDEX_ARB_010	BOOK_01	STRAT_01	2024-06-14	37791.00	-401316.84	-1452891.89	696852.96
7080daa4-0134-4551-8469-1683b4035f95	ACC_010	CC_EMEA_INDEX_ARB_008	BOOK_05	STRAT_05	2024-12-21	33290.20	-175341.09	1635962.38	-1444090.75
9d569240-df58-46f0-990f-749012ce5fbf	ACC_009	CC_AMER_PROG_TRADING_007	BOOK_10	STRAT_03	2024-11-16	49526.56	-12377.19	-862883.84	1325375.92
fc933e2e-b50e-4c2c-a591-6c23657c311b	ACC_001	CC_AMER_PROG_TRADING_006	BOOK_06	STRAT_05	2024-09-11	89762.93	-248756.37	135279.50	-1487445.76
3a52db78-31db-4b3c-930a-34254c14c14e	ACC_004	CC_EMEA_INDEX_ARB_008	BOOK_03	STRAT_01	2024-07-10	1819.64	-348389.61	906949.42	-1386672.98
02f0e381-9737-45d4-8edd-5b0300e6a1b6	ACC_003	CC_AMER_CASH_NY_001	BOOK_04	STRAT_05	2024-11-17	42189.26	278652.59	-165395.81	-808195.58
148e9e0d-e235-401d-9437-414e089bf810	ACC_005	CC_EMEA_INDEX_ARB_009	BOOK_10	STRAT_03	2024-10-14	-70706.57	-243876.53	-476662.65	-571427.57
b4769bb3-23f5-449e-9ddd-7791cc5d2ca7	ACC_006	CC_AMER_CASH_NY_003	BOOK_07	STRAT_01	2024-12-17	58449.28	-466079.16	1043338.20	-1289796.20
d0db1837-35c5-4b73-962b-3fff820d1c63	ACC_005	CC_AMER_CASH_NY_002	BOOK_02	STRAT_03	2024-10-26	98173.57	131164.92	-1642946.74	-939833.12
f59e520c-1a16-4e7e-8398-5e65448540d5	ACC_001	CC_AMER_PROG_TRADING_006	BOOK_08	STRAT_05	2024-12-09	51135.69	-272136.56	-1503507.87	-905725.10
9e358827-89bf-4055-bd6c-b73a9be071d3	ACC_007	CC_AMER_CASH_NY_002	BOOK_01	STRAT_03	2024-04-21	-12472.52	-494029.46	-1845988.57	1538731.88
e845dc74-2b02-44ea-8b8b-7bc878a8cdea	ACC_007	CC_EMEA_INDEX_ARB_010	BOOK_10	STRAT_01	2024-01-27	-38614.92	-333878.60	-1625046.50	346782.20
5475dbb3-896e-4336-aeb3-b666a4422a10	ACC_008	CC_EMEA_INDEX_ARB_009	BOOK_06	STRAT_04	2024-07-07	-71900.14	-338742.96	1883393.38	-1554380.40
d6204b20-d66a-468e-8434-e35096e579fd	ACC_008	CC_APAC_ALGO_G1_012	BOOK_08	STRAT_04	2024-02-04	85689.73	-474956.77	1822818.66	-1292988.19
6c2f2aa0-d27d-41f7-b301-d5930e80dfb6	ACC_001	CC_AMER_CASH_NY_001	BOOK_07	STRAT_04	2024-01-09	64255.38	-430864.76	-894320.68	1125797.40
ad062fdc-4d23-4fdc-8558-a909447135cc	ACC_008	CC_AMER_PROG_TRADING_006	BOOK_09	STRAT_02	2024-02-26	51473.88	-223288.42	-98839.36	-461435.57
4b3317d9-9168-4426-a1bd-51197fda2975	ACC_010	CC_AMER_CASH_NY_004	BOOK_07	STRAT_01	2024-07-02	-9707.44	-54160.30	-267883.87	-1453354.64
c4f5abe5-4367-42fc-8890-6d01240eb4df	ACC_010	CC_APAC_ALGO_G1_013	BOOK_08	STRAT_01	2024-01-08	67523.13	132545.01	458661.40	-679750.85
35fc0a55-f4ec-4934-a94e-f21acba75be3	ACC_003	CC_AMER_PROG_TRADING_006	BOOK_07	STRAT_02	2024-09-23	-59654.13	64321.44	-1955420.94	-1678305.37
8e9af322-5152-44d0-89f6-a05a56b590d4	ACC_002	CC_AMER_PROG_TRADING_006	BOOK_10	STRAT_03	2024-06-23	69294.10	-83179.18	27585.06	39651.43
b1d7e08f-e1d4-46d0-8dbf-0a5fbdc6660c	ACC_006	CC_APAC_ALGO_G1_013	BOOK_04	STRAT_01	2024-06-26	-97372.53	-331696.42	-1681676.71	-1546171.69
01194ff5-879c-4f6e-8c75-71c054f5796e	ACC_009	CC_AMER_CASH_NY_003	BOOK_07	STRAT_05	2024-12-29	-94341.97	-292921.26	1939493.92	889502.89
afff555e-848a-4691-89a7-3423f6f7ee46	ACC_008	CC_AMER_PROG_TRADING_006	BOOK_08	STRAT_05	2024-12-19	11810.78	40037.57	939933.41	592080.33
4a094de6-3228-49eb-9a00-d3c928e55728	ACC_003	CC_EMEA_INDEX_ARB_010	BOOK_05	STRAT_03	2024-07-22	-33.95	-14634.14	836627.57	-411710.79
33e089a3-14a5-4f4c-a427-0c34e7344890	ACC_010	CC_APAC_ALGO_G1_013	BOOK_07	STRAT_01	2024-07-30	-98187.96	476004.60	962997.01	-377721.96
f756022e-0dc4-4819-85d3-c29fd8b75800	ACC_009	CC_EMEA_INDEX_ARB_009	BOOK_02	STRAT_03	2024-04-03	-66151.74	-341104.57	-283084.40	-288390.80
13c70123-e2a2-4713-94a4-6fcd9a3c8e55	ACC_008	CC_APAC_ALGO_G1_011	BOOK_10	STRAT_01	2024-10-11	-93625.51	161573.24	-760736.87	1770025.67
54e6b41d-8cd5-40d6-9e82-5e6245b59124	ACC_007	CC_AMER_CASH_NY_003	BOOK_07	STRAT_01	2024-04-07	-85381.54	-361018.72	-1163304.97	1202966.21
cc68e8fc-18b9-4c7c-9364-fa5d7a01dd49	ACC_006	CC_EMEA_INDEX_ARB_009	BOOK_01	STRAT_01	2024-07-16	448.31	353444.13	-882714.51	57318.41
38afbfb2-4522-4858-80c3-42374c9a84b4	ACC_006	CC_AMER_CASH_NY_004	BOOK_05	STRAT_05	2024-04-30	52672.38	-393841.59	1250191.68	-355537.17
bce925e3-195f-4183-935e-223bded4778b	ACC_009	CC_AMER_CASH_NY_002	BOOK_09	STRAT_04	2024-10-29	43216.18	-343491.71	-1310177.40	811005.61
3fa556b9-70c6-4be0-aab4-852747af1cf2	ACC_002	CC_AMER_PROG_TRADING_007	BOOK_02	STRAT_02	2024-10-14	-89495.25	187189.97	1227677.50	1747746.85
3644b2d9-dd52-4369-8cf2-8ec81593224e	ACC_005	CC_AMER_CASH_NY_003	BOOK_02	STRAT_01	2024-12-11	-78083.76	-172518.58	-1223691.50	-880361.78
05a8e9ee-ebcc-4e7b-bd1e-e2de6a368cf6	ACC_003	CC_AMER_CASH_NY_001	BOOK_05	STRAT_02	2024-12-09	58162.23	81860.08	1390573.87	675905.04
87d57006-bedb-4ed7-b13f-c17cd30071ce	ACC_006	CC_APAC_ALGO_G1_011	BOOK_05	STRAT_02	2024-11-28	-3349.57	-422828.12	-924145.79	512796.95
83c3bf07-aead-4754-baab-4864edd81e6c	ACC_005	CC_AMER_PROG_TRADING_006	BOOK_05	STRAT_01	2024-03-22	-40165.03	187573.45	1922216.11	132705.49
a6923e60-856c-4aad-83bc-26f562c3570d	ACC_009	CC_AMER_PROG_TRADING_006	BOOK_08	STRAT_02	2024-05-20	45198.96	8161.67	1876286.25	454483.40
c7a35a73-cc78-4000-8e1c-66bf3b6d4db4	ACC_009	CC_AMER_CASH_NY_003	BOOK_07	STRAT_01	2024-01-03	9483.50	-336655.30	956874.02	1112612.96
c298054e-a130-474f-a42a-9e7ebdc36a18	ACC_005	CC_EMEA_INDEX_ARB_010	BOOK_02	STRAT_03	2024-10-20	45361.43	464312.35	644724.02	1032853.29
498764c9-ed53-40af-ba74-7bd595c4a6ba	ACC_009	CC_EMEA_INDEX_ARB_010	BOOK_10	STRAT_01	2024-07-26	-36087.03	489295.50	-1151573.44	-1206129.70
ed1cbf0c-309c-4651-bd73-c20e382a216e	ACC_003	CC_EMEA_INDEX_ARB_010	BOOK_08	STRAT_04	2024-10-19	89355.10	-354379.36	21814.30	231248.38
834fb1ba-7334-4a42-b38d-ba729f4e3496	ACC_002	CC_EMEA_INDEX_ARB_008	BOOK_08	STRAT_03	2024-05-09	47998.65	240658.09	2444.49	-1420709.42
9a4ba8c4-f7dd-44e2-acfb-2a9230508fd6	ACC_006	CC_AMER_CASH_NY_003	BOOK_08	STRAT_05	2024-10-28	80387.15	174005.44	1198001.70	604634.69
c672e8f1-b8b7-46f6-8763-cc360736b47e	ACC_010	CC_APAC_ALGO_G1_011	BOOK_03	STRAT_04	2024-10-17	-40341.77	-428423.63	-1307853.99	1685376.33
5706ee61-abee-498c-af54-ae7d55da57ae	ACC_009	CC_AMER_PROG_TRADING_005	BOOK_01	STRAT_03	2024-12-21	89076.65	247708.10	-1119035.24	867423.12
b8336792-6bc2-411f-b12d-e33b946fef90	ACC_002	CC_AMER_CASH_NY_001	BOOK_06	STRAT_01	2024-08-29	-15545.93	495104.78	1112729.25	1460409.34
e446e29f-0893-4cdf-a891-e812fda90bda	ACC_007	CC_AMER_PROG_TRADING_006	BOOK_02	STRAT_04	2024-04-30	93302.26	250628.08	919325.32	1522171.02
738b3f16-30bd-4e4b-9c53-93f5ca5bb085	ACC_004	CC_APAC_ALGO_G1_011	BOOK_04	STRAT_01	2024-06-23	-40296.91	-174054.33	1461414.08	1301434.66
f3224e62-a737-401c-a7d2-90a7e22dd6fc	ACC_010	CC_APAC_ALGO_G1_011	BOOK_07	STRAT_01	2024-12-26	71760.00	-87057.92	-1831391.02	557838.79
532e7458-2581-49b8-b11a-0838a9363654	ACC_007	CC_AMER_CASH_NY_001	BOOK_01	STRAT_05	2024-05-12	94630.96	469579.00	-801210.80	625414.86
8c18a891-03bf-47e9-b6a8-d9d31f9f2b58	ACC_003	CC_APAC_ALGO_G1_011	BOOK_06	STRAT_02	2024-05-29	-96709.61	287132.58	1107012.05	-567411.33
227fcb9d-20cd-4625-8abc-e894211d0dd0	ACC_004	CC_APAC_ALGO_G1_012	BOOK_01	STRAT_01	2024-10-12	-17171.61	29213.35	1193978.92	1741692.54
e9d86bcb-a79a-4c14-b7b9-3777d0a80e28	ACC_003	CC_EMEA_INDEX_ARB_008	BOOK_09	STRAT_05	2024-06-14	-50623.35	487586.16	-817642.71	-736641.88
a2ea8186-e2ce-4252-a49a-e612bd6ba1e1	ACC_009	CC_APAC_ALGO_G1_012	BOOK_02	STRAT_02	2024-04-03	61042.46	156276.53	141612.39	75651.91
b29a8462-36f3-4675-9c3d-8589ecb8c89a	ACC_010	CC_APAC_ALGO_G1_011	BOOK_07	STRAT_02	2024-03-15	-87600.81	-438460.99	1165555.97	-1165331.99
6a425fc2-db29-4cf5-aaaf-c350b521b12f	ACC_007	CC_AMER_PROG_TRADING_006	BOOK_06	STRAT_05	2024-09-28	6218.42	1722.54	1737137.30	757485.36
c6c0de36-232e-4654-bb27-91fd05ce8678	ACC_006	CC_EMEA_INDEX_ARB_010	BOOK_04	STRAT_01	2024-09-30	18875.49	476848.68	10568.28	-382681.54
f1b084c0-e15c-42ec-8ea9-cfb150e5d4f9	ACC_009	CC_EMEA_INDEX_ARB_010	BOOK_04	STRAT_05	2024-08-28	21323.63	-173792.66	829287.69	-1081598.62
abab1cd3-c579-416f-b858-b9cdf02a1f95	ACC_006	CC_AMER_CASH_NY_004	BOOK_09	STRAT_03	2024-03-28	-43484.33	-211779.63	807975.52	-1045877.39
87854217-0e7b-4337-accc-11da6259dd29	ACC_003	CC_AMER_CASH_NY_002	BOOK_02	STRAT_03	2024-06-03	69552.50	283452.57	1931791.67	1216837.89
c11e425c-7a6e-4ffc-b2d4-46052f14b81a	ACC_006	CC_AMER_CASH_NY_003	BOOK_10	STRAT_04	2024-08-24	75380.85	431281.82	1732089.95	228119.37
ab7bbfcb-86e9-4f16-94e3-f18b2a815e82	ACC_009	CC_AMER_PROG_TRADING_005	BOOK_03	STRAT_03	2024-05-08	85120.01	180826.46	-540283.28	-146724.11
9ec3b60e-fc52-4b5e-af41-d70f599128b0	ACC_001	CC_AMER_CASH_NY_001	BOOK_08	STRAT_02	2024-08-07	-34556.77	374607.64	-1965953.50	334643.39
73ce82e0-00d2-4002-9ed0-867da27cfb7f	ACC_006	CC_AMER_CASH_NY_003	BOOK_10	STRAT_05	2024-08-12	62592.41	142815.23	1338843.75	-1481451.02
58d6984a-3734-41c1-b090-c2deae624782	ACC_001	CC_AMER_PROG_TRADING_007	BOOK_09	STRAT_01	2024-12-05	34362.32	101518.07	601091.56	-363896.11
b75dbdc5-b8ed-4d7a-a953-656cbc41142c	ACC_009	CC_AMER_PROG_TRADING_007	BOOK_08	STRAT_02	2024-12-31	49540.78	-327819.81	1752110.97	-1750522.38
fde37393-adbf-41aa-a5f5-8447406dfd2c	ACC_010	CC_APAC_ALGO_G1_013	BOOK_01	STRAT_03	2024-03-14	-16960.72	-413465.46	-431318.96	-1592009.36
af55c3a0-5470-45db-89f2-2f95c0379cbb	ACC_010	CC_AMER_PROG_TRADING_006	BOOK_07	STRAT_03	2024-09-03	57229.92	-472925.38	215611.05	765155.11
d437c9ec-b135-4d57-aa01-3b31b4b42310	ACC_002	CC_AMER_CASH_NY_001	BOOK_05	STRAT_02	2024-12-26	75372.65	380159.83	1548154.57	298979.08
16c473fc-5f82-4478-a1f4-1f8a9a7e7b34	ACC_005	CC_AMER_PROG_TRADING_006	BOOK_05	STRAT_01	2024-01-22	-96606.47	477731.62	-157369.74	1682595.80
08c9707a-f062-45ef-a42d-25300fe21b3e	ACC_003	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_01	2024-04-29	83177.58	-316255.49	1052597.90	817863.58
8df47a67-d1b3-4e31-a1b7-813d3b84479d	ACC_004	CC_AMER_CASH_NY_003	BOOK_09	STRAT_03	2024-11-25	47468.33	-392441.83	1403072.17	-1445993.80
82101585-c4fc-4257-9af1-1a2571a33e0d	ACC_007	CC_AMER_CASH_NY_002	BOOK_03	STRAT_05	2024-05-05	-74095.49	40736.87	564976.67	1309809.74
71b721b2-21a1-4f0f-8165-bd952c2db932	ACC_010	CC_AMER_PROG_TRADING_007	BOOK_09	STRAT_02	2024-10-03	-16486.74	-440914.01	-115863.06	-500340.06
e30d55bf-4a9f-4d79-90d2-97a915d01fe4	ACC_005	CC_AMER_CASH_NY_004	BOOK_08	STRAT_04	2024-10-18	12661.18	331090.41	770820.44	-794517.85
0f1f118d-1ffa-49c8-8f7f-813210190abb	ACC_005	CC_APAC_ALGO_G1_013	BOOK_07	STRAT_01	2024-01-16	-7711.44	173882.30	535842.90	1204149.81
142ee510-f33e-4743-b75b-488443430220	ACC_009	CC_APAC_ALGO_G1_011	BOOK_02	STRAT_02	2024-12-18	-95551.08	130820.24	-1563588.66	31140.29
c5220fb3-cbda-4349-8b79-cbe4999d14f4	ACC_006	CC_APAC_ALGO_G1_013	BOOK_07	STRAT_05	2024-10-10	49523.68	-130669.57	-1479102.63	-905315.97
594fa725-6fb8-4214-ad01-0f0de90fe50f	ACC_005	CC_APAC_ALGO_G1_011	BOOK_06	STRAT_04	2024-10-01	-71001.91	-280614.12	-1944910.30	59717.02
14e1a6c3-ad4d-465e-80e6-9cd255994f27	ACC_004	CC_EMEA_INDEX_ARB_008	BOOK_08	STRAT_04	2024-03-04	81495.45	-475861.08	-97146.87	-1413874.23
792fc52e-886a-4d6c-9cf2-cff14cdbbdf8	ACC_009	CC_APAC_ALGO_G1_013	BOOK_02	STRAT_04	2024-03-07	64257.71	216679.20	1185413.60	-1452157.47
db633ff4-5fdb-4dbe-b5fe-3c1b9bfacf1a	ACC_002	CC_AMER_PROG_TRADING_005	BOOK_08	STRAT_02	2024-04-04	-6069.76	220071.15	198794.61	-627797.55
da8dd7ff-19a5-4360-88ec-cc6474a485ea	ACC_006	CC_AMER_CASH_NY_004	BOOK_03	STRAT_03	2024-09-10	-41127.47	-214991.18	1656869.96	1226451.93
559f98e5-1ef6-4a6b-bdd7-38c7b167103a	ACC_003	CC_APAC_ALGO_G1_012	BOOK_05	STRAT_02	2024-01-11	93801.51	-412084.05	1875580.42	-370235.30
7ea07989-669a-417a-82c6-c14b9c321994	ACC_010	CC_AMER_CASH_NY_004	BOOK_03	STRAT_02	2024-11-13	-73747.58	-483810.51	477447.72	-19414.72
d82d8530-b5e1-402f-9a8a-c7a3e8178f14	ACC_006	CC_AMER_PROG_TRADING_007	BOOK_06	STRAT_04	2024-11-26	19579.64	-193900.09	-522412.92	1711753.84
6c7a34e2-0c8f-43a2-ac25-ef902215b797	ACC_007	CC_EMEA_INDEX_ARB_009	BOOK_06	STRAT_04	2024-05-31	-19086.02	-451732.34	-1134549.24	-650736.79
0fd9fae5-7fbf-435c-a666-3b1ec08080cd	ACC_007	CC_AMER_CASH_NY_002	BOOK_09	STRAT_05	2024-07-26	-11279.47	262650.27	-496198.98	1010154.57
004ebd42-4c05-4e04-bea5-1284148322ba	ACC_003	CC_EMEA_INDEX_ARB_010	BOOK_02	STRAT_03	2024-11-05	17061.63	-129177.93	-537202.83	-1678831.03
3000e3c2-8e06-431b-a2d5-b0873deec5d2	ACC_006	CC_AMER_CASH_NY_002	BOOK_05	STRAT_05	2024-09-06	-68839.33	144065.65	597665.50	809055.70
68911bfe-9871-4b97-aa62-8b2e7a8c925a	ACC_003	CC_EMEA_INDEX_ARB_009	BOOK_07	STRAT_04	2024-12-26	-87331.94	66561.54	-1617474.29	334735.19
485eb71d-a0b9-4d11-af9b-dd474d710d3f	ACC_008	CC_APAC_ALGO_G1_011	BOOK_10	STRAT_03	2024-03-03	-32969.79	-203713.31	-355745.20	1440294.43
3f6ef5fe-67a4-41f0-ad0b-93e4410857a4	ACC_009	CC_AMER_PROG_TRADING_006	BOOK_05	STRAT_05	2024-01-28	-93863.33	-426772.41	-1647059.77	1617628.10
022fbb25-8fba-4ff3-aa84-e1f9f83ac69e	ACC_007	CC_EMEA_INDEX_ARB_010	BOOK_06	STRAT_02	2024-02-11	-18504.49	330786.65	1665648.73	69731.52
db853e05-a151-4012-a849-a03563a2f3d3	ACC_003	CC_AMER_CASH_NY_002	BOOK_08	STRAT_04	2024-03-10	-95539.99	-217323.83	-570570.91	-1351562.79
6ae1f16c-4839-4d41-879f-4cd1abfb5106	ACC_009	CC_AMER_CASH_NY_001	BOOK_07	STRAT_05	2024-05-19	-59117.24	317359.16	1050174.42	-557755.77
99bece45-01d5-4f9f-92b3-6e98e566750c	ACC_007	CC_AMER_CASH_NY_004	BOOK_02	STRAT_03	2024-12-23	-5163.57	109442.69	906582.50	165769.04
2e5bbc32-b620-47d6-927a-d29482581d97	ACC_007	CC_AMER_PROG_TRADING_006	BOOK_01	STRAT_03	2024-01-24	-6091.07	-83956.95	-330087.16	-1645182.77
5795be16-ef11-4a73-b5bd-b1d1c502c7b0	ACC_010	CC_AMER_CASH_NY_002	BOOK_01	STRAT_03	2024-06-25	-21808.87	451915.61	-1588261.54	-524936.58
222ae99a-bc5d-46be-bc8b-d0a39019dfc2	ACC_006	CC_AMER_PROG_TRADING_007	BOOK_06	STRAT_02	2024-12-06	76102.51	-334550.99	-314423.47	-2746.26
47209756-9717-476e-8b69-bb1abb78b771	ACC_010	CC_AMER_CASH_NY_002	BOOK_01	STRAT_03	2024-06-19	55253.55	-274936.15	-1305013.06	1072261.00
f4fbd989-6a7d-4ee1-9722-08ec55350fd7	ACC_006	CC_AMER_PROG_TRADING_005	BOOK_10	STRAT_05	2024-04-10	47420.79	402321.90	770746.11	547340.24
f5b271b0-078c-470f-8bd2-d15fd85444a4	ACC_008	CC_AMER_CASH_NY_001	BOOK_03	STRAT_05	2024-05-28	23192.92	483002.51	1849948.05	-703925.45
40f3be52-7fab-43a1-900f-222b024e9d50	ACC_005	CC_AMER_PROG_TRADING_006	BOOK_06	STRAT_02	2024-02-02	-42825.56	445186.11	-67254.53	463626.17
d1aba1fc-65d4-411e-af38-052acd563b68	ACC_003	CC_APAC_ALGO_G1_012	BOOK_10	STRAT_04	2024-02-27	-70231.46	469306.39	-1319819.41	-757947.78
c51430db-50c8-4dbd-9f9b-f7403b2bd6a8	ACC_003	CC_AMER_PROG_TRADING_007	BOOK_02	STRAT_04	2024-09-12	-37788.20	-35965.85	900728.95	1280352.97
8ec6a039-2353-4170-99df-fcb590f7c555	ACC_007	CC_AMER_PROG_TRADING_007	BOOK_01	STRAT_01	2024-01-12	-46272.99	224586.84	892600.47	1699105.41
8db4db18-d5e1-467f-bef8-be60d7feca0b	ACC_001	CC_APAC_ALGO_G1_012	BOOK_06	STRAT_01	2024-07-11	-26976.67	433900.16	-430493.31	-1325133.90
47a78f5b-7452-4a40-b01b-9155dff8c629	ACC_005	CC_AMER_PROG_TRADING_007	BOOK_05	STRAT_02	2024-06-11	-68584.51	-221144.99	900720.83	1688022.60
118e4c72-749c-455a-a58a-2d31be9729c6	ACC_008	CC_AMER_PROG_TRADING_006	BOOK_08	STRAT_02	2024-03-02	-22214.61	-231873.26	-1693516.58	-1083583.77
79834e69-118a-41f5-96ec-bf99a42a2833	ACC_007	CC_APAC_ALGO_G1_013	BOOK_04	STRAT_01	2024-08-30	56010.74	-252234.36	-655212.45	-194554.65
7acfaeb5-d042-4cb0-aeff-3229f8a80f64	ACC_002	CC_AMER_PROG_TRADING_007	BOOK_07	STRAT_04	2024-05-26	48885.20	137706.07	-1900554.47	1321449.74
fb95a045-522b-41ef-aed8-3cd766ed807b	ACC_010	CC_AMER_PROG_TRADING_005	BOOK_03	STRAT_01	2024-06-29	-73038.86	-89419.48	-288151.79	1616006.50
56f1018f-a1d0-402b-824b-686849eb5079	ACC_003	CC_AMER_CASH_NY_004	BOOK_09	STRAT_05	2024-02-11	92425.51	490621.14	-1307397.74	-92370.34
e744bc45-fb67-4cde-9b7b-0fc6c3c7e35d	ACC_009	CC_AMER_PROG_TRADING_007	BOOK_06	STRAT_04	2024-04-19	65790.49	166288.86	723612.91	1759985.81
85272d34-a828-4d55-b94c-2d9fb31e8ab8	ACC_002	CC_AMER_CASH_NY_002	BOOK_07	STRAT_04	2024-02-16	-43393.33	86797.60	-600081.40	-1266462.76
fce6f21a-1a6c-4658-89d7-08231bba619e	ACC_004	CC_EMEA_INDEX_ARB_008	BOOK_10	STRAT_01	2024-11-19	76564.68	434426.29	-1720116.93	-885204.00
e9d61ad5-2630-4994-8856-950d50721044	ACC_001	CC_AMER_CASH_NY_004	BOOK_06	STRAT_05	2024-10-05	93239.86	-8436.68	-1493123.27	-823584.17
0c769681-8ee7-4118-ba27-d1a988cf2a4e	ACC_006	CC_AMER_PROG_TRADING_005	BOOK_08	STRAT_04	2024-11-02	22.62	-443540.67	1404139.87	-61486.50
e24ec9de-ff3b-4b47-9e95-c285a00af4f3	ACC_008	CC_AMER_PROG_TRADING_007	BOOK_10	STRAT_03	2024-02-09	-88553.23	-249510.17	190870.53	792002.83
ec900ed7-01b2-406a-8751-ed3388522b16	ACC_008	CC_EMEA_INDEX_ARB_009	BOOK_09	STRAT_05	2024-05-27	-64366.33	-219818.18	114834.01	1604909.06
6ff7b487-bc5f-4452-931c-5e30dab30094	ACC_007	CC_AMER_CASH_NY_001	BOOK_03	STRAT_04	2024-10-11	94591.17	-56329.63	1428836.09	1310287.42
6df39e27-a46b-4fe6-8ade-08ee2d3d3d77	ACC_005	CC_EMEA_INDEX_ARB_010	BOOK_07	STRAT_03	2024-12-13	-9180.52	349599.04	921659.18	-906107.73
a37f766f-eb39-4a23-9bd5-5979b1dcdb3b	ACC_004	CC_APAC_ALGO_G1_012	BOOK_05	STRAT_02	2024-09-09	-92519.36	-482003.94	290689.78	-966544.74
453753b2-4e63-4ea8-ba06-7446d9556944	ACC_002	CC_EMEA_INDEX_ARB_009	BOOK_09	STRAT_04	2024-11-19	-49772.43	98920.37	-528739.89	-1193703.48
78b17947-0bba-4706-a056-4b4c00720936	ACC_001	CC_AMER_CASH_NY_001	BOOK_04	STRAT_01	2024-05-26	71171.15	478683.08	-1400879.32	-14403.47
41dc7cb6-338c-416b-81ff-8e712a4c1ebd	ACC_010	CC_APAC_ALGO_G1_013	BOOK_03	STRAT_01	2024-05-08	10476.77	168678.25	1251945.39	-597801.86
4c099502-218d-40f7-8e77-e55c49185e4f	ACC_010	CC_APAC_ALGO_G1_013	BOOK_01	STRAT_02	2024-03-15	76409.66	-440241.89	-1513120.61	1441017.90
347c736b-63a8-49d2-bf0a-a09027bacfbf	ACC_006	CC_APAC_ALGO_G1_013	BOOK_07	STRAT_04	2024-05-25	75294.14	432678.80	-440364.84	1210473.73
6366b817-0b66-46be-a8ca-7b4aacc6c77b	ACC_001	CC_EMEA_INDEX_ARB_010	BOOK_07	STRAT_05	2024-07-02	86991.72	16261.36	-1353299.18	-803721.60
1e023b01-2663-4d29-b439-d7d9fd44a24c	ACC_010	CC_AMER_CASH_NY_004	BOOK_03	STRAT_05	2024-07-07	47825.44	-352606.83	-63447.05	-1387305.93
7c93e350-d0e9-4b7e-a0d7-2a7924180f3c	ACC_002	CC_EMEA_INDEX_ARB_010	BOOK_09	STRAT_04	2024-04-13	-36863.04	-456887.93	441403.32	350262.82
db72e315-068b-4612-bdf1-4a2a70c3fa9b	ACC_002	CC_APAC_ALGO_G1_013	BOOK_04	STRAT_03	2024-05-18	37056.81	10813.85	-1764304.32	-1668764.12
488460db-ad01-47b2-831c-633e90ea9b3b	ACC_005	CC_EMEA_INDEX_ARB_008	BOOK_02	STRAT_05	2024-06-20	87341.63	146165.45	1628649.67	403009.31
d8417668-387a-488f-acbc-cab5d2034537	ACC_007	CC_EMEA_INDEX_ARB_008	BOOK_03	STRAT_03	2024-09-25	43123.82	69189.14	1545281.70	140315.00
a8544dc8-e82b-47fe-acae-886ecf40228f	ACC_009	CC_AMER_PROG_TRADING_006	BOOK_03	STRAT_01	2024-06-15	-53881.35	-212803.33	-1869428.91	607506.95
c2fe62f6-ad3c-452b-9400-179cbcc99bcb	ACC_003	CC_AMER_PROG_TRADING_007	BOOK_04	STRAT_01	2024-07-28	-75168.34	362791.36	-222847.04	1176715.58
f7953196-e6f2-4438-8f8a-950d660913df	ACC_004	CC_AMER_PROG_TRADING_005	BOOK_01	STRAT_03	2024-09-08	-21913.75	-258783.29	205055.70	-480314.25
2e5bf364-1dbe-45a2-ba09-56610cc2ffc2	ACC_002	CC_APAC_ALGO_G1_011	BOOK_02	STRAT_04	2024-11-30	-16731.75	-40799.61	438994.50	1170574.70
9680ccce-52d3-494e-9d0d-3711e490bf32	ACC_008	CC_APAC_ALGO_G1_012	BOOK_03	STRAT_02	2024-03-30	98477.87	216739.12	-22560.18	1415173.93
96e2b03d-af76-4611-be60-b5de55df7a0f	ACC_007	CC_AMER_CASH_NY_001	BOOK_03	STRAT_02	2024-10-30	-10584.67	314762.83	1497549.11	765651.67
9471cea2-f2e1-4d68-aee2-a42b641a8be8	ACC_004	CC_AMER_CASH_NY_001	BOOK_04	STRAT_02	2024-03-03	-2001.00	29186.09	699928.17	1306345.77
d8be4765-94f7-447a-8a76-14b3c8d73624	ACC_001	CC_EMEA_INDEX_ARB_008	BOOK_07	STRAT_05	2024-02-12	-3949.33	272498.77	-1042394.88	188467.03
2b31c997-7812-4cf6-8023-8b703630c598	ACC_007	CC_EMEA_INDEX_ARB_010	BOOK_06	STRAT_05	2024-06-12	28771.42	75299.48	-594012.22	1074699.32
0318f202-33e1-4355-a236-33cd97991e15	ACC_008	CC_APAC_ALGO_G1_013	BOOK_02	STRAT_05	2024-03-02	-38475.86	48955.52	-1629364.59	-61199.03
1fa118be-fb2a-4f8e-8ef2-27f0e2a16edb	ACC_009	CC_AMER_CASH_NY_004	BOOK_04	STRAT_04	2024-03-15	-2512.32	384962.77	-979626.06	1177511.56
cf942432-78ef-4e6a-9f04-9283a2c08bf4	ACC_006	CC_APAC_ALGO_G1_012	BOOK_09	STRAT_04	2024-11-06	28159.82	267905.38	-1541356.39	-1740064.78
c5a12220-6688-48a9-a596-ef066d8a229b	ACC_006	CC_AMER_PROG_TRADING_005	BOOK_08	STRAT_04	2024-03-09	9688.47	117503.25	-1795654.21	1036763.32
b69b0cbe-a353-4bef-9bcc-9cafe827207e	ACC_008	CC_APAC_ALGO_G1_012	BOOK_08	STRAT_01	2024-02-17	54000.99	219937.94	1187231.63	-100221.79
84e2e67e-28e6-4ebd-98f6-856af18784cb	ACC_005	CC_APAC_ALGO_G1_011	BOOK_01	STRAT_03	2024-05-17	-55166.02	248682.74	-1563779.04	1752876.53
62701f30-42e8-4b3a-a2b1-524ea733968d	ACC_006	CC_AMER_PROG_TRADING_005	BOOK_05	STRAT_03	2024-05-15	55563.70	-67788.94	1076315.24	1775716.98
e3946a9b-3fe2-451e-a468-8b28842cc717	ACC_005	CC_AMER_PROG_TRADING_005	BOOK_04	STRAT_02	2024-09-18	88258.25	390903.34	586195.00	250702.41
22ff6515-df84-4768-b50f-c9cdc9487c48	ACC_004	CC_AMER_PROG_TRADING_006	BOOK_03	STRAT_03	2024-08-28	35022.48	-249051.96	-1953740.11	1794249.76
e47008c6-17dc-4bf7-9c4a-2126a2e416aa	ACC_009	CC_EMEA_INDEX_ARB_009	BOOK_01	STRAT_04	2024-02-18	85551.90	266580.77	1826720.12	-1607806.93
5b6fbbba-5c6d-4e8c-aca7-5e6cb3e57fe2	ACC_009	CC_AMER_PROG_TRADING_005	BOOK_05	STRAT_03	2024-05-20	-86888.07	161392.38	280430.49	736910.87
7feb02cc-fba9-42bf-beb5-ef10316696fa	ACC_008	CC_APAC_ALGO_G1_012	BOOK_05	STRAT_05	2024-12-31	88234.76	-417402.57	15340.90	-547395.78
179f1db9-797e-46b6-8208-7bc37a0a1a87	ACC_004	CC_AMER_CASH_NY_004	BOOK_04	STRAT_01	2024-10-06	93086.24	-73862.39	-1901246.12	497494.97
faf2b4b0-da55-4d1f-a3b6-8d2f57071d3f	ACC_006	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_05	2024-07-25	65683.77	311364.92	434756.31	-183949.38
1d939fe8-e02f-4e8e-a402-c584d8ca3a51	ACC_002	CC_APAC_ALGO_G1_012	BOOK_09	STRAT_01	2024-09-06	-41110.35	-41315.43	822928.90	328235.46
12ae6e1c-6656-4923-83d9-1ebf51025bbf	ACC_003	CC_AMER_PROG_TRADING_007	BOOK_06	STRAT_01	2024-05-05	-26493.84	416330.47	-1010777.13	-1019494.41
983ad550-3221-4d4e-8ac4-2d20649b75cf	ACC_002	CC_AMER_PROG_TRADING_005	BOOK_08	STRAT_04	2024-02-14	83701.50	-381084.69	1273023.00	-362445.09
5f5135d7-6193-46c0-9c1e-fecb9e70c945	ACC_006	CC_AMER_CASH_NY_003	BOOK_08	STRAT_02	2024-08-11	-3434.98	340482.30	405486.15	-585246.89
033dfe7a-ade4-426c-aaf3-e4c92973d5f7	ACC_003	CC_APAC_ALGO_G1_011	BOOK_10	STRAT_02	2024-12-02	80434.16	436842.95	681668.47	-261370.05
9a4ebd86-57fd-4977-9f11-f0f60052aefa	ACC_006	CC_AMER_CASH_NY_003	BOOK_03	STRAT_03	2024-05-18	19291.63	-280669.28	-307829.15	-1313542.85
138c698a-b271-4a7f-8987-8dd19349e244	ACC_002	CC_AMER_CASH_NY_001	BOOK_10	STRAT_04	2024-01-24	-42448.75	441168.24	173768.09	-605858.89
9c2090a8-0244-41c0-8613-9cf048214195	ACC_005	CC_AMER_CASH_NY_001	BOOK_01	STRAT_05	2024-12-17	51867.20	-279535.02	1703645.37	-98428.81
1ca6e357-a8e8-4cb9-93f5-fcb35e729628	ACC_009	CC_AMER_CASH_NY_003	BOOK_06	STRAT_04	2024-06-30	-60693.08	395407.92	-726825.27	1721714.67
e26aebb6-3d7c-43dd-a093-d4211fd2d085	ACC_004	CC_AMER_CASH_NY_004	BOOK_02	STRAT_05	2024-09-16	4831.14	-234472.82	50809.53	-1072296.46
f7deb353-4833-48b4-8f93-776450866b70	ACC_004	CC_AMER_PROG_TRADING_005	BOOK_04	STRAT_01	2024-12-08	74412.98	336557.96	-1315876.73	-784538.62
6c087119-f002-4988-9b52-a6a2365c00a4	ACC_010	CC_EMEA_INDEX_ARB_008	BOOK_08	STRAT_02	2024-11-26	47950.60	-78172.47	-1983978.25	447865.76
ca89b3ab-4e6b-4331-b631-0af88bed7c13	ACC_008	CC_AMER_PROG_TRADING_007	BOOK_05	STRAT_02	2024-12-02	47871.26	-484131.10	296792.92	1711403.30
bd4cc94d-c16a-49e6-ab18-dff2554d29a4	ACC_008	CC_EMEA_INDEX_ARB_009	BOOK_07	STRAT_02	2024-09-13	-94564.38	448287.85	-254366.02	-90314.85
694c0996-da76-4e16-ac28-a85fe762748d	ACC_002	CC_AMER_CASH_NY_003	BOOK_07	STRAT_03	2024-01-28	92105.03	-176410.21	-1586644.03	-24472.04
0d95109c-6557-49ed-afa8-eb0ee30815b1	ACC_005	CC_AMER_CASH_NY_004	BOOK_10	STRAT_05	2024-03-22	41729.32	-8947.39	-438164.41	644304.27
f1735215-f93e-42da-a127-6f667aa4cf70	ACC_006	CC_AMER_CASH_NY_001	BOOK_08	STRAT_02	2024-01-27	87235.45	273074.49	-505835.26	-1413414.75
5e4afdff-ca82-472a-953f-cc306f97c107	ACC_004	CC_AMER_CASH_NY_004	BOOK_01	STRAT_01	2024-04-06	65081.21	66794.15	-491835.83	-1681111.58
cf36d9cd-cdad-4e5f-b308-3db7519111dd	ACC_010	CC_EMEA_INDEX_ARB_010	BOOK_08	STRAT_04	2024-07-09	39784.94	154585.23	1534779.05	718379.84
092e59b9-e77f-4b27-aa11-df25b1a02417	ACC_009	CC_EMEA_INDEX_ARB_008	BOOK_08	STRAT_03	2024-12-05	19600.10	-304766.82	1462148.01	1252464.12
b82711a4-fe7e-4eba-a3d5-44d2e3029573	ACC_003	CC_AMER_CASH_NY_003	BOOK_06	STRAT_02	2024-04-07	30100.94	-453036.12	1583481.35	-977939.09
022dd82d-4d03-4ede-9096-2da26a211f5a	ACC_006	CC_EMEA_INDEX_ARB_008	BOOK_07	STRAT_05	2024-03-28	-49707.13	243956.92	-267010.83	-254451.24
fa489832-74f2-4152-bd9b-6fbdec8b94f9	ACC_004	CC_AMER_PROG_TRADING_007	BOOK_07	STRAT_03	2024-02-08	15704.85	87976.32	-521168.84	-1296126.74
73957736-3aa1-45a7-89bd-bc9f4f0c3340	ACC_007	CC_AMER_CASH_NY_001	BOOK_03	STRAT_05	2024-01-25	-74910.80	151880.75	-966357.61	776293.70
fc88c165-4a07-4e18-872e-b65a02d15446	ACC_010	CC_AMER_CASH_NY_001	BOOK_03	STRAT_05	2024-06-05	30585.43	-430703.66	-646323.29	-553004.08
9c9b69d2-4dd7-4587-9866-aae3bcc14ce7	ACC_002	CC_AMER_PROG_TRADING_005	BOOK_06	STRAT_03	2024-05-15	-11805.85	375293.37	-1223732.26	-116828.61
bb13e343-6747-4ee2-8462-e7d24cc07baf	ACC_002	CC_AMER_PROG_TRADING_005	BOOK_05	STRAT_03	2024-05-13	71562.71	51224.17	1390619.10	1469479.35
d618bddf-1930-42f8-8d85-b79877efa091	ACC_010	CC_APAC_ALGO_G1_013	BOOK_06	STRAT_01	2024-03-30	67621.48	-181739.41	1167360.21	-59732.38
5a36b59c-15a3-4b53-973b-195a2102a766	ACC_002	CC_EMEA_INDEX_ARB_008	BOOK_01	STRAT_02	2024-08-28	45378.50	-294464.97	368436.00	931809.34
59827e31-8158-4243-836c-4a274a3df25a	ACC_010	CC_AMER_CASH_NY_002	BOOK_06	STRAT_02	2024-12-28	-87007.85	-336012.06	1075996.57	543952.25
a4ceee56-9e68-4932-9862-f62a82cf578a	ACC_006	CC_APAC_ALGO_G1_011	BOOK_10	STRAT_01	2024-01-15	-61554.91	-107304.20	861722.29	1438441.80
1ec18fc7-c7ac-4cef-a30e-661d681d12d1	ACC_004	CC_AMER_PROG_TRADING_005	BOOK_09	STRAT_03	2024-01-20	-35620.75	232849.10	1213672.43	-1715499.27
35d041ff-f601-44eb-b5ed-2412dcb024e7	ACC_008	CC_AMER_CASH_NY_002	BOOK_03	STRAT_02	2024-08-19	85735.07	-380708.74	328797.70	-362715.11
ce99db17-4647-41ff-a9eb-943b5071f662	ACC_010	CC_APAC_ALGO_G1_013	BOOK_09	STRAT_02	2024-02-01	-71923.09	-493277.67	1777886.36	-1055973.97
24802d73-b7cf-4eec-b0b5-57efd3a98eba	ACC_004	CC_AMER_CASH_NY_002	BOOK_10	STRAT_04	2024-12-13	-9029.06	221548.52	-928176.28	826555.88
304f4183-234e-406b-a37e-d90f2c15273a	ACC_005	CC_AMER_CASH_NY_001	BOOK_01	STRAT_02	2024-05-16	3498.44	420412.85	247167.78	1464851.31
30d86f77-c974-4c51-a8c3-a4e05b489845	ACC_010	CC_AMER_PROG_TRADING_005	BOOK_07	STRAT_05	2024-01-26	-3022.31	-307519.85	335244.66	-258722.13
ca513611-bc29-420c-a0c4-2702ee29f421	ACC_003	CC_APAC_ALGO_G1_013	BOOK_04	STRAT_03	2024-08-13	-48442.30	343329.83	243644.32	1731144.66
3dd39159-cf81-4c08-a1b8-27e7bfe9150b	ACC_002	CC_EMEA_INDEX_ARB_010	BOOK_05	STRAT_03	2024-06-23	-36837.70	-344937.33	414062.24	-1710370.22
b0f5e3ae-eb22-4b8d-9bfc-780bb2a41e07	ACC_008	CC_APAC_ALGO_G1_013	BOOK_05	STRAT_03	2024-11-12	51942.67	-480750.67	-1185660.24	1552915.95
47464283-6bdf-44dd-8aae-cb1d0f533352	ACC_009	CC_EMEA_INDEX_ARB_010	BOOK_03	STRAT_03	2024-03-16	72562.06	353561.33	-540541.44	693845.09
dc2bc881-ff17-4bd5-8cb6-dd129fd2f957	ACC_003	CC_EMEA_INDEX_ARB_009	BOOK_07	STRAT_02	2024-11-15	-79795.20	448311.93	-337445.90	-662997.44
07e228d8-0f20-4bbd-88e5-af835e345040	ACC_010	CC_AMER_PROG_TRADING_005	BOOK_04	STRAT_02	2024-03-12	-99170.23	-265133.41	815664.22	-1049603.19
dfcdb20c-ff44-46f1-a214-5dde39d6247d	ACC_005	CC_AMER_PROG_TRADING_005	BOOK_02	STRAT_01	2024-04-14	29742.10	-214988.15	-1640236.68	438964.15
d655cabf-da43-4d09-8cb5-8cfc5e6ac093	ACC_005	CC_AMER_PROG_TRADING_005	BOOK_07	STRAT_05	2024-04-02	-66457.29	-312821.17	-712472.24	1069063.45
305cf4c7-2ca2-4cb6-9738-b40a414aee4c	ACC_002	CC_EMEA_INDEX_ARB_009	BOOK_09	STRAT_02	2024-12-29	-36028.37	433813.91	-1177328.14	-1057685.95
5be03352-bb9e-4257-bd04-6293c96d48a5	ACC_009	CC_AMER_PROG_TRADING_007	BOOK_03	STRAT_04	2024-04-28	-83045.54	423143.33	302654.65	-724087.01
716ffd7d-c287-47de-9946-81fbd7f153e6	ACC_004	CC_AMER_CASH_NY_001	BOOK_04	STRAT_02	2024-12-07	63597.87	196320.47	1880070.49	1606652.48
5f6ff7be-f8a8-46b0-a371-7f2ac3221ea9	ACC_001	CC_APAC_ALGO_G1_013	BOOK_04	STRAT_02	2024-03-26	-3455.35	-435335.39	532848.50	1297117.06
af1b8ea0-2e02-45dd-85d7-41fe83ea25c5	ACC_002	CC_AMER_CASH_NY_002	BOOK_08	STRAT_01	2024-11-29	38735.60	209604.87	403870.06	269660.38
ab10d446-0e3e-4d91-b933-dcce1ae99c9f	ACC_007	CC_AMER_PROG_TRADING_007	BOOK_03	STRAT_02	2024-03-27	87463.30	97333.31	1123572.94	-366390.83
d2fb54f9-829e-4d47-857e-fdf878beb1c9	ACC_003	CC_AMER_CASH_NY_001	BOOK_04	STRAT_02	2024-11-12	-4579.66	-58938.11	-1553815.16	1104004.44
7aa59775-e9ee-482e-aacc-3561193d78fd	ACC_003	CC_EMEA_INDEX_ARB_009	BOOK_02	STRAT_01	2024-11-06	69191.75	-212131.21	147295.46	655414.09
1e38e665-0e17-44a1-ace5-d2bba532f507	ACC_008	CC_EMEA_INDEX_ARB_010	BOOK_09	STRAT_05	2024-11-04	91181.80	76099.97	778731.78	1307943.12
e0609bc7-fcc1-4861-ae39-dcbdc3a9b919	ACC_006	CC_AMER_CASH_NY_001	BOOK_05	STRAT_04	2024-08-09	95068.02	209477.62	218078.28	820957.05
90e5eedf-18ab-477f-b9ba-cb827fb0c694	ACC_002	CC_AMER_CASH_NY_002	BOOK_10	STRAT_04	2024-10-14	53118.58	190100.13	-1205104.22	1067381.15
eedb6c36-b690-478e-b5e6-ff0912eaf264	ACC_006	CC_EMEA_INDEX_ARB_009	BOOK_07	STRAT_03	2024-06-02	13742.33	199342.15	667901.28	1637532.17
00764607-2599-42fa-939a-100082c56d09	ACC_007	CC_APAC_ALGO_G1_012	BOOK_06	STRAT_04	2024-07-15	-85712.15	-64281.67	-1397234.48	1271517.44
c41f6fa2-46e0-49e9-b562-6329e8de71bf	ACC_002	CC_EMEA_INDEX_ARB_009	BOOK_08	STRAT_01	2024-07-07	43275.46	408901.78	-1898591.19	-824106.48
b0fb5aca-328b-47ee-9991-82917c00c80c	ACC_003	CC_AMER_CASH_NY_001	BOOK_03	STRAT_04	2024-06-27	6151.60	-176640.13	-329168.62	789698.72
ce9d6c58-6d6b-4dae-8f59-6d3c079f67f6	ACC_005	CC_AMER_CASH_NY_001	BOOK_05	STRAT_01	2024-11-04	-43363.95	-46822.75	-863425.77	432417.31
3b213af1-9d43-46b1-9c1d-e9a6b137eaa8	ACC_003	CC_AMER_CASH_NY_001	BOOK_10	STRAT_03	2024-06-07	30336.90	-266292.90	-1682149.70	864598.81
447734e7-da10-42e8-885d-c01a3c320942	ACC_008	CC_EMEA_INDEX_ARB_008	BOOK_04	STRAT_04	2024-01-18	-74427.01	-368158.80	-1048839.94	593348.40
50ec7027-49c4-4526-86ba-9f1a1fea63f6	ACC_006	CC_APAC_ALGO_G1_011	BOOK_06	STRAT_02	2024-04-19	-39798.26	373457.05	1353309.68	354405.26
0ae3abdf-30c5-4495-bb27-c84833dc137f	ACC_002	CC_APAC_ALGO_G1_011	BOOK_09	STRAT_03	2024-05-03	42370.31	-206564.31	1510766.92	439232.92
38ecfc11-4b22-4ef4-92d5-f3244c485524	ACC_010	CC_AMER_PROG_TRADING_005	BOOK_01	STRAT_05	2024-03-09	94352.45	-344187.69	-149358.33	-1412895.06
aa3f0d56-216e-4390-9847-ba028b5300e6	ACC_007	CC_EMEA_INDEX_ARB_010	BOOK_09	STRAT_01	2024-03-09	63853.07	-223412.68	389704.57	-1422471.84
8c80a683-d183-4e09-9924-66b9ce11b20c	ACC_002	CC_AMER_PROG_TRADING_005	BOOK_08	STRAT_03	2024-05-08	-43958.89	43412.15	-1087711.02	1779127.41
ed97afa6-437a-4afb-a5a1-edeabdd080b6	ACC_006	CC_AMER_CASH_NY_001	BOOK_02	STRAT_05	2024-04-11	72846.36	-9329.95	619895.09	-863233.20
a677e45f-0bb1-464f-a777-886be5ff28bb	ACC_008	CC_EMEA_INDEX_ARB_010	BOOK_04	STRAT_03	2024-05-01	45109.69	-488414.21	-1837466.83	-496942.86
34c8dcaa-15ec-4630-b984-757190421167	ACC_010	CC_AMER_CASH_NY_004	BOOK_07	STRAT_04	2024-07-01	95700.14	199270.05	1425519.29	1153331.23
bf117268-1052-42e9-b34d-93f2f665806c	ACC_008	CC_AMER_CASH_NY_001	BOOK_09	STRAT_04	2024-10-26	96621.96	-170052.44	-1945372.87	-362688.81
0cf54f68-0c64-4abd-8f2b-09aa64252f38	ACC_004	CC_EMEA_INDEX_ARB_009	BOOK_02	STRAT_01	2024-08-28	-27815.40	389258.38	-143238.28	-1084632.19
1213f9cd-946c-410b-8fc1-537a8cc6b1fe	ACC_005	CC_EMEA_INDEX_ARB_010	BOOK_03	STRAT_01	2024-02-26	-71755.92	-50807.82	1349105.51	1047978.08
38c14f3b-00a7-43a3-9561-4484fef4f7fb	ACC_009	CC_EMEA_INDEX_ARB_009	BOOK_07	STRAT_04	2024-02-19	22116.59	257811.24	-1147531.22	-1672537.38
0109bb4a-3a75-4ccf-9ff8-2c9fc5b7187b	ACC_007	CC_AMER_PROG_TRADING_007	BOOK_03	STRAT_04	2024-05-24	-27457.42	-237151.33	1478463.96	1507697.70
7ca2b134-08fb-4228-a280-b55c63563d0c	ACC_006	CC_AMER_PROG_TRADING_005	BOOK_02	STRAT_02	2024-02-03	94265.05	62656.51	-445559.67	-21807.25
c5495958-a44e-4ebd-84cd-ee9077f50fdc	ACC_007	CC_AMER_CASH_NY_002	BOOK_10	STRAT_02	2024-05-12	-15492.27	-244666.27	408035.71	96780.39
49b029f8-abd8-44f9-9942-e819e2d0d379	ACC_003	CC_EMEA_INDEX_ARB_008	BOOK_06	STRAT_01	2024-03-01	45590.19	-142955.65	1432343.24	954157.69
07fd4204-bd8a-4cc3-870d-403775fdf590	ACC_004	CC_EMEA_INDEX_ARB_009	BOOK_06	STRAT_02	2024-12-19	-27239.81	470299.74	-1408415.59	200687.90
a5da3fa1-d91f-4070-880c-8973252b201b	ACC_010	CC_AMER_PROG_TRADING_006	BOOK_07	STRAT_03	2024-04-26	-57096.56	-323897.65	611165.32	-1504809.67
4ce00a7c-b0cc-4a99-864f-acd8808cc4b4	ACC_006	CC_EMEA_INDEX_ARB_008	BOOK_01	STRAT_01	2024-01-01	-79701.12	-132450.19	-1875535.85	-151774.29
86a2a4f8-fa7f-4f44-a21a-c861a2a876b4	ACC_004	CC_AMER_PROG_TRADING_007	BOOK_08	STRAT_02	2024-05-17	79221.86	-8731.02	1461693.08	1119788.09
9029c52a-ff11-400e-ba7a-9d68e7aeae34	ACC_009	CC_AMER_CASH_NY_001	BOOK_05	STRAT_04	2024-03-08	-88898.18	394138.77	437514.23	-821934.12
1d2e15c7-a486-44c6-bd66-f97a732c016c	ACC_003	CC_AMER_CASH_NY_004	BOOK_03	STRAT_01	2024-05-24	-56273.62	-456025.64	1546094.78	183572.75
77b9e956-983e-4ec5-8f12-39a48fa54659	ACC_001	CC_AMER_CASH_NY_004	BOOK_01	STRAT_03	2024-08-18	16033.52	-141210.88	-1711339.79	-906469.88
6bcb33a4-484b-4a48-b667-6eada1f4e8d1	ACC_006	CC_APAC_ALGO_G1_011	BOOK_02	STRAT_03	2024-02-15	41083.77	79453.41	502698.14	446193.02
6855becc-db66-40b5-aea2-4ea8b5bc1b11	ACC_003	CC_EMEA_INDEX_ARB_009	BOOK_03	STRAT_04	2024-01-23	52994.48	-152714.75	1900902.23	-314254.70
ed2c9742-0ea1-4482-9c2f-2749f835d29e	ACC_007	CC_AMER_CASH_NY_002	BOOK_07	STRAT_02	2024-06-30	-18084.01	-458687.42	-920788.93	61690.21
7fd607c9-1a12-47a0-9511-c757a04d9b83	ACC_003	CC_AMER_PROG_TRADING_007	BOOK_01	STRAT_05	2024-07-13	86640.09	-407298.67	-440513.43	-99885.67
e2e6a93e-53cf-452e-aa87-66c7beb753ec	ACC_005	CC_AMER_CASH_NY_003	BOOK_06	STRAT_03	2024-02-22	38698.76	-155261.44	622153.61	1751896.06
dcc36091-45e0-448a-856e-48dbffc32cb8	ACC_002	CC_APAC_ALGO_G1_013	BOOK_01	STRAT_05	2024-01-16	19652.41	83245.95	-1016281.99	1387908.68
db0267ce-411b-40d4-b8cb-dd9df9612f21	ACC_002	CC_AMER_CASH_NY_003	BOOK_07	STRAT_04	2024-02-17	28250.02	133387.93	-1845074.99	-483790.60
d077b567-8806-48b4-affc-1959364a66a0	ACC_004	CC_EMEA_INDEX_ARB_008	BOOK_03	STRAT_03	2024-07-07	49188.27	-187600.24	-593638.19	288460.36
1dae3f4c-c4ed-4746-a5d5-1b22af765f16	ACC_003	CC_APAC_ALGO_G1_013	BOOK_10	STRAT_04	2024-12-21	-36460.86	314487.80	14294.74	329776.62
2983621f-8857-4666-917b-40783e94a4c5	ACC_003	CC_AMER_PROG_TRADING_006	BOOK_03	STRAT_03	2024-04-02	-19992.10	391843.64	259951.14	-701243.15
d3797b5f-1b90-4e42-bf69-56bda771a0a3	ACC_006	CC_AMER_CASH_NY_001	BOOK_08	STRAT_04	2024-12-09	46998.99	78888.03	166318.79	-1119358.12
1abac722-0bc5-4a23-8fa5-fe18109345c4	ACC_006	CC_APAC_ALGO_G1_013	BOOK_07	STRAT_01	2024-12-07	55956.96	-59073.30	-301061.84	-212635.21
090fe594-a349-4090-a72a-aca8a1809a70	ACC_010	CC_EMEA_INDEX_ARB_010	BOOK_08	STRAT_02	2024-11-11	-57041.92	-82742.00	-1979559.71	-1610227.12
ca5d8390-8446-4851-9f83-11cccb939ffb	ACC_006	CC_APAC_ALGO_G1_012	BOOK_02	STRAT_01	2024-12-08	-34460.29	-213719.48	1964695.65	-1571590.60
ac5aea39-8e20-4ae5-b093-0f99e836b314	ACC_010	CC_EMEA_INDEX_ARB_009	BOOK_10	STRAT_02	2024-02-02	-71270.53	490330.64	1303472.85	-17140.17
b7e2cf0c-460a-4860-8d70-3f656d842ede	ACC_003	CC_APAC_ALGO_G1_011	BOOK_09	STRAT_04	2024-03-20	-78613.60	22683.78	171373.33	1048456.44
d7ed7594-bb4a-4e24-996b-0639f2188b73	ACC_004	CC_AMER_CASH_NY_003	BOOK_05	STRAT_03	2024-06-07	-94203.14	-66782.06	408004.28	139134.59
5dc76c5d-41ab-48dc-8259-9ec7fc93a9fb	ACC_006	CC_AMER_CASH_NY_004	BOOK_06	STRAT_03	2024-07-15	70642.67	-104873.28	-1668774.39	-225631.66
a51938c6-1ead-4c65-979d-9eb1a9b5e5c4	ACC_005	CC_AMER_CASH_NY_001	BOOK_04	STRAT_01	2024-09-23	92303.81	36789.95	106420.24	-534856.84
65f9d4f7-4c2c-4f47-a556-d913ed543b0b	ACC_008	CC_AMER_PROG_TRADING_006	BOOK_02	STRAT_02	2024-03-30	11669.24	467855.95	109733.92	570514.65
fd36671a-a199-4b7a-ba48-bb5adb4993c5	ACC_008	CC_AMER_CASH_NY_002	BOOK_06	STRAT_05	2024-01-27	23194.73	-28392.27	-1494856.90	-280663.60
7da77a47-b9d5-4545-a621-d2e39a65820f	ACC_002	CC_APAC_ALGO_G1_013	BOOK_05	STRAT_03	2024-04-10	56096.18	466313.42	495169.86	1546996.30
b6613e46-1ba4-4b0f-bf4b-f4919717d34d	ACC_005	CC_AMER_CASH_NY_004	BOOK_08	STRAT_02	2024-11-29	-77688.86	2908.99	1243590.46	1247759.68
c2350455-6724-4200-938d-7084496452bb	ACC_005	CC_EMEA_INDEX_ARB_009	BOOK_07	STRAT_02	2024-01-21	44451.92	-185056.79	-622366.94	1123032.76
39634e43-398e-4ec6-89d6-6143db20d70e	ACC_004	CC_AMER_CASH_NY_004	BOOK_10	STRAT_05	2024-04-09	-89788.87	-244772.16	-880537.32	826718.91
813c6e5c-c89c-493e-bf8c-be9be6f34f53	ACC_007	CC_AMER_CASH_NY_003	BOOK_09	STRAT_04	2024-10-09	-14780.60	390561.24	-1590328.29	-555105.76
4444ff45-00bd-4bf8-8d57-9d2d4642e626	ACC_005	CC_EMEA_INDEX_ARB_010	BOOK_04	STRAT_01	2024-04-05	-72301.45	-391422.75	174753.81	-253205.06
f1101c70-e232-4a25-93a0-e63ea65a911c	ACC_007	CC_AMER_CASH_NY_003	BOOK_04	STRAT_04	2024-01-10	17647.57	185498.27	365754.80	-1730634.56
750c5a33-3b9c-4087-aff7-5a993ab2ae71	ACC_001	CC_APAC_ALGO_G1_011	BOOK_09	STRAT_03	2024-12-07	-38432.20	24573.95	-1461246.02	-1595906.42
5a14ba69-65d8-4115-ae04-8937adcf1855	ACC_010	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_02	2024-05-29	-79134.83	-132959.17	932392.82	1129396.75
f0e45c4e-c476-4c1c-9d48-c539fb208b3e	ACC_010	CC_AMER_CASH_NY_003	BOOK_09	STRAT_04	2024-02-11	94798.94	67646.72	-982481.33	552799.52
33cbf7dc-8ea8-44cf-a134-e1562aef0548	ACC_010	CC_AMER_PROG_TRADING_006	BOOK_08	STRAT_01	2024-05-29	15958.27	-152538.19	-1112688.72	-980576.11
c787eb9e-f02e-4e60-ab19-c1231b6b680b	ACC_006	CC_AMER_PROG_TRADING_007	BOOK_04	STRAT_01	2024-02-06	4174.27	56.00	-1777365.88	-1199810.67
f83ed6bb-6026-401b-bc39-5a2f73d9ff6d	ACC_006	CC_APAC_ALGO_G1_012	BOOK_02	STRAT_03	2024-10-12	31440.34	-256646.12	-751577.28	1011249.43
e1d65143-e950-4e2e-ad00-9ee8ef0e577e	ACC_007	CC_APAC_ALGO_G1_013	BOOK_01	STRAT_02	2024-10-24	-80541.83	-431556.44	1130827.56	696436.29
5ff182b8-393c-47e9-952e-f7f896d1a697	ACC_002	CC_AMER_CASH_NY_001	BOOK_09	STRAT_02	2024-01-23	-59930.66	-166656.10	1371644.10	1540680.58
1c5687f8-7e84-49e4-8021-31d251a79109	ACC_004	CC_APAC_ALGO_G1_011	BOOK_04	STRAT_05	2024-01-28	47251.87	-265784.43	1742459.53	-39885.92
41051557-7618-455d-bcb0-5511d956a39f	ACC_002	CC_AMER_CASH_NY_004	BOOK_10	STRAT_02	2024-08-01	7862.13	84923.61	-1516492.50	912285.65
004aa793-96ae-483f-afaa-8044b2ffd1d6	ACC_010	CC_EMEA_INDEX_ARB_010	BOOK_02	STRAT_05	2024-08-23	78001.41	420451.63	631189.18	879169.39
e85c4a1b-e0b0-48b5-8c28-65e2e13bb897	ACC_001	CC_EMEA_INDEX_ARB_009	BOOK_07	STRAT_01	2024-03-15	-90169.32	-196471.37	1347606.87	-636144.41
ef8d7a12-fc89-4669-8abf-5674eeab6feb	ACC_008	CC_AMER_CASH_NY_004	BOOK_02	STRAT_04	2024-06-28	48431.17	220188.18	1669142.46	1207728.87
ba1eed4c-c15b-40bd-9a38-4b7f721bc187	ACC_006	CC_AMER_CASH_NY_004	BOOK_10	STRAT_02	2024-03-27	43312.16	59830.36	-471905.43	463592.70
979cfb69-11a2-4e12-9cf2-38934eb5644c	ACC_009	CC_EMEA_INDEX_ARB_010	BOOK_07	STRAT_01	2024-02-06	-21049.13	292235.39	455667.06	-1390270.09
8d2d12b0-3fee-4150-880c-1d279356015e	ACC_009	CC_AMER_CASH_NY_004	BOOK_01	STRAT_05	2024-11-16	79518.77	283680.19	-767925.55	1386144.69
ba0b89ec-58da-4544-9fb2-1e6db12077e2	ACC_002	CC_APAC_ALGO_G1_013	BOOK_09	STRAT_04	2024-04-16	-5253.23	-434955.53	-616615.25	10243.05
0aaa61af-da8d-4723-8b54-ef8a3dd1676c	ACC_008	CC_EMEA_INDEX_ARB_010	BOOK_09	STRAT_04	2024-04-02	98773.61	-431452.86	-454968.20	-247096.72
bab9c83c-86f4-4eda-82ae-f55adbef5802	ACC_004	CC_AMER_CASH_NY_002	BOOK_01	STRAT_04	2024-07-28	10321.34	52785.48	-1289283.39	-1309608.81
2da2aae8-6958-4d72-8f1a-6688027bacec	ACC_005	CC_AMER_CASH_NY_002	BOOK_08	STRAT_03	2024-06-14	-5874.21	-27453.85	-141445.60	783114.11
346e898a-657b-4153-8f6c-2ac2ca129c11	ACC_009	CC_AMER_PROG_TRADING_005	BOOK_03	STRAT_05	2024-12-18	-35799.45	-68328.04	247321.49	1257952.03
1a33f260-1fd1-45f3-bb60-dbfbe79a372e	ACC_005	CC_EMEA_INDEX_ARB_009	BOOK_03	STRAT_04	2024-03-24	50603.88	-35713.84	526856.27	244702.38
532b3a89-efd8-4095-81db-b16140484692	ACC_001	CC_EMEA_INDEX_ARB_008	BOOK_01	STRAT_02	2024-05-15	16144.63	449450.26	299439.94	1449121.04
65cf2bd4-466d-486d-9c05-a8695e0f3977	ACC_003	CC_AMER_CASH_NY_002	BOOK_10	STRAT_04	2024-11-29	-33714.26	-307187.01	-525923.23	-1397780.05
c4ddc911-8fd9-4986-93a3-83cd657d794e	ACC_009	CC_AMER_PROG_TRADING_006	BOOK_09	STRAT_02	2024-03-22	51112.22	-273759.02	250565.77	-714848.38
bc1e9066-f76a-4d93-97b0-6ded7b77c029	ACC_010	CC_AMER_PROG_TRADING_005	BOOK_02	STRAT_03	2024-01-08	11128.65	270012.63	-1644402.61	-934738.80
89f19758-70b3-4c19-8dc6-e350a3ec8d55	ACC_007	CC_AMER_CASH_NY_001	BOOK_09	STRAT_03	2024-11-24	81968.87	138014.66	-1358334.69	-99016.68
40a268e1-f4b9-4041-a7d2-9b5778c875bb	ACC_005	CC_EMEA_INDEX_ARB_009	BOOK_07	STRAT_03	2024-03-20	-38452.48	-347220.63	1820201.22	-1677318.21
852235fe-0958-4b58-aa92-873b1da96c98	ACC_009	CC_AMER_CASH_NY_004	BOOK_06	STRAT_03	2024-02-22	-13363.91	-160012.36	882201.81	1478882.03
802f853f-0c5b-4132-b982-487a9f1b752e	ACC_009	CC_APAC_ALGO_G1_012	BOOK_06	STRAT_04	2024-11-21	21052.87	-465037.04	-1883066.48	820129.12
244f4da4-fc4a-47d8-9eff-c5ff3243378d	ACC_008	CC_AMER_PROG_TRADING_007	BOOK_09	STRAT_03	2024-07-28	33758.72	71279.84	-564264.39	1186279.48
30542996-e202-422a-b3d2-10e4a01db6a3	ACC_003	CC_AMER_CASH_NY_003	BOOK_10	STRAT_04	2024-01-13	-67207.05	-409038.65	1102292.51	695596.62
5192b348-fb93-41fb-a387-d300ce603d30	ACC_008	CC_EMEA_INDEX_ARB_010	BOOK_10	STRAT_04	2024-06-18	-63745.36	-321274.86	1197640.16	1780890.80
c982b51d-e35a-40c0-a9bb-c9533beef8bf	ACC_004	CC_AMER_CASH_NY_001	BOOK_05	STRAT_03	2024-11-03	-51244.91	430303.14	858299.44	-37256.39
337e277c-2550-4c40-9f9b-fb68e98ad2f4	ACC_004	CC_EMEA_INDEX_ARB_008	BOOK_08	STRAT_01	2024-04-22	44697.69	230324.19	1576102.68	1645327.81
52e0f9fa-e5b6-4a2c-9186-9b944fa06ed6	ACC_001	CC_AMER_CASH_NY_001	BOOK_03	STRAT_01	2024-08-27	-78846.27	166718.31	-1919820.69	108740.96
8fd497d6-03f6-439e-8e6c-42c38830d2a6	ACC_002	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_02	2024-05-20	41236.51	-359069.58	1101100.81	-924470.19
d02edcf3-fab8-4066-bf54-a0e32342fce0	ACC_009	CC_AMER_CASH_NY_003	BOOK_07	STRAT_05	2024-02-19	-39659.14	14227.65	465190.68	-1503959.62
19caed7f-a5dd-497f-b700-74634ae8a69e	ACC_009	CC_AMER_PROG_TRADING_006	BOOK_09	STRAT_03	2024-07-23	80136.03	-132783.56	1877555.82	40638.19
c81d3c98-5631-45cc-bbe3-808f9a02a346	ACC_008	CC_AMER_CASH_NY_003	BOOK_03	STRAT_05	2024-07-31	-51525.11	-302199.63	422769.82	1166195.86
c91b95f0-0d4d-4ca9-adfb-41618a228605	ACC_009	CC_APAC_ALGO_G1_011	BOOK_08	STRAT_02	2024-12-18	10859.85	-103650.52	528992.11	-774188.62
c85a90dd-45b0-4e4d-a9ab-d69159fcd08e	ACC_005	CC_APAC_ALGO_G1_012	BOOK_02	STRAT_01	2024-08-13	80782.45	-66324.51	720034.50	-202746.57
97690736-2768-47d1-a997-8e94ef27ac28	ACC_002	CC_EMEA_INDEX_ARB_008	BOOK_05	STRAT_02	2024-07-09	-84657.27	42843.22	-4423.65	1024740.27
ed352a45-c0f0-4e20-8d38-8349a8399d2f	ACC_007	CC_EMEA_INDEX_ARB_010	BOOK_02	STRAT_04	2024-02-15	-84099.22	347011.65	-53792.78	944048.90
184d8191-cac2-4e67-a038-136e3083f3a3	ACC_004	CC_APAC_ALGO_G1_013	BOOK_01	STRAT_02	2024-07-20	11081.25	108821.70	-1566791.04	72665.83
57f1cf4b-2d16-447d-af78-c5c450ad69de	ACC_003	CC_EMEA_INDEX_ARB_009	BOOK_05	STRAT_03	2024-03-16	58335.67	-363548.37	215365.97	-1444270.59
817c672c-6807-4195-9790-9406a10671ee	ACC_004	CC_APAC_ALGO_G1_012	BOOK_06	STRAT_04	2024-11-29	24351.51	-467054.02	1189004.56	1791599.89
c1c63789-5996-4e67-b710-5a8b6269a4e5	ACC_006	CC_APAC_ALGO_G1_011	BOOK_09	STRAT_04	2024-08-07	50278.17	-60552.74	1983153.34	110230.87
85c546c6-319b-44d8-835c-0663df25dfc3	ACC_007	CC_AMER_PROG_TRADING_007	BOOK_01	STRAT_01	2024-04-20	-73377.11	-460165.01	1251348.20	233812.96
63f5dab8-8754-4b5a-8503-8b90c009f031	ACC_009	CC_AMER_PROG_TRADING_007	BOOK_08	STRAT_04	2024-02-29	22284.99	366633.00	659004.90	-1569425.96
322c2da1-62d3-44d4-9a84-3edb5d7bdab6	ACC_004	CC_AMER_PROG_TRADING_006	BOOK_10	STRAT_04	2024-10-16	42267.27	105899.37	221234.98	-896205.20
971d8eaf-4205-495b-94c4-531b70686467	ACC_004	CC_AMER_CASH_NY_001	BOOK_03	STRAT_04	2024-05-30	-86234.95	-232425.63	1417392.63	447635.70
9d60bfb2-d00c-4842-8338-15fc236ffb10	ACC_007	CC_EMEA_INDEX_ARB_010	BOOK_03	STRAT_03	2024-12-04	13610.83	-387960.65	-1588236.72	-287183.46
860f80cd-cc3c-487b-8567-5168894ad080	ACC_005	CC_AMER_PROG_TRADING_006	BOOK_04	STRAT_02	2024-04-17	89136.57	-372384.58	994270.39	-1672234.69
e0aea22b-d46f-4beb-806f-4daea2ff4a44	ACC_007	CC_AMER_CASH_NY_004	BOOK_09	STRAT_01	2024-10-26	4902.33	485592.30	-1291204.64	362246.08
4fca8be4-f190-4597-9531-bcc324f6ad90	ACC_001	CC_AMER_CASH_NY_001	BOOK_06	STRAT_01	2024-01-21	-98149.15	443049.21	-1004368.64	321324.46
903ff165-cab7-4588-b655-963a1d472afd	ACC_010	CC_APAC_ALGO_G1_013	BOOK_09	STRAT_02	2024-01-02	77234.45	151277.49	1265740.38	761910.88
79f13911-f9aa-479c-be72-6dd362cb20cc	ACC_005	CC_APAC_ALGO_G1_011	BOOK_03	STRAT_04	2024-11-28	-45161.69	474305.67	-1940668.63	277706.89
790a9d98-7ad7-40e0-9f7e-0eb7c1a7f3ed	ACC_003	CC_APAC_ALGO_G1_013	BOOK_07	STRAT_01	2024-03-15	-63526.41	-130818.02	1645046.52	-1632939.28
977bc1ba-3d93-4141-81a6-5a096f123e5b	ACC_006	CC_APAC_ALGO_G1_013	BOOK_07	STRAT_02	2024-05-24	-22179.13	439711.93	1472985.53	1298595.69
36ff44db-c847-4e20-9299-00da66fc162b	ACC_008	CC_AMER_CASH_NY_001	BOOK_05	STRAT_03	2024-08-13	-23077.46	-221990.75	-780628.28	1718270.19
28cc24ed-f11c-484c-8dad-bda0577b3fcb	ACC_002	CC_APAC_ALGO_G1_011	BOOK_01	STRAT_01	2024-10-25	-15944.61	-458369.68	-1541774.49	-683130.19
74c697c6-8de6-43d0-bdad-088751f5c388	ACC_007	CC_APAC_ALGO_G1_013	BOOK_03	STRAT_03	2024-08-08	-58108.98	-49406.86	-421194.12	-645349.74
ebcd6d0f-6204-4b55-8329-8d40467455d6	ACC_005	CC_AMER_PROG_TRADING_005	BOOK_03	STRAT_04	2024-08-27	-67244.35	15695.51	-207469.88	-342685.66
cc75d3fa-f6f3-4d4a-8d5b-0becde51f109	ACC_009	CC_AMER_PROG_TRADING_005	BOOK_07	STRAT_04	2024-02-10	-46374.24	-193272.30	1934351.26	-360768.98
d4a61cad-1dc5-4248-9691-64151217de94	ACC_001	CC_AMER_PROG_TRADING_007	BOOK_03	STRAT_02	2024-05-29	84193.88	-342019.74	-1564904.51	382953.10
9773a552-715b-4644-86b4-eca156034479	ACC_002	CC_AMER_PROG_TRADING_006	BOOK_09	STRAT_02	2024-05-31	95346.33	351006.81	-548061.07	-531189.30
1598d8b7-1fed-4484-9104-57c23809fc00	ACC_009	CC_APAC_ALGO_G1_012	BOOK_07	STRAT_05	2024-03-08	-51085.73	-193128.99	1746454.31	-63083.76
d9e2bc5e-46ee-4022-88a3-e0de6fef3ce9	ACC_008	CC_AMER_CASH_NY_001	BOOK_04	STRAT_03	2024-08-07	90078.56	-37951.19	-299119.06	-381519.84
\.


--
-- Data for Name: hierarchy_bridge; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.hierarchy_bridge (bridge_id, parent_node_id, leaf_node_id, structure_id, path_length) FROM stdin;
3e722e5b-c49f-47bd-8e44-05889b75a0bd	ROOT	CC_AMER_CASH_NY_001	MOCK_ATLAS_v1	5
a7b79d34-5d61-4616-a3c3-37c6a0542b12	ROOT	CC_AMER_CASH_NY_002	MOCK_ATLAS_v1	5
8ffd58df-3d53-461a-a016-bd1f90bcd089	ROOT	CC_AMER_CASH_NY_003	MOCK_ATLAS_v1	5
00193b88-9c81-4860-a00e-5697488d855b	ROOT	CC_AMER_CASH_NY_004	MOCK_ATLAS_v1	5
2045f007-c7c0-4e8a-a035-13dd4114fcdc	ROOT	CC_AMER_PROG_TRADING_005	MOCK_ATLAS_v1	5
ca429122-7566-4c40-bd93-307056d9b94a	ROOT	CC_AMER_PROG_TRADING_006	MOCK_ATLAS_v1	5
4efb7250-6b15-47fa-bd14-f1ee17ccec3a	ROOT	CC_AMER_PROG_TRADING_007	MOCK_ATLAS_v1	5
bc11756b-ff5d-46bc-bee5-05d8feee52ef	ROOT	CC_EMEA_INDEX_ARB_008	MOCK_ATLAS_v1	5
df4c0f96-c350-46f0-97fc-def4380b130f	ROOT	CC_EMEA_INDEX_ARB_009	MOCK_ATLAS_v1	5
22e0d5c3-afb9-4bd8-9fdc-74e9d276e389	ROOT	CC_EMEA_INDEX_ARB_010	MOCK_ATLAS_v1	5
5d2f2024-4954-45f3-a646-719bfc6f1b9c	ROOT	CC_APAC_ALGO_G1_011	MOCK_ATLAS_v1	5
4e5d1208-22c9-474b-89e6-3f245c7e205e	ROOT	CC_APAC_ALGO_G1_012	MOCK_ATLAS_v1	5
976e53b8-6f92-4768-b183-3a78425a8e0c	ROOT	CC_APAC_ALGO_G1_013	MOCK_ATLAS_v1	5
34a65cc8-a3e0-4fc8-857b-23deb7a31a42	AMER	CC_AMER_CASH_NY_001	MOCK_ATLAS_v1	4
b37ef4f6-8ca2-4b4e-890b-6c2c15f92157	AMER	CC_AMER_CASH_NY_002	MOCK_ATLAS_v1	4
8baec9f9-0f62-49d1-9ece-b0ad71249d8f	AMER	CC_AMER_CASH_NY_003	MOCK_ATLAS_v1	4
692a15c2-a2ac-47e0-a078-e566e297ead2	AMER	CC_AMER_CASH_NY_004	MOCK_ATLAS_v1	4
801910de-55ca-437f-a4a0-73e647166280	AMER	CC_AMER_PROG_TRADING_005	MOCK_ATLAS_v1	4
ab2d27d6-d977-486f-8041-4f6a4a69f554	AMER	CC_AMER_PROG_TRADING_006	MOCK_ATLAS_v1	4
6dccacec-bcb8-449d-a61d-b64f27a89f2b	AMER	CC_AMER_PROG_TRADING_007	MOCK_ATLAS_v1	4
bfd554a2-c82b-4418-99e0-618d0f9dc76f	AMER	CC_EMEA_INDEX_ARB_008	MOCK_ATLAS_v1	4
32da9f8e-7903-4f35-a8dc-2adbe2709a5c	AMER	CC_EMEA_INDEX_ARB_009	MOCK_ATLAS_v1	4
8caae86d-ca9f-4b6c-8a60-81d630bed240	AMER	CC_EMEA_INDEX_ARB_010	MOCK_ATLAS_v1	4
fb44b1f7-a71e-40f1-9c44-94f46b3cceb4	AMER	CC_APAC_ALGO_G1_011	MOCK_ATLAS_v1	4
a723fb6f-a87c-4814-a705-297d64ebbdf0	AMER	CC_APAC_ALGO_G1_012	MOCK_ATLAS_v1	4
29e09ea2-bc25-40e1-9fdf-85f5ddd85c51	AMER	CC_APAC_ALGO_G1_013	MOCK_ATLAS_v1	4
4e149f5f-0559-4ea2-b69d-1452730c57ba	AMER_CASH_EQUITIES	CC_AMER_CASH_NY_001	MOCK_ATLAS_v1	3
982c4ffb-dd06-4bd5-9137-6dadd58590e5	AMER_CASH_EQUITIES	CC_AMER_CASH_NY_002	MOCK_ATLAS_v1	3
7a71bbca-0fb1-48bf-9d57-a2b24734d405	AMER_CASH_EQUITIES	CC_AMER_CASH_NY_003	MOCK_ATLAS_v1	3
5740b403-d069-41ad-990b-564e6555b5e8	AMER_CASH_EQUITIES	CC_AMER_CASH_NY_004	MOCK_ATLAS_v1	3
128a39c1-f74e-47e8-97a8-6d0b775784f7	AMER_CASH_EQUITIES	CC_AMER_PROG_TRADING_005	MOCK_ATLAS_v1	3
2d4361d3-6637-48f4-839b-9d5e133ce1f1	AMER_CASH_EQUITIES	CC_AMER_PROG_TRADING_006	MOCK_ATLAS_v1	3
9595af89-bbb0-4ba1-b012-20875ba45d50	AMER_CASH_EQUITIES	CC_AMER_PROG_TRADING_007	MOCK_ATLAS_v1	3
1d5ab682-54a6-41f1-9f7a-a4ded28f1077	AMER_CASH_EQUITIES	CC_EMEA_INDEX_ARB_008	MOCK_ATLAS_v1	3
645b2e0d-ba52-41fa-93d9-fb08124f62b1	AMER_CASH_EQUITIES	CC_EMEA_INDEX_ARB_009	MOCK_ATLAS_v1	3
a5286a8b-2c01-406a-8bf4-351a8ca96bf5	AMER_CASH_EQUITIES	CC_EMEA_INDEX_ARB_010	MOCK_ATLAS_v1	3
a99d6dab-6343-4398-b9c5-e6a49da47a8b	AMER_CASH_EQUITIES	CC_APAC_ALGO_G1_011	MOCK_ATLAS_v1	3
e6fc9eee-9abe-4c17-a43a-7b60787cebf5	AMER_CASH_EQUITIES	CC_APAC_ALGO_G1_012	MOCK_ATLAS_v1	3
f8303821-2a40-4d82-9c4a-04e2c3fe02b4	AMER_CASH_EQUITIES	CC_APAC_ALGO_G1_013	MOCK_ATLAS_v1	3
0076bd45-b17f-4eea-98a1-393d5e2d8e92	AMER_CASH_EQUITIES_HIGH_TOUCH	CC_AMER_CASH_NY_001	MOCK_ATLAS_v1	2
a478b5fe-7f50-4a0b-ac22-9ebbf3d3f05d	AMER_CASH_EQUITIES_HIGH_TOUCH	CC_AMER_CASH_NY_002	MOCK_ATLAS_v1	2
07ca914a-665a-4e7c-9eb6-91358e240a13	AMER_CASH_EQUITIES_HIGH_TOUCH	CC_AMER_CASH_NY_003	MOCK_ATLAS_v1	2
f092b52a-5ee7-46a0-a18d-0aae1750ad0f	AMER_CASH_EQUITIES_HIGH_TOUCH	CC_AMER_CASH_NY_004	MOCK_ATLAS_v1	2
3354e915-3215-4c16-a67b-623ce74dbf76	AMER_CASH_EQUITIES_HIGH_TOUCH	CC_AMER_PROG_TRADING_005	MOCK_ATLAS_v1	2
bcd1cf9c-d7d7-453c-97f1-d2643fdc24eb	AMER_CASH_EQUITIES_HIGH_TOUCH	CC_AMER_PROG_TRADING_006	MOCK_ATLAS_v1	2
27b42760-c5f7-4e68-a8ff-73a5af572ce9	AMER_CASH_EQUITIES_HIGH_TOUCH	CC_AMER_PROG_TRADING_007	MOCK_ATLAS_v1	2
9ec001ab-406e-4324-8060-809ceddb9883	AMER_CASH_EQUITIES_HIGH_TOUCH	CC_EMEA_INDEX_ARB_008	MOCK_ATLAS_v1	2
2a5bb6e0-d50e-4569-9fdf-1eabdeffb339	AMER_CASH_EQUITIES_HIGH_TOUCH	CC_EMEA_INDEX_ARB_009	MOCK_ATLAS_v1	2
e0815462-d592-4c2c-a60e-13c36a34826c	AMER_CASH_EQUITIES_HIGH_TOUCH	CC_EMEA_INDEX_ARB_010	MOCK_ATLAS_v1	2
f2e9c5bd-8ece-4e6f-99f2-d8f5e9aeac52	AMER_CASH_EQUITIES_HIGH_TOUCH	CC_APAC_ALGO_G1_011	MOCK_ATLAS_v1	2
ffcfac2d-92eb-4df4-98a9-407f6ea8ced4	AMER_CASH_EQUITIES_HIGH_TOUCH	CC_APAC_ALGO_G1_012	MOCK_ATLAS_v1	2
e612a510-70d4-4af2-952e-5cb967b46fd1	AMER_CASH_EQUITIES_HIGH_TOUCH	CC_APAC_ALGO_G1_013	MOCK_ATLAS_v1	2
c468efbd-58b9-47d1-a6c4-4b705311cc6c	AMER_CASH_NY	CC_AMER_CASH_NY_001	MOCK_ATLAS_v1	1
e87aad16-ef0c-4760-8fb7-ef80873b654f	AMER_CASH_NY	CC_AMER_CASH_NY_002	MOCK_ATLAS_v1	1
64d672ad-e9ae-4e48-aabf-0d4fffb75d10	AMER_CASH_NY	CC_AMER_CASH_NY_003	MOCK_ATLAS_v1	1
af80e73b-0fc7-4fde-a5a8-c74117ca839e	AMER_CASH_NY	CC_AMER_CASH_NY_004	MOCK_ATLAS_v1	1
41f0bd72-bd13-4470-a59c-f80789edc745	AMER_PROG_TRADING	CC_AMER_PROG_TRADING_005	MOCK_ATLAS_v1	1
afaed632-deb8-4620-a3b8-9e543c176073	AMER_PROG_TRADING	CC_AMER_PROG_TRADING_006	MOCK_ATLAS_v1	1
d13722c5-9855-48a1-ab75-c2717433798b	AMER_PROG_TRADING	CC_AMER_PROG_TRADING_007	MOCK_ATLAS_v1	1
022b2c0f-e865-442f-ac98-766b03bff681	EMEA_INDEX_ARB	CC_EMEA_INDEX_ARB_008	MOCK_ATLAS_v1	1
0327fdce-8c6a-44c2-a181-3ac5217864aa	EMEA_INDEX_ARB	CC_EMEA_INDEX_ARB_009	MOCK_ATLAS_v1	1
d234ee66-20af-4f97-837b-1d35a4d1dc78	EMEA_INDEX_ARB	CC_EMEA_INDEX_ARB_010	MOCK_ATLAS_v1	1
ad76760b-e334-4650-a134-f5faa21c537f	APAC_ALGO_G1	CC_APAC_ALGO_G1_011	MOCK_ATLAS_v1	1
8025896d-c088-453c-9842-a8378f86aeab	APAC_ALGO_G1	CC_APAC_ALGO_G1_012	MOCK_ATLAS_v1	1
ef828bb8-ea46-4d4d-9352-fb8b8a7172b2	APAC_ALGO_G1	CC_APAC_ALGO_G1_013	MOCK_ATLAS_v1	1
\.


--
-- Data for Name: history_snapshots; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.history_snapshots (snapshot_id, use_case_id, snapshot_name, snapshot_date, created_by, rules_snapshot, results_snapshot, notes, version_tag) FROM stdin;
\.


--
-- Data for Name: metadata_rules; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.metadata_rules (rule_id, use_case_id, node_id, predicate_json, sql_where, logic_en, last_modified_by, created_at, last_modified_at) FROM stdin;
2	b90f1708-4087-4117-9820-9226ed1115bb	AMER_CASH_NY	{"conditions": [{"field": "book_id", "value": "B_TEST_99", "operator": "equals"}], "conjunction": "AND"}	book_id = 'B_TEST_99'	book_id equals 'B_TEST_99'	user123	2025-12-21 00:04:33.839549	2025-12-21 00:04:33.839549
3	b90f1708-4087-4117-9820-9226ed1115bb	CC_AMER_CASH_NY_002	{"conditions": [{"field": "book_id", "value": "B01", "operator": "not_equals"}], "conjunction": "AND"}	book_id != 'B01'	exclude bookn "B01"	user123	2025-12-21 00:56:18.426333	2025-12-21 00:56:18.426333
4	b90f1708-4087-4117-9820-9226ed1115bb	AMER	{"conditions": [{"field": "strategy_id", "value": "CORE", "operator": "not_equals"}], "conjunction": "AND"}	strategy_id != 'CORE'	Exclude Strategy ='CORE'	user123	2025-12-21 11:21:37.511663	2025-12-21 11:21:37.511663
5	b90f1708-4087-4117-9820-9226ed1115bb	AMER_CASH_EQUITIES	{"conditions": [{"field": "strategy_id", "value": ["S1", "S2", "S3"], "operator": "in"}], "conjunction": "AND"}	strategy_id IN ('S1', 'S2', 'S3')	strategy_id in (S1, S2, S3)	user123	2025-12-21 12:10:42.320647	2025-12-21 12:10:42.320647
39	a26121d8-9e01-4e70-9761-588b1854fe06	AMER_CASH_EQUITIES	{"conditions": [{"field": "strategy_id", "value": ["S1", "S2", "S3"], "operator": "in"}], "conjunction": "AND"}	strategy_id IN ('S1', 'S2', 'S3')	strategy_id in (S1, S2, S3)	user123	2025-12-26 22:23:15.938284	2025-12-26 22:23:15.938284
40	a26121d8-9e01-4e70-9761-588b1854fe06	AMER_CASH_NY	{"conditions": [{"field": "book_id", "value": "B_TEST_99", "operator": "equals"}], "conjunction": "AND"}	book_id = 'B_TEST_99'	book_id equals 'B_TEST_99'	user123	2025-12-26 22:23:15.938284	2025-12-26 22:23:15.938284
41	a26121d8-9e01-4e70-9761-588b1854fe06	CC_AMER_CASH_NY_002	{"conditions": [{"field": "book_id", "value": "B01", "operator": "not_equals"}], "conjunction": "AND"}	book_id != 'B01'	exclude bookn "B01"	user123	2025-12-26 22:23:15.938284	2025-12-26 22:23:15.938284
42	a26121d8-9e01-4e70-9761-588b1854fe06	ROOT	{"conditions": [{"field": "book_id", "value": "B_TEST_99", "operator": "equals"}], "conjunction": "AND"}	book_id = 'B_TEST_99'	book_id equals 'B_TEST_99'	user123	2025-12-26 22:23:15.938284	2025-12-26 22:23:15.938284
38	a26121d8-9e01-4e70-9761-588b1854fe06	AMER	{"conditions": [{"field": "strategy_id", "value": "CORE", "operator": "not_equals"}, {"field": "book_id", "value": ["TEST"], "operator": "not_in"}], "conjunction": "AND"}	strategy_id != 'CORE' AND book_id NOT IN ('TEST')	Exclude Strategy ='CORE' and BOOKS NOT IN TEST	user123	2025-12-26 22:23:15.938284	2025-12-26 22:51:46.453238
43	a26121d8-9e01-4e70-9761-588b1854fe06	CC_AMER_CASH_NY_003	{"conditions": [{"field": "book_id", "value": "TEST123", "operator": "not_equals"}], "conjunction": "AND"}	book_id != 'TEST123'	book_id not equals 'TEST123'	user123	2025-12-26 22:55:42.627131	2025-12-26 22:55:42.627131
44	a26121d8-9e01-4e70-9761-588b1854fe06	AMER_PROG_TRADING	{"conditions": [{"field": "cc_id", "value": "1234", "operator": "not_equals"}], "conjunction": "AND"}	cc_id != '1234'	cc_id not equals '1234'	user123	2025-12-26 22:56:10.288896	2025-12-26 22:56:10.288896
\.


--
-- Data for Name: report_registrations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.report_registrations (report_id, report_name, atlas_structure_id, selected_measures, selected_dimensions, owner_id, created_at, updated_at, measure_scopes, dimension_scopes) FROM stdin;
40a4d840-bc25-45ab-84d1-3ce1b9f2460b	America Desk Reporting POC 2	MOCK_ATLAS_v1	["daily", "mtd", "wtd"]	["product", "strategy", "desk"]	current_user	2025-12-20 13:57:00.22533	2025-12-20 13:57:00.22533	{"mtd": ["input", "rule", "output"], "wtd": ["input", "rule", "output"], "daily": ["input", "rule", "output"]}	{"desk": ["input", "rule", "output"], "product": ["input", "rule", "output"], "strategy": ["input", "rule", "output"]}
3efbe9ce-99ac-4699-b771-d361d53ce27f	America Desk POC	MOCK_ATLAS_v1	["daily", "mtd", "ytd", "wtd"]	["product", "desk", "strategy"]	current_user	2025-12-20 13:17:49.113181	2025-12-21 02:10:38.076988	{"mtd": ["input", "rule", "output"], "wtd": ["input", "output", "rule"], "ytd": ["input", "rule", "output"], "daily": ["input", "rule", "output"]}	{"desk": ["rule", "output", "input"], "product": ["rule", "output", "input"], "strategy": ["rule", "output", "input"]}
639ac744-02e4-42c9-8574-fd5aa8cc2439	America Trading P&L	MOCK_ATLAS_v1	["daily", "mtd", "ytd"]	["region", "product", "desk", "strategy"]	default_user	2025-12-21 17:15:23.697305	2025-12-21 17:15:23.697305	{"mtd": ["input", "rule", "output"], "ytd": ["input", "rule", "output"], "daily": ["input", "rule", "output"]}	{"desk": ["input", "rule", "output"], "region": ["input", "rule", "output"], "product": ["input", "rule", "output"], "strategy": ["input", "rule", "output"]}
\.


--
-- Data for Name: use_case_runs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.use_case_runs (run_id, use_case_id, version_tag, run_timestamp, parameters_snapshot, status, triggered_by, calculation_duration_ms) FROM stdin;
fe305dbd-a064-47ed-82e4-d4a6703d8f96	b90f1708-4087-4117-9820-9226ed1115bb	run_1766296309	2025-12-21 11:21:49.329292	{"rule_ids": [4, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	62
f5ce5535-bd32-43b0-ab97-43968cd39180	b90f1708-4087-4117-9820-9226ed1115bb	run_1766299208	2025-12-21 12:10:08.354665	{"rule_ids": [4, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	50
7b5cafc7-c164-4d8a-8717-f47501bd86f7	b90f1708-4087-4117-9820-9226ed1115bb	run_1766312037	2025-12-21 15:43:57.85561	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	143
14b82eae-70ae-41f3-9da0-2a85d208b166	b90f1708-4087-4117-9820-9226ed1115bb	run_1766314000	2025-12-21 16:16:40.739933	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	82
9fc9d040-3963-4e55-8af0-37f76a93497b	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766581252	2025-12-24 18:30:52.248349	{}	FAILED	system	\N
052dd7f2-80a4-4f96-bfbc-defd9df7a201	b90f1708-4087-4117-9820-9226ed1115bb	run_1766545224	2025-12-24 08:30:24.975017	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	111
14767656-6c4a-48f6-9f74-accd4f168970	b90f1708-4087-4117-9820-9226ed1115bb	run_1766545265	2025-12-24 08:31:05.860165	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	54
f215bdef-c312-4ef5-b87a-79665f402528	b90f1708-4087-4117-9820-9226ed1115bb	run_1766545496	2025-12-24 08:34:56.127729	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	56
acdc8efb-126c-405d-86c5-c558a75cf25b	b90f1708-4087-4117-9820-9226ed1115bb	run_1766545537	2025-12-24 08:35:37.293775	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	48
b5c1b4c1-7832-4edc-a106-1ddaa38c2426	b90f1708-4087-4117-9820-9226ed1115bb	run_1766545558	2025-12-24 08:35:58.074714	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	44
127e85a1-86c3-4a87-a1b0-5350137bc654	b90f1708-4087-4117-9820-9226ed1115bb	run_1766545631	2025-12-24 08:37:11.26282	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	57
c3c48f17-cee5-4e7c-8d05-f8a7173b40aa	b90f1708-4087-4117-9820-9226ed1115bb	run_1766546745	2025-12-24 08:55:45.522911	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	134
843012f0-f06b-4ed9-aa34-5028798116e2	b90f1708-4087-4117-9820-9226ed1115bb	run_1766547800	2025-12-24 09:13:20.001737	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	42
db3eb6c1-913e-45f6-8f42-b6943ab75600	b90f1708-4087-4117-9820-9226ed1115bb	sterling_dummy_20251224	2025-12-24 10:07:27.893753	\N	COMPLETED	sterling_step3	\N
f2f49c89-d3a1-46d4-a69f-7d2093ab2eac	a26121d8-9e01-4e70-9761-588b1854fe06	Sterling_20251224	2025-12-24 10:52:53.76096	\N	COMPLETED	sterling_step3_qa_auditor	\N
9c42b192-9459-4561-96f0-6d02d47da660	a26121d8-9e01-4e70-9761-588b1854fe06	Sterling_20251224	2025-12-24 10:53:33.543143	\N	COMPLETED	sterling_step3_qa_auditor	\N
38965e16-4c85-42f6-af77-bbcd3c13e2a7	a26121d8-9e01-4e70-9761-588b1854fe06	Sterling_20251224	2025-12-24 10:53:48.63943	\N	COMPLETED	sterling_step3_qa_auditor	\N
8eb341e3-1d18-48d9-95f2-cf0515100454	a26121d8-9e01-4e70-9761-588b1854fe06	Sterling_20251224	2025-12-24 10:54:09.129284	\N	COMPLETED	sterling_step3_qa_auditor	\N
08f477c7-4eb0-4627-b19f-c8941ba51854	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766562527	2025-12-24 13:18:47.502475	{}	IN_PROGRESS	system	\N
d5439ea9-7cca-4a06-a373-a99244432aea	b90f1708-4087-4117-9820-9226ed1115bb	run_1766562538	2025-12-24 13:18:58.1341	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	119
e907b32f-7d97-4fec-b0a2-db5ef6b26a7f	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766562696	2025-12-24 13:21:36.836792	{}	IN_PROGRESS	system	\N
2fa70f34-7bf0-4113-b22b-02ea8d609ead	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766562997	2025-12-24 13:26:37.796132	{}	FAILED	system	\N
98e94b48-cfb2-41ed-81fd-277aeaf74010	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766563504	2025-12-24 13:35:04.321793	{}	FAILED	system	\N
18047c5f-c015-4e8e-8487-f871b296366e	b90f1708-4087-4117-9820-9226ed1115bb	run_1766581187	2025-12-24 18:29:47.624931	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	197
251fc308-78e9-4f02-a978-2d93a3e916b2	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766581352	2025-12-24 18:32:32.39875	{}	FAILED	system	\N
194cc4ec-45a0-4b96-80cb-be4122661b18	b90f1708-4087-4117-9820-9226ed1115bb	run_1766581520	2025-12-24 18:35:20.093136	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	65
06465daa-0743-42de-ad87-3b609c39124c	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766581527	2025-12-24 18:35:27.129567	{}	FAILED	system	\N
2344e561-b5a7-4739-bf99-03361ebba56e	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766582312	2025-12-24 18:48:32.464711	{}	FAILED	system	\N
a0a721a4-2ac0-4d7f-90f8-6f17e5b43846	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766582339	2025-12-24 18:48:59.925846	{}	FAILED	system	\N
f52ab584-889d-4dd3-a23c-1c1ab0aab482	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766582548	2025-12-24 18:52:28.883265	{}	FAILED	system	\N
2cde40aa-c4ac-435e-95b6-8038e3821fca	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766582567	2025-12-24 18:52:47.81831	{}	FAILED	system	\N
87981ee2-707b-4788-8540-6c353a53e994	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766582975	2025-12-24 18:59:35.845702	{}	FAILED	system	\N
ccab7ae7-eaf0-43e4-9012-1c4ac84884b0	b90f1708-4087-4117-9820-9226ed1115bb	run_1766582992	2025-12-24 18:59:52.475451	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	55
3f10b4ed-6b75-4033-84fd-d14c2ff2abc0	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766582998	2025-12-24 18:59:58.296108	{}	FAILED	system	\N
5d3a580e-0a18-4926-b2c3-a6a91b87b0f8	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766583217	2025-12-24 19:03:37.129491	{}	FAILED	system	\N
f2830355-2d4a-432f-96aa-0bf24ef70ca1	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766583239	2025-12-24 19:03:59.034852	{}	FAILED	system	\N
9dcccaf3-b31f-412a-adfa-6cd97b4ccd6e	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766583599	2025-12-24 19:09:59.185793	{}	FAILED	system	\N
0f52366c-311c-460f-a541-d5887f62d9b3	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766583633	2025-12-24 19:10:33.583982	{}	FAILED	system	\N
1276ce56-6165-46bc-af47-1d58453c10ed	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766583962	2025-12-24 19:16:02.510013	{}	FAILED	system	\N
9768cb77-ddaa-4281-b516-785cb806c5d7	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766584035	2025-12-24 19:17:15.4914	{}	FAILED	system	\N
370499cf-fabf-492f-82dd-07aa710036f7	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766584211	2025-12-24 19:20:11.329246	{}	FAILED	system	\N
9453eeef-9a24-4414-b1a4-06132c643373	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766584426	2025-12-24 19:23:46.493826	{}	FAILED	system	\N
4a52fb08-b5f2-4e4a-bb6e-bf92c48b5cb9	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766584547	2025-12-24 19:25:47.25198	{}	FAILED	system	\N
c5255455-8207-46a3-8f8e-19e802dd913d	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766584889	2025-12-24 19:31:29.872381	{}	FAILED	system	\N
6304d59c-ecfc-49d8-8195-01535a074d4e	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766584980	2025-12-24 19:33:00.449945	{}	FAILED	system	\N
4f8e3c90-0f0d-4029-bbe3-71e599f8e466	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766585197	2025-12-24 19:36:37.846216	{}	FAILED	system	\N
6e3b771f-5cde-4d2c-9980-48e34ec50ada	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766585934	2025-12-24 19:48:54.221089	{}	FAILED	system	\N
5665eeda-66ef-4e0d-9bf6-fad2e64dd5c4	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766586398	2025-12-24 19:56:38.485887	{}	FAILED	system	\N
d62f6fb4-667d-411d-ad62-2e919f70f697	b90f1708-4087-4117-9820-9226ed1115bb	run_1766586413	2025-12-24 19:56:53.95865	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	142
7c7aea14-97c7-4abe-a188-fb36721b83d4	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766586420	2025-12-24 19:57:00.297693	{}	FAILED	system	\N
25eab13c-742b-4266-8965-cd65ed5a0d02	b90f1708-4087-4117-9820-9226ed1115bb	run_1766586513	2025-12-24 19:58:33.905251	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	140
39052ce2-304e-44fb-bba2-8487161de67a	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766586973	2025-12-24 20:06:13.434843	{"rule_ids": [28, 29, 30, 31, 32, 33, 34, 35, 36, 37], "num_nodes": 21, "num_results": 21, "rules_applied": 0}	COMPLETED	system	134
6f3c8ddb-1914-4dd3-bba9-5ff74e7291ee	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766592403	2025-12-24 21:36:43.945579	{"rule_ids": [28, 29, 30, 31, 32, 33, 34, 35, 36, 37], "num_nodes": 21, "num_results": 21, "rules_applied": 0}	COMPLETED	system	93
cd2d0419-9ff5-4bfc-8037-6eaa238fc3d1	b90f1708-4087-4117-9820-9226ed1115bb	run_1766592410	2025-12-24 21:36:50.198066	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	98
3b484679-d759-444d-b9fc-bf58d7ee4802	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766765121	2025-12-26 21:35:21.717434	{"rule_ids": [28, 29, 30, 31, 32, 33, 34, 35, 36, 37], "num_nodes": 21, "num_results": 21, "rules_applied": 0}	COMPLETED	system	112
0989025d-a103-45a6-8e1e-12939ac26bfc	b90f1708-4087-4117-9820-9226ed1115bb	run_1766765134	2025-12-26 21:35:34.099094	{"rule_ids": [4, 5, 2, 3, 1], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	217
a03e7003-b41b-4587-994e-75b790fb7667	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766765482	2025-12-26 21:41:22.363025	{"rule_ids": [28, 29, 30, 31, 32, 33, 34, 35, 36, 37], "num_nodes": 21, "num_results": 21, "rules_applied": 0}	COMPLETED	system	220
e4e23be7-66e1-4389-ba9d-4ca2ca5b7fd7	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766766525	2025-12-26 21:58:45.270632	{"rule_ids": [28, 29, 30, 31, 32, 33, 34, 35, 36, 37], "num_nodes": 21, "num_results": 21, "rules_applied": 0}	COMPLETED	system	92
1bafc99d-ef4c-4644-86f7-5b67b57f2045	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766766611	2025-12-26 22:00:11.546343	{"rule_ids": [28, 29, 30, 31, 32, 33, 34, 35, 36, 37], "num_nodes": 21, "num_results": 21, "rules_applied": 0}	COMPLETED	system	147
469f8f88-c7d8-4d32-9a0b-4264aad6ba03	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766767490	2025-12-26 22:14:50.507841	{"rule_ids": [28, 29, 30, 31, 32, 33, 34, 35, 36, 37], "num_nodes": 21, "num_results": 21, "rules_applied": 0}	COMPLETED	system	89
7b9c4bd2-7d1d-437a-b68a-615f5ae05e42	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766768305	2025-12-26 22:28:25.368177	{"rule_ids": [38, 39, 40, 41, 42], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	134
e1a1364c-00ce-403c-8f2e-01423af9c471	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766768383	2025-12-26 22:29:43.872169	{"rule_ids": [38, 39, 40, 41, 42], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	79
e8581cc4-7b61-418a-a31c-5e57846e42ee	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766769573	2025-12-26 22:49:33.878595	{"rule_ids": [38, 39, 40, 41, 42], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	73
9ad67223-cd8e-4e8d-8dd2-94e624953806	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766769722	2025-12-26 22:52:02.452793	{"rule_ids": [38, 39, 40, 41, 42], "num_nodes": 21, "num_results": 21, "rules_applied": 1}	COMPLETED	system	69
6a44256b-45b2-4e3c-b555-e93ccf2b1f00	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766770016	2025-12-26 22:56:56.580572	{"rule_ids": [38, 39, 40, 44, 41, 43, 42], "num_nodes": 21, "num_results": 21, "rules_applied": 3}	COMPLETED	system	95
80d4d457-c260-47eb-8186-4eeb20ce7e2c	a26121d8-9e01-4e70-9761-588b1854fe06	run_1766770036	2025-12-26 22:57:16.353506	{"rule_ids": [38, 39, 40, 44, 41, 43, 42], "num_nodes": 21, "num_results": 21, "rules_applied": 3}	COMPLETED	system	144
\.


--
-- Data for Name: use_cases; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.use_cases (use_case_id, name, description, owner_id, atlas_structure_id, status, created_at) FROM stdin;
b90f1708-4087-4117-9820-9226ed1115bb	America Trading P&L	TEST	default_user	MOCK_ATLAS_v1	ACTIVE	2025-12-20 12:16:43.025063
a26121d8-9e01-4e70-9761-588b1854fe06	Project Sterling - Multi-Dimensional Facts	High-complexity dataset for F2B testing with multi-measure waterfall calibration	sterling_import	MOCK_ATLAS_v1	ACTIVE	2025-12-24 09:58:18.223779
\.


--
-- Name: metadata_rules_rule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.metadata_rules_rule_id_seq', 44, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: calculation_runs calculation_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calculation_runs
    ADD CONSTRAINT calculation_runs_pkey PRIMARY KEY (id);


--
-- Name: dim_dictionary dim_dictionary_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_dictionary
    ADD CONSTRAINT dim_dictionary_pkey PRIMARY KEY (id);


--
-- Name: dim_hierarchy dim_hierarchy_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_hierarchy
    ADD CONSTRAINT dim_hierarchy_pkey PRIMARY KEY (node_id);


--
-- Name: fact_calculated_results fact_calculated_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_calculated_results
    ADD CONSTRAINT fact_calculated_results_pkey PRIMARY KEY (result_id);


--
-- Name: fact_pnl_entries fact_pnl_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_pnl_entries
    ADD CONSTRAINT fact_pnl_entries_pkey PRIMARY KEY (id);


--
-- Name: fact_pnl_gold fact_pnl_gold_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_pnl_gold
    ADD CONSTRAINT fact_pnl_gold_pkey PRIMARY KEY (fact_id);


--
-- Name: hierarchy_bridge hierarchy_bridge_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hierarchy_bridge
    ADD CONSTRAINT hierarchy_bridge_pkey PRIMARY KEY (bridge_id);


--
-- Name: history_snapshots history_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.history_snapshots
    ADD CONSTRAINT history_snapshots_pkey PRIMARY KEY (snapshot_id);


--
-- Name: metadata_rules metadata_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metadata_rules
    ADD CONSTRAINT metadata_rules_pkey PRIMARY KEY (rule_id);


--
-- Name: report_registrations report_registrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_registrations
    ADD CONSTRAINT report_registrations_pkey PRIMARY KEY (report_id);


--
-- Name: dim_dictionary uq_category_tech_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_dictionary
    ADD CONSTRAINT uq_category_tech_id UNIQUE (category, tech_id);


--
-- Name: metadata_rules uq_use_case_node; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metadata_rules
    ADD CONSTRAINT uq_use_case_node UNIQUE (use_case_id, node_id);


--
-- Name: use_case_runs use_case_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.use_case_runs
    ADD CONSTRAINT use_case_runs_pkey PRIMARY KEY (run_id);


--
-- Name: use_cases use_cases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.use_cases
    ADD CONSTRAINT use_cases_pkey PRIMARY KEY (use_case_id);


--
-- Name: ix_calculation_runs_date_use_case; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_calculation_runs_date_use_case ON public.calculation_runs USING btree (pnl_date, use_case_id);


--
-- Name: ix_calculation_runs_pnl_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_calculation_runs_pnl_date ON public.calculation_runs USING btree (pnl_date);


--
-- Name: ix_calculation_runs_use_case_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_calculation_runs_use_case_id ON public.calculation_runs USING btree (use_case_id);


--
-- Name: ix_dim_dictionary_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dim_dictionary_category ON public.dim_dictionary USING btree (category);


--
-- Name: ix_dim_dictionary_tech_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dim_dictionary_tech_id ON public.dim_dictionary USING btree (tech_id);


--
-- Name: ix_fact_calculated_results_calc_run_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_fact_calculated_results_calc_run_id ON public.fact_calculated_results USING btree (calculation_run_id);


--
-- Name: ix_fact_pnl_entries_pnl_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_fact_pnl_entries_pnl_date ON public.fact_pnl_entries USING btree (pnl_date);


--
-- Name: ix_fact_pnl_entries_scenario; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_fact_pnl_entries_scenario ON public.fact_pnl_entries USING btree (scenario);


--
-- Name: ix_fact_pnl_entries_use_case_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_fact_pnl_entries_use_case_id ON public.fact_pnl_entries USING btree (use_case_id);


--
-- Name: calculation_runs calculation_runs_use_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calculation_runs
    ADD CONSTRAINT calculation_runs_use_case_id_fkey FOREIGN KEY (use_case_id) REFERENCES public.use_cases(use_case_id) ON DELETE CASCADE;


--
-- Name: dim_hierarchy dim_hierarchy_parent_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_hierarchy
    ADD CONSTRAINT dim_hierarchy_parent_node_id_fkey FOREIGN KEY (parent_node_id) REFERENCES public.dim_hierarchy(node_id);


--
-- Name: fact_calculated_results fact_calculated_results_calculation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_calculated_results
    ADD CONSTRAINT fact_calculated_results_calculation_run_id_fkey FOREIGN KEY (calculation_run_id) REFERENCES public.calculation_runs(id) ON DELETE CASCADE;


--
-- Name: fact_calculated_results fact_calculated_results_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_calculated_results
    ADD CONSTRAINT fact_calculated_results_node_id_fkey FOREIGN KEY (node_id) REFERENCES public.dim_hierarchy(node_id);


--
-- Name: fact_calculated_results fact_calculated_results_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_calculated_results
    ADD CONSTRAINT fact_calculated_results_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.use_case_runs(run_id) ON DELETE CASCADE;


--
-- Name: fact_pnl_entries fact_pnl_entries_use_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_pnl_entries
    ADD CONSTRAINT fact_pnl_entries_use_case_id_fkey FOREIGN KEY (use_case_id) REFERENCES public.use_cases(use_case_id) ON DELETE CASCADE;


--
-- Name: hierarchy_bridge hierarchy_bridge_leaf_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hierarchy_bridge
    ADD CONSTRAINT hierarchy_bridge_leaf_node_id_fkey FOREIGN KEY (leaf_node_id) REFERENCES public.dim_hierarchy(node_id);


--
-- Name: hierarchy_bridge hierarchy_bridge_parent_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hierarchy_bridge
    ADD CONSTRAINT hierarchy_bridge_parent_node_id_fkey FOREIGN KEY (parent_node_id) REFERENCES public.dim_hierarchy(node_id);


--
-- Name: history_snapshots history_snapshots_use_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.history_snapshots
    ADD CONSTRAINT history_snapshots_use_case_id_fkey FOREIGN KEY (use_case_id) REFERENCES public.use_cases(use_case_id);


--
-- Name: metadata_rules metadata_rules_node_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metadata_rules
    ADD CONSTRAINT metadata_rules_node_id_fkey FOREIGN KEY (node_id) REFERENCES public.dim_hierarchy(node_id);


--
-- Name: metadata_rules metadata_rules_use_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metadata_rules
    ADD CONSTRAINT metadata_rules_use_case_id_fkey FOREIGN KEY (use_case_id) REFERENCES public.use_cases(use_case_id) ON DELETE CASCADE;


--
-- Name: use_case_runs use_case_runs_use_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.use_case_runs
    ADD CONSTRAINT use_case_runs_use_case_id_fkey FOREIGN KEY (use_case_id) REFERENCES public.use_cases(use_case_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict O58z81XQDnROhSkDDJqIGDTRMAXoriubZiqn09kdKXUnO2E9rVLAWOJXvRoM67X

