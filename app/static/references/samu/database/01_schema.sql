-- =============================================================================
-- Sistema SAMU 192 - Estrutura do Banco de Dados
-- PostgreSQL
-- =============================================================================

-- Tipos de Unidade SAMU (CRU, ALFA, BETA, VIR, etc.)
CREATE TABLE IF NOT EXISTS tipos_unidade_samu (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    sigla VARCHAR(20) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    predefinido BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Bases Descentralizadas (endereço completo para viaturas)
CREATE TABLE IF NOT EXISTS bases_descentralizadas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    logradouro VARCHAR(300),
    numero VARCHAR(20),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    uf VARCHAR(2),
    cep VARCHAR(9),
    telefone VARCHAR(20),
    email VARCHAR(200),
    link_google_maps VARCHAR(500),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Unidades SAMU (centrais de regulação ou viaturas)
CREATE TABLE IF NOT EXISTS unidades_samu (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    sigla VARCHAR(20),
    endereco VARCHAR(300),
    municipio VARCHAR(100),
    uf VARCHAR(2),
    telefone VARCHAR(20),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Usuários/Profissionais (login por usuário de acesso)
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(80) NOT NULL UNIQUE,
    senha_hash VARCHAR(256) NOT NULL,
    perfil VARCHAR(200) NOT NULL DEFAULT 'tarm',  -- perfis separados por vírgula
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    nome VARCHAR(150) NOT NULL,
    apelido VARCHAR(80),
    email VARCHAR(200),
    foto_perfil VARCHAR(200),
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    unidade_samu_id INTEGER REFERENCES unidades_samu(id) ON DELETE SET NULL,
    -- Dados pessoais
    cpf VARCHAR(14),
    cns VARCHAR(20),
    sexo VARCHAR(1),
    data_nasc DATE,
    nome_mae VARCHAR(200),
    nome_pai VARCHAR(200),
    nacionalidade VARCHAR(20) DEFAULT 'brasileira',
    uf_nasc VARCHAR(2),
    municipio_nasc VARCHAR(100),
    dt_entrada_pais DATE,
    pais_origem VARCHAR(100),
    rg VARCHAR(20),
    rg_uf VARCHAR(2),
    rg_orgao VARCHAR(50),
    rg_emissao DATE,
    escolaridade VARCHAR(2),
    frequenta_escola BOOLEAN,
    -- Endereço
    end_logradouro VARCHAR(300),
    end_numero VARCHAR(20),
    end_complemento VARCHAR(100),
    end_bairro VARCHAR(100),
    end_municipio VARCHAR(100),
    end_uf VARCHAR(2),
    end_cep VARCHAR(9),
    telefone VARCHAR(20),
    whatsapp VARCHAR(20),
    -- Dados profissionais
    reg_conselho VARCHAR(30),
    orgao_emissor VARCHAR(50),
    vinculo VARCHAR(1),
    tipo_vinculo VARCHAR(1),
    carga_horaria SMALLINT,
    cbo VARCHAR(10),
    especialidade_residencia VARCHAR(200),
    dt_entrada_unidade DATE,
    matricula VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS ix_usuarios_usuario ON usuarios(usuario);

-- Unidades de Saúde (hospitais, UBS, UPA, etc.)
CREATE TABLE IF NOT EXISTS unidades_saude (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    apelido VARCHAR(100),
    sigla VARCHAR(20),
    cnes VARCHAR(7),
    tipo VARCHAR(50),
    endereco VARCHAR(300),
    municipio VARCHAR(100),
    uf VARCHAR(2),
    telefone VARCHAR(20),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tipos de ligação
CREATE TABLE IF NOT EXISTS tipos_ligacao (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao VARCHAR(300),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Origens de ligação
CREATE TABLE IF NOT EXISTS origens_ligacao (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao VARCHAR(300),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Algoritmos de acolhimento (Manchester)
CREATE TABLE IF NOT EXISTS algoritmos_acolhimento (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL,
    nome VARCHAR(150) NOT NULL,
    descricao TEXT,
    cor VARCHAR(20),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CID-10
CREATE TABLE IF NOT EXISTS cid10 (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) NOT NULL,
    descricao VARCHAR(300) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_cid10_codigo ON cid10(codigo);

-- CID-O (morfologia de neoplasias)
CREATE TABLE IF NOT EXISTS cido (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL,
    descricao VARCHAR(300) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_cido_codigo ON cido(codigo);

-- Tipos de ocorrência
CREATE TABLE IF NOT EXISTS tipos_ocorrencia (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao VARCHAR(300),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Motivos de ocorrência
CREATE TABLE IF NOT EXISTS motivos_ocorrencia (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    descricao VARCHAR(300),
    tipo_ocorrencia_id INTEGER REFERENCES tipos_ocorrencia(id) ON DELETE SET NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Intercorrências
CREATE TABLE IF NOT EXISTS intercorrencias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    descricao VARCHAR(300),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Feriados
CREATE TABLE IF NOT EXISTS feriados (
    id SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    nome VARCHAR(150) NOT NULL,
    tipo_folga VARCHAR(20) NOT NULL DEFAULT 'feriado',
    natureza VARCHAR(20) NOT NULL DEFAULT 'nacional',
    numero_decreto VARCHAR(50),
    link_decreto VARCHAR(500),
    descricao VARCHAR(300),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Faltas abonadas
CREATE TABLE IF NOT EXISTS faltas_abonadas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    unidade_samu_id INTEGER REFERENCES unidades_samu(id) ON DELETE SET NULL,
    data_falta DATE NOT NULL,
    funcao VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ativa',
    motivo_cancelamento TEXT,
    cancelado_em TIMESTAMP WITHOUT TIME ZONE,
    cancelado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    criado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL
);
