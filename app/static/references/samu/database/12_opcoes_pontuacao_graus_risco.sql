-- Pontuação em cada opção de resposta (para grau de risco)
ALTER TABLE opcoes_resposta ADD COLUMN IF NOT EXISTS pontuacao SMALLINT NOT NULL DEFAULT 0;

-- Faixas de pontuação → grau de risco (JSON: [{"min":0,"max":3,"grau":"Baixo"},...])
ALTER TABLE algoritmos_acolhimento ADD COLUMN IF NOT EXISTS graus_risco JSON;
