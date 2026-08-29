CREATE TABLE IF NOT EXISTS tipos_unidade_saude (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    sigla VARCHAR(20) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tipos pré-cadastrados
INSERT INTO tipos_unidade_saude (nome, sigla) SELECT 'Atenção Primária', 'APS' WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_saude WHERE sigla = 'APS');
INSERT INTO tipos_unidade_saude (nome, sigla) SELECT 'Atenção Especializada', 'AES' WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_saude WHERE sigla = 'AES');
INSERT INTO tipos_unidade_saude (nome, sigla) SELECT 'Hospital', 'HOS' WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_saude WHERE sigla = 'HOS');
INSERT INTO tipos_unidade_saude (nome, sigla) SELECT 'Unidade de Pronto Atendimento', 'UPA' WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_saude WHERE sigla = 'UPA');
INSERT INTO tipos_unidade_saude (nome, sigla) SELECT 'Unidade Pré-Hospitalar', 'UPH' WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_saude WHERE sigla = 'UPH');
INSERT INTO tipos_unidade_saude (nome, sigla) SELECT 'Pronto Atendimento', 'PA' WHERE NOT EXISTS (SELECT 1 FROM tipos_unidade_saude WHERE sigla = 'PA');

ALTER TABLE unidades_saude ADD COLUMN IF NOT EXISTS tipo_unidade_id INTEGER REFERENCES tipos_unidade_saude(id) ON DELETE SET NULL;
ALTER TABLE unidades_saude ADD COLUMN IF NOT EXISTS logradouro VARCHAR(300);
ALTER TABLE unidades_saude ADD COLUMN IF NOT EXISTS numero VARCHAR(20);
ALTER TABLE unidades_saude ADD COLUMN IF NOT EXISTS complemento VARCHAR(100);
ALTER TABLE unidades_saude ADD COLUMN IF NOT EXISTS bairro VARCHAR(100);
ALTER TABLE unidades_saude ADD COLUMN IF NOT EXISTS cidade VARCHAR(100);
ALTER TABLE unidades_saude ADD COLUMN IF NOT EXISTS cep VARCHAR(9);
ALTER TABLE unidades_saude ADD COLUMN IF NOT EXISTS email VARCHAR(200);
ALTER TABLE unidades_saude ADD COLUMN IF NOT EXISTS link_google_maps VARCHAR(500);
ALTER TABLE unidades_saude ADD COLUMN IF NOT EXISTS hora_inicio TIME;
ALTER TABLE unidades_saude ADD COLUMN IF NOT EXISTS hora_fim TIME;
ALTER TABLE unidades_saude ADD COLUMN IF NOT EXISTS funcionamento_24h BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE unidades_saude SET logradouro = endereco WHERE logradouro IS NULL AND endereco IS NOT NULL;
UPDATE unidades_saude SET cidade = municipio WHERE cidade IS NULL AND municipio IS NOT NULL;
