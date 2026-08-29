--
-- PostgreSQL database dump
--

\restrict FRmmLTG34hxW2xEULrribONWaelCyGBnZLTBDFbB0GdIQmxu5JhGfZuIEgGZob8

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

--
-- Name: unaccent; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;


--
-- Name: EXTENSION unaccent; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION unaccent IS 'text search dictionary that removes accents';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: condicao_equipamento; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.condicao_equipamento AS ENUM (
    'excelente',
    'boa',
    'regular',
    'ruim',
    'inservivel'
);


--
-- Name: perfil_usuario; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.perfil_usuario AS ENUM (
    'administrador',
    'gestor_secretaria',
    'manutencao',
    'coordenador',
    'administrativo',
    'profissional'
);


--
-- Name: prioridade_chamado; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.prioridade_chamado AS ENUM (
    'baixa',
    'media',
    'alta',
    'urgente'
);


--
-- Name: status_chamado; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.status_chamado AS ENUM (
    'aberto',
    'em_andamento',
    'aguardando_peca',
    'concluido',
    'cancelado'
);


--
-- Name: status_contrato; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.status_contrato AS ENUM (
    'vigente',
    'a_vencer',
    'vencido'
);


--
-- Name: status_equipamento; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.status_equipamento AS ENUM (
    'ativo',
    'em_manutencao',
    'baixado'
);


--
-- Name: status_unidade; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.status_unidade AS ENUM (
    'ativa',
    'inativa'
);


--
-- Name: tipo_campo; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.tipo_campo AS ENUM (
    'texto',
    'numero',
    'selecao',
    'data',
    'booleano',
    'texto_longo'
);


--
-- Name: tipo_chamado; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.tipo_chamado AS ENUM (
    'predial',
    'equipamento',
    'tecnologia',
    'contratual',
    'outro'
);


--
-- Name: tipo_unidade; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.tipo_unidade AS ENUM (
    'UBS',
    'USF',
    'UPA',
    'PA',
    'CAPS',
    'CEO',
    'Policlinica',
    'Outro'
);


--
-- Name: set_atualizado_em(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_atualizado_em() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: acao_planejamento_empresas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.acao_planejamento_empresas (
    acao_id integer CONSTRAINT acacao_empresas_acao_id_not_null NOT NULL,
    empresa_id integer CONSTRAINT acacao_empresas_empresa_id_not_null NOT NULL
);


--
-- Name: acao_planejamento_responsaveis; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.acao_planejamento_responsaveis (
    acao_id integer CONSTRAINT acacao_responsaveis_acao_id_not_null NOT NULL,
    usuario_id integer CONSTRAINT acacao_responsaveis_usuario_id_not_null NOT NULL
);


--
-- Name: acoes_planejamento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.acoes_planejamento (
    id integer CONSTRAINT acoes_plano_id_not_null NOT NULL,
    planejamento_id integer CONSTRAINT acoes_plano_plano_id_not_null NOT NULL,
    titulo character varying(300) CONSTRAINT acoes_plano_titulo_not_null NOT NULL,
    descricao text,
    status character varying(20) DEFAULT 'backlog'::character varying CONSTRAINT acoes_plano_status_not_null NOT NULL,
    ordem integer DEFAULT 0 CONSTRAINT acoes_plano_ordem_not_null NOT NULL,
    criado_por integer,
    criado_em timestamp without time zone DEFAULT CURRENT_TIMESTAMP CONSTRAINT acoes_plano_criado_em_not_null NOT NULL,
    prazo date
);


--
-- Name: acoes_planejamento_obs_anexos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.acoes_planejamento_obs_anexos (
    id integer CONSTRAINT acoes_plano_obs_anexos_id_not_null NOT NULL,
    observacao_id integer CONSTRAINT acoes_plano_obs_anexos_observacao_id_not_null NOT NULL,
    filename character varying(200) CONSTRAINT acoes_plano_obs_anexos_filename_not_null NOT NULL,
    original character varying(200) CONSTRAINT acoes_plano_obs_anexos_original_not_null NOT NULL,
    mime_type character varying(100)
);


--
-- Name: acoes_planejamento_observacoes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.acoes_planejamento_observacoes (
    id integer CONSTRAINT acoes_plano_observacoes_id_not_null NOT NULL,
    acao_id integer CONSTRAINT acoes_plano_observacoes_acao_id_not_null NOT NULL,
    usuario_id integer,
    texto text CONSTRAINT acoes_plano_observacoes_texto_not_null NOT NULL,
    criado_em timestamp without time zone DEFAULT CURRENT_TIMESTAMP CONSTRAINT acoes_plano_observacoes_criado_em_not_null NOT NULL
);


--
-- Name: acoes_plano_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.acoes_plano_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: acoes_plano_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.acoes_plano_id_seq OWNED BY public.acoes_planejamento.id;


--
-- Name: acoes_plano_obs_anexos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.acoes_plano_obs_anexos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: acoes_plano_obs_anexos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.acoes_plano_obs_anexos_id_seq OWNED BY public.acoes_planejamento_obs_anexos.id;


--
-- Name: acoes_plano_observacoes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.acoes_plano_observacoes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: acoes_plano_observacoes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.acoes_plano_observacoes_id_seq OWNED BY public.acoes_planejamento_observacoes.id;


--
-- Name: andamento_anexos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.andamento_anexos (
    id integer NOT NULL,
    andamento_id integer NOT NULL,
    filename character varying(200) NOT NULL,
    original character varying(200),
    mime_type character varying(80),
    tamanho_bytes integer,
    criado_em timestamp without time zone NOT NULL
);


--
-- Name: andamento_anexos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.andamento_anexos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: andamento_anexos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.andamento_anexos_id_seq OWNED BY public.andamento_anexos.id;


--
-- Name: auditoria; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auditoria (
    id integer NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    usuario_id integer,
    acao character varying(50),
    modulo character varying(80),
    endpoint character varying(200),
    url character varying(500),
    method character varying(10),
    parametros jsonb,
    entity_type character varying(80),
    entity_id integer,
    ip_address character varying(45),
    user_agent character varying(500),
    response_status integer,
    detalhes text
);


--
-- Name: auditoria_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auditoria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auditoria_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auditoria_id_seq OWNED BY public.auditoria.id;


--
-- Name: campos_tipo_equipamento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.campos_tipo_equipamento (
    id integer NOT NULL,
    tipo_equipamento_id integer NOT NULL,
    nome_campo character varying(100) NOT NULL,
    tipo_dado character varying(30) DEFAULT 'texto'::public.tipo_campo NOT NULL,
    obrigatorio boolean DEFAULT false NOT NULL,
    opcoes_selecao jsonb,
    ordem integer DEFAULT 0,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    campo_destaque boolean DEFAULT false NOT NULL
);


--
-- Name: campos_tipo_equipamento_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.campos_tipo_equipamento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: campos_tipo_equipamento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.campos_tipo_equipamento_id_seq OWNED BY public.campos_tipo_equipamento.id;


--
-- Name: chamado_fotos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chamado_fotos (
    id integer NOT NULL,
    chamado_id integer NOT NULL,
    filename character varying(200) NOT NULL,
    original character varying(200),
    mime_type character varying(80),
    criado_em timestamp without time zone NOT NULL
);


--
-- Name: chamado_fotos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chamado_fotos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chamado_fotos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chamado_fotos_id_seq OWNED BY public.chamado_fotos.id;


--
-- Name: chamado_historico; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chamado_historico (
    id integer NOT NULL,
    chamado_id integer NOT NULL,
    usuario_id integer,
    acao character varying(200) NOT NULL,
    observacao text,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    tipo_andamento character varying(30) DEFAULT 'andamento'::character varying NOT NULL,
    requer_resposta boolean DEFAULT false NOT NULL,
    respondido_em timestamp without time zone,
    contrato_id integer
);


--
-- Name: chamado_historico_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chamado_historico_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chamado_historico_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chamado_historico_id_seq OWNED BY public.chamado_historico.id;


--
-- Name: chamados; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chamados (
    id integer NOT NULL,
    numero character varying(20) NOT NULL,
    unidade_id integer NOT NULL,
    sala_id integer,
    equipamento_id integer,
    tipo_chamado character varying(20) DEFAULT 'equipamento'::public.tipo_chamado NOT NULL,
    titulo character varying(200) NOT NULL,
    descricao text NOT NULL,
    prioridade character varying(20) DEFAULT 'media'::public.prioridade_chamado NOT NULL,
    status character varying(20) DEFAULT 'aberto'::public.status_chamado NOT NULL,
    aberto_por integer NOT NULL,
    responsavel_id integer,
    setor_id integer,
    observacao_conclusao text,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp without time zone DEFAULT now() NOT NULL,
    fechado_em timestamp without time zone,
    predio_id integer,
    bp_num_patrimonio character varying(60),
    bp_nome_equip character varying(200),
    bp_fabricante_modelo character varying(200),
    bp_num_serie character varying(100),
    bp_categoria character varying(30),
    bp_servico character varying(20),
    bp_problema_em character varying(20),
    bp_rechamado boolean DEFAULT false,
    bp_data_rechamado date
);


--
-- Name: chamados_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chamados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chamados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chamados_id_seq OWNED BY public.chamados.id;


--
-- Name: contrato_acoes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contrato_acoes (
    id integer NOT NULL,
    contrato_id integer NOT NULL,
    tipo character varying(50) NOT NULL,
    data_acao date NOT NULL,
    observacao text,
    periodo_dias integer,
    nova_data_fim date,
    valor_adicional numeric(14,2),
    porcentagem_adicional numeric(6,2),
    porcentagem_multa numeric(6,2),
    anexo_filename character varying(200),
    criado_por integer,
    criado_em timestamp without time zone NOT NULL,
    periodo_meses integer
);


--
-- Name: contrato_acoes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contrato_acoes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contrato_acoes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contrato_acoes_id_seq OWNED BY public.contrato_acoes.id;


--
-- Name: contrato_equipamentos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contrato_equipamentos (
    id integer NOT NULL,
    contrato_id integer NOT NULL,
    equipamento_id integer NOT NULL,
    descricao_cobertura text
);


--
-- Name: contrato_equipamentos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contrato_equipamentos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contrato_equipamentos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contrato_equipamentos_id_seq OWNED BY public.contrato_equipamentos.id;


--
-- Name: contrato_financeiro; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contrato_financeiro (
    id integer NOT NULL,
    tipo character varying(50),
    processo character varying(100),
    motivo character varying(80),
    prestador character varying(200),
    objeto text,
    referencia character varying(150),
    valor_total numeric(14,2),
    especializada character varying(100),
    vigilancia character varying(100),
    atencao_basica character varying(100),
    outros character varying(100),
    tabela_sus character varying(100),
    complemento character varying(150),
    emenda_municipal character varying(100),
    emenda_estadual character varying(100),
    emenda_federal character varying(100),
    observacao text,
    data_necessaria date,
    data_envio_divisao date,
    data_envio_fms date,
    data_devolucao_setor date,
    reservas character varying(200),
    criado_em timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    contrato_id integer
);


--
-- Name: contrato_financeiro_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contrato_financeiro_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contrato_financeiro_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contrato_financeiro_id_seq OWNED BY public.contrato_financeiro.id;


--
-- Name: contrato_tipos_equipamento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contrato_tipos_equipamento (
    id integer NOT NULL,
    contrato_id integer NOT NULL,
    tipo_equipamento_id integer NOT NULL,
    descricao_cobertura text,
    marca_id integer,
    modelo_id integer
);


--
-- Name: contrato_tipos_equipamento_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contrato_tipos_equipamento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contrato_tipos_equipamento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contrato_tipos_equipamento_id_seq OWNED BY public.contrato_tipos_equipamento.id;


--
-- Name: contratos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contratos (
    id integer NOT NULL,
    numero_sei character varying(100),
    empresa character varying(200),
    tipo_contrato character varying(100),
    objeto text,
    data_inicio date NOT NULL,
    data_fim date NOT NULL,
    valor_total numeric(14,2),
    status character varying(20) DEFAULT 'vigente'::public.status_contrato NOT NULL,
    observacoes text,
    criado_por integer,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp without time zone DEFAULT now() NOT NULL,
    empresa_id integer,
    cpl character varying(30),
    link_sei character varying(500),
    modalidade character varying(80),
    secao character varying(100),
    numero_contrato character varying(50),
    data_assinatura date,
    vigencia character varying(100),
    fonte character varying(150),
    valor_inicial numeric(14,2),
    valor_atual numeric(14,2),
    valor_mensal_atual numeric(14,2),
    aditivo_data_pct character varying(200),
    reajuste_data_base_pct character varying(200),
    fiscalizacao character varying(200),
    supressao_data_pct character varying(200),
    contato_nome_telefone character varying(300),
    empenhos text,
    tag character varying(80),
    mandado_judicial boolean DEFAULT false
);


--
-- Name: contratos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contratos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contratos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contratos_id_seq OWNED BY public.contratos.id;


--
-- Name: divisoes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.divisoes (
    id integer NOT NULL,
    nome character varying(150) NOT NULL,
    descricao text,
    tipos_chamado json,
    tipos_unidade_ids json,
    ativo boolean NOT NULL,
    criado_em timestamp without time zone NOT NULL
);


--
-- Name: divisoes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.divisoes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: divisoes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.divisoes_id_seq OWNED BY public.divisoes.id;


--
-- Name: documentos_transferencia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documentos_transferencia (
    id integer NOT NULL,
    tipo character varying(20) NOT NULL,
    unidade_origem_id integer NOT NULL,
    unidade_destino_id integer NOT NULL,
    criado_por integer,
    aceito_por integer,
    sala_destino_id integer,
    status character varying(20) NOT NULL,
    observacao text,
    observacao_aceite text,
    criado_em timestamp without time zone NOT NULL,
    resolvido_em timestamp without time zone
);


--
-- Name: documentos_transferencia_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.documentos_transferencia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: documentos_transferencia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.documentos_transferencia_id_seq OWNED BY public.documentos_transferencia.id;


--
-- Name: empresas_contratadas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.empresas_contratadas (
    id integer NOT NULL,
    cnpj character varying(18) NOT NULL,
    razao_social character varying(255) NOT NULL,
    nome_comum character varying(150),
    telefone character varying(30),
    email character varying(150),
    logo_filename character varying(200),
    ativo boolean NOT NULL,
    criado_em timestamp without time zone NOT NULL,
    atualizado_em timestamp without time zone NOT NULL,
    endereco text,
    email_suporte character varying(150),
    telefone_suporte character varying(30),
    logradouro character varying(200),
    numero character varying(20),
    complemento character varying(100),
    bairro character varying(100),
    cidade character varying(100),
    estado character varying(2),
    cep character varying(10)
);


--
-- Name: empresas_contratadas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.empresas_contratadas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: empresas_contratadas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.empresas_contratadas_id_seq OWNED BY public.empresas_contratadas.id;


--
-- Name: equipamento_campo_valores; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.equipamento_campo_valores (
    id integer NOT NULL,
    equipamento_id integer NOT NULL,
    campo_id integer NOT NULL,
    valor text
);


--
-- Name: equipamento_campo_valores_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.equipamento_campo_valores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: equipamento_campo_valores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.equipamento_campo_valores_id_seq OWNED BY public.equipamento_campo_valores.id;


--
-- Name: equipamento_usuarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.equipamento_usuarios (
    id integer NOT NULL,
    equipamento_id integer NOT NULL,
    usuario_id integer NOT NULL,
    observacao character varying(200),
    vinculado_em timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: equipamento_usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.equipamento_usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: equipamento_usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.equipamento_usuarios_id_seq OWNED BY public.equipamento_usuarios.id;


--
-- Name: equipamentos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.equipamentos (
    id integer NOT NULL,
    sala_id integer NOT NULL,
    tipo_equipamento_id integer NOT NULL,
    numero_patrimonio character varying(80),
    numero_serie character varying(150),
    marca_id integer,
    modelo_id integer,
    data_aquisicao date,
    valor_estimado numeric(12,2),
    tempo_uso_anos numeric(5,1),
    status character varying(20) DEFAULT 'ativo'::public.status_equipamento NOT NULL,
    condicao character varying(20) DEFAULT 'boa'::public.condicao_equipamento NOT NULL,
    observacoes text,
    ativo boolean DEFAULT true NOT NULL,
    criado_por integer,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: equipamentos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.equipamentos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: equipamentos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.equipamentos_id_seq OWNED BY public.equipamentos.id;


--
-- Name: faltas_abonadas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.faltas_abonadas (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    unidade_id integer,
    data_falta date NOT NULL,
    funcao character varying(200) NOT NULL,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    criado_por integer,
    status character varying(20) DEFAULT 'ativa'::character varying NOT NULL,
    motivo_cancelamento text,
    cancelado_em timestamp without time zone,
    cancelado_por integer
);


--
-- Name: faltas_abonadas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.faltas_abonadas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: faltas_abonadas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.faltas_abonadas_id_seq OWNED BY public.faltas_abonadas.id;


--
-- Name: ficha_cnes_vinculo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ficha_cnes_vinculo (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    unidade_id integer NOT NULL,
    tipo character varying(20) DEFAULT 'cadastro'::character varying NOT NULL,
    vinculo character varying(1),
    tipo_vinculo character varying(1),
    carga_horaria smallint,
    cbo character varying(10),
    especialidade_residencia character varying(200),
    dt_entrada_unidade date,
    cns_profissional character varying(20),
    observacoes text,
    gerado_por integer,
    gerado_em timestamp without time zone DEFAULT now() NOT NULL,
    emails_enviados boolean DEFAULT false NOT NULL,
    cnpj_empresa character varying(20),
    nome_empresa character varying(200)
);


--
-- Name: ficha_cnes_vinculo_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ficha_cnes_vinculo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ficha_cnes_vinculo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ficha_cnes_vinculo_id_seq OWNED BY public.ficha_cnes_vinculo.id;


--
-- Name: historico_equipamento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.historico_equipamento (
    id integer NOT NULL,
    equipamento_id integer NOT NULL,
    usuario_id integer,
    acao character varying(300) NOT NULL,
    observacao text,
    criado_em timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: historico_equipamento_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.historico_equipamento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: historico_equipamento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.historico_equipamento_id_seq OWNED BY public.historico_equipamento.id;


--
-- Name: itens_documento_transferencia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.itens_documento_transferencia (
    id integer NOT NULL,
    documento_id integer NOT NULL,
    equipamento_id integer,
    quantidade integer NOT NULL,
    descricao character varying(500),
    classificacao character varying(1) NOT NULL,
    numero_patrimonio character varying(80),
    numero_serie character varying(150)
);


--
-- Name: itens_documento_transferencia_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.itens_documento_transferencia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: itens_documento_transferencia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.itens_documento_transferencia_id_seq OWNED BY public.itens_documento_transferencia.id;


--
-- Name: itens_lojinha; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.itens_lojinha (
    id integer NOT NULL,
    unidade_id integer NOT NULL,
    equipamento_id integer,
    quantidade integer NOT NULL,
    descricao character varying(500),
    classificacao character varying(1) NOT NULL,
    numero_patrimonio character varying(80),
    numero_serie character varying(150),
    criado_por integer,
    criado_em timestamp without time zone NOT NULL,
    ativo boolean NOT NULL
);


--
-- Name: itens_lojinha_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.itens_lojinha_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: itens_lojinha_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.itens_lojinha_id_seq OWNED BY public.itens_lojinha.id;


--
-- Name: links_uteis; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.links_uteis (
    id integer NOT NULL,
    nome character varying(150) NOT NULL,
    descricao character varying(300),
    url character varying(500),
    imagem_url character varying(500),
    icone character varying(60),
    nova_aba boolean NOT NULL,
    ativo boolean NOT NULL,
    ordem integer NOT NULL,
    perfis_acesso json NOT NULL,
    criado_por integer,
    criado_em timestamp without time zone NOT NULL,
    atualizado_em timestamp without time zone NOT NULL,
    imagem_path character varying(300),
    tipo_link_id integer
);


--
-- Name: links_uteis_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.links_uteis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: links_uteis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.links_uteis_id_seq OWNED BY public.links_uteis.id;


--
-- Name: marca_tipo_equipamento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.marca_tipo_equipamento (
    marca_id integer NOT NULL,
    tipo_equipamento_id integer NOT NULL
);


--
-- Name: marcas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.marcas (
    id integer NOT NULL,
    nome character varying(100) NOT NULL,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: marcas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.marcas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: marcas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.marcas_id_seq OWNED BY public.marcas.id;


--
-- Name: matriculas_profissionais; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.matriculas_profissionais (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    numero character varying(50) NOT NULL,
    vinculo character varying(1),
    tipo_vinculo character varying(1),
    cbo character varying(10),
    reg_conselho character varying(30),
    orgao_emissor character varying(50),
    ativo boolean DEFAULT true NOT NULL,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: matriculas_profissionais_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.matriculas_profissionais_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: matriculas_profissionais_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.matriculas_profissionais_id_seq OWNED BY public.matriculas_profissionais.id;


--
-- Name: modelos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.modelos (
    id integer NOT NULL,
    marca_id integer,
    nome character varying(150) NOT NULL,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    tipo_equipamento_id integer,
    atualizado_em timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: modelos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.modelos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: modelos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.modelos_id_seq OWNED BY public.modelos.id;


--
-- Name: notificacoes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notificacoes (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    tipo character varying(30) NOT NULL,
    titulo character varying(200) NOT NULL,
    texto text,
    chamado_id integer,
    lida boolean NOT NULL,
    criado_em timestamp without time zone NOT NULL
);


--
-- Name: notificacoes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.notificacoes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: notificacoes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.notificacoes_id_seq OWNED BY public.notificacoes.id;


--
-- Name: perfil_permissoes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.perfil_permissoes (
    perfil character varying(50) NOT NULL,
    secao character varying(80) NOT NULL,
    ver boolean NOT NULL,
    editar boolean NOT NULL,
    adicionar boolean NOT NULL
);


--
-- Name: planejamentos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.planejamentos (
    id integer CONSTRAINT planos_id_not_null NOT NULL,
    unidade_id integer CONSTRAINT planos_unidade_id_not_null NOT NULL,
    titulo character varying(200) CONSTRAINT planos_titulo_not_null NOT NULL,
    descricao text,
    gravidade integer DEFAULT 1 CONSTRAINT planos_gravidade_not_null NOT NULL,
    urgencia integer DEFAULT 1 CONSTRAINT planos_urgencia_not_null NOT NULL,
    tendencia integer DEFAULT 1 CONSTRAINT planos_tendencia_not_null NOT NULL,
    criado_por integer,
    criado_em timestamp without time zone DEFAULT CURRENT_TIMESTAMP CONSTRAINT planos_criado_em_not_null NOT NULL,
    atualizado_por integer,
    atualizado_em timestamp without time zone
);


--
-- Name: planejamentos_anexos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.planejamentos_anexos (
    id integer CONSTRAINT planos_anexos_id_not_null NOT NULL,
    planejamento_id integer CONSTRAINT planos_anexos_plano_id_not_null NOT NULL,
    filename character varying(200) CONSTRAINT planos_anexos_filename_not_null NOT NULL,
    original character varying(200) CONSTRAINT planos_anexos_original_not_null NOT NULL,
    mime_type character varying(100),
    criado_em timestamp without time zone DEFAULT CURRENT_TIMESTAMP CONSTRAINT planos_anexos_criado_em_not_null NOT NULL
);


--
-- Name: planos_anexos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.planos_anexos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: planos_anexos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.planos_anexos_id_seq OWNED BY public.planejamentos_anexos.id;


--
-- Name: planos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.planos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: planos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.planos_id_seq OWNED BY public.planejamentos.id;


--
-- Name: predios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.predios (
    id integer NOT NULL,
    nome character varying(200) NOT NULL,
    endereco character varying(300),
    numero character varying(20),
    bairro character varying(100),
    cidade character varying(100) DEFAULT 'Sorocaba'::character varying,
    uf character varying(2) DEFAULT 'SP'::character varying,
    cep character varying(9),
    telefone character varying(20),
    responsavel_predial_id integer,
    observacoes text,
    ativo boolean DEFAULT true NOT NULL,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    link_maps text,
    atualizado_em timestamp without time zone DEFAULT now() NOT NULL,
    complemento character varying(100)
);


--
-- Name: predios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.predios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: predios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.predios_id_seq OWNED BY public.predios.id;


--
-- Name: salas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.salas (
    id integer NOT NULL,
    unidade_id integer NOT NULL,
    nome character varying(150) NOT NULL,
    tipo character varying(100),
    responsavel character varying(150),
    ativo boolean DEFAULT true NOT NULL,
    observacoes text,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp without time zone DEFAULT now() NOT NULL,
    tipo_sala_id integer,
    ramal character varying(20)
);


--
-- Name: salas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.salas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: salas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.salas_id_seq OWNED BY public.salas.id;


--
-- Name: setores_manutencao; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.setores_manutencao (
    id integer NOT NULL,
    nome character varying(150) NOT NULL,
    descricao text,
    tipos_chamado jsonb DEFAULT '[]'::jsonb,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    divisao_id integer
);


--
-- Name: setores_manutencao_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.setores_manutencao_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: setores_manutencao_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.setores_manutencao_id_seq OWNED BY public.setores_manutencao.id;


--
-- Name: solicitacoes_vinculo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.solicitacoes_vinculo (
    id integer NOT NULL,
    unidade_id integer NOT NULL,
    status character varying(20) NOT NULL,
    nome character varying(200) NOT NULL,
    email character varying(200) NOT NULL,
    cpf character varying(20),
    cns character varying(20),
    sexo character varying(1),
    data_nasc date,
    nome_mae character varying(200),
    nome_pai character varying(200),
    nacionalidade character varying(20),
    municipio_nasc character varying(100),
    uf_nasc character varying(2),
    rg character varying(30),
    rg_uf character varying(2),
    rg_orgao character varying(30),
    rg_emissao date,
    escolaridade character varying(2),
    end_logradouro character varying(200),
    end_numero character varying(10),
    end_bairro character varying(100),
    end_municipio character varying(100),
    end_uf character varying(2),
    end_cep character varying(10),
    telefone character varying(20),
    orgao_emissor character varying(50),
    reg_conselho character varying(50),
    cbo character varying(10),
    vinculo character varying(1),
    tipo_vinculo character varying(1),
    carga_horaria smallint,
    cnpj_empresa character varying(20),
    nome_empresa character varying(200),
    dt_entrada date,
    criado_em timestamp without time zone NOT NULL,
    aprovado_por integer,
    aprovado_em timestamp without time zone,
    usuario_criado integer,
    observacao text,
    dt_entrada_pais date,
    pais_origem character varying(100),
    assinatura_base64 text
);


--
-- Name: solicitacoes_vinculo_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.solicitacoes_vinculo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: solicitacoes_vinculo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.solicitacoes_vinculo_id_seq OWNED BY public.solicitacoes_vinculo.id;


--
-- Name: status_chamados; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.status_chamados (
    id integer NOT NULL,
    slug character varying(30) NOT NULL,
    label character varying(80) NOT NULL,
    badge_cor character varying(20) NOT NULL,
    ativo boolean NOT NULL,
    padrao_listagem boolean NOT NULL,
    encerra_chamado boolean NOT NULL,
    ordem integer NOT NULL,
    criado_em timestamp without time zone NOT NULL
);


--
-- Name: status_chamados_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.status_chamados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: status_chamados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.status_chamados_id_seq OWNED BY public.status_chamados.id;


--
-- Name: tipos_equipamento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipos_equipamento (
    id integer NOT NULL,
    nome character varying(150) NOT NULL,
    descricao text,
    tem_patrimonio boolean DEFAULT true NOT NULL,
    icone character varying(80) DEFAULT 'bi-box'::character varying,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    ativo boolean DEFAULT true NOT NULL,
    atualizado_em timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: tipos_equipamento_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tipos_equipamento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tipos_equipamento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tipos_equipamento_id_seq OWNED BY public.tipos_equipamento.id;


--
-- Name: tipos_link; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipos_link (
    id integer NOT NULL,
    nome character varying(100) NOT NULL,
    descricao character varying(300),
    icone character varying(60) NOT NULL,
    cor character varying(7) NOT NULL,
    ordem integer NOT NULL,
    ativo boolean NOT NULL,
    criado_em timestamp without time zone NOT NULL,
    atualizado_em timestamp without time zone NOT NULL
);


--
-- Name: tipos_link_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tipos_link_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tipos_link_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tipos_link_id_seq OWNED BY public.tipos_link.id;


--
-- Name: tipos_sala; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipos_sala (
    id integer NOT NULL,
    nome character varying(100) NOT NULL,
    descricao text,
    icone character varying(50) DEFAULT 'bi-door-open'::character varying NOT NULL,
    ativo boolean DEFAULT true NOT NULL,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: tipos_sala_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tipos_sala_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tipos_sala_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tipos_sala_id_seq OWNED BY public.tipos_sala.id;


--
-- Name: tipos_unidade; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipos_unidade (
    id integer NOT NULL,
    nome character varying(60) NOT NULL,
    sigla character varying(20) NOT NULL,
    descricao text,
    ativo boolean DEFAULT true NOT NULL,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: tipos_unidade_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tipos_unidade_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tipos_unidade_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tipos_unidade_id_seq OWNED BY public.tipos_unidade.id;


--
-- Name: transferencias_equipamento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transferencias_equipamento (
    id integer NOT NULL,
    equipamento_id integer NOT NULL,
    sala_origem_id integer,
    sala_destino_id integer,
    unidade_origem_id integer NOT NULL,
    unidade_destino_id integer NOT NULL,
    solicitado_por integer,
    aceito_por integer,
    status character varying(20) DEFAULT 'pendente'::character varying NOT NULL,
    observacao text,
    observacao_aceite text,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    resolvido_em timestamp without time zone
);


--
-- Name: transferencias_equipamento_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transferencias_equipamento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transferencias_equipamento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transferencias_equipamento_id_seq OWNED BY public.transferencias_equipamento.id;


--
-- Name: unidades; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.unidades (
    id integer NOT NULL,
    nome character varying(200) NOT NULL,
    tipo character varying(30) DEFAULT 'UBS'::public.tipo_unidade NOT NULL,
    endereco character varying(300),
    numero character varying(20),
    bairro character varying(100),
    cidade character varying(100) DEFAULT 'Sorocaba'::character varying,
    uf character(2) DEFAULT 'SP'::bpchar,
    cep character varying(9),
    telefone character varying(20),
    email character varying(200),
    status character varying(10) DEFAULT 'ativa'::public.status_unidade NOT NULL,
    observacoes text,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp without time zone DEFAULT now() NOT NULL,
    tipo_unidade_id integer,
    predio_id integer,
    link_maps character varying(500),
    numero_cnes character varying(20),
    ramal character varying(20),
    complemento character varying(100)
);


--
-- Name: unidades_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.unidades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: unidades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.unidades_id_seq OWNED BY public.unidades.id;


--
-- Name: usuario_setor; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuario_setor (
    usuario_id integer NOT NULL,
    setor_id integer NOT NULL
);


--
-- Name: usuario_unidade; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuario_unidade (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    unidade_id integer NOT NULL,
    papel character varying(50),
    ativo boolean DEFAULT true NOT NULL,
    vinculado_em timestamp without time zone DEFAULT now() NOT NULL,
    matricula_id integer
);


--
-- Name: usuario_unidade_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.usuario_unidade_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: usuario_unidade_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.usuario_unidade_id_seq OWNED BY public.usuario_unidade.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    nome character varying(150) NOT NULL,
    email character varying(200) NOT NULL,
    senha_hash character varying(256) NOT NULL,
    perfil character varying(30) DEFAULT 'profissional'::public.perfil_usuario NOT NULL,
    ativo boolean DEFAULT true NOT NULL,
    criado_em timestamp without time zone DEFAULT now() NOT NULL,
    atualizado_em timestamp without time zone DEFAULT now() NOT NULL,
    whatsapp character varying(20),
    cpf character varying(14),
    cns character varying(20),
    sexo character varying(1),
    data_nasc date,
    nome_mae character varying(200),
    nome_pai character varying(200),
    nacionalidade character varying(20) DEFAULT 'brasileira'::character varying,
    uf_nasc character varying(2),
    municipio_nasc character varying(100),
    dt_entrada_pais date,
    pais_origem character varying(100),
    rg character varying(20),
    rg_uf character varying(2),
    rg_orgao character varying(50),
    rg_emissao date,
    escolaridade character varying(2),
    end_logradouro character varying(300),
    end_numero character varying(20),
    end_complemento character varying(100),
    end_bairro character varying(100),
    end_municipio character varying(100),
    end_uf character varying(2),
    end_cep character varying(9),
    telefone character varying(20),
    reg_conselho character varying(30),
    orgao_emissor character varying(50),
    vinculo character varying(1),
    tipo_vinculo character varying(1),
    carga_horaria smallint,
    cbo character varying(10),
    especialidade_residencia character varying(200),
    dt_entrada_unidade date,
    matricula character varying(50),
    frequenta_escola boolean,
    foto_perfil character varying(200),
    unidade_padrao_id integer
);


--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: acoes_planejamento id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acoes_planejamento ALTER COLUMN id SET DEFAULT nextval('public.acoes_plano_id_seq'::regclass);


--
-- Name: acoes_planejamento_obs_anexos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acoes_planejamento_obs_anexos ALTER COLUMN id SET DEFAULT nextval('public.acoes_plano_obs_anexos_id_seq'::regclass);


--
-- Name: acoes_planejamento_observacoes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acoes_planejamento_observacoes ALTER COLUMN id SET DEFAULT nextval('public.acoes_plano_observacoes_id_seq'::regclass);


--
-- Name: andamento_anexos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.andamento_anexos ALTER COLUMN id SET DEFAULT nextval('public.andamento_anexos_id_seq'::regclass);


--
-- Name: auditoria id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria ALTER COLUMN id SET DEFAULT nextval('public.auditoria_id_seq'::regclass);


--
-- Name: campos_tipo_equipamento id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campos_tipo_equipamento ALTER COLUMN id SET DEFAULT nextval('public.campos_tipo_equipamento_id_seq'::regclass);


--
-- Name: chamado_fotos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamado_fotos ALTER COLUMN id SET DEFAULT nextval('public.chamado_fotos_id_seq'::regclass);


--
-- Name: chamado_historico id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamado_historico ALTER COLUMN id SET DEFAULT nextval('public.chamado_historico_id_seq'::regclass);


--
-- Name: chamados id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamados ALTER COLUMN id SET DEFAULT nextval('public.chamados_id_seq'::regclass);


--
-- Name: contrato_acoes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_acoes ALTER COLUMN id SET DEFAULT nextval('public.contrato_acoes_id_seq'::regclass);


--
-- Name: contrato_equipamentos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_equipamentos ALTER COLUMN id SET DEFAULT nextval('public.contrato_equipamentos_id_seq'::regclass);


--
-- Name: contrato_financeiro id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_financeiro ALTER COLUMN id SET DEFAULT nextval('public.contrato_financeiro_id_seq'::regclass);


--
-- Name: contrato_tipos_equipamento id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_tipos_equipamento ALTER COLUMN id SET DEFAULT nextval('public.contrato_tipos_equipamento_id_seq'::regclass);


--
-- Name: contratos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contratos ALTER COLUMN id SET DEFAULT nextval('public.contratos_id_seq'::regclass);


--
-- Name: divisoes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.divisoes ALTER COLUMN id SET DEFAULT nextval('public.divisoes_id_seq'::regclass);


--
-- Name: documentos_transferencia id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentos_transferencia ALTER COLUMN id SET DEFAULT nextval('public.documentos_transferencia_id_seq'::regclass);


--
-- Name: empresas_contratadas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresas_contratadas ALTER COLUMN id SET DEFAULT nextval('public.empresas_contratadas_id_seq'::regclass);


--
-- Name: equipamento_campo_valores id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamento_campo_valores ALTER COLUMN id SET DEFAULT nextval('public.equipamento_campo_valores_id_seq'::regclass);


--
-- Name: equipamento_usuarios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamento_usuarios ALTER COLUMN id SET DEFAULT nextval('public.equipamento_usuarios_id_seq'::regclass);


--
-- Name: equipamentos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamentos ALTER COLUMN id SET DEFAULT nextval('public.equipamentos_id_seq'::regclass);


--
-- Name: faltas_abonadas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faltas_abonadas ALTER COLUMN id SET DEFAULT nextval('public.faltas_abonadas_id_seq'::regclass);


--
-- Name: ficha_cnes_vinculo id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ficha_cnes_vinculo ALTER COLUMN id SET DEFAULT nextval('public.ficha_cnes_vinculo_id_seq'::regclass);


--
-- Name: historico_equipamento id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historico_equipamento ALTER COLUMN id SET DEFAULT nextval('public.historico_equipamento_id_seq'::regclass);


--
-- Name: itens_documento_transferencia id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itens_documento_transferencia ALTER COLUMN id SET DEFAULT nextval('public.itens_documento_transferencia_id_seq'::regclass);


--
-- Name: itens_lojinha id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itens_lojinha ALTER COLUMN id SET DEFAULT nextval('public.itens_lojinha_id_seq'::regclass);


--
-- Name: links_uteis id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.links_uteis ALTER COLUMN id SET DEFAULT nextval('public.links_uteis_id_seq'::regclass);


--
-- Name: marcas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.marcas ALTER COLUMN id SET DEFAULT nextval('public.marcas_id_seq'::regclass);


--
-- Name: matriculas_profissionais id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.matriculas_profissionais ALTER COLUMN id SET DEFAULT nextval('public.matriculas_profissionais_id_seq'::regclass);


--
-- Name: modelos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modelos ALTER COLUMN id SET DEFAULT nextval('public.modelos_id_seq'::regclass);


--
-- Name: notificacoes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notificacoes ALTER COLUMN id SET DEFAULT nextval('public.notificacoes_id_seq'::regclass);


--
-- Name: planejamentos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.planejamentos ALTER COLUMN id SET DEFAULT nextval('public.planos_id_seq'::regclass);


--
-- Name: planejamentos_anexos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.planejamentos_anexos ALTER COLUMN id SET DEFAULT nextval('public.planos_anexos_id_seq'::regclass);


--
-- Name: predios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predios ALTER COLUMN id SET DEFAULT nextval('public.predios_id_seq'::regclass);


--
-- Name: salas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salas ALTER COLUMN id SET DEFAULT nextval('public.salas_id_seq'::regclass);


--
-- Name: setores_manutencao id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setores_manutencao ALTER COLUMN id SET DEFAULT nextval('public.setores_manutencao_id_seq'::regclass);


--
-- Name: solicitacoes_vinculo id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solicitacoes_vinculo ALTER COLUMN id SET DEFAULT nextval('public.solicitacoes_vinculo_id_seq'::regclass);


--
-- Name: status_chamados id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.status_chamados ALTER COLUMN id SET DEFAULT nextval('public.status_chamados_id_seq'::regclass);


--
-- Name: tipos_equipamento id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipos_equipamento ALTER COLUMN id SET DEFAULT nextval('public.tipos_equipamento_id_seq'::regclass);


--
-- Name: tipos_link id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipos_link ALTER COLUMN id SET DEFAULT nextval('public.tipos_link_id_seq'::regclass);


--
-- Name: tipos_sala id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipos_sala ALTER COLUMN id SET DEFAULT nextval('public.tipos_sala_id_seq'::regclass);


--
-- Name: tipos_unidade id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipos_unidade ALTER COLUMN id SET DEFAULT nextval('public.tipos_unidade_id_seq'::regclass);


--
-- Name: transferencias_equipamento id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencias_equipamento ALTER COLUMN id SET DEFAULT nextval('public.transferencias_equipamento_id_seq'::regclass);


--
-- Name: unidades id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.unidades ALTER COLUMN id SET DEFAULT nextval('public.unidades_id_seq'::regclass);


--
-- Name: usuario_unidade id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_unidade ALTER COLUMN id SET DEFAULT nextval('public.usuario_unidade_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Data for Name: acao_planejamento_empresas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.acao_planejamento_empresas (acao_id, empresa_id) FROM stdin;
1	1
2	1
\.


--
-- Data for Name: acao_planejamento_responsaveis; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.acao_planejamento_responsaveis (acao_id, usuario_id) FROM stdin;
3	10
\.


--
-- Data for Name: acoes_planejamento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.acoes_planejamento (id, planejamento_id, titulo, descricao, status, ordem, criado_por, criado_em, prazo) FROM stdin;
2	1	CAPS Alegria de Viver	\N	backlog	1	4	2026-03-05 21:55:24.07532	2026-07-31
1	1	CAPS Roda Viva	\N	backlog	0	4	2026-03-05 20:11:37.933772	2026-06-30
3	2	Abrir chamado no WebAtendimento RNDS	\N	em_andamento	1	2	2026-03-06 15:09:11.703969	2026-03-10
\.


--
-- Data for Name: acoes_planejamento_obs_anexos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.acoes_planejamento_obs_anexos (id, observacao_id, filename, original, mime_type) FROM stdin;
\.


--
-- Data for Name: acoes_planejamento_observacoes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.acoes_planejamento_observacoes (id, acao_id, usuario_id, texto, criado_em) FROM stdin;
1	1	4	<div>Enviado e-mail para <a href="mailto:suportesis.sorocaba@sorocaba.sp.gov.br" target="_blank" rel="noopener">Suporte SIS</a> registrando a demanda</div>	2026-03-05 21:04:39.616465
2	3	2	<div>Chamado Aberto.<br>Solicitação nº 202600035974 foi criado com sucesso!<br>CPF de Registro 304.461.388-43<br><a href="https://webmail.sorocaba.sp.gov.br/owa/redir.aspx?C=3DEvLucJSXsghMofwlq5I8x4c7ExjdszUcrsV7XBeIpi7vpDkHveCA..&amp;URL=https%3a%2f%2fwebatendimento.saude.gov.br%2facompanhamento" target="_blank" rel="noopener">Acompanhamento aqui</a></div>	2026-03-06 15:11:13.683625
3	3	2	<div><a href="https://webatendimento.saude.gov.br/acompanhamento" target="_blank" rel="noopener">https://webatendimento.saude.gov.br/acompanhamento</a><br>304.461.388-43<br>202600035974&nbsp;<br><br>Tramitado</div><div>RNDS - Nível 01 para RNDS - Negocial</div><div>Enviado em 06/03/2026 12:14</div>	2026-03-06 20:15:20.177233
\.


--
-- Data for Name: andamento_anexos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.andamento_anexos (id, andamento_id, filename, original, mime_type, tamanho_bytes, criado_em) FROM stdin;
\.


--
-- Data for Name: auditoria; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auditoria (id, created_at, usuario_id, acao, modulo, endpoint, url, method, parametros, entity_type, entity_id, ip_address, user_agent, response_status, detalhes) FROM stdin;
1	2026-03-07 01:33:12.797339	\N	view	auth	auth.index	http://localhost:5000/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
2	2026-03-07 01:33:12.839796	\N	view	auth	auth.login	http://localhost:5000/login	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
3	2026-03-07 01:33:23.988447	2	login	auth	auth.login	http://localhost:5000/login	POST	{"form": {"email": "dbispo@sorocaba.sp.gov.br"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
4	2026-03-07 01:33:24.252128	2	view	dashboard	dashboard.index	http://localhost:5000/dashboard	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
5	2026-03-07 01:33:28.949957	2	view	planejamentos	planejamentos.listar	http://localhost:5000/planejamentos/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
6	2026-03-07 02:16:14.956041	2	view	auth	auth.index	http://localhost:5000/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
7	2026-03-07 02:16:15.054975	2	view	dashboard	dashboard.index	http://localhost:5000/dashboard	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
8	2026-03-07 15:52:01.676207	\N	view	auth	auth.index	http://192.168.0.46:5000/	GET	null	\N	\N	192.168.0.45	Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36	302	\N
9	2026-03-07 15:52:01.840724	\N	view	auth	auth.login	http://192.168.0.46:5000/login	GET	null	\N	\N	192.168.0.45	Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36	200	\N
10	2026-03-07 15:52:41.157451	2	login	auth	auth.login	http://192.168.0.46:5000/login	POST	{"form": {"email": "dbispo@sorocaba.sp.gov.br"}}	\N	\N	192.168.0.45	Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36	302	\N
11	2026-03-07 15:52:41.235449	2	view	dashboard	dashboard.index	http://192.168.0.46:5000/dashboard	GET	null	\N	\N	192.168.0.45	Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36	200	\N
12	2026-03-07 16:05:23.029831	2	view	notificacoes	notificacoes.contagem	http://192.168.0.46:5000/notificacoes/contagem	GET	null	\N	\N	192.168.0.45	Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36	200	\N
13	2026-03-07 16:09:02.13117	\N	view	auth	auth.index	http://localhost:5000/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
14	2026-03-07 16:09:02.386338	\N	view	auth	auth.login	http://localhost:5000/login	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
15	2026-03-07 16:09:14.305029	4	login	auth	auth.login	http://localhost:5000/login	POST	{"form": {"email": "administrador.sigus@sorocaba.sp.gov.br"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
16	2026-03-07 16:09:14.53918	4	view	dashboard	dashboard.index	http://localhost:5000/dashboard	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
17	2026-03-07 16:09:20.157327	4	view	predios	predios.listar	http://localhost:5000/predios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
18	2026-03-07 16:09:23.086487	4	view	predios	predios.novo	http://localhost:5000/predios/novo	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
19	2026-03-07 16:10:24.561538	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
20	2026-03-07 16:10:48.225824	4	create	predios	predios.novo	http://localhost:5000/predios/novo	POST	{"form": {"cep": "18013-280", "nome": "Secretaria da Saúde", "bairro": "Alto da Boa Vista", "cidade": "Sorocaba", "numero": "3041", "endereco": "Avenida Engenheiro Carlos Reinaldo Mendes", "telefone": "(15) 3238-2332", "link_maps": "https://maps.app.goo.gl/vrZNmykxz7AaDNAP6", "observacoes": "", "responsavel_predial_id": ""}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
21	2026-03-07 16:10:48.54595	4	view	predios	predios.detalhe	http://localhost:5000/predios/2	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
22	2026-03-07 16:11:49.556839	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
23	2026-03-07 16:12:49.250875	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
24	2026-03-07 16:13:49.545159	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
25	2026-03-07 16:14:40.801984	4	view	unidades	unidades.listar	http://localhost:5000/unidades/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
26	2026-03-07 16:14:43.778548	4	view	unidades	unidades.nova	http://localhost:5000/unidades/nova	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
27	2026-03-07 16:15:44.441295	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
29	2026-03-07 16:16:14.48868	4	view	unidades	unidades.detalhe	http://localhost:5000/unidades/4	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
30	2026-03-07 16:16:54.749103	4	view	unidades	unidades.listar	http://localhost:5000/unidades/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
28	2026-03-07 16:16:14.112345	4	update	unidades	unidades.nova	http://localhost:5000/unidades/nova	POST	{"form": {"uf": "SP", "cep": "18013-280", "nome": "Divisão de Administração e Gestão", "email": "", "ramal": "2249", "bairro": "Alto da Boa Vista", "cidade": "Sorocaba", "numero": "3041", "endereco": "Avenida Engenheiro Carlos Reinaldo Mendes", "telefone": "(15) 3238-2332", "link_maps": "https://maps.app.goo.gl/vrZNmykxz7AaDNAP6", "predio_id": "2", "numero_cnes": "5697107", "observacoes": "", "tipo_unidade_id": "2"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
32	2026-03-07 16:17:00.430536	4	view	unidades	unidades.editar	http://localhost:5000/unidades/4/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
33	2026-03-07 16:17:30.030171	4	view	predios	predios.listar	http://localhost:5000/predios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
36	2026-03-07 16:17:52.299902	4	view	predios	predios.editar	http://localhost:5000/predios/2/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
31	2026-03-07 16:16:57.595703	4	view	unidades	unidades.detalhe	http://localhost:5000/unidades/4	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
34	2026-03-07 16:17:47.899614	4	view	predios	predios.listar	http://localhost:5000/predios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
35	2026-03-07 16:17:50.189552	4	view	predios	predios.detalhe	http://localhost:5000/predios/2	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
37	2026-03-07 16:18:53.246718	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
38	2026-03-07 16:19:53.185203	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
39	2026-03-07 16:20:19.130985	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
40	2026-03-07 16:20:20.290414	4	view	dashboard	dashboard.index	http://localhost:5000/dashboard	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
41	2026-03-07 16:20:22.181379	4	view	predios	predios.listar	http://localhost:5000/predios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
42	2026-03-07 16:20:23.717201	4	view	unidades	unidades.listar	http://localhost:5000/unidades/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
43	2026-03-07 16:20:24.939584	4	view	dashboard	dashboard.index	http://localhost:5000/dashboard	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
44	2026-03-07 16:20:25.749112	4	view	predios	predios.listar	http://localhost:5000/predios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
45	2026-03-07 16:20:27.956098	4	view	predios	predios.detalhe	http://localhost:5000/predios/2	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
46	2026-03-07 16:20:30.350548	4	view	predios	predios.editar	http://localhost:5000/predios/2/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
47	2026-03-07 16:20:41.76604	4	update	predios	predios.editar	http://localhost:5000/predios/2/editar	POST	{"form": {"cep": "18013-280", "nome": "Secretaria da Saúde", "bairro": "Alto da Boa Vista", "cidade": "Sorocaba", "numero": "3041", "endereco": "Avenida Engenheiro Carlos Reinaldo Mendes", "telefone": "(15) 3238-2332", "link_maps": "https://maps.app.goo.gl/vrZNmykxz7AaDNAP6", "complemento": "2º Andar", "observacoes": "", "responsavel_predial_id": ""}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
48	2026-03-07 16:20:41.779046	4	view	predios	predios.detalhe	http://localhost:5000/predios/2	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
49	2026-03-07 16:20:54.137339	4	view	unidades	unidades.listar	http://localhost:5000/unidades/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
50	2026-03-07 16:20:56.439975	4	view	unidades	unidades.detalhe	http://localhost:5000/unidades/1	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
51	2026-03-07 16:20:58.666946	4	view	unidades	unidades.editar	http://localhost:5000/unidades/1/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
52	2026-03-07 16:21:59.331691	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
53	2026-03-07 16:22:45.979579	4	view	unidades	unidades.listar	http://localhost:5000/unidades/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
54	2026-03-07 16:22:46.953722	4	view	predios	predios.listar	http://localhost:5000/predios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
55	2026-03-07 16:22:48.033722	4	view	predios	predios.detalhe	http://localhost:5000/predios/1	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
56	2026-03-07 16:22:49.821138	4	view	predios	predios.editar	http://localhost:5000/predios/1/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
57	2026-03-07 16:23:18.07542	4	update	predios	predios.editar	http://localhost:5000/predios/1/editar	POST	{"form": {"cep": "18010-004", "nome": "Palácio da Saúde", "bairro": "Centro", "cidade": "Sorocaba", "numero": "1176", "endereco": "Rua da Penha", "telefone": "(15) 3238-2771", "link_maps": "https://maps.app.goo.gl/EoLRkoAPt6CPas8U6", "complemento": "", "observacoes": "", "responsavel_predial_id": ""}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
58	2026-03-07 16:23:18.396153	4	view	predios	predios.detalhe	http://localhost:5000/predios/1	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
59	2026-03-07 16:23:56.838328	4	view	unidades	unidades.listar	http://localhost:5000/unidades/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
60	2026-03-07 16:23:58.956	4	view	unidades	unidades.detalhe	http://localhost:5000/unidades/1	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
61	2026-03-07 16:24:01.727094	4	view	unidades	unidades.editar	http://localhost:5000/unidades/1/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
62	2026-03-07 16:24:03.672772	4	view	unidades	unidades.listar	http://localhost:5000/unidades/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
63	2026-03-07 16:24:06.133481	4	view	unidades	unidades.detalhe	http://localhost:5000/unidades/1	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
64	2026-03-07 16:24:47.188396	4	view	salas	salas.editar	http://localhost:5000/salas/1/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
65	2026-03-07 16:24:57.364637	4	update	salas	salas.editar	http://localhost:5000/salas/1/editar	POST	{"form": {"nome": "Sala 05", "ramal": "", "observacoes": "", "responsavel": "", "tipo_sala_id": "1"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
68	2026-03-07 16:25:04.854762	4	view	predios	predios.listar	http://localhost:5000/predios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
72	2026-03-07 16:25:17.823624	4	view	predios	predios.detalhe	http://localhost:5000/predios/1	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
75	2026-03-07 16:27:03.25367	4	view	chamados	chamados.detalhe	http://localhost:5000/chamados/7	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
78	2026-03-07 16:27:29.531994	4	print	chamados	chamados.imprimir	http://localhost:5000/chamados/7/imprimir	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
66	2026-03-07 16:24:57.665335	4	view	salas	salas.detalhe	http://localhost:5000/salas/1	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
69	2026-03-07 16:25:07.49328	4	view	predios	predios.detalhe	http://localhost:5000/predios/2	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
76	2026-03-07 16:27:08.366189	4	update	chamados	chamados.atualizar_status	http://localhost:5000/chamados/7/atualizar	POST	{"form": {"status": "cancelado", "setor_id": "", "observacao": ""}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
67	2026-03-07 16:25:03.58424	4	view	chamados	chamados.detalhe	http://localhost:5000/chamados/7	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
70	2026-03-07 16:25:13.563717	4	view	predios	predios.listar	http://localhost:5000/predios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
71	2026-03-07 16:25:14.44813	4	view	predios	predios.detalhe	http://localhost:5000/predios/1	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
73	2026-03-07 16:25:58.332251	4	view	chamados	chamados.detalhe	http://localhost:5000/chamados/7	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
74	2026-03-07 16:26:57.350165	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
77	2026-03-07 16:27:08.38519	4	view	chamados	chamados.detalhe	http://localhost:5000/chamados/7	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
79	2026-03-07 16:28:09.304632	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
80	2026-03-07 16:29:08.734645	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
81	2026-03-07 16:29:55.803419	4	print	chamados	chamados.imprimir	http://localhost:5000/chamados/7/imprimir	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
82	2026-03-07 16:30:09.245973	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
83	2026-03-07 16:31:09.040287	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
84	2026-03-07 16:32:08.741762	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
85	2026-03-07 16:33:09.053048	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
86	2026-03-07 16:34:08.739152	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
87	2026-03-07 16:35:09.039939	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
88	2026-03-07 16:36:08.740292	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
89	2026-03-07 16:37:09.045193	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
90	2026-03-07 16:38:08.737892	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
91	2026-03-07 16:39:09.592782	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
92	2026-03-07 16:40:10.554685	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
93	2026-03-07 16:41:08.74383	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
94	2026-03-07 16:42:09.56924	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
95	2026-03-07 16:43:09.249462	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
96	2026-03-07 16:44:10.563567	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
97	2026-03-07 16:45:11.572519	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
98	2026-03-07 16:46:12.553871	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
99	2026-03-07 16:47:13.560916	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
100	2026-03-07 16:48:14.564029	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
101	2026-03-07 16:49:15.556132	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
102	2026-03-07 16:50:16.563424	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
103	2026-03-07 16:51:17.56708	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
104	2026-03-07 16:52:18.556303	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
105	2026-03-07 16:53:19.564434	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
106	2026-03-07 16:54:20.567747	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
107	2026-03-07 16:55:21.558635	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
108	2026-03-07 16:56:22.565169	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
109	2026-03-07 16:57:08.750462	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
110	2026-03-07 16:58:09.052814	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
111	2026-03-07 16:59:08.733514	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
112	2026-03-07 17:00:09.048709	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
113	2026-03-07 17:01:08.732703	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
114	2026-03-07 17:02:09.06005	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
115	2026-03-07 17:03:08.743253	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
116	2026-03-07 17:04:09.049906	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
117	2026-03-07 17:05:08.749319	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
118	2026-03-07 17:06:09.046381	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
119	2026-03-07 17:07:08.746595	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
120	2026-03-07 17:08:09.034451	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
121	2026-03-07 17:09:09.046695	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
122	2026-03-07 17:10:08.738221	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
123	2026-03-07 17:11:09.036534	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
124	2026-03-07 17:12:09.254561	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
125	2026-03-07 17:13:10.548531	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
126	2026-03-07 17:14:11.547219	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
127	2026-03-07 17:15:12.571263	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
128	2026-03-07 17:16:13.544281	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
129	2026-03-07 17:17:14.566229	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
130	2026-03-07 17:18:15.559314	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
131	2026-03-07 17:19:16.558421	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
132	2026-03-07 17:20:17.551798	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
133	2026-03-07 17:21:18.54551	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
134	2026-03-07 17:22:19.557904	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
135	2026-03-07 17:23:20.560783	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
136	2026-03-07 17:24:21.545938	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
137	2026-03-07 17:25:22.547776	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
138	2026-03-07 17:26:23.54702	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
139	2026-03-07 17:27:24.552691	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
140	2026-03-07 17:28:25.554136	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
141	2026-03-07 17:29:26.553197	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
142	2026-03-07 17:30:27.559332	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
143	2026-03-07 17:31:28.546937	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
144	2026-03-07 17:32:29.544028	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
145	2026-03-07 17:33:30.551471	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
146	2026-03-07 17:34:31.550014	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
147	2026-03-07 17:35:09.253965	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
148	2026-03-07 17:36:10.548685	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
149	2026-03-07 17:36:15.299285	4	print	chamados	chamados.imprimir	http://localhost:5000/chamados/7/imprimir	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
150	2026-03-07 17:36:52.093158	4	view	dashboard	dashboard.index	http://localhost:5000/dashboard	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
151	2026-03-07 17:36:54.271373	4	view	predios	predios.listar	http://localhost:5000/predios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
152	2026-03-07 17:36:56.291301	4	view	predios	predios.detalhe	http://localhost:5000/predios/1	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
153	2026-03-07 17:37:07.718309	4	view	usuarios	usuarios.listar	http://localhost:5000/usuarios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
154	2026-03-07 17:37:10.12744	4	view	usuarios	usuarios.novo	http://localhost:5000/usuarios/novo	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
155	2026-03-07 17:38:11.016425	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
156	2026-03-07 17:39:10.975743	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
157	2026-03-07 17:40:11.034324	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
184	2026-03-07 17:49:32.479297	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
158	2026-03-07 17:40:35.166393	4	create	usuarios	usuarios.novo	http://localhost:5000/usuarios/novo	POST	{"form": {"rg": "", "cns": "706804113463030", "cpf": "37345759822", "nome": "Évelyn de Oliveira Moraes", "sexo": "F", "email": "emoraes@sorocaba.sp.gov.br", "rg_uf": "", "end_uf": "SP", "perfil": "gestor_secretaria", "end_cep": "18086230", "uf_nasc": "SP", "nome_mae": "Eliceia de Oliveira Moraes Feliciano", "nome_pai": "", "rg_orgao": "", "whatsapp": "15988000802", "data_nasc": "1989-02-27", "end_bairro": "Jardim Ibiti do Paço", "end_numero": "196", "rg_emissao": "", "pais_origem": "", "escolaridade": "08", "end_municipio": "Sorocaba", "nacionalidade": "brasileira", "end_logradouro": "Rua Armando Landulfo", "municipio_nasc": "SOROCABA", "dt_entrada_pais": "", "end_complemento": "", "frequenta_escola": "0"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
159	2026-03-07 17:40:35.419416	4	view	usuarios	usuarios.listar	http://localhost:5000/usuarios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
160	2026-03-07 17:41:22.714668	4	view	usuarios	usuarios.editar	http://localhost:5000/usuarios/11/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
161	2026-03-07 17:42:14.525299	4	update	usuarios	usuarios.criar_matricula	http://localhost:5000/usuarios/11/matriculas	POST	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
162	2026-03-07 17:42:14.610807	4	view	usuarios	usuarios.editar	http://localhost:5000/usuarios/11/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
163	2026-03-07 17:42:20.586221	4	view	unidades	unidades.listar	http://localhost:5000/unidades/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
164	2026-03-07 17:42:24.840202	4	view	unidades	unidades.detalhe	http://localhost:5000/unidades/4	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
165	2026-03-07 17:42:31.528094	4	view	usuarios	usuarios.listar_matriculas_json	http://localhost:5000/usuarios/11/matriculas/json	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
166	2026-03-07 17:42:53.40105	4	update	unidades	unidades.vincular_usuario	http://localhost:5000/unidades/4/vincular	POST	{"form": {"cbo": "131210", "vinculo": "1", "usuario_id": "11", "observacoes": "", "matricula_id": "10", "tipo_vinculo": "1", "carga_horaria": "40", "cns_profissional": "706804113463030", "dt_entrada_unidade": "2025-09-01", "especialidade_residencia": ""}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
167	2026-03-07 17:42:53.554119	4	view	unidades	unidades.detalhe	http://localhost:5000/unidades/4	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
168	2026-03-07 17:43:22.847887	4	view	unidades	unidades.ficha_cnes_vinculo	http://localhost:5000/unidades/ficha-cnes/11	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
169	2026-03-07 17:43:54.698489	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
170	2026-03-07 17:44:07.742455	4	view	unidades	unidades.detalhe	http://localhost:5000/unidades/4	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
171	2026-03-07 17:45:08.256825	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
172	2026-03-07 17:46:08.208147	4	view	salas	salas.nova	http://localhost:5000/salas/nova/4	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
173	2026-03-07 17:46:08.44516	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
174	2026-03-07 17:46:20.351843	4	update	salas	salas.nova	http://localhost:5000/salas/nova/4	POST	{"form": {"nome": "Seção de Aquisição e Manutenção de Equipamentos e Mobiliários", "ramal": "", "observacoes": "", "responsavel": "", "tipo_sala_id": "1"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
175	2026-03-07 17:46:20.694396	4	view	unidades	unidades.detalhe	http://localhost:5000/unidades/4	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
176	2026-03-07 17:47:01.921501	4	view	unidades	unidades.detalhe	http://localhost:5000/unidades/4	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
177	2026-03-07 17:47:44.519134	4	view	unidades	unidades.detalhe	http://localhost:5000/unidades/4	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
178	2026-03-07 17:47:49.617136	4	view	salas	salas.detalhe	http://localhost:5000/salas/4	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
179	2026-03-07 17:48:22.313215	4	view	predios	predios.listar	http://localhost:5000/predios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
180	2026-03-07 17:48:24.029203	4	view	predios	predios.detalhe	http://localhost:5000/predios/2	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
181	2026-03-07 17:48:26.443211	4	view	predios	predios.editar	http://localhost:5000/predios/2/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
182	2026-03-07 17:48:29.111759	4	view	predios	predios.listar	http://localhost:5000/predios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
183	2026-03-07 17:48:31.812363	4	view	predios	predios.detalhe	http://localhost:5000/predios/2	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
185	2026-03-07 17:50:32.15708	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
188	2026-03-07 17:53:32.455638	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
191	2026-03-07 17:56:32.156533	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
194	2026-03-07 17:59:32.462223	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
197	2026-03-07 18:02:32.158174	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
200	2026-03-07 18:05:32.561633	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
203	2026-03-07 18:08:35.55706	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
186	2026-03-07 17:51:32.467931	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
189	2026-03-07 17:54:32.164291	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
192	2026-03-07 17:57:32.454266	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
195	2026-03-07 18:00:32.152079	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
198	2026-03-07 18:03:32.464998	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
201	2026-03-07 18:06:33.548919	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
187	2026-03-07 17:52:32.154049	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
190	2026-03-07 17:55:32.460435	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
193	2026-03-07 17:58:32.167275	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
196	2026-03-07 18:01:32.479799	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
199	2026-03-07 18:04:32.15838	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
202	2026-03-07 18:07:34.555304	4	view	notificacoes	notificacoes.contagem	http://localhost:5000/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
204	2026-03-12 18:07:57.457646	\N	view	contratos	contratos.listar	http://localhost:5000/contratos/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
205	2026-03-12 18:07:57.583348	\N	view	auth	auth.login	http://localhost:5000/login?next=/contratos/	GET	{"args": {"next": "/contratos/"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
206	2026-03-12 18:08:52.523346	\N	view	auth	auth.index	http://localhost:5000/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
207	2026-03-12 18:12:36.408932	\N	view	auth	auth.index	http://localhost:5000/	GET	null	\N	\N	[::1]:59868	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
208	2026-03-12 18:12:36.421043	\N	view	auth	auth.index	http://localhost:5000/	GET	null	\N	\N	[::1]:59868	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
209	2026-03-12 18:19:12.134263	\N	view	auth	auth.index	http://localhost:5000/	GET	null	\N	\N	[::1]:60422	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
210	2026-03-12 18:19:12.145486	\N	view	auth	auth.index	http://localhost:5000/	GET	null	\N	\N	[::1]:60422	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
211	2026-03-12 18:19:56.269347	\N	view	auth	auth.index	http://localhost:5000/	GET	null	\N	\N	[::1]:55119	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
212	2026-03-12 18:19:56.284128	\N	view	auth	auth.index	http://localhost:5000/	GET	null	\N	\N	[::1]:55119	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
213	2026-03-12 18:22:48.378079	\N	view	auth	auth.index	http://localhost:5000/sigus/	GET	null	\N	\N	[::1]:57157	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
214	2026-03-12 18:22:48.416275	\N	view	auth	auth.login	http://localhost:5000/sigus/login	GET	null	\N	\N	[::1]:57157	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
215	2026-03-12 18:23:17.934893	2	login	auth	auth.login	http://localhost:5000/sigus/login	POST	{"form": {"email": "dbispo@sorocaba.sp.gov.br", "lembrar": "on"}}	\N	\N	[::1]:57157	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
216	2026-03-12 18:23:18.032615	2	view	dashboard	dashboard.index	http://localhost:5000/sigus/dashboard	GET	null	\N	\N	[::1]:57157	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
217	2026-03-12 18:23:48.17915	2	view	auth	auth.perfil	http://localhost:5000/sigus/perfil	GET	null	\N	\N	[::1]:54306	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
218	2026-03-12 18:26:31.155596	2	view	auth	auth.perfil	http://localhost:5000/sigus/perfil	GET	null	\N	\N	[::1]:62646	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
219	2026-03-12 18:26:35.657892	2	view	chamados	chamados.listar	http://localhost:5000/sigus/chamados/	GET	null	\N	\N	[::1]:60316	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
220	2026-03-12 18:26:39.836903	2	view	chamados	chamados.gestao	http://localhost:5000/sigus/chamados/gestao	GET	null	\N	\N	[::1]:60197	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
221	2026-03-12 18:26:45.895378	2	view	transferencias	transferencias.listar	http://localhost:5000/sigus/transferencias/	GET	null	\N	\N	[::1]:60197	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
222	2026-03-12 18:26:47.453853	2	view	contratos	contratos.listar	http://localhost:5000/sigus/contratos/	GET	null	\N	\N	[::1]:60316	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
223	2026-03-12 18:26:48.836778	2	view	transferencias	transferencias.listar	http://localhost:5000/sigus/transferencias/	GET	null	\N	\N	[::1]:60197	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
224	2026-03-12 18:26:49.890798	2	search	transferencias	transferencias.listar	http://localhost:5000/sigus/transferencias/?aba=lojinha&lojinha_classificacao=	GET	{"args": {"aba": "lojinha", "lojinha_classificacao": ""}}	\N	\N	[::1]:60316	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
225	2026-03-12 18:26:51.605764	2	search	transferencias	transferencias.listar	http://localhost:5000/sigus/transferencias/?aba=pendentes	GET	{"args": {"aba": "pendentes"}}	\N	\N	[::1]:63180	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
226	2026-03-12 18:26:52.598857	2	view	contratos	contratos.listar	http://localhost:5000/sigus/contratos/	GET	null	\N	\N	[::1]:60197	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
227	2026-03-12 18:26:53.518981	2	view	contrato_financeiro	contrato_financeiro.listar	http://localhost:5000/sigus/contratos/empenhos/	GET	null	\N	\N	[::1]:63180	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
232	2026-03-12 18:27:22.825786	\N	view	auth	auth.login	http://localhost:5000/sigus/login	GET	null	\N	\N	[::1]:62646	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
239	2026-03-12 18:28:05.413828	4	view	planejamentos	planejamentos.listar	http://localhost:5000/sigus/planejamentos/	GET	null	\N	\N	[::1]:60197	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
240	2026-03-12 18:28:06.163845	4	view	empresas	empresas.listar	http://localhost:5000/sigus/empresas/	GET	null	\N	\N	[::1]:60197	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
228	2026-03-12 18:26:54.371091	2	view	empresas	empresas.listar	http://localhost:5000/sigus/empresas/	GET	null	\N	\N	[::1]:63180	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
229	2026-03-12 18:27:00.082451	2	view	planejamentos	planejamentos.listar	http://localhost:5000/sigus/planejamentos/	GET	null	\N	\N	[::1]:60197	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
230	2026-03-12 18:27:09.005467	2	view	relatorios	relatorios.index	http://localhost:5000/sigus/relatorios/	GET	null	\N	\N	[::1]:62646	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
234	2026-03-12 18:27:32.238487	4	view	dashboard	dashboard.index	http://localhost:5000/sigus/dashboard	GET	null	\N	\N	[::1]:60197	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
236	2026-03-12 18:27:45.627019	4	view	relatorios	relatorios.index	http://localhost:5000/sigus/relatorios/	GET	null	\N	\N	[::1]:63180	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
231	2026-03-12 18:27:22.816347	\N	view	auth	auth.logout	http://localhost:5000/sigus/logout	GET	null	\N	\N	[::1]:62646	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
233	2026-03-12 18:27:32.190189	4	login	auth	auth.login	http://localhost:5000/sigus/login	POST	{"form": {"email": "administrador.sigus@sorocaba.sp.gov.br", "lembrar": "on"}}	\N	\N	[::1]:60197	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
235	2026-03-12 18:27:43.158845	4	view	links	links.index	http://localhost:5000/sigus/links/	GET	null	\N	\N	[::1]:60316	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
237	2026-03-12 18:27:46.340653	4	view	planejamentos	planejamentos.listar	http://localhost:5000/sigus/planejamentos/	GET	null	\N	\N	[::1]:49938	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
238	2026-03-12 18:27:52.451644	4	view	relatorios	relatorios.index	http://localhost:5000/sigus/relatorios/	GET	null	\N	\N	[::1]:63180	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
241	2026-03-12 18:32:43.199128	4	view	empresas	empresas.listar	http://localhost:5000/sigus/empresas/	GET	null	\N	\N	[::1]:60013	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
242	2026-03-12 18:33:40.697462	4	view	empresas	empresas.listar	http://localhost:5000/sigus/empresas/	GET	null	\N	\N	[::1]:52801	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
243	2026-03-12 18:34:12.559527	4	view	empresas	empresas.listar	http://localhost:5000/sigus/empresas/	GET	null	\N	\N	[::1]:52801	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
244	2026-03-12 18:34:15.77245	4	view	empresas	empresas.listar	http://localhost:5000/sigus/empresas/	GET	null	\N	\N	[::1]:55041	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
245	2026-03-12 18:34:35.417371	4	view	relatorios	relatorios.index	http://localhost:5000/sigus/relatorios/	GET	null	\N	\N	[::1]:60013	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
246	2026-03-12 18:34:37.26599	4	view	relatorios	relatorios.inventario	http://localhost:5000/sigus/relatorios/inventario	GET	null	\N	\N	[::1]:61087	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
247	2026-03-12 18:35:22.489479	4	view	relatorios	relatorios.inventario	http://localhost:5000/sigus/relatorios/inventario	GET	null	\N	\N	[::1]:60013	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
248	2026-03-12 18:35:30.399521	\N	view	auth	auth.logout	http://localhost:5000/sigus/logout	GET	null	\N	\N	[::1]:60013	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
249	2026-03-12 18:35:30.409812	\N	view	auth	auth.login	http://localhost:5000/sigus/login	GET	null	\N	\N	[::1]:60013	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
250	2026-03-12 18:35:39.190889	\N	view	auth	auth.index	http://localhost:5000/sigus/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
251	2026-03-12 18:35:39.196235	\N	view	auth	auth.login	http://localhost:5000/sigus/login	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
252	2026-03-12 18:35:50.617461	4	login	auth	auth.login	http://localhost:5000/sigus/login	POST	{"form": {"email": "administrador.sigus@sorocaba.sp.gov.br"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
253	2026-03-12 18:35:50.873897	4	view	dashboard	dashboard.index	http://localhost:5000/sigus/dashboard	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
254	2026-03-12 18:36:04.422499	4	update	auth	auth.definir_unidade_padrao	http://localhost:5000/sigus/unidade-padrao	POST	{"form": {"unidade_id": "4"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
255	2026-03-12 18:36:04.703634	4	view	dashboard	dashboard.index	http://localhost:5000/sigus/dashboard	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
256	2026-03-12 18:36:32.725357	4	view	usuarios	usuarios.listar	http://localhost:5000/sigus/usuarios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
257	2026-03-12 18:36:43.905347	4	view	usuarios	usuarios.editar	http://localhost:5000/sigus/usuarios/2/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
258	2026-03-12 18:36:46.865264	4	view	usuarios	usuarios.listar	http://localhost:5000/sigus/usuarios/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
259	2026-03-12 18:36:48.455338	4	view	chamados	chamados.listar	http://localhost:5000/sigus/chamados/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
260	2026-03-12 18:36:52.956398	4	view	unidades	unidades.detalhe	http://localhost:5000/sigus/unidades/4	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
261	2026-03-12 18:37:04.638272	4	update	auth	auth.definir_unidade_padrao	http://localhost:5000/sigus/unidade-padrao	POST	{"form": {"unidade_id": ""}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
262	2026-03-12 18:37:04.658793	4	view	dashboard	dashboard.index	http://localhost:5000/sigus/dashboard	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
263	2026-03-12 18:37:08.792816	4	view	dashboard	dashboard.index	http://localhost:5000/sigus/dashboard	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
264	2026-03-12 18:37:21.254778	4	view	unidades	unidades.listar	http://localhost:5000/sigus/unidades/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
265	2026-03-12 18:37:29.024329	4	update	auth	auth.definir_unidade_padrao	http://localhost:5000/sigus/unidade-padrao	POST	{"form": {"unidade_id": "1"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
269	2026-03-12 18:37:45.763872	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/usuarios/6/matriculas/json	GET	{"args": {"next": "/sigus/usuarios/6/matriculas/json"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
273	2026-03-12 18:38:37.562244	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
266	2026-03-12 18:37:29.045876	4	view	dashboard	dashboard.index	http://localhost:5000/sigus/dashboard	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
270	2026-03-12 18:38:06.581099	\N	view	unidades	unidades.editar	http://localhost:5000/sigus/unidades/1/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
267	2026-03-12 18:37:35.95658	4	view	unidades	unidades.detalhe	http://localhost:5000/sigus/unidades/1	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
271	2026-03-12 18:38:06.890618	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/unidades/1/editar	GET	{"args": {"next": "/sigus/unidades/1/editar"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
268	2026-03-12 18:37:45.444993	\N	view	usuarios	usuarios.listar_matriculas_json	http://localhost:5000/sigus/usuarios/6/matriculas/json	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
272	2026-03-12 18:38:37.252614	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
274	2026-03-12 18:39:37.245358	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
275	2026-03-12 18:39:37.572974	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
276	2026-03-12 18:40:37.242161	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
277	2026-03-12 18:40:37.551799	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
278	2026-03-12 18:41:37.247228	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
279	2026-03-12 18:41:37.559438	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
280	2026-03-12 18:42:37.860881	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
281	2026-03-12 18:42:37.90035	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
282	2026-03-12 18:43:11.110594	\N	view	unidades	unidades.detalhe	http://localhost:5000/sigus/unidades/1	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
283	2026-03-12 18:43:11.115419	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/unidades/1	GET	{"args": {"next": "/sigus/unidades/1"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
284	2026-03-12 18:43:17.435311	4	login	auth	auth.login	http://localhost:5000/sigus/login	POST	{"form": {"email": "administrador.sigus@sorocaba.sp.gov.br"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
285	2026-03-12 18:43:17.712536	4	view	dashboard	dashboard.index	http://localhost:5000/sigus/dashboard	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
286	2026-03-12 18:43:21.377495	4	view	configuracoes	configuracoes.index	http://localhost:5000/sigus/configuracoes/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
287	2026-03-12 18:43:31.635584	4	view	configuracoes	configuracoes.perfis	http://localhost:5000/sigus/configuracoes/perfis	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
288	2026-03-12 18:43:35.870835	4	view	configuracoes	configuracoes.editar_perfil	http://localhost:5000/sigus/configuracoes/perfis/gestor_secretaria/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
289	2026-03-12 18:43:58.491449	4	view	configuracoes	configuracoes.perfis	http://localhost:5000/sigus/configuracoes/perfis	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
290	2026-03-12 18:44:42.437976	4	view	unidades	unidades.detalhe	http://localhost:5000/sigus/unidades/1	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
291	2026-03-12 18:44:49.228828	4	view	usuarios	usuarios.editar	http://localhost:5000/sigus/usuarios/2/editar	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
292	2026-03-12 18:45:50.55532	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
293	2026-03-12 18:45:50.82053	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
294	2026-03-12 18:46:50.243255	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
295	2026-03-12 18:46:50.552981	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
296	2026-03-12 18:47:50.242226	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
297	2026-03-12 18:47:50.552168	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
298	2026-03-12 18:48:50.240587	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
299	2026-03-12 18:48:50.553068	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
302	2026-03-12 18:50:50.254543	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
300	2026-03-12 18:49:50.251925	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
303	2026-03-12 18:50:50.567095	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
301	2026-03-12 18:49:50.588865	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
304	2026-03-12 18:51:40.854483	\N	view	auth	auth.index	http://localhost:5000/sigus/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
305	2026-03-12 18:51:40.89364	\N	view	auth	auth.login	http://localhost:5000/sigus/login	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
306	2026-03-12 18:51:41.233019	\N	view	manifest	manifest	http://localhost:5000/sigus/manifest.json	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
307	2026-03-12 18:51:52.658487	4	login	auth	auth.login	http://localhost:5000/sigus/login	POST	{"form": {"email": "administrador.sigus@sorocaba.sp.gov.br"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
308	2026-03-12 18:51:52.926624	4	view	dashboard	dashboard.index	http://localhost:5000/sigus/dashboard	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
309	2026-03-12 18:51:52.950666	\N	view	manifest	manifest	http://localhost:5000/sigus/manifest.json	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
310	2026-03-12 18:52:01.904416	4	view	transferencias	transferencias.listar	http://localhost:5000/sigus/transferencias/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
311	2026-03-12 18:52:02.236912	\N	view	manifest	manifest	http://localhost:5000/sigus/manifest.json	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
312	2026-03-12 18:52:02.869769	4	view	contratos	contratos.listar	http://localhost:5000/sigus/contratos/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
313	2026-03-12 18:52:02.899505	\N	view	manifest	manifest	http://localhost:5000/sigus/manifest.json	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
314	2026-03-12 18:52:06.080817	4	view	contrato_financeiro	contrato_financeiro.listar	http://localhost:5000/sigus/contratos/empenhos/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
315	2026-03-12 18:52:06.407822	\N	view	manifest	manifest	http://localhost:5000/sigus/manifest.json	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
316	2026-03-12 18:52:07.902332	4	view	empresas	empresas.listar	http://localhost:5000/sigus/empresas/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
317	2026-03-12 18:52:07.924826	\N	view	manifest	manifest	http://localhost:5000/sigus/manifest.json	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
318	2026-03-12 18:52:08.84012	4	view	contratos	contratos.listar	http://localhost:5000/sigus/contratos/	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
319	2026-03-12 18:52:09.171229	\N	view	manifest	manifest	http://localhost:5000/sigus/manifest.json	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
320	2026-03-12 18:52:10.085819	4	view	contratos	contratos.detalhe	http://localhost:5000/sigus/contratos/1	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
321	2026-03-12 18:52:10.364663	\N	view	manifest	manifest	http://localhost:5000/sigus/manifest.json	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
322	2026-03-12 18:52:19.802603	4	print	contratos	contratos.imprimir	http://localhost:5000/sigus/contratos/1/imprimir	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
323	2026-03-12 18:53:11.251575	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
324	2026-03-12 18:53:11.555872	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
325	2026-03-12 18:54:11.251505	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
326	2026-03-12 18:54:11.566076	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
327	2026-03-12 18:55:11.566116	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
328	2026-03-12 18:55:11.830263	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
329	2026-03-12 18:56:11.243885	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
330	2026-03-12 18:56:11.556079	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
331	2026-03-12 18:57:11.242563	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
335	2026-03-12 18:59:11.245842	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
339	2026-03-12 19:01:13.560398	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
343	2026-03-12 19:03:15.565139	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
347	2026-03-12 19:05:16.244387	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
351	2026-03-12 19:07:16.245424	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
332	2026-03-12 18:57:11.551901	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
336	2026-03-12 18:59:11.55976	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
340	2026-03-12 19:01:13.825215	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
344	2026-03-12 19:03:15.832137	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
348	2026-03-12 19:05:16.557778	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
352	2026-03-12 19:07:16.557647	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
333	2026-03-12 18:58:11.252399	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
337	2026-03-12 19:00:12.558313	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
341	2026-03-12 19:02:14.566544	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
345	2026-03-12 19:04:16.56001	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
349	2026-03-12 19:06:16.252125	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
334	2026-03-12 18:58:11.561227	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
338	2026-03-12 19:00:12.809113	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
342	2026-03-12 19:02:14.818859	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
346	2026-03-12 19:04:16.825279	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
350	2026-03-12 19:06:16.570301	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
353	2026-03-12 19:08:16.24749	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
354	2026-03-12 19:08:16.573884	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
355	2026-03-12 19:09:16.243483	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
356	2026-03-12 19:09:16.557485	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
357	2026-03-12 19:10:16.251918	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
358	2026-03-12 19:10:16.560863	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
359	2026-03-12 19:11:16.254242	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
360	2026-03-12 19:11:16.563015	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
361	2026-03-12 19:12:16.25359	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
362	2026-03-12 19:12:16.563978	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
363	2026-03-12 19:13:16.246824	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
364	2026-03-12 19:13:16.559061	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
365	2026-03-12 19:14:16.241234	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
366	2026-03-12 19:14:16.551045	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
367	2026-03-12 19:15:16.250422	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
368	2026-03-12 19:15:16.565993	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
369	2026-03-12 19:16:16.263075	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
370	2026-03-12 19:16:16.580858	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
371	2026-03-12 19:17:17.399892	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
372	2026-03-12 19:17:17.442393	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
373	2026-03-12 19:18:16.798452	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
374	2026-03-12 19:18:16.860936	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
375	2026-03-12 19:19:16.250293	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
376	2026-03-12 19:19:16.560045	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
377	2026-03-12 19:20:16.247411	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
378	2026-03-12 19:20:16.558822	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
379	2026-03-12 19:21:16.254422	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
380	2026-03-12 19:21:16.566235	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
381	2026-03-12 19:22:16.253731	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
382	2026-03-12 19:22:16.56439	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
383	2026-03-12 19:23:16.250453	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
384	2026-03-12 19:23:16.560345	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
385	2026-03-12 19:24:16.241475	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
386	2026-03-12 19:24:16.551694	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
387	2026-03-12 19:25:16.554739	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
388	2026-03-12 19:25:16.820649	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
389	2026-03-12 19:26:16.245902	\N	view	notificacoes	notificacoes.contagem	http://localhost:5000/sigus/notificacoes/contagem	GET	null	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	302	\N
390	2026-03-12 19:26:16.557966	\N	view	auth	auth.login	http://localhost:5000/sigus/login?next=/sigus/notificacoes/contagem	GET	{"args": {"next": "/sigus/notificacoes/contagem"}}	\N	\N	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36	200	\N
\.


--
-- Data for Name: campos_tipo_equipamento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.campos_tipo_equipamento (id, tipo_equipamento_id, nome_campo, tipo_dado, obrigatorio, opcoes_selecao, ordem, criado_em, campo_destaque) FROM stdin;
1	5	Polegadas	numero	f	null	1	2026-02-28 18:47:40.183314	f
2	7	BTUs	numero	f	null	1	2026-02-28 20:51:54.101523	t
\.


--
-- Data for Name: chamado_fotos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chamado_fotos (id, chamado_id, filename, original, mime_type, criado_em) FROM stdin;
1	5	14de663590a8476ea8dab8508a6f319a.webp	Janela.webp	image/webp	2026-03-01 04:25:35.933441
\.


--
-- Data for Name: chamado_historico; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chamado_historico (id, chamado_id, usuario_id, acao, observacao, criado_em, tipo_andamento, requer_resposta, respondido_em, contrato_id) FROM stdin;
1	1	2	Chamado de Bem Permanente aberto	Notebook parou de ligar	2026-03-01 02:38:34.422015	andamento	f	\N	\N
2	2	4	Chamado Predial aberto	A Janela não está fechando	2026-03-01 03:08:45.339082	andamento	f	\N	\N
3	2	4	Status alterado: aberto → cancelado	Resolvido	2026-03-01 03:22:11.877585	andamento	f	\N	\N
4	1	4	Status alterado: aberto → concluido	Realizado!	2026-03-01 03:28:03.878059	andamento	f	\N	\N
5	3	2	Chamado de Bem Permanente aberto	Sistema operacional travou	2026-03-01 04:09:50.163097	andamento	f	\N	\N
6	4	2	Chamado Predial aberto	JANELA VOLTOU A NÃO ABRIR	2026-03-01 04:20:12.277203	andamento	f	\N	\N
7	4	2	Chamado encaminhado para equipe contratada | Status: aberto → em_andamento	Enviado e-mail	2026-03-01 04:22:07.516221	andamento	f	\N	\N
8	4	2	Status alterado: em_andamento → cancelado	TESTE DA FOTO	2026-03-01 04:25:07.748251	andamento	f	\N	\N
9	5	2	Chamado Predial aberto	JANELA QUEBRADA	2026-03-01 04:25:35.935651	andamento	f	\N	\N
10	3	2	Status alterado: aberto → cancelado	A	2026-03-01 04:30:15.038068	andamento	f	\N	\N
11	5	4	Status alterado: aberto → cancelado		2026-03-02 15:08:14.873069	andamento	f	\N	\N
12	6	2	Chamado de Bem Permanente aberto	CARREGADOR COM CABO CORTADO	2026-03-02 16:33:25.374891	andamento	f	\N	\N
13	6	2	Status alterado: aberto → em_andamento		2026-03-02 16:34:59.850407	andamento	f	\N	\N
14	7	2	Chamado Predial aberto	goteira no telhado	2026-03-02 17:48:49.898364	andamento	f	\N	\N
15	7	2	Status alterado: aberto → em_andamento		2026-03-02 17:49:04.745619	andamento	f	\N	\N
16	7	4	Status alterado: em_andamento → cancelado		2026-03-07 16:27:08.364189	andamento	f	\N	\N
\.


--
-- Data for Name: chamados; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chamados (id, numero, unidade_id, sala_id, equipamento_id, tipo_chamado, titulo, descricao, prioridade, status, aberto_por, responsavel_id, setor_id, observacao_conclusao, criado_em, atualizado_em, fechado_em, predio_id, bp_num_patrimonio, bp_nome_equip, bp_fabricante_modelo, bp_num_serie, bp_categoria, bp_servico, bp_problema_em, bp_rechamado, bp_data_rechamado) FROM stdin;
2	CH2026030001	1	1	\N	predial	Predial: Geral	A Janela não está fechando	media	cancelado	4	\N	\N	Resolvido	2026-03-01 03:08:45.336666	2026-03-01 00:22:11.872458	2026-03-01 03:22:11.873022	1	\N	\N	\N	\N	\N	\N	\N	f	\N
1	CH2026020001	1	\N	1	equipamento	Manutenção: Notebook - Positivo - TST-2026-02-28 [PMS-388466]	Notebook parou de ligar	alta	concluido	2	\N	\N	Realizado!	2026-03-01 02:38:34.417916	2026-03-01 00:28:03.874658	2026-03-01 03:28:03.875693	\N	\N	\N	\N	\N	\N	corretiva	bem	f	\N
4	CH2026030003	1	1	\N	predial	Predial: Geral	JANELA VOLTOU A NÃO ABRIR	media	cancelado	2	\N	\N	TESTE DA FOTO	2026-03-01 04:20:12.276188	2026-03-01 01:25:07.740942	2026-03-01 04:25:07.747255	1	\N	\N	\N	\N	\N	\N	\N	f	\N
3	CH2026030002	1	\N	1	equipamento	Manutenção: Notebook - Positivo - TST-2026-02-28 [PMS-388466]	Sistema operacional travou	media	cancelado	2	\N	\N	A	2026-03-01 04:09:50.160928	2026-03-01 01:30:15.027642	2026-03-01 04:30:15.032189	\N	\N	\N	\N	\N	\N	corretiva	bem	f	\N
5	CH2026030004	1	1	\N	predial	Predial: Geral	JANELA QUEBRADA	media	cancelado	2	\N	\N		2026-03-01 04:25:35.926866	2026-03-02 12:08:14.827728	2026-03-02 15:08:14.828885	1	\N	\N	\N	\N	\N	\N	\N	f	\N
6	CE202603020001	1	\N	1	equipamento	Manutenção: Notebook - Positivo - TST-2026-02-28 [PMS-388466]	CARREGADOR COM CABO CORTADO	media	em_andamento	2	\N	\N	\N	2026-03-02 16:33:25.372359	2026-03-02 13:34:59.841773	\N	\N	\N	\N	\N	\N	\N	corretiva	acessorio	f	\N
7	CP202603020001	1	1	\N	predial	Predial: Geral	goteira no telhado	media	cancelado	2	\N	\N		2026-03-02 17:48:49.896338	2026-03-07 13:27:08.359448	2026-03-07 16:27:08.360192	1	\N	\N	\N	\N	\N	\N	\N	f	\N
\.


--
-- Data for Name: contrato_acoes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contrato_acoes (id, contrato_id, tipo, data_acao, observacao, periodo_dias, nova_data_fim, valor_adicional, porcentagem_adicional, porcentagem_multa, anexo_filename, criado_por, criado_em, periodo_meses) FROM stdin;
1	1	prorrogacao_excepcional	2026-03-05	\N	\N	2026-07-05	\N	\N	\N	\N	4	2026-03-05 23:26:30.233268	6
\.


--
-- Data for Name: contrato_equipamentos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contrato_equipamentos (id, contrato_id, equipamento_id, descricao_cobertura) FROM stdin;
\.


--
-- Data for Name: contrato_financeiro; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contrato_financeiro (id, tipo, processo, motivo, prestador, objeto, referencia, valor_total, especializada, vigilancia, atencao_basica, outros, tabela_sus, complemento, emenda_municipal, emenda_estadual, emenda_federal, observacao, data_necessaria, data_envio_divisao, data_envio_fms, data_devolucao_setor, reservas, criado_em, atualizado_em, contrato_id) FROM stdin;
\.


--
-- Data for Name: contrato_tipos_equipamento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contrato_tipos_equipamento (id, contrato_id, tipo_equipamento_id, descricao_cobertura, marca_id, modelo_id) FROM stdin;
\.


--
-- Data for Name: contratos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contratos (id, numero_sei, empresa, tipo_contrato, objeto, data_inicio, data_fim, valor_total, status, observacoes, criado_por, criado_em, atualizado_em, empresa_id, cpl, link_sei, modalidade, secao, numero_contrato, data_assinatura, vigencia, fonte, valor_inicial, valor_atual, valor_mensal_atual, aditivo_data_pct, reajuste_data_base_pct, fiscalizacao, supressao_data_pct, contato_nome_telefone, empenhos, tag, mandado_judicial) FROM stdin;
1	\N	Vivver Sistemas LTDA	Suporte Técnico e Manutenção de Sistema	SERVIÇOS DE SUPORTE TÉCNICO, MANUTENÇÃO CORRETIVA E MELHORIAS EVOLUTIVAS SOB DEMANDA, PARA O SISTEMA INTEGRADO DE SAÚDE - SIS	2020-01-06	2026-07-05	\N	vigente		4	2026-03-05 22:59:22.49723	2026-03-05 20:26:30.174101	1	424/2020	\N	Inexigibilidade	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f
\.


--
-- Data for Name: divisoes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.divisoes (id, nome, descricao, tipos_chamado, tipos_unidade_ids, ativo, criado_em) FROM stdin;
\.


--
-- Data for Name: documentos_transferencia; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.documentos_transferencia (id, tipo, unidade_origem_id, unidade_destino_id, criado_por, aceito_por, sala_destino_id, status, observacao, observacao_aceite, criado_em, resolvido_em) FROM stdin;
1	transferencia	1	3	2	2	\N	cancelada	\N	Cancelado pelo solicitante.	2026-03-06 17:15:50.591025	2026-03-06 17:17:17.21481
3	transferencia	3	1	2	2	1	aceita	Solicitação a partir da Lojinha Interna.		2026-03-06 17:57:49.847955	2026-03-06 18:00:04.757884
4	doacao	3	1	2	2	\N	cancelada	Solicitação a partir da Lojinha Interna.	Cancelado pelo solicitante.	2026-03-06 18:42:07.907206	2026-03-06 18:56:00.338328
2	transferencia	1	3	2	2	\N	cancelada	\N	Cancelado pelo solicitante.	2026-03-06 17:51:12.802021	2026-03-06 18:56:06.008066
5	doacao	3	1	2	2	1	aceita	Solicitação a partir da Lojinha Interna.		2026-03-06 18:56:20.258162	2026-03-06 18:56:35.234268
\.


--
-- Data for Name: empresas_contratadas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.empresas_contratadas (id, cnpj, razao_social, nome_comum, telefone, email, logo_filename, ativo, criado_em, atualizado_em, endereco, email_suporte, telefone_suporte, logradouro, numero, complemento, bairro, cidade, estado, cep) FROM stdin;
1	03381389000150	Vivver Sistemas LTDA	Suporte SIS	3130253550	contato@vivver.com.br	6d19a2c7febe40ec88f8cfe6ae1cc220.png	t	2026-03-05 22:36:41.612317	2026-03-05 22:36:41.616	\N	suportesis.sorocaba@sorocaba.sp.gov.br	1532382113	Avenida do Contorno	7069	10º Andar	Santo Antônio	Belo Horizonte	MG	30110043
\.


--
-- Data for Name: equipamento_campo_valores; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.equipamento_campo_valores (id, equipamento_id, campo_id, valor) FROM stdin;
\.


--
-- Data for Name: equipamento_usuarios; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.equipamento_usuarios (id, equipamento_id, usuario_id, observacao, vinculado_em) FROM stdin;
1	1	2	\N	2026-02-28 20:36:16.962793
\.


--
-- Data for Name: equipamentos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.equipamentos (id, sala_id, tipo_equipamento_id, numero_patrimonio, numero_serie, marca_id, modelo_id, data_aquisicao, valor_estimado, tempo_uso_anos, status, condicao, observacoes, ativo, criado_por, criado_em, atualizado_em) FROM stdin;
1	1	3	PMS-388466	\N	1	1	2024-12-01	5000.00	1.0	ativo	excelente		t	\N	2026-02-28 20:35:51.467511	2026-02-28 23:15:32.455301
\.


--
-- Data for Name: faltas_abonadas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.faltas_abonadas (id, usuario_id, unidade_id, data_falta, funcao, criado_em, criado_por, status, motivo_cancelamento, cancelado_em, cancelado_por) FROM stdin;
2	2	1	2026-03-20	GERENTE DE PROJETOS DE SAÚDE DIGITAL	2026-03-02 15:53:13.214943	2	ativa	\N	\N	\N
3	2	1	2026-01-30	GERENTE DE PROJETOS DE SAÚDE DIGITAL	2026-03-02 15:59:03.552825	2	ativa	\N	\N	\N
1	4	\N	2026-03-20	GERENTE DE PROJETOS DE SAÚDE DIGITAL	2026-03-02 15:29:48.377973	4	cancelada	Não oficial	2026-03-05 20:04:57.313357	4
\.


--
-- Data for Name: ficha_cnes_vinculo; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ficha_cnes_vinculo (id, usuario_id, unidade_id, tipo, vinculo, tipo_vinculo, carga_horaria, cbo, especialidade_residencia, dt_entrada_unidade, cns_profissional, observacoes, gerado_por, gerado_em, emails_enviados, cnpj_empresa, nome_empresa) FROM stdin;
1	2	1	alteracao	1	1	40	131210	\N	\N	700001893926707	\N	\N	2026-02-28 19:38:27.873973	f	\N	\N
2	2	1	descadastro	\N	\N	\N	\N	\N	\N	\N	\N	\N	2026-02-28 19:38:44.823845	f	\N	\N
3	2	1	cadastro	1	1	40	131210	\N	2025-02-01	700001893926707	\N	\N	2026-02-28 19:41:50.775836	f	\N	\N
4	3	1	cadastro	1	1	40	131210	\N	\N	705002269608351	\N	\N	2026-02-28 19:57:43.789481	f	\N	\N
5	5	2	cadastro	1	1	40	131210	\N	2024-01-01	702302104463015	\N	4	2026-03-01 04:52:32.354408	f	\N	\N
6	6	2	cadastro	1	1	40	322245	\N	2024-01-01	702503346193035	\N	4	2026-03-01 05:03:27.159922	f	\N	\N
7	7	1	cadastro	6	3	25	411005	\N	2025-05-15	700401170454950	\N	2	2026-03-01 06:40:47.58862	f	61600839026545	CIEE (CENTRO DE INTEGRAÇÃO EMPRESA-ESCOLA)
9	9	3	cadastro	1	1	40	131210	\N	2019-01-01	709802065692791	\N	4	2026-03-06 01:41:01.303162	f	\N	\N
10	10	1	cadastro	1	1	40	131210	\N	2021-02-01	704506166754720	\N	2	2026-03-06 15:03:52.883964	f	\N	\N
11	11	4	cadastro	1	1	40	131210	\N	2025-09-01	706804113463030	\N	4	2026-03-07 17:42:53.38305	f	\N	\N
\.


--
-- Data for Name: historico_equipamento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.historico_equipamento (id, equipamento_id, usuario_id, acao, observacao, criado_em) FROM stdin;
1	1	2	Transferência solicitado para UBS Fiori	Documento #1. 	2026-03-06 17:15:50.598518
2	1	2	Transferência cancelado	Cancelado por Diego Bispo Fernandes.	2026-03-06 17:17:17.219796
3	1	2	Transferência solicitado para UBS Fiori	Documento #2. 	2026-03-06 17:51:12.806034
4	1	2	Transferência cancelado	Cancelado por Diego Bispo Fernandes.	2026-03-06 18:56:06.017827
\.


--
-- Data for Name: itens_documento_transferencia; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.itens_documento_transferencia (id, documento_id, equipamento_id, quantidade, descricao, classificacao, numero_patrimonio, numero_serie) FROM stdin;
1	1	1	1	\N	A	\N	\N
2	2	1	1	\N	A	\N	\N
3	3	\N	1	Etiquetadora	A	\N	\N
4	4	\N	1	Etiquetadora	A	\N	\N
5	5	\N	1	Etiquetadora	A	\N	\N
\.


--
-- Data for Name: itens_lojinha; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.itens_lojinha (id, unidade_id, equipamento_id, quantidade, descricao, classificacao, numero_patrimonio, numero_serie, criado_por, criado_em, ativo) FROM stdin;
1	1	1	1	\N	A	\N	\N	2	2026-03-06 17:13:03.617269	f
2	1	\N	2	Teclado USB	A	\N	\N	2	2026-03-06 17:18:08.095422	f
5	3	\N	0	Etiquetadora	A	\N	\N	2	2026-03-06 17:47:10.496805	f
3	1	\N	2	Teclado USB	A	\N	\N	2	2026-03-06 17:41:32.936763	f
4	1	\N	2	Mouse USB	A	\N	\N	2	2026-03-06 17:41:32.936763	f
\.


--
-- Data for Name: links_uteis; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.links_uteis (id, nome, descricao, url, imagem_url, icone, nova_aba, ativo, ordem, perfis_acesso, criado_por, criado_em, atualizado_em, imagem_path, tipo_link_id) FROM stdin;
7	SEI! Cidades - Gerar link para alterar senha	Link para geração de nova senha	https://cidades.sei.sp.gov.br/sorocaba/sip/login_gerar_link_alterar_senha.php?acao=11	\N	bi-link-45deg	t	t	6	["todos"]	\N	2026-03-01 01:43:24.989785	2026-03-01 01:55:19.496644	3547da21a732421d959e44ca41cc1c34.png	1
1	Secretaria da Saúde	Site oficial da Secretaria da Saúde de Sorocaba	https://saude.sorocaba.sp.gov.br/	\N	bi-link-45deg	t	t	0	["todos"]	\N	2026-03-01 01:07:39.845631	2026-03-01 01:55:19.494621	63072ec7292d4748a172749bf02578f0.png	1
8	Extensão Crescer	Extensão para assinaturas digitais do SISWEB	https://chromewebstore.google.com/detail/crescer/jbafkelcjochnjgagbbibeimebiacofl?hl=pt-PT	\N	bi-link-45deg	t	t	7	["todos"]	\N	2026-03-01 01:48:42.039224	2026-03-01 01:55:19.497751	825d129b88d34e90a4a479c6c4860545.png	1
9	Solicitação de Transporte (Zeladoria)	Sistema de Gestão de Transporte Intermunicipal	http://docker.sorocaba.sp.gov.br/zeladoria	\N	bi-link-45deg	t	t	8	["todos"]	\N	2026-03-01 01:50:51.84978	2026-03-01 01:55:19.497751	20b7f77b78154addabecffbbda95d912.png	2
10	Gráficos de Solicitação de Transportes	Análise de Dados de Solicitação de Transportes Zeladoria	https://servicos.sorocaba.sp.gov.br/metabase/dashboard/152-solicitacoes-de-transporte?data_de_agendamento=thisyear	\N	bi-link-45deg	t	t	9	["todos"]	\N	2026-03-01 01:51:59.051155	2026-03-01 01:55:19.497751	e093f0aa9b9242c6ab277ab59204ed7e.png	2
11	Holerite Online	Acesso ao Holerite Online	https://portal.conam.com.br/rhsorocaba/login.php	\N	bi-link-45deg	t	t	10	["todos"]	\N	2026-03-01 02:08:35.275867	2026-03-01 02:08:35.275867	b26bfedaf8e14588a3463d69412277be.png	7
12	Velti (Espelho Ponto)	Sistema de Espelho Ponto	http://frequencia.sorocaba.sp.gov.br/veltiponto/login.jsf	\N	bi-link-45deg	t	t	11	["todos"]	\N	2026-03-01 02:09:44.925986	2026-03-01 02:09:44.925986	23362a67748b4b17a2b4b2b5ffb30f30.png	7
2	SISWEB	Sistema de Gestão Pública de Saúde	https://sisweb.sorocaba.sp.gov.br/	\N	bi-link-45deg	t	t	1	["todos"]	\N	2026-03-01 01:30:31.770421	2026-03-01 01:55:19.494621	fb50f9560ef14aaaa1ff3643e75b47b1.png	1
3	SIS Delphi (Download)	Versão legada do Sistema de Gestão Pública de Saúde	https://drive.google.com/drive/folders/1uogkXL2yJx7zmYlcufRj_PuYTtOupxS2?usp=sharing	\N	bi-link-45deg	t	t	2	["todos"]	\N	2026-03-01 01:32:20.891483	2026-03-01 01:55:19.495637	c59062758f2a44488dadd63a6481e43f.png	1
4	Estante SES	Manuais Institucionais	https://estante-ses.sorocaba.sp.gov.br/books/manuais-de-utilizacao-do-sisweb	\N	bi-link-45deg	t	t	3	["todos"]	\N	2026-03-01 01:33:37.939052	2026-03-01 01:55:19.495637	d8aa789787864f7283f71058ce756d5e.png	1
5	Como configurar o Mozilla Thunderbird	Manual oficial de configuração do Thunderbird	https://drive.google.com/uc?export=download&id=1nBSkQd9HF50rgPmkCpOiGLfzSQsbYXKk	\N	bi-link-45deg	t	t	4	["todos"]	\N	2026-03-01 01:39:39.047573	2026-03-01 01:55:19.496644	abdfda51018d4fefbb8abb59d5005a82.png	1
6	SEI! Cidades	Sistema de Gestão Documental	https://cidades.sei.sp.gov.br/sorocaba/sip/login.php?sigla_orgao_sistema=RASOROCABA&sigla_sistema=SEI&infra_url=L3Nvcm9jYWJhL3NlaS8=	\N	bi-link-45deg	t	t	5	["todos"]	\N	2026-03-01 01:40:35.679656	2026-03-01 01:55:19.496644	7871b2ad19b94321b20147cc2a291b5f.png	1
13	Formulários RH	Formulários Oficiais de Recursos Humanos (Falta Abonada, Justificativa de Horas Extras, etc.)	https://recursoshumanos.sorocaba.sp.gov.br/servidores/formularios/	\N	bi-link-45deg	t	t	12	["todos"]	\N	2026-03-01 02:10:51.432579	2026-03-01 02:10:51.432579	e983e4b753eb46dbb2da7662bb4c06fa.png	7
14	Escola de Gestão Pública EAD	Sistema EAD de Gestão Pública	https://egp.sorocaba.sp.gov.br/	\N	bi-link-45deg	t	t	13	["todos"]	\N	2026-03-01 02:12:07.314251	2026-03-01 02:12:07.314251	5ae66ceeec804a2b89f7261ce25e288c.png	7
\.


--
-- Data for Name: marca_tipo_equipamento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.marca_tipo_equipamento (marca_id, tipo_equipamento_id) FROM stdin;
1	3
\.


--
-- Data for Name: marcas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.marcas (id, nome, criado_em, atualizado_em) FROM stdin;
1	Positivo	2026-02-28 18:48:47.999727	2026-02-28 18:48:47.999727
\.


--
-- Data for Name: matriculas_profissionais; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.matriculas_profissionais (id, usuario_id, numero, vinculo, tipo_vinculo, cbo, reg_conselho, orgao_emissor, ativo, criado_em, atualizado_em) FROM stdin;
1	2	468091	1	1	411005	\N	\N	t	2026-02-28 18:52:16.263106	2026-02-28 19:37:47.003943
2	3	467087	1	1	223605	CREFITO	68713F	t	2026-02-28 19:54:59.421486	2026-02-28 19:54:59.421486
3	5	500564	1	1	322205	2443578	COREN-SP	t	2026-03-01 04:51:53.128249	2026-03-01 04:51:53.128249
4	6	472340	1	1	322245	812022	COREN-SP	t	2026-03-01 05:02:54.521021	2026-03-01 05:02:54.521021
7	9	554790	1	1	223505	405349	COREN-SP	t	2026-03-06 01:32:09.738963	2026-03-06 01:32:09.738963
8	9	468997	1	1	322205	764834	COREN-SP	t	2026-03-06 01:32:54.08259	2026-03-06 01:32:54.08259
9	10	558648	1	1	411005	\N	\N	t	2026-03-06 15:02:33.81525	2026-03-06 15:02:33.81525
10	11	458541	1	1	411005	\N	\N	t	2026-03-07 17:42:14.517301	2026-03-07 17:42:14.517301
\.


--
-- Data for Name: modelos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.modelos (id, marca_id, nome, criado_em, tipo_equipamento_id, atualizado_em) FROM stdin;
1	1	TST-2026-02-28	2026-02-28 18:49:12.234083	3	2026-02-28 18:49:12.234083
\.


--
-- Data for Name: notificacoes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.notificacoes (id, usuario_id, tipo, titulo, texto, chamado_id, lida, criado_em) FROM stdin;
1	3	chamado_aberto	Novo chamado aberto: CH2026030002	Manutenção: Notebook - Positivo - TST-2026-02-28 [PMS-388466]	3	t	2026-03-01 04:09:50.167395
2	3	chamado_aberto	Novo chamado aberto: CH2026030003	Predial: Geral	4	t	2026-03-01 04:20:12.278206
3	3	chamado_aberto	Novo chamado aberto: CH2026030004	Predial: Geral	5	t	2026-03-01 04:25:35.940244
4	2	pedido_info	Nova solicitação de vínculo — Thiago Aparecido Oliveira Hergesel	Thiago Aparecido Oliveira Hergesel solicitou vínculo como profissional na unidade Saúde Digital.	\N	t	2026-03-01 06:39:12.309163
5	3	pedido_info	Nova solicitação de vínculo — Thiago Aparecido Oliveira Hergesel	Thiago Aparecido Oliveira Hergesel solicitou vínculo como profissional na unidade Saúde Digital.	\N	t	2026-03-01 06:39:12.309163
6	3	chamado_aberto	Novo chamado: CE202603020001	Manutenção: Notebook - Positivo - TST-2026-02-28 [PMS-388466]	6	f	2026-03-02 16:33:25.379452
7	3	chamado_aberto	Novo chamado: CP202603020001	Predial: Geral	7	f	2026-03-02 17:48:49.902447
8	10	chamado_aberto	Chamado em aberto: CP202603020001	Predial: Geral	7	t	2026-03-06 15:03:52.896732
9	10	chamado_aberto	Chamado em aberto: CE202603020001	Manutenção: Notebook - Positivo - TST-2026-02-28 [PMS-388466]	6	t	2026-03-06 15:03:52.896732
\.


--
-- Data for Name: perfil_permissoes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.perfil_permissoes (perfil, secao, ver, editar, adicionar) FROM stdin;
administrador	Unidades	t	t	t
administrador	Salas	t	t	t
administrador	Equipamentos	t	t	t
administrador	Chamados	t	t	t
administrador	Contratos	t	t	t
administrador	Usuários	t	t	t
administrador	Relatórios	t	f	f
administrador	Configurações	t	t	t
administrador	Transferências	t	t	t
administrador	Planejamentos	t	t	t
administrador	Auditoria	t	f	f
gestor_secretaria	Unidades	t	f	f
gestor_secretaria	Salas	f	f	f
gestor_secretaria	Equipamentos	f	f	f
gestor_secretaria	Chamados	t	t	f
gestor_secretaria	Contratos	t	t	t
gestor_secretaria	Usuários	t	f	t
gestor_secretaria	Relatórios	t	f	f
gestor_secretaria	Configurações	f	f	f
gestor_secretaria	Transferências	t	t	t
gestor_secretaria	Planejamentos	t	t	t
gestor_secretaria	Auditoria	f	f	f
coordenador	Unidades	t	f	f
coordenador	Salas	t	t	t
coordenador	Equipamentos	t	t	t
coordenador	Chamados	t	t	t
coordenador	Contratos	f	f	f
coordenador	Usuários	t	f	t
coordenador	Relatórios	t	f	f
coordenador	Configurações	f	f	f
coordenador	Transferências	t	t	t
coordenador	Planejamentos	t	t	t
coordenador	Auditoria	f	f	f
administrativo	Unidades	t	f	f
administrativo	Salas	t	f	f
administrativo	Equipamentos	t	t	t
administrativo	Chamados	t	t	t
administrativo	Contratos	f	f	f
administrativo	Usuários	t	f	t
administrativo	Relatórios	f	f	f
administrativo	Configurações	f	f	f
administrativo	Transferências	t	t	t
administrativo	Planejamentos	t	t	t
administrativo	Auditoria	f	f	f
profissional	Unidades	t	f	f
profissional	Salas	t	f	f
profissional	Equipamentos	t	f	f
profissional	Chamados	t	f	t
profissional	Contratos	f	f	f
profissional	Usuários	f	f	f
profissional	Relatórios	f	f	f
profissional	Configurações	f	f	f
profissional	Transferências	f	f	f
profissional	Planejamentos	t	t	t
profissional	Auditoria	f	f	f
\.


--
-- Data for Name: planejamentos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.planejamentos (id, unidade_id, titulo, descricao, gravidade, urgencia, tendencia, criado_por, criado_em, atualizado_por, atualizado_em) FROM stdin;
1	1	Implantação do PEC nos CAPS	\N	2	2	1	4	2026-03-05 19:44:59.2789	2	2026-03-06 15:51:32.273214
2	1	Problema de Transmissão de Vacinas RNDS	\N	5	4	5	2	2026-03-06 15:08:18.206874	2	2026-03-06 20:15:20.178486
\.


--
-- Data for Name: planejamentos_anexos; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.planejamentos_anexos (id, planejamento_id, filename, original, mime_type, criado_em) FROM stdin;
1	2	f0c8062d0ea34aaab8b38f7028390c3e.pdf	Sorocaba SP - Chamado RNDS RIA Problema de Token.pdf	application/pdf	2026-03-06 15:35:11.793226
\.


--
-- Data for Name: predios; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.predios (id, nome, endereco, numero, bairro, cidade, uf, cep, telefone, responsavel_predial_id, observacoes, ativo, criado_em, link_maps, atualizado_em, complemento) FROM stdin;
2	Secretaria da Saúde	Avenida Engenheiro Carlos Reinaldo Mendes	3041	Alto da Boa Vista	Sorocaba	SP	18013-280	(15) 3238-2332	\N	\N	t	2026-03-07 16:10:48.217812	https://maps.app.goo.gl/vrZNmykxz7AaDNAP6	2026-03-07 16:20:41.76104	2º Andar
1	Palácio da Saúde	Rua da Penha	1176	Centro	Sorocaba	SP	18010-004	(15) 3238-2771	\N	\N	t	2026-02-28 18:40:47.33543	https://maps.app.goo.gl/EoLRkoAPt6CPas8U6	2026-03-07 16:23:18.07242	\N
\.


--
-- Data for Name: salas; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.salas (id, unidade_id, nome, tipo, responsavel, ativo, observacoes, criado_em, atualizado_em, tipo_sala_id, ramal) FROM stdin;
2	2	Consultório 1	Consultório		t		2026-03-01 04:46:55.183918	2026-03-01 04:46:55.183918	2	\N
3	2	Consultório 2	Consultório		t		2026-03-01 04:47:03.848723	2026-03-01 01:47:13.630739	2	\N
1	1	Sala 05	Administrativa		t		2026-02-28 20:32:23.080139	2026-03-07 13:24:57.319686	1	\N
4	4	Seção de Aquisição e Manutenção de Equipamentos e Mobiliários	Administrativa		t		2026-03-07 17:46:20.345846	2026-03-07 17:46:20.345846	1	\N
\.


--
-- Data for Name: setores_manutencao; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.setores_manutencao (id, nome, descricao, tipos_chamado, criado_em, divisao_id) FROM stdin;
\.


--
-- Data for Name: solicitacoes_vinculo; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.solicitacoes_vinculo (id, unidade_id, status, nome, email, cpf, cns, sexo, data_nasc, nome_mae, nome_pai, nacionalidade, municipio_nasc, uf_nasc, rg, rg_uf, rg_orgao, rg_emissao, escolaridade, end_logradouro, end_numero, end_bairro, end_municipio, end_uf, end_cep, telefone, orgao_emissor, reg_conselho, cbo, vinculo, tipo_vinculo, carga_horaria, cnpj_empresa, nome_empresa, dt_entrada, criado_em, aprovado_por, aprovado_em, usuario_criado, observacao, dt_entrada_pais, pais_origem, assinatura_base64) FROM stdin;
1	1	aprovado	Thiago Aparecido Oliveira Hergesel	thiago2005hergesel@gmail.com	540.450.048-40	700401170454950	M	2005-07-15	Eva Vilma Mendes de Oliveira Hergesel	Valdeci Fogaça Hergesel	brasileira	Sorocaba	SP	636245809	SP	SSP	\N	07	Rua Antonio Caetano	179	Parque Jatai	Votorantim	SP	18117242	(15) 99850-9546	\N	\N	411005	6	3	25	61600839026545	CIEE (CENTRO DE INTEGRAÇÃO EMPRESA-ESCOLA)	2025-05-15	2026-03-01 06:39:12.29732	2	2026-03-01 06:40:47.587396	7	\N	\N	\N	\N
\.


--
-- Data for Name: status_chamados; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.status_chamados (id, slug, label, badge_cor, ativo, padrao_listagem, encerra_chamado, ordem, criado_em) FROM stdin;
1	aberto	Aberto	danger	t	t	f	0	2026-03-01 03:31:55.139555
2	em_andamento	Em Andamento	warning	t	t	f	1	2026-03-01 03:31:55.141912
3	sem_contrato	Sem Contrato	info	t	t	f	2	2026-03-01 03:31:55.14292
4	concluido	Concluido	success	t	f	t	3	2026-03-01 03:31:55.144185
5	cancelado	Cancelado	secondary	t	f	t	4	2026-03-01 03:31:55.144185
6	aguardando_peca	Aguardando Peca	info	f	f	f	5	2026-03-01 03:31:55.145269
\.


--
-- Data for Name: tipos_equipamento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipos_equipamento (id, nome, descricao, tem_patrimonio, icone, criado_em, ativo, atualizado_em) FROM stdin;
1	Computador (Gabinete)		t	bi-pc	2026-02-28 18:45:36.648737	t	2026-02-28 18:45:36.648737
2	All-In-One		t	bi-pc-display-horizontal	2026-02-28 18:46:12.515629	t	2026-02-28 18:46:12.515629
3	Notebook		t	bi-laptop	2026-02-28 18:46:39.898567	t	2026-02-28 18:46:39.898567
4	Monitor		t	bi-display	2026-02-28 18:46:57.83211	t	2026-02-28 18:46:57.83211
5	TV		t	bi-tv	2026-02-28 18:47:19.651977	t	2026-02-28 18:47:19.651977
6	Impressora		t	bi-printer	2026-02-28 18:48:09.14997	t	2026-02-28 18:48:09.14997
7	Ar-condicionado		t	bi-wind	2026-02-28 20:51:45.702513	t	2026-02-28 20:51:45.702513
\.


--
-- Data for Name: tipos_link; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipos_link (id, nome, descricao, icone, cor, ordem, ativo, criado_em, atualizado_em) FROM stdin;
1	MAIS UTILIZADOS	\N	bi-award	#1a6abf	0	t	2026-03-01 01:17:42.888904	2026-03-01 02:06:56.006547
4	AMBIENTES DE TREINO	\N	bi-book	#1a6abf	1	t	2026-03-01 02:04:09.799662	2026-03-01 02:06:56.007553
2	SEÇÃO DE TRANSPORTE	\N	bi-truck	#1a6abf	2	t	2026-03-01 01:27:41.574875	2026-03-01 02:06:56.008775
5	OUTROS SISTEMAS	\N	bi-boxes	#1a6abf	3	t	2026-03-01 02:04:49.002109	2026-03-01 02:06:56.009772
6	FORMULÁRIOS SES	\N	bi-journal-bookmark	#1a6abf	4	t	2026-03-01 02:06:51.734267	2026-03-01 02:06:56.009772
3	APOIO ADMINISTRATIVO	\N	bi-folder	#1a6abf	5	t	2026-03-01 01:52:53.243081	2026-03-01 02:06:56.009772
7	RECURSOS HUMANOS	\N	bi-person-check	#1a6abf	6	t	2026-03-01 02:07:37.466109	2026-03-01 02:07:37.466109
\.


--
-- Data for Name: tipos_sala; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipos_sala (id, nome, descricao, icone, ativo, criado_em, atualizado_em) FROM stdin;
1	Administrativa	\N	bi-pen	t	2026-02-28 18:42:45.4811	2026-02-28 18:42:45.4811
2	Consultório	\N	bi-file-medical	t	2026-02-28 18:44:43.94782	2026-02-28 18:44:43.94782
\.


--
-- Data for Name: tipos_unidade; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipos_unidade (id, nome, sigla, descricao, ativo, criado_em, atualizado_em) FROM stdin;
1	Atenção Primária à Saúde	APS	Unidades de Atenção Primária a Saúde	t	2026-02-28 18:41:38.396397	2026-02-28 18:41:38.396397
2	Administração	ADM	Setores Administrativos	t	2026-02-28 18:41:56.496536	2026-02-28 18:41:56.496536
\.


--
-- Data for Name: transferencias_equipamento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.transferencias_equipamento (id, equipamento_id, sala_origem_id, sala_destino_id, unidade_origem_id, unidade_destino_id, solicitado_por, aceito_por, status, observacao, observacao_aceite, criado_em, resolvido_em) FROM stdin;
\.


--
-- Data for Name: unidades; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.unidades (id, nome, tipo, endereco, numero, bairro, cidade, uf, cep, telefone, email, status, observacoes, criado_em, atualizado_em, tipo_unidade_id, predio_id, link_maps, numero_cnes, ramal, complemento) FROM stdin;
1	Saúde Digital	ADM	Rua da Penha	1176	Centro	Sorocaba	SP	18010-004	(15) 3238-2771	saudedigital@sorocaba.sp.gov.br	ativa		2026-02-28 19:27:33.180888	2026-02-28 17:24:59.065784	2	1	https://www.google.com/maps/place/Pal%C3%A1cio+da+Sa%C3%BAde+Municipal+%7C+Sorocaba/@-23.5022632,-47.4649645,17z/data=!4m14!1m7!3m6!1s0x94c58b9b418c8dc7:0xf6ad17af2fbb79cc!2sPal%C3%A1cio+da+Sa%C3%BAde+Municipal+%7C+Sorocaba!8m2!3d-23.5022632!4d-47.4649645!16s%2Fg%2F11vf3dg9yb!3m5!1s0x94c58b9b418c8dc7:0xf6ad17af2fbb79cc!8m2!3d-23.5022632!4d-47.4649645!16s%2Fg%2F11vf3dg9yb?entry=ttu&g_ep=EgoyMDI2MDIyNS4wIKXMDSoASAFQAw%3D%3D	5697107	2817	\N
2	USF Brigadeiro Tobias	APS	Rua Ana Gomes Correa	55	Brigadeiro Tobias	Sorocaba	SP	18108-185	(15) 3236-6005	csbrigadeirotobias@sorocaba.sp.gov.br	ativa		2026-03-01 04:46:36.352921	2026-03-01 04:46:36.352921	1	\N	https://maps.app.goo.gl/UhZ7FP4GcKy2CGvT9	2070693	\N	\N
3	UBS Fiori	APS	Rua André Manente	20	Vila Olímpia	Sorocaba	SP	18075-130	(15) 3235-7171	csfiore@sorocaba.sp.gov.br	ativa		2026-03-06 00:52:35.613796	2026-03-06 00:52:35.613796	1	\N	https://maps.app.goo.gl/hiFhniAXkJgeP6PG6	2055678	\N	\N
4	Divisão de Administração e Gestão	ADM	Avenida Engenheiro Carlos Reinaldo Mendes	3041	Alto da Boa Vista	Sorocaba	SP	18013-280	(15) 3238-2332		ativa		2026-03-07 16:16:14.104834	2026-03-07 16:16:14.104834	2	2	https://maps.app.goo.gl/vrZNmykxz7AaDNAP6	5697107	2249	\N
\.


--
-- Data for Name: usuario_setor; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.usuario_setor (usuario_id, setor_id) FROM stdin;
\.


--
-- Data for Name: usuario_unidade; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.usuario_unidade (id, usuario_id, unidade_id, papel, ativo, vinculado_em, matricula_id) FROM stdin;
1	2	1	gerente	t	2026-02-28 19:27:33.183016	1
2	3	1	\N	t	2026-02-28 19:57:43.790543	2
3	5	2	\N	t	2026-03-01 04:52:32.356757	3
4	6	2	\N	t	2026-03-01 05:03:27.159922	4
5	7	1	\N	t	2026-03-01 06:40:47.58493	\N
7	9	3	\N	t	2026-03-06 01:41:01.304664	7
8	10	1	\N	t	2026-03-06 15:03:52.887502	9
9	11	4	\N	t	2026-03-07 17:42:53.38705	10
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.usuarios (id, nome, email, senha_hash, perfil, ativo, criado_em, atualizado_em, whatsapp, cpf, cns, sexo, data_nasc, nome_mae, nome_pai, nacionalidade, uf_nasc, municipio_nasc, dt_entrada_pais, pais_origem, rg, rg_uf, rg_orgao, rg_emissao, escolaridade, end_logradouro, end_numero, end_complemento, end_bairro, end_municipio, end_uf, end_cep, telefone, reg_conselho, orgao_emissor, vinculo, tipo_vinculo, carga_horaria, cbo, especialidade_residencia, dt_entrada_unidade, matricula, frequenta_escola, foto_perfil, unidade_padrao_id) FROM stdin;
5	Elisangela de Góes Souza	egsouza@sorocaba.sp.gov.br	scrypt:32768:8:1$vqly7Ziu0vdbhW4s$4d52529c0351242df4aef1fe0295d8f67225a7a25745620f82f2990ef8a2819508de2fe86ead8e65b826031e79e05f91fc8ace981ea163faca3a67fadfa9aea3	coordenador	t	2026-03-01 04:50:41.846304	2026-03-01 03:05:53.3454	15991134283	290.075.238-80	702302104463015	F	1979-08-01	Zelita de Souza Góes	Vicente de Góes	brasileira	SP	Sorocaba	\N	\N	\N	\N	\N	\N	08	Rua Manoel Rodrigues Peres	74	\N	Brigadeiro Tobias	Sorocaba	SP	18108231	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f	b1d32d6c8a004dd7ada4e3c6cc370000.jpg	\N
3	Camila Cruz	cacruz@sorocaba.sp.gov.br	scrypt:32768:8:1$ygji35194JsVFaFi$4cd88842eb9bebd52287932d71851342139cf5c0161fc749fc357dc3c9f18e7a9227bced7f9f55e95c6f820964a2b8d63f7b6e1d19dea6e5a079e5cf42e2f476	coordenador	t	2026-02-28 19:50:27.777104	2026-03-01 03:06:38.267347	15991174799	29573551837	705002269608351	F	1980-09-28	Nadia Sofia Martins Cruz	Osvaldo Cruz da Cunha	brasileira	SP	Sorocaba	\N	\N	\N	\N	\N	\N	09	Avenida Dr. Armando Pannunzio	1893	Ap 401 Bloco 07	Jardim Vera Cruz	Sorocaba	SP	1805000	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f	85cb9354b7494e69ac78df138a9d06bb.jpg	\N
7	Thiago Aparecido Oliveira Hergesel	thiago2005hergesel@gmail.com	scrypt:32768:8:1$MLmqXdWbymQh9hdq$46dc3b3cb27f48a2ae5df0144c252c90df4a43779add033a7090faaa8bdd30f9411894fa0ddb27e45a4a5c5a7f568a95fcb41f75958992b41b0bdfcc7a1b5e8e	profissional	t	2026-03-01 06:40:47.581602	2026-03-01 06:40:47.581602	\N	540.450.048-40	700401170454950	M	2005-07-15	Eva Vilma Mendes de Oliveira Hergesel	Valdeci Fogaça Hergesel	brasileira	SP	Sorocaba	\N	\N	636245809	SP	SSP	\N	07	Rua Antonio Caetano	179	\N	Parque Jatai	Votorantim	SP	18117242	(15) 99850-9546	\N	\N	6	3	25	411005	\N	\N	\N	\N	\N	\N
4	Administrador SIGUS	administrador.sigus@sorocaba.sp.gov.br	scrypt:32768:8:1$ycGBqPkZun3dC2k5$ad3f14b37f89f1c3045fb1e952d3b0a5c06caac0fa72a8b82ca083c7a9c3063ae13d767b2c80f5bc8c1effded586b013054278c504676508846701ef0e059616	administrador	t	2026-03-01 02:15:55.873627	2026-03-12 15:37:29.017321	\N	\N	\N	\N	\N	\N	\N	brasileira	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	0040f3f7ccf143d38753efd32e70f9fa.png	1
6	Adla Meyrielle Barros de Siqueira	adsiqueira@sorocaba.sp.gov.br	scrypt:32768:8:1$i36ILoIOsrLhA95g$2b20acaaa4ca7cc6e0f1e5337800f121e8dd6b5b4e707a2eb84320035b45b45fc17e273ada9e6cec1d3f5830a20129c20cb59544d61827bab77d518685543a8a	profissional	t	2026-03-01 05:00:06.999538	2026-03-01 02:40:53.643866	11974246026	33597224857	702503346193035	F	1986-02-02	Ivanira Barros Cordeiro de Siqueira	Victor Olegario de Siqueira	brasileira	PE	Itapetim	\N	\N	339522975	SP	SSP	2003-08-02	07	Rodovia Raposo Tavares	340	KM 65	Marmeleiro	Mairinque	SP	18120901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	t	110bb8f0fd064e538ac8ecd1b831a29b.jpg	\N
2	Diego Bispo Fernandes	dbispo@sorocaba.sp.gov.br	scrypt:32768:8:1$J3K8EqjuRz8YMJeA$6f679111bf6ac091a754be9d25503af844d2fa15adc7b6d5c73e1627f94731226e0e2836b15f3313e640e5a26347a1db49d4b43df0c27491e661350c14d39d9f	gestor_secretaria	t	2026-02-28 18:50:30.830398	2026-03-06 14:49:05.265379	11995673131	33273576847	700001893926707	M	1990-12-13	Ivanilda Galindo Bispo Fernandes	Eloni José Fernandes	brasileira	SP	São Roque	\N	\N	477136229	SP	SSP	2002-03-23	09	Rua Ida Taraborelli	452	\N	Jardim Alvorada	Alumínio	SP	18126174	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f	5d2e6468ae644515afc4c3f17f7692b7.jpg	1
9	Caroline Abes Sant'Ana	caroline.abes@sorocaba.sp.gov.br	scrypt:32768:8:1$zD7xROg72ztpVIdU$0f84d7b499e4eb4ca0f7af7288fe09ebdde0c2342776e779053be52b8dce2df29cc1fa84122efc4fd74eb0afb54cb8e49a68f6909e85ce953c34fe76157517d9	coordenador	t	2026-03-06 01:31:04.250891	2026-03-06 01:31:04.250891	15991075165	38262633830	709802065692791	F	1989-03-17	Lucimara Abes Sant'Ana	Doraci Sant'Ana	brasileira	SP	Sorocaba	\N	\N	\N	\N	\N	\N	09	Rua Manoel Lopes	377	\N	Vila Hortência	Sorocaba	SP	18020-218	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f	\N	\N
10	Ricardo Rocha	rirocha@sorocaba.sp.gov.br	scrypt:32768:8:1$4JyMim56Ij4hywY4$6302736a8c7fb846089c52b6abe9b613be2d5bda1dfbd1fe2c22ba0464443ccf089c0dab3ad19e8f0a513f59028bd079ef4d21c75344016574b80a717a5965d7	gestor_secretaria	t	2026-03-06 15:00:46.453158	2026-03-06 12:06:25.718587	15997791449	30446138843	704506166754720	M	1982-02-27	Salvadora Teixeira Rocha	Vicente Barbosa Rocha	brasileira	SP	São Paulo	\N	\N	\N	\N	\N	\N	08	Avenida Engenheiro Carlos Reinaldo Mendes	3038	\N	Além Ponte	Sorocaba	SP	18013280	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f	6f4b7737d35b40b5bb8e77cb746c2116.jpg	\N
11	Évelyn de Oliveira Moraes	emoraes@sorocaba.sp.gov.br	scrypt:32768:8:1$RxY0mPVf9vegIwuQ$84845c67ff15661bdf838a05e9ed01ed8fb14049ad3bc61d7de20034d6168188d81c11779ed7acc9013ff1463bd109a19b9ec23e2eb7bca5c2676e5b6222007a	gestor_secretaria	t	2026-03-07 17:40:35.160397	2026-03-07 17:40:35.160397	15988000802	37345759822	706804113463030	F	1989-02-27	Eliceia de Oliveira Moraes Feliciano	\N	brasileira	SP	SOROCABA	\N	\N	\N	\N	\N	\N	08	Rua Armando Landulfo	196	\N	Jardim Ibiti do Paço	Sorocaba	SP	18086230	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f	\N	\N
\.


--
-- Name: acoes_plano_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.acoes_plano_id_seq', 3, true);


--
-- Name: acoes_plano_obs_anexos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.acoes_plano_obs_anexos_id_seq', 1, false);


--
-- Name: acoes_plano_observacoes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.acoes_plano_observacoes_id_seq', 3, true);


--
-- Name: andamento_anexos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.andamento_anexos_id_seq', 1, false);


--
-- Name: auditoria_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auditoria_id_seq', 390, true);


--
-- Name: campos_tipo_equipamento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.campos_tipo_equipamento_id_seq', 2, true);


--
-- Name: chamado_fotos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.chamado_fotos_id_seq', 1, true);


--
-- Name: chamado_historico_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.chamado_historico_id_seq', 16, true);


--
-- Name: chamados_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.chamados_id_seq', 7, true);


--
-- Name: contrato_acoes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contrato_acoes_id_seq', 1, true);


--
-- Name: contrato_equipamentos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contrato_equipamentos_id_seq', 1, false);


--
-- Name: contrato_financeiro_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contrato_financeiro_id_seq', 1, false);


--
-- Name: contrato_tipos_equipamento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contrato_tipos_equipamento_id_seq', 1, false);


--
-- Name: contratos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contratos_id_seq', 1, true);


--
-- Name: divisoes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.divisoes_id_seq', 1, false);


--
-- Name: documentos_transferencia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.documentos_transferencia_id_seq', 5, true);


--
-- Name: empresas_contratadas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.empresas_contratadas_id_seq', 1, true);


--
-- Name: equipamento_campo_valores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.equipamento_campo_valores_id_seq', 1, false);


--
-- Name: equipamento_usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.equipamento_usuarios_id_seq', 1, true);


--
-- Name: equipamentos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.equipamentos_id_seq', 1, true);


--
-- Name: faltas_abonadas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.faltas_abonadas_id_seq', 3, true);


--
-- Name: ficha_cnes_vinculo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ficha_cnes_vinculo_id_seq', 11, true);


--
-- Name: historico_equipamento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.historico_equipamento_id_seq', 4, true);


--
-- Name: itens_documento_transferencia_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.itens_documento_transferencia_id_seq', 5, true);


--
-- Name: itens_lojinha_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.itens_lojinha_id_seq', 5, true);


--
-- Name: links_uteis_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.links_uteis_id_seq', 14, true);


--
-- Name: marcas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.marcas_id_seq', 1, true);


--
-- Name: matriculas_profissionais_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.matriculas_profissionais_id_seq', 10, true);


--
-- Name: modelos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.modelos_id_seq', 1, true);


--
-- Name: notificacoes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.notificacoes_id_seq', 9, true);


--
-- Name: planos_anexos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.planos_anexos_id_seq', 1, true);


--
-- Name: planos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.planos_id_seq', 2, true);


--
-- Name: predios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.predios_id_seq', 2, true);


--
-- Name: salas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.salas_id_seq', 4, true);


--
-- Name: setores_manutencao_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.setores_manutencao_id_seq', 1, false);


--
-- Name: solicitacoes_vinculo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.solicitacoes_vinculo_id_seq', 1, true);


--
-- Name: status_chamados_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.status_chamados_id_seq', 6, true);


--
-- Name: tipos_equipamento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tipos_equipamento_id_seq', 7, true);


--
-- Name: tipos_link_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tipos_link_id_seq', 7, true);


--
-- Name: tipos_sala_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tipos_sala_id_seq', 2, true);


--
-- Name: tipos_unidade_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tipos_unidade_id_seq', 2, true);


--
-- Name: transferencias_equipamento_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.transferencias_equipamento_id_seq', 1, false);


--
-- Name: unidades_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.unidades_id_seq', 4, true);


--
-- Name: usuario_unidade_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuario_unidade_id_seq', 9, true);


--
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 11, true);


--
-- Name: acao_planejamento_empresas acacao_empresas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acao_planejamento_empresas
    ADD CONSTRAINT acacao_empresas_pkey PRIMARY KEY (acao_id, empresa_id);


--
-- Name: acao_planejamento_responsaveis acacao_responsaveis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acao_planejamento_responsaveis
    ADD CONSTRAINT acacao_responsaveis_pkey PRIMARY KEY (acao_id, usuario_id);


--
-- Name: acoes_planejamento_obs_anexos acoes_plano_obs_anexos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acoes_planejamento_obs_anexos
    ADD CONSTRAINT acoes_plano_obs_anexos_pkey PRIMARY KEY (id);


--
-- Name: acoes_planejamento_observacoes acoes_plano_observacoes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acoes_planejamento_observacoes
    ADD CONSTRAINT acoes_plano_observacoes_pkey PRIMARY KEY (id);


--
-- Name: acoes_planejamento acoes_plano_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acoes_planejamento
    ADD CONSTRAINT acoes_plano_pkey PRIMARY KEY (id);


--
-- Name: andamento_anexos andamento_anexos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.andamento_anexos
    ADD CONSTRAINT andamento_anexos_pkey PRIMARY KEY (id);


--
-- Name: auditoria auditoria_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT auditoria_pkey PRIMARY KEY (id);


--
-- Name: campos_tipo_equipamento campos_tipo_equipamento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campos_tipo_equipamento
    ADD CONSTRAINT campos_tipo_equipamento_pkey PRIMARY KEY (id);


--
-- Name: chamado_fotos chamado_fotos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamado_fotos
    ADD CONSTRAINT chamado_fotos_pkey PRIMARY KEY (id);


--
-- Name: chamado_historico chamado_historico_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamado_historico
    ADD CONSTRAINT chamado_historico_pkey PRIMARY KEY (id);


--
-- Name: chamados chamados_numero_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamados
    ADD CONSTRAINT chamados_numero_key UNIQUE (numero);


--
-- Name: chamados chamados_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamados
    ADD CONSTRAINT chamados_pkey PRIMARY KEY (id);


--
-- Name: contrato_acoes contrato_acoes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_acoes
    ADD CONSTRAINT contrato_acoes_pkey PRIMARY KEY (id);


--
-- Name: contrato_equipamentos contrato_equipamentos_contrato_id_equipamento_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_equipamentos
    ADD CONSTRAINT contrato_equipamentos_contrato_id_equipamento_id_key UNIQUE (contrato_id, equipamento_id);


--
-- Name: contrato_equipamentos contrato_equipamentos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_equipamentos
    ADD CONSTRAINT contrato_equipamentos_pkey PRIMARY KEY (id);


--
-- Name: contrato_financeiro contrato_financeiro_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_financeiro
    ADD CONSTRAINT contrato_financeiro_pkey PRIMARY KEY (id);


--
-- Name: contrato_tipos_equipamento contrato_tipos_equipamento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_tipos_equipamento
    ADD CONSTRAINT contrato_tipos_equipamento_pkey PRIMARY KEY (id);


--
-- Name: contratos contratos_numero_sei_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT contratos_numero_sei_key UNIQUE (numero_sei);


--
-- Name: contratos contratos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT contratos_pkey PRIMARY KEY (id);


--
-- Name: divisoes divisoes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.divisoes
    ADD CONSTRAINT divisoes_pkey PRIMARY KEY (id);


--
-- Name: documentos_transferencia documentos_transferencia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentos_transferencia
    ADD CONSTRAINT documentos_transferencia_pkey PRIMARY KEY (id);


--
-- Name: empresas_contratadas empresas_contratadas_cnpj_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresas_contratadas
    ADD CONSTRAINT empresas_contratadas_cnpj_key UNIQUE (cnpj);


--
-- Name: empresas_contratadas empresas_contratadas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empresas_contratadas
    ADD CONSTRAINT empresas_contratadas_pkey PRIMARY KEY (id);


--
-- Name: equipamento_campo_valores equipamento_campo_valores_equipamento_id_campo_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamento_campo_valores
    ADD CONSTRAINT equipamento_campo_valores_equipamento_id_campo_id_key UNIQUE (equipamento_id, campo_id);


--
-- Name: equipamento_campo_valores equipamento_campo_valores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamento_campo_valores
    ADD CONSTRAINT equipamento_campo_valores_pkey PRIMARY KEY (id);


--
-- Name: equipamento_usuarios equipamento_usuarios_equipamento_id_usuario_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamento_usuarios
    ADD CONSTRAINT equipamento_usuarios_equipamento_id_usuario_id_key UNIQUE (equipamento_id, usuario_id);


--
-- Name: equipamento_usuarios equipamento_usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamento_usuarios
    ADD CONSTRAINT equipamento_usuarios_pkey PRIMARY KEY (id);


--
-- Name: equipamentos equipamentos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamentos
    ADD CONSTRAINT equipamentos_pkey PRIMARY KEY (id);


--
-- Name: faltas_abonadas faltas_abonadas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faltas_abonadas
    ADD CONSTRAINT faltas_abonadas_pkey PRIMARY KEY (id);


--
-- Name: ficha_cnes_vinculo ficha_cnes_vinculo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ficha_cnes_vinculo
    ADD CONSTRAINT ficha_cnes_vinculo_pkey PRIMARY KEY (id);


--
-- Name: historico_equipamento historico_equipamento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historico_equipamento
    ADD CONSTRAINT historico_equipamento_pkey PRIMARY KEY (id);


--
-- Name: itens_documento_transferencia itens_documento_transferencia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itens_documento_transferencia
    ADD CONSTRAINT itens_documento_transferencia_pkey PRIMARY KEY (id);


--
-- Name: itens_lojinha itens_lojinha_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itens_lojinha
    ADD CONSTRAINT itens_lojinha_pkey PRIMARY KEY (id);


--
-- Name: links_uteis links_uteis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.links_uteis
    ADD CONSTRAINT links_uteis_pkey PRIMARY KEY (id);


--
-- Name: marca_tipo_equipamento marca_tipo_equipamento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.marca_tipo_equipamento
    ADD CONSTRAINT marca_tipo_equipamento_pkey PRIMARY KEY (marca_id, tipo_equipamento_id);


--
-- Name: marcas marcas_nome_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.marcas
    ADD CONSTRAINT marcas_nome_key UNIQUE (nome);


--
-- Name: marcas marcas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.marcas
    ADD CONSTRAINT marcas_pkey PRIMARY KEY (id);


--
-- Name: matriculas_profissionais matriculas_profissionais_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.matriculas_profissionais
    ADD CONSTRAINT matriculas_profissionais_pkey PRIMARY KEY (id);


--
-- Name: modelos modelos_marca_id_nome_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modelos
    ADD CONSTRAINT modelos_marca_id_nome_key UNIQUE (marca_id, nome);


--
-- Name: modelos modelos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modelos
    ADD CONSTRAINT modelos_pkey PRIMARY KEY (id);


--
-- Name: notificacoes notificacoes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notificacoes
    ADD CONSTRAINT notificacoes_pkey PRIMARY KEY (id);


--
-- Name: perfil_permissoes perfil_permissoes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.perfil_permissoes
    ADD CONSTRAINT perfil_permissoes_pkey PRIMARY KEY (perfil, secao);


--
-- Name: planejamentos_anexos planos_anexos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.planejamentos_anexos
    ADD CONSTRAINT planos_anexos_pkey PRIMARY KEY (id);


--
-- Name: planejamentos planos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.planejamentos
    ADD CONSTRAINT planos_pkey PRIMARY KEY (id);


--
-- Name: predios predios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predios
    ADD CONSTRAINT predios_pkey PRIMARY KEY (id);


--
-- Name: salas salas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salas
    ADD CONSTRAINT salas_pkey PRIMARY KEY (id);


--
-- Name: setores_manutencao setores_manutencao_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setores_manutencao
    ADD CONSTRAINT setores_manutencao_pkey PRIMARY KEY (id);


--
-- Name: solicitacoes_vinculo solicitacoes_vinculo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solicitacoes_vinculo
    ADD CONSTRAINT solicitacoes_vinculo_pkey PRIMARY KEY (id);


--
-- Name: status_chamados status_chamados_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.status_chamados
    ADD CONSTRAINT status_chamados_pkey PRIMARY KEY (id);


--
-- Name: status_chamados status_chamados_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.status_chamados
    ADD CONSTRAINT status_chamados_slug_key UNIQUE (slug);


--
-- Name: tipos_equipamento tipos_equipamento_nome_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipos_equipamento
    ADD CONSTRAINT tipos_equipamento_nome_key UNIQUE (nome);


--
-- Name: tipos_equipamento tipos_equipamento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipos_equipamento
    ADD CONSTRAINT tipos_equipamento_pkey PRIMARY KEY (id);


--
-- Name: tipos_link tipos_link_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipos_link
    ADD CONSTRAINT tipos_link_pkey PRIMARY KEY (id);


--
-- Name: tipos_sala tipos_sala_nome_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipos_sala
    ADD CONSTRAINT tipos_sala_nome_key UNIQUE (nome);


--
-- Name: tipos_sala tipos_sala_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipos_sala
    ADD CONSTRAINT tipos_sala_pkey PRIMARY KEY (id);


--
-- Name: tipos_unidade tipos_unidade_nome_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipos_unidade
    ADD CONSTRAINT tipos_unidade_nome_key UNIQUE (nome);


--
-- Name: tipos_unidade tipos_unidade_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipos_unidade
    ADD CONSTRAINT tipos_unidade_pkey PRIMARY KEY (id);


--
-- Name: tipos_unidade tipos_unidade_sigla_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipos_unidade
    ADD CONSTRAINT tipos_unidade_sigla_key UNIQUE (sigla);


--
-- Name: transferencias_equipamento transferencias_equipamento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencias_equipamento
    ADD CONSTRAINT transferencias_equipamento_pkey PRIMARY KEY (id);


--
-- Name: unidades unidades_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.unidades
    ADD CONSTRAINT unidades_pkey PRIMARY KEY (id);


--
-- Name: contrato_tipos_equipamento uq_contrato_tipo_marca_modelo; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_tipos_equipamento
    ADD CONSTRAINT uq_contrato_tipo_marca_modelo UNIQUE (contrato_id, tipo_equipamento_id, marca_id, modelo_id);


--
-- Name: usuario_setor usuario_setor_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_setor
    ADD CONSTRAINT usuario_setor_pkey PRIMARY KEY (usuario_id, setor_id);


--
-- Name: usuario_unidade usuario_unidade_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_unidade
    ADD CONSTRAINT usuario_unidade_pkey PRIMARY KEY (id);


--
-- Name: usuario_unidade usuario_unidade_usuario_id_unidade_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_unidade
    ADD CONSTRAINT usuario_unidade_usuario_id_unidade_id_key UNIQUE (usuario_id, unidade_id);


--
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: idx_chamados_equipamento; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chamados_equipamento ON public.chamados USING btree (equipamento_id);


--
-- Name: idx_chamados_predio; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chamados_predio ON public.chamados USING btree (predio_id);


--
-- Name: idx_chamados_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chamados_status ON public.chamados USING btree (status);


--
-- Name: idx_chamados_unidade; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chamados_unidade ON public.chamados USING btree (unidade_id);


--
-- Name: idx_equipamentos_sala; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_equipamentos_sala ON public.equipamentos USING btree (sala_id);


--
-- Name: idx_equipamentos_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_equipamentos_status ON public.equipamentos USING btree (status);


--
-- Name: idx_equipamentos_tipo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_equipamentos_tipo ON public.equipamentos USING btree (tipo_equipamento_id);


--
-- Name: idx_fcv_unidade; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fcv_unidade ON public.ficha_cnes_vinculo USING btree (unidade_id);


--
-- Name: idx_fcv_usuario; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fcv_usuario ON public.ficha_cnes_vinculo USING btree (usuario_id);


--
-- Name: idx_hist_equip; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hist_equip ON public.historico_equipamento USING btree (equipamento_id);


--
-- Name: idx_salas_unidade; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_salas_unidade ON public.salas USING btree (unidade_id);


--
-- Name: idx_transf_destino; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transf_destino ON public.transferencias_equipamento USING btree (unidade_destino_id);


--
-- Name: idx_transf_equipamento; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transf_equipamento ON public.transferencias_equipamento USING btree (equipamento_id);


--
-- Name: idx_transf_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transf_status ON public.transferencias_equipamento USING btree (status);


--
-- Name: idx_unidades_predio; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_unidades_predio ON public.unidades USING btree (predio_id);


--
-- Name: idx_usuario_unidade_unidade; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usuario_unidade_unidade ON public.usuario_unidade USING btree (unidade_id);


--
-- Name: idx_usuario_unidade_usuario; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usuario_unidade_usuario ON public.usuario_unidade USING btree (usuario_id);


--
-- Name: idx_uu_papel; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_uu_papel ON public.usuario_unidade USING btree (papel);


--
-- Name: ix_faltas_abonadas_data; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faltas_abonadas_data ON public.faltas_abonadas USING btree (data_falta);


--
-- Name: ix_faltas_abonadas_usuario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faltas_abonadas_usuario_id ON public.faltas_abonadas USING btree (usuario_id);


--
-- Name: chamados trg_chamados_atualizado; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_chamados_atualizado BEFORE UPDATE ON public.chamados FOR EACH ROW EXECUTE FUNCTION public.set_atualizado_em();


--
-- Name: contratos trg_contratos_atualizado; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_contratos_atualizado BEFORE UPDATE ON public.contratos FOR EACH ROW EXECUTE FUNCTION public.set_atualizado_em();


--
-- Name: equipamentos trg_equipamentos_atualizado; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_equipamentos_atualizado BEFORE UPDATE ON public.equipamentos FOR EACH ROW EXECUTE FUNCTION public.set_atualizado_em();


--
-- Name: salas trg_salas_atualizado; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_salas_atualizado BEFORE UPDATE ON public.salas FOR EACH ROW EXECUTE FUNCTION public.set_atualizado_em();


--
-- Name: unidades trg_unidades_atualizado; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_unidades_atualizado BEFORE UPDATE ON public.unidades FOR EACH ROW EXECUTE FUNCTION public.set_atualizado_em();


--
-- Name: usuarios trg_usuarios_atualizado; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_usuarios_atualizado BEFORE UPDATE ON public.usuarios FOR EACH ROW EXECUTE FUNCTION public.set_atualizado_em();


--
-- Name: acao_planejamento_empresas acacao_empresas_acao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acao_planejamento_empresas
    ADD CONSTRAINT acacao_empresas_acao_id_fkey FOREIGN KEY (acao_id) REFERENCES public.acoes_planejamento(id) ON DELETE CASCADE;


--
-- Name: acao_planejamento_empresas acacao_empresas_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acao_planejamento_empresas
    ADD CONSTRAINT acacao_empresas_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas_contratadas(id) ON DELETE CASCADE;


--
-- Name: acao_planejamento_responsaveis acacao_responsaveis_acao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acao_planejamento_responsaveis
    ADD CONSTRAINT acacao_responsaveis_acao_id_fkey FOREIGN KEY (acao_id) REFERENCES public.acoes_planejamento(id) ON DELETE CASCADE;


--
-- Name: acao_planejamento_responsaveis acacao_responsaveis_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acao_planejamento_responsaveis
    ADD CONSTRAINT acacao_responsaveis_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: acoes_planejamento acoes_plano_criado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acoes_planejamento
    ADD CONSTRAINT acoes_plano_criado_por_fkey FOREIGN KEY (criado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: acoes_planejamento_obs_anexos acoes_plano_obs_anexos_observacao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acoes_planejamento_obs_anexos
    ADD CONSTRAINT acoes_plano_obs_anexos_observacao_id_fkey FOREIGN KEY (observacao_id) REFERENCES public.acoes_planejamento_observacoes(id) ON DELETE CASCADE;


--
-- Name: acoes_planejamento_observacoes acoes_plano_observacoes_acao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acoes_planejamento_observacoes
    ADD CONSTRAINT acoes_plano_observacoes_acao_id_fkey FOREIGN KEY (acao_id) REFERENCES public.acoes_planejamento(id) ON DELETE CASCADE;


--
-- Name: acoes_planejamento_observacoes acoes_plano_observacoes_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acoes_planejamento_observacoes
    ADD CONSTRAINT acoes_plano_observacoes_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: acoes_planejamento acoes_plano_plano_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acoes_planejamento
    ADD CONSTRAINT acoes_plano_plano_id_fkey FOREIGN KEY (planejamento_id) REFERENCES public.planejamentos(id) ON DELETE CASCADE;


--
-- Name: andamento_anexos andamento_anexos_andamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.andamento_anexos
    ADD CONSTRAINT andamento_anexos_andamento_id_fkey FOREIGN KEY (andamento_id) REFERENCES public.chamado_historico(id) ON DELETE CASCADE;


--
-- Name: auditoria auditoria_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT auditoria_user_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: campos_tipo_equipamento campos_tipo_equipamento_tipo_equipamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.campos_tipo_equipamento
    ADD CONSTRAINT campos_tipo_equipamento_tipo_equipamento_id_fkey FOREIGN KEY (tipo_equipamento_id) REFERENCES public.tipos_equipamento(id) ON DELETE CASCADE;


--
-- Name: chamado_fotos chamado_fotos_chamado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamado_fotos
    ADD CONSTRAINT chamado_fotos_chamado_id_fkey FOREIGN KEY (chamado_id) REFERENCES public.chamados(id) ON DELETE CASCADE;


--
-- Name: chamado_historico chamado_historico_chamado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamado_historico
    ADD CONSTRAINT chamado_historico_chamado_id_fkey FOREIGN KEY (chamado_id) REFERENCES public.chamados(id) ON DELETE CASCADE;


--
-- Name: chamado_historico chamado_historico_contrato_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamado_historico
    ADD CONSTRAINT chamado_historico_contrato_id_fkey FOREIGN KEY (contrato_id) REFERENCES public.contratos(id) ON DELETE SET NULL;


--
-- Name: chamado_historico chamado_historico_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamado_historico
    ADD CONSTRAINT chamado_historico_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: chamados chamados_aberto_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamados
    ADD CONSTRAINT chamados_aberto_por_fkey FOREIGN KEY (aberto_por) REFERENCES public.usuarios(id) ON DELETE RESTRICT;


--
-- Name: chamados chamados_equipamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamados
    ADD CONSTRAINT chamados_equipamento_id_fkey FOREIGN KEY (equipamento_id) REFERENCES public.equipamentos(id) ON DELETE SET NULL;


--
-- Name: chamados chamados_predio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamados
    ADD CONSTRAINT chamados_predio_id_fkey FOREIGN KEY (predio_id) REFERENCES public.predios(id) ON DELETE SET NULL;


--
-- Name: chamados chamados_responsavel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamados
    ADD CONSTRAINT chamados_responsavel_id_fkey FOREIGN KEY (responsavel_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: chamados chamados_sala_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamados
    ADD CONSTRAINT chamados_sala_id_fkey FOREIGN KEY (sala_id) REFERENCES public.salas(id) ON DELETE SET NULL;


--
-- Name: chamados chamados_setor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamados
    ADD CONSTRAINT chamados_setor_id_fkey FOREIGN KEY (setor_id) REFERENCES public.setores_manutencao(id) ON DELETE SET NULL;


--
-- Name: chamados chamados_unidade_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chamados
    ADD CONSTRAINT chamados_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES public.unidades(id) ON DELETE RESTRICT;


--
-- Name: contrato_acoes contrato_acoes_contrato_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_acoes
    ADD CONSTRAINT contrato_acoes_contrato_id_fkey FOREIGN KEY (contrato_id) REFERENCES public.contratos(id) ON DELETE CASCADE;


--
-- Name: contrato_acoes contrato_acoes_criado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_acoes
    ADD CONSTRAINT contrato_acoes_criado_por_fkey FOREIGN KEY (criado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: contrato_equipamentos contrato_equipamentos_contrato_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_equipamentos
    ADD CONSTRAINT contrato_equipamentos_contrato_id_fkey FOREIGN KEY (contrato_id) REFERENCES public.contratos(id) ON DELETE CASCADE;


--
-- Name: contrato_equipamentos contrato_equipamentos_equipamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_equipamentos
    ADD CONSTRAINT contrato_equipamentos_equipamento_id_fkey FOREIGN KEY (equipamento_id) REFERENCES public.equipamentos(id) ON DELETE CASCADE;


--
-- Name: contrato_financeiro contrato_financeiro_contrato_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_financeiro
    ADD CONSTRAINT contrato_financeiro_contrato_id_fkey FOREIGN KEY (contrato_id) REFERENCES public.contratos(id) ON DELETE SET NULL;


--
-- Name: contrato_tipos_equipamento contrato_tipos_equipamento_contrato_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_tipos_equipamento
    ADD CONSTRAINT contrato_tipos_equipamento_contrato_id_fkey FOREIGN KEY (contrato_id) REFERENCES public.contratos(id) ON DELETE CASCADE;


--
-- Name: contrato_tipos_equipamento contrato_tipos_equipamento_marca_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_tipos_equipamento
    ADD CONSTRAINT contrato_tipos_equipamento_marca_id_fkey FOREIGN KEY (marca_id) REFERENCES public.marcas(id) ON DELETE CASCADE;


--
-- Name: contrato_tipos_equipamento contrato_tipos_equipamento_modelo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_tipos_equipamento
    ADD CONSTRAINT contrato_tipos_equipamento_modelo_id_fkey FOREIGN KEY (modelo_id) REFERENCES public.modelos(id) ON DELETE CASCADE;


--
-- Name: contrato_tipos_equipamento contrato_tipos_equipamento_tipo_equipamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato_tipos_equipamento
    ADD CONSTRAINT contrato_tipos_equipamento_tipo_equipamento_id_fkey FOREIGN KEY (tipo_equipamento_id) REFERENCES public.tipos_equipamento(id) ON DELETE CASCADE;


--
-- Name: contratos contratos_criado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT contratos_criado_por_fkey FOREIGN KEY (criado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: contratos contratos_empresa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contratos
    ADD CONSTRAINT contratos_empresa_id_fkey FOREIGN KEY (empresa_id) REFERENCES public.empresas_contratadas(id) ON DELETE SET NULL;


--
-- Name: documentos_transferencia documentos_transferencia_aceito_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentos_transferencia
    ADD CONSTRAINT documentos_transferencia_aceito_por_fkey FOREIGN KEY (aceito_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: documentos_transferencia documentos_transferencia_criado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentos_transferencia
    ADD CONSTRAINT documentos_transferencia_criado_por_fkey FOREIGN KEY (criado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: documentos_transferencia documentos_transferencia_sala_destino_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentos_transferencia
    ADD CONSTRAINT documentos_transferencia_sala_destino_id_fkey FOREIGN KEY (sala_destino_id) REFERENCES public.salas(id) ON DELETE SET NULL;


--
-- Name: documentos_transferencia documentos_transferencia_unidade_destino_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentos_transferencia
    ADD CONSTRAINT documentos_transferencia_unidade_destino_id_fkey FOREIGN KEY (unidade_destino_id) REFERENCES public.unidades(id) ON DELETE RESTRICT;


--
-- Name: documentos_transferencia documentos_transferencia_unidade_origem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentos_transferencia
    ADD CONSTRAINT documentos_transferencia_unidade_origem_id_fkey FOREIGN KEY (unidade_origem_id) REFERENCES public.unidades(id) ON DELETE RESTRICT;


--
-- Name: equipamento_campo_valores equipamento_campo_valores_campo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamento_campo_valores
    ADD CONSTRAINT equipamento_campo_valores_campo_id_fkey FOREIGN KEY (campo_id) REFERENCES public.campos_tipo_equipamento(id) ON DELETE CASCADE;


--
-- Name: equipamento_campo_valores equipamento_campo_valores_equipamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamento_campo_valores
    ADD CONSTRAINT equipamento_campo_valores_equipamento_id_fkey FOREIGN KEY (equipamento_id) REFERENCES public.equipamentos(id) ON DELETE CASCADE;


--
-- Name: equipamento_usuarios equipamento_usuarios_equipamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamento_usuarios
    ADD CONSTRAINT equipamento_usuarios_equipamento_id_fkey FOREIGN KEY (equipamento_id) REFERENCES public.equipamentos(id) ON DELETE CASCADE;


--
-- Name: equipamento_usuarios equipamento_usuarios_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamento_usuarios
    ADD CONSTRAINT equipamento_usuarios_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: equipamentos equipamentos_criado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamentos
    ADD CONSTRAINT equipamentos_criado_por_fkey FOREIGN KEY (criado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: equipamentos equipamentos_marca_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamentos
    ADD CONSTRAINT equipamentos_marca_id_fkey FOREIGN KEY (marca_id) REFERENCES public.marcas(id) ON DELETE SET NULL;


--
-- Name: equipamentos equipamentos_modelo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamentos
    ADD CONSTRAINT equipamentos_modelo_id_fkey FOREIGN KEY (modelo_id) REFERENCES public.modelos(id) ON DELETE SET NULL;


--
-- Name: equipamentos equipamentos_sala_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamentos
    ADD CONSTRAINT equipamentos_sala_id_fkey FOREIGN KEY (sala_id) REFERENCES public.salas(id) ON DELETE RESTRICT;


--
-- Name: equipamentos equipamentos_tipo_equipamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equipamentos
    ADD CONSTRAINT equipamentos_tipo_equipamento_id_fkey FOREIGN KEY (tipo_equipamento_id) REFERENCES public.tipos_equipamento(id) ON DELETE RESTRICT;


--
-- Name: faltas_abonadas faltas_abonadas_cancelado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faltas_abonadas
    ADD CONSTRAINT faltas_abonadas_cancelado_por_fkey FOREIGN KEY (cancelado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: faltas_abonadas faltas_abonadas_criado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faltas_abonadas
    ADD CONSTRAINT faltas_abonadas_criado_por_fkey FOREIGN KEY (criado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: faltas_abonadas faltas_abonadas_unidade_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faltas_abonadas
    ADD CONSTRAINT faltas_abonadas_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES public.unidades(id) ON DELETE SET NULL;


--
-- Name: faltas_abonadas faltas_abonadas_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faltas_abonadas
    ADD CONSTRAINT faltas_abonadas_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: ficha_cnes_vinculo ficha_cnes_vinculo_gerado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ficha_cnes_vinculo
    ADD CONSTRAINT ficha_cnes_vinculo_gerado_por_fkey FOREIGN KEY (gerado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: ficha_cnes_vinculo ficha_cnes_vinculo_unidade_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ficha_cnes_vinculo
    ADD CONSTRAINT ficha_cnes_vinculo_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES public.unidades(id) ON DELETE CASCADE;


--
-- Name: ficha_cnes_vinculo ficha_cnes_vinculo_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ficha_cnes_vinculo
    ADD CONSTRAINT ficha_cnes_vinculo_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: historico_equipamento historico_equipamento_equipamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historico_equipamento
    ADD CONSTRAINT historico_equipamento_equipamento_id_fkey FOREIGN KEY (equipamento_id) REFERENCES public.equipamentos(id) ON DELETE CASCADE;


--
-- Name: historico_equipamento historico_equipamento_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historico_equipamento
    ADD CONSTRAINT historico_equipamento_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: itens_documento_transferencia itens_documento_transferencia_documento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itens_documento_transferencia
    ADD CONSTRAINT itens_documento_transferencia_documento_id_fkey FOREIGN KEY (documento_id) REFERENCES public.documentos_transferencia(id) ON DELETE CASCADE;


--
-- Name: itens_documento_transferencia itens_documento_transferencia_equipamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itens_documento_transferencia
    ADD CONSTRAINT itens_documento_transferencia_equipamento_id_fkey FOREIGN KEY (equipamento_id) REFERENCES public.equipamentos(id) ON DELETE SET NULL;


--
-- Name: itens_lojinha itens_lojinha_criado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itens_lojinha
    ADD CONSTRAINT itens_lojinha_criado_por_fkey FOREIGN KEY (criado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: itens_lojinha itens_lojinha_equipamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itens_lojinha
    ADD CONSTRAINT itens_lojinha_equipamento_id_fkey FOREIGN KEY (equipamento_id) REFERENCES public.equipamentos(id) ON DELETE SET NULL;


--
-- Name: itens_lojinha itens_lojinha_unidade_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.itens_lojinha
    ADD CONSTRAINT itens_lojinha_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES public.unidades(id) ON DELETE CASCADE;


--
-- Name: links_uteis links_uteis_criado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.links_uteis
    ADD CONSTRAINT links_uteis_criado_por_fkey FOREIGN KEY (criado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: links_uteis links_uteis_tipo_link_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.links_uteis
    ADD CONSTRAINT links_uteis_tipo_link_id_fkey FOREIGN KEY (tipo_link_id) REFERENCES public.tipos_link(id) ON DELETE SET NULL;


--
-- Name: marca_tipo_equipamento marca_tipo_equipamento_marca_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.marca_tipo_equipamento
    ADD CONSTRAINT marca_tipo_equipamento_marca_id_fkey FOREIGN KEY (marca_id) REFERENCES public.marcas(id) ON DELETE CASCADE;


--
-- Name: marca_tipo_equipamento marca_tipo_equipamento_tipo_equipamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.marca_tipo_equipamento
    ADD CONSTRAINT marca_tipo_equipamento_tipo_equipamento_id_fkey FOREIGN KEY (tipo_equipamento_id) REFERENCES public.tipos_equipamento(id) ON DELETE CASCADE;


--
-- Name: matriculas_profissionais matriculas_profissionais_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.matriculas_profissionais
    ADD CONSTRAINT matriculas_profissionais_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: modelos modelos_marca_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modelos
    ADD CONSTRAINT modelos_marca_id_fkey FOREIGN KEY (marca_id) REFERENCES public.marcas(id) ON DELETE SET NULL;


--
-- Name: modelos modelos_tipo_equipamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modelos
    ADD CONSTRAINT modelos_tipo_equipamento_id_fkey FOREIGN KEY (tipo_equipamento_id) REFERENCES public.tipos_equipamento(id) ON DELETE SET NULL;


--
-- Name: notificacoes notificacoes_chamado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notificacoes
    ADD CONSTRAINT notificacoes_chamado_id_fkey FOREIGN KEY (chamado_id) REFERENCES public.chamados(id) ON DELETE CASCADE;


--
-- Name: notificacoes notificacoes_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notificacoes
    ADD CONSTRAINT notificacoes_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: planejamentos_anexos planos_anexos_plano_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.planejamentos_anexos
    ADD CONSTRAINT planos_anexos_plano_id_fkey FOREIGN KEY (planejamento_id) REFERENCES public.planejamentos(id) ON DELETE CASCADE;


--
-- Name: planejamentos planos_atualizado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.planejamentos
    ADD CONSTRAINT planos_atualizado_por_fkey FOREIGN KEY (atualizado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: planejamentos planos_criado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.planejamentos
    ADD CONSTRAINT planos_criado_por_fkey FOREIGN KEY (criado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: planejamentos planos_unidade_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.planejamentos
    ADD CONSTRAINT planos_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES public.unidades(id) ON DELETE CASCADE;


--
-- Name: predios predios_responsavel_predial_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.predios
    ADD CONSTRAINT predios_responsavel_predial_id_fkey FOREIGN KEY (responsavel_predial_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: salas salas_tipo_sala_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salas
    ADD CONSTRAINT salas_tipo_sala_id_fkey FOREIGN KEY (tipo_sala_id) REFERENCES public.tipos_sala(id) ON DELETE SET NULL;


--
-- Name: salas salas_unidade_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.salas
    ADD CONSTRAINT salas_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES public.unidades(id) ON DELETE CASCADE;


--
-- Name: setores_manutencao setores_manutencao_divisao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setores_manutencao
    ADD CONSTRAINT setores_manutencao_divisao_id_fkey FOREIGN KEY (divisao_id) REFERENCES public.divisoes(id) ON DELETE SET NULL;


--
-- Name: solicitacoes_vinculo solicitacoes_vinculo_aprovado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solicitacoes_vinculo
    ADD CONSTRAINT solicitacoes_vinculo_aprovado_por_fkey FOREIGN KEY (aprovado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: solicitacoes_vinculo solicitacoes_vinculo_unidade_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solicitacoes_vinculo
    ADD CONSTRAINT solicitacoes_vinculo_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES public.unidades(id) ON DELETE CASCADE;


--
-- Name: solicitacoes_vinculo solicitacoes_vinculo_usuario_criado_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solicitacoes_vinculo
    ADD CONSTRAINT solicitacoes_vinculo_usuario_criado_fkey FOREIGN KEY (usuario_criado) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: transferencias_equipamento transferencias_equipamento_aceito_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencias_equipamento
    ADD CONSTRAINT transferencias_equipamento_aceito_por_fkey FOREIGN KEY (aceito_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: transferencias_equipamento transferencias_equipamento_equipamento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencias_equipamento
    ADD CONSTRAINT transferencias_equipamento_equipamento_id_fkey FOREIGN KEY (equipamento_id) REFERENCES public.equipamentos(id) ON DELETE CASCADE;


--
-- Name: transferencias_equipamento transferencias_equipamento_sala_destino_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencias_equipamento
    ADD CONSTRAINT transferencias_equipamento_sala_destino_id_fkey FOREIGN KEY (sala_destino_id) REFERENCES public.salas(id) ON DELETE SET NULL;


--
-- Name: transferencias_equipamento transferencias_equipamento_sala_origem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencias_equipamento
    ADD CONSTRAINT transferencias_equipamento_sala_origem_id_fkey FOREIGN KEY (sala_origem_id) REFERENCES public.salas(id) ON DELETE SET NULL;


--
-- Name: transferencias_equipamento transferencias_equipamento_solicitado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencias_equipamento
    ADD CONSTRAINT transferencias_equipamento_solicitado_por_fkey FOREIGN KEY (solicitado_por) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: transferencias_equipamento transferencias_equipamento_unidade_destino_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencias_equipamento
    ADD CONSTRAINT transferencias_equipamento_unidade_destino_id_fkey FOREIGN KEY (unidade_destino_id) REFERENCES public.unidades(id) ON DELETE RESTRICT;


--
-- Name: transferencias_equipamento transferencias_equipamento_unidade_origem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencias_equipamento
    ADD CONSTRAINT transferencias_equipamento_unidade_origem_id_fkey FOREIGN KEY (unidade_origem_id) REFERENCES public.unidades(id) ON DELETE RESTRICT;


--
-- Name: unidades unidades_predio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.unidades
    ADD CONSTRAINT unidades_predio_id_fkey FOREIGN KEY (predio_id) REFERENCES public.predios(id) ON DELETE SET NULL;


--
-- Name: unidades unidades_tipo_unidade_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.unidades
    ADD CONSTRAINT unidades_tipo_unidade_id_fkey FOREIGN KEY (tipo_unidade_id) REFERENCES public.tipos_unidade(id) ON DELETE SET NULL;


--
-- Name: usuario_setor usuario_setor_setor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_setor
    ADD CONSTRAINT usuario_setor_setor_id_fkey FOREIGN KEY (setor_id) REFERENCES public.setores_manutencao(id) ON DELETE CASCADE;


--
-- Name: usuario_setor usuario_setor_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_setor
    ADD CONSTRAINT usuario_setor_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: usuario_unidade usuario_unidade_matricula_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_unidade
    ADD CONSTRAINT usuario_unidade_matricula_id_fkey FOREIGN KEY (matricula_id) REFERENCES public.matriculas_profissionais(id) ON DELETE SET NULL;


--
-- Name: usuario_unidade usuario_unidade_unidade_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_unidade
    ADD CONSTRAINT usuario_unidade_unidade_id_fkey FOREIGN KEY (unidade_id) REFERENCES public.unidades(id) ON DELETE CASCADE;


--
-- Name: usuario_unidade usuario_unidade_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_unidade
    ADD CONSTRAINT usuario_unidade_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: usuarios usuarios_unidade_padrao_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_unidade_padrao_id_fkey FOREIGN KEY (unidade_padrao_id) REFERENCES public.unidades(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict FRmmLTG34hxW2xEULrribONWaelCyGBnZLTBDFbB0GdIQmxu5JhGfZuIEgGZob8

