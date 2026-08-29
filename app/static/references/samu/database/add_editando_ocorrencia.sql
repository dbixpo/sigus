-- Adiciona colunas de bloqueio de edição concorrente em ocorrências (executar uma vez)
-- Se der erro "column already exists", ignore.
ALTER TABLE ocorrencias ADD COLUMN editando_por_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL;
ALTER TABLE ocorrencias ADD COLUMN editando_desde TIMESTAMP WITHOUT TIME ZONE;
