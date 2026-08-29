-- Timestamps do RO para acompanhamento da ocorrência (estilo eSUS SAMU)
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS envio_viatura_em TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS saida_base_em TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS chegada_local_em TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS saida_local_em TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS chegada_destino_em TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS equipe_liberada_em TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS chegada_base_em TIMESTAMP WITHOUT TIME ZONE;
-- Cancelamento do envio
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS cancelamento_intercorrencia_id INTEGER REFERENCES intercorrencias(id) ON DELETE SET NULL;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS cancelamento_observacao TEXT;
-- Intercorrência: disponível para cancelamento do envio
ALTER TABLE intercorrencias ADD COLUMN IF NOT EXISTS disponivel_cancelamento BOOLEAN NOT NULL DEFAULT FALSE;
