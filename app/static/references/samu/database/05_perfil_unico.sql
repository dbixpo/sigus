-- Migra perfis múltiplos (vírgula) para perfil único (primeiro da lista)
UPDATE usuarios SET perfil = TRIM(SPLIT_PART(perfil, ',', 1))
WHERE perfil LIKE '%,%';
