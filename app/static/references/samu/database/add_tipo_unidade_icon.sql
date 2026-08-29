-- Ícone para cada tipo de unidade SAMU (Bootstrap Icons: bi-ambulance, bi-motorcycle, etc.)
ALTER TABLE tipos_unidade_samu ADD COLUMN IF NOT EXISTS icon VARCHAR(50);
