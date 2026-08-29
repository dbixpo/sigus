-- Data Comemorativa: emoji, cores customizadas (navbar/sidebar)
-- psql -d samu -f database/10_feriados_data_comemorativa.sql

ALTER TABLE feriados ADD COLUMN IF NOT EXISTS emoji VARCHAR(20);
ALTER TABLE feriados ADD COLUMN IF NOT EXISTS cor_primaria VARCHAR(7);
ALTER TABLE feriados ADD COLUMN IF NOT EXISTS cor_secundaria VARCHAR(7);
ALTER TABLE feriados ADD COLUMN IF NOT EXISTS cor_fonte_primaria VARCHAR(7);
ALTER TABLE feriados ADD COLUMN IF NOT EXISTS cor_fonte_secundaria VARCHAR(7);
