# -*- coding: utf-8 -*-
"""Catálogo de inventário para banco novo ou dump anterior a esta entrega.

Idempotente. Não renomeia item, não apaga equipamento e não lê planilha.

- Colunas de incorporação do equipamento (ano, próprio, nota, empenho…)
- Classificação RENEM (Médico-Assistencial, Apoio, Infraestrutura, Geral, Veículos)
- Status do equipamento (Ativo, Inservível, Aguardando Instalação, Disponível, Sobressalente)
- Itens de veículo da RENEM e a coluna veiculos.tipo_veiculo_id

    python migrations/add_inventario_catalogo.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text

from app import create_app, db
from app.models.equipamento import CategoriaEquipamento
from app.models.status_equipamento import garantir_status_equipamento
from app.models.veiculo import (
    CLASSIFICACAO_VEICULOS, DESCRICAO_VEICULOS, ITENS_RENEM_VEICULO,
    TipoVeiculo, icone_tipo_veiculo,
)

COMANDOS = [
    "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS ano_fabricacao INTEGER",
    "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS proprio BOOLEAN",
    "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS forma_incorporacao VARCHAR(30)",
    "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS numero_nota_fiscal VARCHAR(60)",
    "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS numero_empenho VARCHAR(60)",
    "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS fonte_recurso VARCHAR(150)",
    "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS numero_processo VARCHAR(80)",
    "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS numero_contrato_af VARCHAR(80)",
    "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS fornecedor VARCHAR(200)",
    "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS data_entrega_unidade DATE",
    "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS garantia VARCHAR(120)",
    "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS vida_util_estimada VARCHAR(80)",
    "ALTER TABLE equipamentos ADD COLUMN IF NOT EXISTS data_desativacao DATE",
    "ALTER TABLE marcas ADD COLUMN IF NOT EXISTS pendente BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE modelos ADD COLUMN IF NOT EXISTS pendente BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE unidades ADD COLUMN IF NOT EXISTS inventario_inicial_concluido BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE veiculos ADD COLUMN IF NOT EXISTS tipo_veiculo_id INTEGER",
]

CATEGORIAS = (
    (1, 'Médico-Assistencial', 'Equipamento usado na assistência direta.'),
    (2, 'Apoio', 'Apoio à assistência.'),
    (3, 'Infraestrutura', 'Instalação predial e redes.'),
    (4, 'Geral', 'Mobiliário, informática e uso geral.'),
    (5, CLASSIFICACAO_VEICULOS, DESCRICAO_VEICULOS),
)


def _categoria(nome, ordem, descricao):
    categoria = CategoriaEquipamento.query.filter(
        db.func.lower(CategoriaEquipamento.nome) == nome.lower()
    ).first()
    if categoria:
        return categoria
    categoria = CategoriaEquipamento(nome=nome, ordem=ordem, descricao=descricao, ativo=True)
    db.session.add(categoria)
    db.session.flush()
    return categoria


app = create_app()
with app.app_context():
    CategoriaEquipamento.__table__.create(db.engine, checkfirst=True)
    TipoVeiculo.__table__.create(db.engine, checkfirst=True)
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE tipos_equipamento ADD COLUMN IF NOT EXISTS categoria_id INTEGER "
            "REFERENCES categorias_equipamento(id) ON DELETE SET NULL"
        ))
        for sql in COMANDOS:
            conn.execute(text(sql))
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'veiculos_tipo_veiculo_id_fkey'
                ) THEN
                    ALTER TABLE veiculos
                    ADD CONSTRAINT veiculos_tipo_veiculo_id_fkey
                    FOREIGN KEY (tipo_veiculo_id) REFERENCES tipos_veiculo(id) ON DELETE SET NULL;
                END IF;
            END $$;
        """))
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_categorias_equipamento_nome "
            "ON categorias_equipamento (lower(nome))"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_tipos_equipamento_categoria "
            "ON tipos_equipamento (categoria_id)"
        ))
        conn.commit()
    veiculos = None
    for ordem, nome, descricao in CATEGORIAS:
        categoria = _categoria(nome, ordem, descricao)
        if nome == CLASSIFICACAO_VEICULOS:
            veiculos = categoria
    for nome in ITENS_RENEM_VEICULO:
        existe = TipoVeiculo.query.filter(
            db.func.lower(TipoVeiculo.nome) == nome.lower()
        ).first()
        if existe:
            if veiculos and not existe.categoria_id:
                existe.categoria_id = veiculos.id
            continue
        db.session.add(TipoVeiculo(
            nome=nome,
            icone=icone_tipo_veiculo(nome),
            categoria_id=veiculos.id if veiculos else None,
            ativo=True,
        ))
    db.session.commit()
    garantir_status_equipamento()
    print(
        'OK: inventário.',
        'categorias', CategoriaEquipamento.query.count(),
        'tipos de veículo', TipoVeiculo.query.count(),
    )
