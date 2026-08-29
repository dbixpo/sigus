CREATE TABLE IF NOT EXISTS palavras_chave_protocolo (
    id SERIAL PRIMARY KEY,
    algoritmo_id INTEGER NOT NULL REFERENCES algoritmos_acolhimento(id) ON DELETE CASCADE,
    palavra VARCHAR(100) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_palavras_chave_algoritmo ON palavras_chave_protocolo(algoritmo_id);
CREATE INDEX IF NOT EXISTS ix_palavras_chave_palavra ON palavras_chave_protocolo(LOWER(palavra));

CREATE TABLE IF NOT EXISTS perguntas_protocolo (
    id SERIAL PRIMARY KEY,
    algoritmo_id INTEGER NOT NULL REFERENCES algoritmos_acolhimento(id) ON DELETE CASCADE,
    secao VARCHAR(100),
    enunciado VARCHAR(500) NOT NULL,
    tipo VARCHAR(30) NOT NULL DEFAULT 'texto',
    ordem SMALLINT NOT NULL DEFAULT 0,
    obrigatoria BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_perguntas_protocolo_algoritmo ON perguntas_protocolo(algoritmo_id);

CREATE TABLE IF NOT EXISTS opcoes_resposta (
    id SERIAL PRIMARY KEY,
    pergunta_id INTEGER NOT NULL REFERENCES perguntas_protocolo(id) ON DELETE CASCADE,
    texto VARCHAR(200) NOT NULL,
    ordem SMALLINT NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_opcoes_resposta_pergunta ON opcoes_resposta(pergunta_id);

ALTER TABLE algoritmos_acolhimento ADD COLUMN IF NOT EXISTS ordem SMALLINT NOT NULL DEFAULT 0;
