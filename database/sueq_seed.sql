
-- Dados de teste para validar as telas (não é o dump de produção do Patrick)
INSERT INTO sueq.parlamentares (nome, ativo) VALUES
    ('Iara Bernardi', true),
    ('Dr. Rodrigo Manga', true),
    ('Delegado Fernando', true);

INSERT INTO sueq.unidades (nome, nome_chave, endereco, telefone, ativo)
SELECT DISTINCT ON (u.nome)
    u.nome,
    lower(regexp_replace(unaccent(u.nome), '[^a-zA-Z0-9]+', '-', 'g')),
    COALESCE(u.endereco, ''),
    COALESCE(u.telefone, ''),
    true
FROM public.unidades u
WHERE u.nome IS NOT NULL
ORDER BY u.nome
LIMIT 12;

INSERT INTO sueq.status_opcoes (contexto, nome, ordem, ativo) VALUES
    ('licitacao', 'Em andamento', 1, true),
    ('licitacao', 'Homologado', 2, true),
    ('licitacao', 'Fracassado', 3, true),
    ('emenda_item', 'Aguardando licitação', 1, true),
    ('emenda_item', 'Em licitação', 2, true),
    ('emenda_item', 'Entregue', 3, true);

INSERT INTO sueq.processos (identificador, tipo, objeto, modalidade, status, secao, valor_estimado)
VALUES
    ('CPL 086/2025', 'Aquisição', 'Aquisição de aparelhos de ar-condicionado', 'Pregão Eletrônico', 'Em andamento', 'SUEQ', 420000),
    ('CPL 012/2026', 'ATA', 'Ata de registro de preços — mobiliário clínico', 'Pregão Eletrônico', 'Homologado', 'SUEQ', 180000);

INSERT INTO sueq.emendas (tipo, emenda, parlamentar, sei_emenda, valor_cedido, unidade, ano, unidade_id)
SELECT 'Federal', '2026/014', 'Iara Bernardi', 'SEI 12.345/2026', 250000,
       (SELECT nome FROM sueq.unidades ORDER BY id LIMIT 1),
       2026, (SELECT id FROM sueq.unidades ORDER BY id LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM sueq.emendas WHERE emenda = '2026/014');

INSERT INTO sueq.emendas (tipo, emenda, parlamentar, sei_emenda, valor_cedido, unidade, ano, unidade_id)
SELECT 'Estadual', '2026/022', 'Dr. Rodrigo Manga', 'SEI 12.400/2026', 180000,
       (SELECT nome FROM sueq.unidades OFFSET 1 LIMIT 1),
       2026, (SELECT id FROM sueq.unidades OFFSET 1 LIMIT 1)
WHERE NOT EXISTS (SELECT 1 FROM sueq.emendas WHERE emenda = '2026/022');

INSERT INTO sueq.emenda_itens (
    emenda_id, emenda, item, qtde, vl_unitario, vl_total, cpl, status,
    qtde_cadastrada, vl_unitario_cadastrado, vl_total_cadastrado,
    unidade_beneficiada, unidade_beneficiada_id, processo_id
)
SELECT e.id, e.emenda, 'Ar-condicionado inverter 24.000 BTU', 10, 3749.82, 37498.20,
       'CPL 086/2025', 'Em licitação', 10, 3800, 38000,
       e.unidade, e.unidade_id, p.id
FROM sueq.emendas e
CROSS JOIN LATERAL (SELECT id FROM sueq.processos WHERE identificador = 'CPL 086/2025' LIMIT 1) p
WHERE e.emenda = '2026/014'
  AND NOT EXISTS (SELECT 1 FROM sueq.emenda_itens WHERE emenda = '2026/014');

INSERT INTO sueq.emenda_itens (
    emenda_id, emenda, item, qtde, vl_unitario, vl_total, status,
    qtde_cadastrada, vl_unitario_cadastrado, vl_total_cadastrado,
    unidade_beneficiada, unidade_beneficiada_id
)
SELECT e.id, e.emenda, 'Autoclave 21 litros', 4, 8900, 35600,
       'Aguardando licitação', 4, 8900, 35600,
       e.unidade, e.unidade_id
FROM sueq.emendas e
WHERE e.emenda = '2026/022'
  AND NOT EXISTS (SELECT 1 FROM sueq.emenda_itens WHERE emenda = '2026/022');

INSERT INTO sueq.chamados (
    protocolo, data_solicitacao, unidade, equipamento, fabricante, patrimonio,
    categoria, servico, problema, descricao, endereco, telefone, responsavel,
    grau_urgencia, status, unidade_id
)
SELECT 'SUEQ-2026-0001', to_char(CURRENT_DATE, 'DD/MM/YYYY'), u.nome,
       'Ar-condicionado', 'Agratto', '123456', 'Manutenção', 'Corretiva',
       'Não gela', 'Unidade relatou que o aparelho da recepção não está gelando.',
       COALESCE(u.endereco, ''), COALESCE(u.telefone, ''), 'Técnico da unidade',
       'Média', 'Aguardando abertura', u.id
FROM sueq.unidades u
ORDER BY u.id
LIMIT 1;

INSERT INTO sueq.chamados (
    protocolo, data_solicitacao, unidade, equipamento, fabricante, patrimonio,
    categoria, servico, problema, descricao, grau_urgencia, status, unidade_id
)
SELECT 'SUEQ-2026-0002', to_char(CURRENT_DATE, 'DD/MM/YYYY'), u.nome,
       'Autoclave', 'Stermax', '778899', 'Manutenção', 'Preventiva',
       'Vazamento de vapor', 'Vazamento na porta durante o ciclo.',
       'Alta', 'Aberto', u.id
FROM sueq.unidades u
ORDER BY u.id OFFSET 1
LIMIT 1;

INSERT INTO sueq.chamados_controle (protocolo, status, chamado_protocolo, chamado_id)
SELECT c.protocolo, 'Aguardando abertura', c.protocolo, c.id
FROM sueq.chamados c
WHERE NOT EXISTS (
    SELECT 1 FROM sueq.chamados_controle cc WHERE cc.protocolo = c.protocolo
);
