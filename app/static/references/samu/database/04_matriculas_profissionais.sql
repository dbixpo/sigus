-- Matrículas profissionais (como no SIGUS): número, vínculo, CBO, conselho, etc.
CREATE TABLE IF NOT EXISTS matriculas_profissionais (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    numero VARCHAR(50) NOT NULL,
    vinculo VARCHAR(1),
    tipo_vinculo VARCHAR(1),
    cbo VARCHAR(10),
    reg_conselho VARCHAR(30),
    orgao_emissor VARCHAR(50),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_matriculas_profissionais_usuario ON matriculas_profissionais(usuario_id);
