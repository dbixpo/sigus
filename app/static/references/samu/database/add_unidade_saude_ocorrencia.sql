-- Adiciona unidade_saude_id em ocorrencias para persistir seleção (origem Unidade de Saúde)
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS unidade_saude_id INTEGER REFERENCES unidades_saude(id) ON DELETE SET NULL;
