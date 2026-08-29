-- Adiciona colunas em feriados (executar se a tabela ja existir)
-- psql -d samu -f database/02_feriados_alter.sql

ALTER TABLE feriados ADD COLUMN IF NOT EXISTS tipo_folga VARCHAR(20) NOT NULL DEFAULT 'feriado';
ALTER TABLE feriados ADD COLUMN IF NOT EXISTS natureza VARCHAR(20) NOT NULL DEFAULT 'nacional';
ALTER TABLE feriados ADD COLUMN IF NOT EXISTS numero_decreto VARCHAR(50);
ALTER TABLE feriados ADD COLUMN IF NOT EXISTS link_decreto VARCHAR(500);
