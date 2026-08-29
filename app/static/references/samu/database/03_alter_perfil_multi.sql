-- Permite múltiplos perfis (códigos separados por vírgula)
ALTER TABLE usuarios ALTER COLUMN perfil TYPE VARCHAR(200);
