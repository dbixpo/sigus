-- =============================================================================
-- Equipes: viatura + veículo + profissionais (Montar Equipes - Rádio Operador)
-- =============================================================================

CREATE TABLE IF NOT EXISTS equipes (
    id SERIAL PRIMARY KEY,
    unidade_samu_id INTEGER NOT NULL REFERENCES unidades_samu(id) ON DELETE CASCADE,
    veiculo_id INTEGER REFERENCES veiculos(id) ON DELETE SET NULL,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(unidade_samu_id)
);

CREATE TABLE IF NOT EXISTS equipes_membros (
    id SERIAL PRIMARY KEY,
    equipe_id INTEGER NOT NULL REFERENCES equipes(id) ON DELETE CASCADE,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    cbo VARCHAR(10) NOT NULL,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(equipe_id, usuario_id)
);

CREATE INDEX IF NOT EXISTS ix_equipes_unidade_samu ON equipes(unidade_samu_id);
CREATE INDEX IF NOT EXISTS ix_equipes_membros_equipe ON equipes_membros(equipe_id);
