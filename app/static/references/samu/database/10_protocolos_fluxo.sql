-- Migração: proxima_pergunta_id em opcoes_resposta (fluxograma)
ALTER TABLE opcoes_resposta ADD COLUMN IF NOT EXISTS proxima_pergunta_id INTEGER REFERENCES perguntas_protocolo(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS ix_opcoes_resposta_proxima ON opcoes_resposta(proxima_pergunta_id);
