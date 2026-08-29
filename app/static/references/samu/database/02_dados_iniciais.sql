-- =============================================================================
-- Sistema SAMU 192 - Dados Iniciais
-- Executar após 01_schema.sql
-- =============================================================================

-- Unidade SAMU padrão (apenas se tabela estiver vazia)
INSERT INTO unidades_samu (nome, sigla, ativo)
SELECT 'Central SAMU 192', 'CENTRAL', TRUE
WHERE NOT EXISTS (SELECT 1 FROM unidades_samu LIMIT 1);
