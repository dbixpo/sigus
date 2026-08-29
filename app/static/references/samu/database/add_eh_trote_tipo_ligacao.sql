-- Adiciona eh_trote em tipos_ligacao (para identificar trotes no dashboard)
ALTER TABLE tipos_ligacao ADD COLUMN IF NOT EXISTS eh_trote BOOLEAN NOT NULL DEFAULT FALSE;
