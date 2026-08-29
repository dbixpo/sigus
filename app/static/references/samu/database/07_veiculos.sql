-- =============================================================================
-- Veículos SAMU (conforme CRLV)
-- =============================================================================

CREATE TABLE IF NOT EXISTS veiculos (
    id SERIAL PRIMARY KEY,
    prefixo VARCHAR(30) NOT NULL,
    marca VARCHAR(100),
    modelo VARCHAR(150),
    placa VARCHAR(7),
    renavam VARCHAR(11),
    tipo VARCHAR(50),
    combustivel VARCHAR(30),
    ano_fabricacao INTEGER,
    ano_modelo INTEGER,
    crlv_anexo VARCHAR(255),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
