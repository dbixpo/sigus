-- Classificações de risco (Manchester)
CREATE TABLE IF NOT EXISTS classificacoes_risco (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    cor VARCHAR(20) NOT NULL,
    ordem INTEGER NOT NULL DEFAULT 0,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO classificacoes_risco (nome, cor, ordem) SELECT '1 - Vermelho', '#dc3545', 1 WHERE NOT EXISTS (SELECT 1 FROM classificacoes_risco WHERE nome = '1 - Vermelho');
INSERT INTO classificacoes_risco (nome, cor, ordem) SELECT '2 - Laranja', '#fd7e14', 2 WHERE NOT EXISTS (SELECT 1 FROM classificacoes_risco WHERE nome = '2 - Laranja');
INSERT INTO classificacoes_risco (nome, cor, ordem) SELECT '3 - Verde', '#198754', 3 WHERE NOT EXISTS (SELECT 1 FROM classificacoes_risco WHERE nome = '3 - Verde');
INSERT INTO classificacoes_risco (nome, cor, ordem) SELECT '4 - Azul', '#0d6efd', 4 WHERE NOT EXISTS (SELECT 1 FROM classificacoes_risco WHERE nome = '4 - Azul');
INSERT INTO classificacoes_risco (nome, cor, ordem) SELECT '5 - Cinza', '#6c757d', 5 WHERE NOT EXISTS (SELECT 1 FROM classificacoes_risco WHERE nome = '5 - Cinza');

-- ordem_prioridade em tipos_unidade_samu
ALTER TABLE tipos_unidade_samu ADD COLUMN IF NOT EXISTS ordem_prioridade INTEGER DEFAULT 0;

-- Campos de regulação em ocorrências
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS tipo_ocorrencia_id INTEGER REFERENCES tipos_ocorrencia(id) ON DELETE SET NULL;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS motivo_ocorrencia_id INTEGER REFERENCES motivos_ocorrencia(id) ON DELETE SET NULL;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS avaliacao_medica_historico TEXT;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS decisao_protocolo TEXT;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS decisoes_medicas JSONB DEFAULT '[]';
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS regulada_por_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS regulada_em TIMESTAMP WITHOUT TIME ZONE;
