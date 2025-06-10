--
-- PostgreSQL database dump
--

-- Dumped from database version 15.4 (Debian 15.4-1.pgdg110+1)
-- Dumped by pg_dump version 15.4 (Debian 15.4-1.pgdg110+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: tiger; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA tiger;


ALTER SCHEMA tiger OWNER TO postgres;

--
-- Name: tiger_data; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA tiger_data;


ALTER SCHEMA tiger_data OWNER TO postgres;

--
-- Name: topology; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA topology;


ALTER SCHEMA topology OWNER TO postgres;

--
-- Name: SCHEMA topology; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA topology IS 'PostGIS Topology schema';


--
-- Name: fuzzystrmatch; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;


--
-- Name: EXTENSION fuzzystrmatch; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION fuzzystrmatch IS 'determine similarities and distance between strings';


--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: postgis_tiger_geocoder; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder WITH SCHEMA tiger;


--
-- Name: EXTENSION postgis_tiger_geocoder; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_tiger_geocoder IS 'PostGIS tiger geocoder and reverse geocoder';


--
-- Name: postgis_topology; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;


--
-- Name: EXTENSION postgis_topology; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_topology IS 'PostGIS topology spatial types and functions';


--
-- Name: get_database_stats(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_database_stats() RETURNS TABLE(table_name text, row_count bigint, size_pretty text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname||'.'||tablename::TEXT as table_name,
        n_live_tup::BIGINT as row_count,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_pretty
    FROM pg_stat_user_tables
    ORDER BY n_live_tup DESC;
END;
$$;


ALTER FUNCTION public.get_database_stats() OWNER TO postgres;

--
-- Name: refresh_road_statistics(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.refresh_road_statistics() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY road_statistics;
END;
$$;


ALTER FUNCTION public.refresh_road_statistics() OWNER TO postgres;

--
-- Name: search_roads(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.search_roads(search_term text, limit_count integer DEFAULT 100) RETURNS TABLE(linearid character varying, fullname text, road_category character varying, county_fips character varying, state_code character varying, similarity real)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.linearid,
        r.fullname,
        r.road_category,
        r.county_fips,
        r.state_code,
        similarity(r.fullname, search_term) AS similarity
    FROM roads r
    WHERE r.fullname % search_term  -- trigram similarity
    ORDER BY similarity DESC
    LIMIT limit_count;
END;
$$;


ALTER FUNCTION public.search_roads(search_term text, limit_count integer) OWNER TO postgres;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: businesses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.businesses (
    id integer NOT NULL,
    place_id character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    address text,
    latitude numeric(10,8),
    longitude numeric(11,8),
    rating numeric(2,1),
    user_ratings_total integer,
    types text[],
    phone character varying(50),
    website text,
    opening_hours jsonb,
    price_level integer,
    road_linearid character varying(22),
    county_fips character(5),
    state_code character(2),
    crawled_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.businesses OWNER TO postgres;

--
-- Name: businesses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.businesses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.businesses_id_seq OWNER TO postgres;

--
-- Name: businesses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.businesses_id_seq OWNED BY public.businesses.id;


--
-- Name: cities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cities (
    city_id integer NOT NULL,
    city_name character varying(100) NOT NULL,
    state_code character(2) NOT NULL,
    county_fips character(5),
    population integer,
    geom public.geometry(Point,4326),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.cities OWNER TO postgres;

--
-- Name: cities_city_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.cities_city_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cities_city_id_seq OWNER TO postgres;

--
-- Name: cities_city_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.cities_city_id_seq OWNED BY public.cities.city_id;


--
-- Name: city_counties; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.city_counties (
    city_id integer NOT NULL,
    county_fips character varying(5) NOT NULL
);


ALTER TABLE public.city_counties OWNER TO postgres;

--
-- Name: roads; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roads (
    id bigint NOT NULL,
    linearid character varying(22) NOT NULL,
    fullname character varying(100),
    rttyp character varying(1),
    mtfcc character varying(5),
    state_code character(2) NOT NULL,
    county_fips character(5) NOT NULL,
    geom public.geometry(LineString,4326),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    road_category character varying(20)
);


ALTER TABLE public.roads OWNER TO postgres;

--
-- Name: city_roads; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.city_roads AS
 SELECT c.city_name,
    c.state_code,
    r.linearid,
    r.fullname,
    r.rttyp,
    r.mtfcc,
    r.road_category,
    r.county_fips,
    r.geom
   FROM ((public.roads r
     JOIN public.city_counties cc ON ((r.county_fips = (cc.county_fips)::bpchar)))
     JOIN public.cities c ON ((cc.city_id = c.city_id)));


ALTER TABLE public.city_roads OWNER TO postgres;

--
-- Name: counties; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.counties (
    county_fips character(5) NOT NULL,
    county_name character varying(100) NOT NULL,
    state_code character(2) NOT NULL,
    total_roads integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.counties OWNER TO postgres;

--
-- Name: crawl_status; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.crawl_status (
    id integer NOT NULL,
    county_fips character(5) NOT NULL,
    total_roads integer DEFAULT 0,
    crawled_roads integer DEFAULT 0,
    total_businesses integer DEFAULT 0,
    status character varying(20) DEFAULT 'pending'::character varying,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.crawl_status OWNER TO postgres;

--
-- Name: crawl_status_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.crawl_status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.crawl_status_id_seq OWNER TO postgres;

--
-- Name: crawl_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.crawl_status_id_seq OWNED BY public.crawl_status.id;


--
-- Name: states; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.states (
    state_code character(2) NOT NULL,
    state_name character varying(100) NOT NULL,
    total_roads integer DEFAULT 0,
    total_counties integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.states OWNER TO postgres;

--
-- Name: road_statistics; Type: MATERIALIZED VIEW; Schema: public; Owner: postgres
--

CREATE MATERIALIZED VIEW public.road_statistics AS
 SELECT s.state_code,
    s.state_name,
    count(DISTINCT c.county_fips) AS county_count,
    count(r.id) AS total_roads,
    count(
        CASE
            WHEN ((r.road_category)::text = 'Primary Roads'::text) THEN 1
            ELSE NULL::integer
        END) AS primary_roads,
    count(
        CASE
            WHEN ((r.road_category)::text = 'Secondary Roads'::text) THEN 1
            ELSE NULL::integer
        END) AS secondary_roads,
    count(
        CASE
            WHEN ((r.road_category)::text = 'Local Streets'::text) THEN 1
            ELSE NULL::integer
        END) AS local_streets,
    count(
        CASE
            WHEN ((r.road_category)::text = 'Special Roads'::text) THEN 1
            ELSE NULL::integer
        END) AS special_roads,
    count(
        CASE
            WHEN (r.fullname IS NOT NULL) THEN 1
            ELSE NULL::integer
        END) AS roads_with_names,
    count(
        CASE
            WHEN (r.fullname IS NULL) THEN 1
            ELSE NULL::integer
        END) AS roads_without_names
   FROM ((public.states s
     LEFT JOIN public.counties c ON ((s.state_code = c.state_code)))
     LEFT JOIN public.roads r ON ((c.county_fips = r.county_fips)))
  GROUP BY s.state_code, s.state_name
  WITH NO DATA;


ALTER TABLE public.road_statistics OWNER TO postgres;

--
-- Name: roads_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.roads_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.roads_id_seq OWNER TO postgres;

--
-- Name: roads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.roads_id_seq OWNED BY public.roads.id;


--
-- Name: businesses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.businesses ALTER COLUMN id SET DEFAULT nextval('public.businesses_id_seq'::regclass);


--
-- Name: cities city_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cities ALTER COLUMN city_id SET DEFAULT nextval('public.cities_city_id_seq'::regclass);


--
-- Name: crawl_status id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.crawl_status ALTER COLUMN id SET DEFAULT nextval('public.crawl_status_id_seq'::regclass);


--
-- Name: roads id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roads ALTER COLUMN id SET DEFAULT nextval('public.roads_id_seq'::regclass);


--
-- Name: businesses businesses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.businesses
    ADD CONSTRAINT businesses_pkey PRIMARY KEY (id);


--
-- Name: businesses businesses_place_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.businesses
    ADD CONSTRAINT businesses_place_id_key UNIQUE (place_id);


--
-- Name: cities cities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT cities_pkey PRIMARY KEY (city_id);


--
-- Name: city_counties city_counties_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.city_counties
    ADD CONSTRAINT city_counties_pkey PRIMARY KEY (city_id, county_fips);


--
-- Name: counties counties_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.counties
    ADD CONSTRAINT counties_pkey PRIMARY KEY (county_fips);


--
-- Name: crawl_status crawl_status_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.crawl_status
    ADD CONSTRAINT crawl_status_pkey PRIMARY KEY (id);


--
-- Name: roads roads_linearid_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roads
    ADD CONSTRAINT roads_linearid_unique UNIQUE (linearid);


--
-- Name: roads roads_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roads
    ADD CONSTRAINT roads_pkey PRIMARY KEY (id);


--
-- Name: states states_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.states
    ADD CONSTRAINT states_pkey PRIMARY KEY (state_code);


--
-- Name: idx_businesses_county; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_businesses_county ON public.businesses USING btree (county_fips);


--
-- Name: idx_businesses_location; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_businesses_location ON public.businesses USING btree (latitude, longitude);


--
-- Name: idx_businesses_name_trgm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_businesses_name_trgm ON public.businesses USING gin (name public.gin_trgm_ops);


--
-- Name: idx_businesses_road; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_businesses_road ON public.businesses USING btree (road_linearid);


--
-- Name: idx_businesses_state; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_businesses_state ON public.businesses USING btree (state_code);


--
-- Name: idx_crawl_status_county; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_crawl_status_county ON public.crawl_status USING btree (county_fips);


--
-- Name: idx_crawl_status_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_crawl_status_status ON public.crawl_status USING btree (status);


--
-- Name: idx_road_statistics_state; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_road_statistics_state ON public.road_statistics USING btree (state_code);


--
-- Name: idx_roads_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_roads_category ON public.roads USING btree (road_category);


--
-- Name: idx_roads_county; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_roads_county ON public.roads USING btree (county_fips);


--
-- Name: idx_roads_fullname; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_roads_fullname ON public.roads USING btree (fullname);


--
-- Name: idx_roads_fullname_lower; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_roads_fullname_lower ON public.roads USING btree (lower((fullname)::text));


--
-- Name: idx_roads_fullname_trgm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_roads_fullname_trgm ON public.roads USING gin (fullname public.gin_trgm_ops);


--
-- Name: idx_roads_geom; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_roads_geom ON public.roads USING gist (geom);


--
-- Name: idx_roads_linearid; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_roads_linearid ON public.roads USING btree (linearid);


--
-- Name: idx_roads_state; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_roads_state ON public.roads USING btree (state_code);


--
-- Name: businesses update_businesses_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_businesses_updated_at BEFORE UPDATE ON public.businesses FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: cities update_cities_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_cities_updated_at BEFORE UPDATE ON public.cities FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: counties update_counties_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_counties_updated_at BEFORE UPDATE ON public.counties FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: crawl_status update_crawl_status_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_crawl_status_updated_at BEFORE UPDATE ON public.crawl_status FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: states update_states_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_states_updated_at BEFORE UPDATE ON public.states FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: businesses businesses_county_fips_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.businesses
    ADD CONSTRAINT businesses_county_fips_fkey FOREIGN KEY (county_fips) REFERENCES public.counties(county_fips);


--
-- Name: businesses businesses_state_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.businesses
    ADD CONSTRAINT businesses_state_code_fkey FOREIGN KEY (state_code) REFERENCES public.states(state_code);


--
-- Name: cities cities_county_fips_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT cities_county_fips_fkey FOREIGN KEY (county_fips) REFERENCES public.counties(county_fips);


--
-- Name: cities cities_state_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT cities_state_code_fkey FOREIGN KEY (state_code) REFERENCES public.states(state_code);


--
-- Name: city_counties city_counties_city_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.city_counties
    ADD CONSTRAINT city_counties_city_id_fkey FOREIGN KEY (city_id) REFERENCES public.cities(city_id);


--
-- Name: city_counties city_counties_county_fips_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.city_counties
    ADD CONSTRAINT city_counties_county_fips_fkey FOREIGN KEY (county_fips) REFERENCES public.counties(county_fips);


--
-- Name: counties counties_state_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.counties
    ADD CONSTRAINT counties_state_code_fkey FOREIGN KEY (state_code) REFERENCES public.states(state_code);


--
-- Name: crawl_status crawl_status_county_fips_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.crawl_status
    ADD CONSTRAINT crawl_status_county_fips_fkey FOREIGN KEY (county_fips) REFERENCES public.counties(county_fips);


--
-- Name: roads roads_county_fips_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roads
    ADD CONSTRAINT roads_county_fips_fkey FOREIGN KEY (county_fips) REFERENCES public.counties(county_fips);


--
-- Name: roads roads_state_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roads
    ADD CONSTRAINT roads_state_code_fkey FOREIGN KEY (state_code) REFERENCES public.states(state_code);


--
-- Name: businesses Enable read access for all; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Enable read access for all" ON public.businesses FOR SELECT USING (true);


--
-- Name: cities Enable read access for all; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Enable read access for all" ON public.cities FOR SELECT USING (true);


--
-- Name: counties Enable read access for all; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Enable read access for all" ON public.counties FOR SELECT USING (true);


--
-- Name: roads Enable read access for all; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Enable read access for all" ON public.roads FOR SELECT USING (true);


--
-- Name: states Enable read access for all; Type: POLICY; Schema: public; Owner: postgres
--

CREATE POLICY "Enable read access for all" ON public.states FOR SELECT USING (true);


--
-- Name: businesses; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.businesses ENABLE ROW LEVEL SECURITY;

--
-- Name: cities; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.cities ENABLE ROW LEVEL SECURITY;

--
-- Name: counties; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.counties ENABLE ROW LEVEL SECURITY;

--
-- Name: roads; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.roads ENABLE ROW LEVEL SECURITY;

--
-- Name: states; Type: ROW SECURITY; Schema: public; Owner: postgres
--

ALTER TABLE public.states ENABLE ROW LEVEL SECURITY;

--
-- PostgreSQL database dump complete
--

