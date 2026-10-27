--
-- PostgreSQL database dump
--


-- Dumped from database version 16.15 (Debian 16.15-1.pgdg13+2)
-- Dumped by pg_dump version 16.15 (Debian 16.15-1.pgdg13+2)

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
-- Name: gender; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.gender AS ENUM (
    'male',
    'female',
    'other'
);


--
-- Name: interestedin; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.interestedin AS ENUM (
    'male',
    'female',
    'everyone'
);


--
-- Name: swipetype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.swipetype AS ENUM (
    'like',
    'pass_',
    'super_like'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversations (
    conversation_id integer NOT NULL,
    user1_id integer NOT NULL,
    user2_id integer NOT NULL,
    last_message_id integer,
    user1_seen boolean NOT NULL,
    user2_seen boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: conversations_conversation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.conversations_conversation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: conversations_conversation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.conversations_conversation_id_seq OWNED BY public.conversations.conversation_id;


--
-- Name: messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.messages (
    message_id integer NOT NULL,
    conversation_id integer NOT NULL,
    sender_id integer NOT NULL,
    content character varying(1000) NOT NULL,
    is_read boolean NOT NULL,
    reply_to_id integer,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: messages_message_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.messages_message_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: messages_message_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.messages_message_id_seq OWNED BY public.messages.message_id;


--
-- Name: swipes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.swipes (
    swipe_id integer NOT NULL,
    from_user_id integer NOT NULL,
    to_user_id integer NOT NULL,
    swipe_type public.swipetype NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: swipes_swipe_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.swipes_swipe_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: swipes_swipe_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.swipes_swipe_id_seq OWNED BY public.swipes.swipe_id;


--
-- Name: user_blocks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_blocks (
    id integer NOT NULL,
    blocker_id integer NOT NULL,
    blocked_id integer NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: user_blocks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_blocks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_blocks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_blocks_id_seq OWNED BY public.user_blocks.id;


--
-- Name: user_images; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_images (
    image_id integer NOT NULL,
    user_id integer NOT NULL,
    image_key character varying(255) NOT NULL,
    "position" integer NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: user_images_image_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_images_image_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_images_image_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_images_image_id_seq OWNED BY public.user_images.image_id;


--
-- Name: user_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_reports (
    id integer NOT NULL,
    reporter_id integer NOT NULL,
    reported_id integer NOT NULL,
    reason character varying(100) NOT NULL,
    message text,
    status character varying(20) NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: user_reports_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_reports_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_reports_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_reports_id_seq OWNED BY public.user_reports.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    first_name character varying(50) NOT NULL,
    last_name character varying(50) NOT NULL,
    email character varying(255) NOT NULL,
    password character varying(255),
    auth_provider character varying(20) NOT NULL,
    oauth_id character varying(255),
    country character varying(2) NOT NULL,
    birthdate date,
    bio character varying(500) NOT NULL,
    gender public.gender NOT NULL,
    interested_in public.interestedin NOT NULL,
    interests character varying[] NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: conversations conversation_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations ALTER COLUMN conversation_id SET DEFAULT nextval('public.conversations_conversation_id_seq'::regclass);


--
-- Name: messages message_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages ALTER COLUMN message_id SET DEFAULT nextval('public.messages_message_id_seq'::regclass);


--
-- Name: swipes swipe_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.swipes ALTER COLUMN swipe_id SET DEFAULT nextval('public.swipes_swipe_id_seq'::regclass);


--
-- Name: user_blocks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_blocks ALTER COLUMN id SET DEFAULT nextval('public.user_blocks_id_seq'::regclass);


--
-- Name: user_images image_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_images ALTER COLUMN image_id SET DEFAULT nextval('public.user_images_image_id_seq'::regclass);


--
-- Name: user_reports id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_reports ALTER COLUMN id SET DEFAULT nextval('public.user_reports_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (conversation_id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (message_id);


--
-- Name: swipes swipes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.swipes
    ADD CONSTRAINT swipes_pkey PRIMARY KEY (swipe_id);


--
-- Name: swipes uq_swipe_pair; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.swipes
    ADD CONSTRAINT uq_swipe_pair UNIQUE (from_user_id, to_user_id);


--
-- Name: user_blocks uq_user_block; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_blocks
    ADD CONSTRAINT uq_user_block UNIQUE (blocker_id, blocked_id);


--
-- Name: user_blocks user_blocks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_blocks
    ADD CONSTRAINT user_blocks_pkey PRIMARY KEY (id);


--
-- Name: user_images user_images_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_images
    ADD CONSTRAINT user_images_pkey PRIMARY KEY (image_id);


--
-- Name: user_reports user_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_reports
    ADD CONSTRAINT user_reports_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: ix_conversations_user1_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conversations_user1_id ON public.conversations USING btree (user1_id);


--
-- Name: ix_conversations_user2_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conversations_user2_id ON public.conversations USING btree (user2_id);


--
-- Name: ix_messages_conversation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_messages_conversation_id ON public.messages USING btree (conversation_id);


--
-- Name: ix_messages_sender_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_messages_sender_id ON public.messages USING btree (sender_id);


--
-- Name: ix_swipes_from_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_swipes_from_user_id ON public.swipes USING btree (from_user_id);


--
-- Name: ix_swipes_to_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_swipes_to_user_id ON public.swipes USING btree (to_user_id);


--
-- Name: ix_user_blocks_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_blocks_id ON public.user_blocks USING btree (id);


--
-- Name: ix_user_images_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_images_user_id ON public.user_images USING btree (user_id);


--
-- Name: ix_user_reports_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_reports_id ON public.user_reports USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: uq_conversation_pair; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_conversation_pair ON public.conversations USING btree (LEAST(user1_id, user2_id), GREATEST(user1_id, user2_id));


--
-- Name: conversations conversations_last_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_last_message_id_fkey FOREIGN KEY (last_message_id) REFERENCES public.messages(message_id) ON DELETE SET NULL;


--
-- Name: conversations conversations_user1_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user1_id_fkey FOREIGN KEY (user1_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: conversations conversations_user2_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user2_id_fkey FOREIGN KEY (user2_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: messages messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(conversation_id) ON DELETE CASCADE;


--
-- Name: messages messages_reply_to_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_reply_to_id_fkey FOREIGN KEY (reply_to_id) REFERENCES public.messages(message_id) ON DELETE SET NULL;


--
-- Name: messages messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: swipes swipes_from_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.swipes
    ADD CONSTRAINT swipes_from_user_id_fkey FOREIGN KEY (from_user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: swipes swipes_to_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.swipes
    ADD CONSTRAINT swipes_to_user_id_fkey FOREIGN KEY (to_user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: user_blocks user_blocks_blocked_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_blocks
    ADD CONSTRAINT user_blocks_blocked_id_fkey FOREIGN KEY (blocked_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: user_blocks user_blocks_blocker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_blocks
    ADD CONSTRAINT user_blocks_blocker_id_fkey FOREIGN KEY (blocker_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: user_images user_images_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_images
    ADD CONSTRAINT user_images_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: user_reports user_reports_reported_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_reports
    ADD CONSTRAINT user_reports_reported_id_fkey FOREIGN KEY (reported_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: user_reports user_reports_reporter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_reports
    ADD CONSTRAINT user_reports_reporter_id_fkey FOREIGN KEY (reporter_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--


