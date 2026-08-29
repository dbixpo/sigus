-- Adiciona coluna perfil em equipes_membros (categoria por perfil)
ALTER TABLE equipes_membros ADD COLUMN IF NOT EXISTS perfil VARCHAR(50);
-- Permite cbo nulo (legado)
ALTER TABLE equipes_membros ALTER COLUMN cbo DROP NOT NULL;
