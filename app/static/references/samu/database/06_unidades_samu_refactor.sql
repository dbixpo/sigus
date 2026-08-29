-- =============================================================================
-- Refatoração Unidades SAMU: seed tipos, alterações em unidades_samu
-- As tabelas tipos_unidade_samu e bases_descentralizadas são criadas no 01_schema
-- =============================================================================

-- 1. Seed Tipos de Unidade SAMU
INSERT INTO tipos_unidade_samu (id, nome, sigla, predefinido)
SELECT 1, 'Central de Regulação de Urgência', 'CRU', TRUE WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_samu WHERE id = 1);
INSERT INTO tipos_unidade_samu (id, nome, sigla, predefinido)
SELECT 2, 'Unidade de Suporte Avançado de Vida', 'ALFA', TRUE WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_samu WHERE id = 2);
INSERT INTO tipos_unidade_samu (id, nome, sigla, predefinido)
SELECT 3, 'Unidade de Suporte Básico de Vida', 'BETA', TRUE WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_samu WHERE id = 3);
INSERT INTO tipos_unidade_samu (id, nome, sigla, predefinido)
SELECT 4, 'Veículo de Intervenção Rápida', 'VIR', TRUE WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_samu WHERE id = 4);
INSERT INTO tipos_unidade_samu (id, nome, sigla, predefinido)
SELECT 5, 'Motolância', 'MOT', TRUE WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_samu WHERE id = 5);
INSERT INTO tipos_unidade_samu (id, nome, sigla, predefinido)
SELECT 6, 'Aeromédico', 'AER', TRUE WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_samu WHERE id = 6);
INSERT INTO tipos_unidade_samu (id, nome, sigla, predefinido)
SELECT 7, 'Ambulanchas', 'EMB', TRUE WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_samu WHERE id = 7);
INSERT INTO tipos_unidade_samu (id, nome, sigla, predefinido)
SELECT 8, 'Unidade de Simples Remoção', 'USR', TRUE WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_samu WHERE id = 8);

-- 2. Alterar unidades_samu (adicionar colunas para central/viatura)
ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS tipo_registro VARCHAR(20) DEFAULT 'central';
ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS apelido VARCHAR(100);
ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS cnes VARCHAR(7);
ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS logradouro VARCHAR(300);
ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS numero VARCHAR(20);
ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS complemento VARCHAR(100);
ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS bairro VARCHAR(100);
ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS cidade VARCHAR(100);
ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS cep VARCHAR(9);
ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS email VARCHAR(200);
ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS link_google_maps VARCHAR(500);
ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS base_id INTEGER REFERENCES bases_descentralizadas(id) ON DELETE SET NULL;
ALTER TABLE unidades_samu ADD COLUMN IF NOT EXISTS tipo_unidade_id INTEGER REFERENCES tipos_unidade_samu(id) ON DELETE SET NULL;

-- Migrar dados antigos (endereco -> logradouro, municipio -> cidade)
UPDATE unidades_samu SET tipo_registro = 'central' WHERE tipo_registro IS NULL;
UPDATE unidades_samu SET logradouro = endereco WHERE logradouro IS NULL AND endereco IS NOT NULL;
UPDATE unidades_samu SET cidade = municipio WHERE cidade IS NULL AND municipio IS NOT NULL;
