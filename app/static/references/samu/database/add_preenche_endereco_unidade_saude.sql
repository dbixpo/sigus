-- Adiciona coluna preenche_endereco_unidade_saude em origens_ligacao (executar uma vez)
-- Se der erro "column already exists", ignore.
ALTER TABLE origens_ligacao ADD COLUMN IF NOT EXISTS preenche_endereco_unidade_saude BOOLEAN NOT NULL DEFAULT FALSE;
