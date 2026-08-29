-- Adiciona coluna criado_por_id à tabela avisos
ALTER TABLE avisos ADD COLUMN IF NOT EXISTS criado_por_id INTEGER REFERENCES usuarios(id);
