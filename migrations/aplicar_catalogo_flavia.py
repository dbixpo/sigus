# -*- coding: utf-8 -*-
"""Troca o catálogo de itens da planilha antiga pelo da Flávia e abre os campos do inventário.

A planilha traz descrição, classificação RENEM (RDC 509/2021), marca e modelo.
Nomes longos que são o mesmo item são encurtados (o id permanece, o kit de sala
continua apontando para ele). Item que a Flávia não listou fica como está.
Equipamento de informática entra como Geral.

Uso:
    python migrations/aplicar_catalogo_flavia.py
    python migrations/aplicar_catalogo_flavia.py --planilha "C:\\caminho\\Itens SIGUS.xlsx"
"""
import argparse
import os
import re
import sys
import unicodedata
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl
from sqlalchemy import text

from app import create_app, db
from app.models.equipamento import (
    CONDICAO_POR_STATUS, Marca, Modelo, TipoEquipamento,
)

PLANILHA_PADRAO = r'C:\Users\dbixpo\Desktop\jessica\flavia\Itens SIGUS.xlsx'

# Nome que está no SIGUS hoje → nome oficial da planilha da Flávia. Só pares 1:1.
RENOMEAR = {
    'Amalgamador odontológico': 'Amalgamador Odontológico',
    'Aminioscópio': 'Amnioscópio',
    'Aparelho de Raios X – Odontológico c/ Sensores e Suporte': 'Aparelho de Raios X Odontológico',
    'Ar-condicionado': 'Ar Condicionado',
    'Armário Alto de Madeira': 'Armário Alto',
    'Armário Vitrine Armário alto de madeira 1 porta': 'Armário Vitrine',
    'Balança Antropométrica Digital Adulto': 'Balança Antropométrica Adulto',
    'Balança Antropométrica Digital Infantil': 'Balança Antropométrica Infantil',
    'Balança Antropométrica Digital Obeso': 'Balança Antropométrica para Obesos',
    'Biombo triplo': 'Biombo',
    'Bomba à Vacuo Odontológica': 'Bomba à Vácuo Odontológica',
    'Bomba de infusão': 'Bomba de Infusão',
    'Cadeira de rodas Adulto': 'Cadeira de Rodas Adulto',
    'Cadeira de Rodas Obeso': 'Cadeira de Rodas para Obeso',
    'Cadeira Odontológica Completa': 'Cadeira Odontológica',
    'Cama Hospitalar Tipo Fawler Mecânica Elétrica': 'Cama Hospitalar Tipo Fawler Mecânica',
    'Câmara de Vacina': 'Câmara para Conservação de Imunobiológicos e Termolábeis',
    'Carro de curativo': 'Carro de Curativos',
    'Carro de emergência': 'Carro de Emergência',
    'Compressor': 'Compressor de Ar',
    'DEA (RCP)': 'DEA - Desfibrilador Externo Automático',
    'Detector Fetal de Mesa': 'Detector Fetal',
    'Eletrocardiógrafo com carrinho': 'Eletrocardiógrafo',
    'Fotopolimerizador': 'Fotopolimerizador de Resinas',
    'Micromotor com localizador de ápice': 'Micromotor Elétrico com Localizador de Ápice',
    'Otoscópio': 'Otoscópio Simples',
    'Seladora grau cirúrgico': 'Seladora de Grau Cirúrgico',
    'Suporte de Hamper inox': 'Suporte de Hamper',
    'Suporte de soro inox': 'Suporte de Soro',
    'Telefone': 'Aparelho de Telefone',
    'Ultrassom odontológico': 'Ultrassom Odontológico',
    'Unidade auxiliar com Sugador': 'Unidade Auxiliar com Sugador',
    'Ventilador Pulmonar Pressométrico e Volumétrico de Transporte': 'Ventilador Pulmonar de Transporte',
}

# Informática fica em Geral mesmo quando a planilha não lista o item.
INFORMATICA = {
    'Computador (Gabinete)',
    'Computador All-In-One',
    'Notebook',
    'Tablet',
    'Impressora',
    'Monitor',
    'TV',
    'Projetor',
    'No-Break (para servidor)',
    'Sistema de senha para atendimento',
    'Tela de Projeção',
    'Aparelho de Telefone',
}

ICONES = {
    'Médico-Assistencial': 'fas fa-stethoscope',
    'Apoio': 'fas fa-hand-holding-medical',
    'Infraestrutura': 'fas fa-screwdriver-wrench',
    'Geral': 'fas fa-box',
}

SCHEMA = [
    "ALTER TABLE equipamentos ALTER COLUMN status TYPE VARCHAR(40)",
    "ALTER TABLE equipamentos ALTER COLUMN condicao TYPE VARCHAR(40)",
    "ALTER TABLE equipamentos ALTER COLUMN condicao DROP NOT NULL",
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
    "ALTER TABLE modelos DROP CONSTRAINT IF EXISTS modelos_marca_id_nome_key",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_modelo_tipo_marca_nome ON modelos (tipo_equipamento_id, marca_id, nome)",
    "ALTER TABLE unidades ADD COLUMN IF NOT EXISTS inventario_inicial_concluido BOOLEAN NOT NULL DEFAULT FALSE",
    """
    CREATE TABLE IF NOT EXISTS equipamento_documentos (
        id              SERIAL PRIMARY KEY,
        equipamento_id  INTEGER NOT NULL REFERENCES equipamentos(id) ON DELETE CASCADE,
        filename        VARCHAR(80) NOT NULL,
        original        VARCHAR(200),
        mime_type       VARCHAR(100),
        tamanho_bytes   INTEGER,
        criado_por      INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
        criado_em       TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
]


def norm(valor):
    texto = unicodedata.normalize('NFD', valor or '')
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower().replace('–', ' ').replace('-', ' ')
    texto = re.sub(r'[^a-z0-9 ]', ' ', texto)
    return re.sub(r'\s+', ' ', texto).strip()


def limpar(valor):
    if valor is None:
        return ''
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return ' '.join(str(valor).split())


def ler_planilha(caminho):
    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb.active
    catalogo = OrderedDict()
    for row in ws.iter_rows(min_row=2, values_only=True):
        desc, clas, marca, modelo = (row + (None, None, None, None))[:4]
        nome = limpar(desc)
        classificacao = limpar(clas)
        if not nome or nome == 'Descrição' or classificacao == 'Classificação RENEM':
            continue
        item = catalogo.setdefault(nome, {'clas': classificacao, 'marcas': OrderedDict()})
        if classificacao:
            item['clas'] = classificacao
        marca = limpar(marca)
        modelo = limpar(modelo)
        if marca:
            item['marcas'].setdefault(marca, [])
            if modelo and modelo not in item['marcas'][marca]:
                item['marcas'][marca].append(modelo)
    return catalogo


def garantir_marca(nome, cache):
    chave = nome.lower()
    if chave in cache:
        return cache[chave]
    marca = Marca.query.filter(db.func.lower(Marca.nome) == chave).first()
    if not marca:
        marca = Marca(nome=nome, pendente=False)
        db.session.add(marca)
        db.session.flush()
    cache[chave] = marca
    return marca


def garantir_modelo(tipo, marca, nome):
    with db.session.no_autoflush:
        modelo = Modelo.query.filter_by(
            tipo_equipamento_id=tipo.id, marca_id=marca.id, nome=nome,
        ).first()
        if modelo:
            return
        solto = Modelo.query.filter_by(
            tipo_equipamento_id=None, marca_id=marca.id, nome=nome,
        ).first()
    if solto:
        solto.tipo_equipamento_id = tipo.id
        solto.pendente = False
        return
    db.session.add(Modelo(
        tipo_equipamento_id=tipo.id, marca_id=marca.id, nome=nome, pendente=False,
    ))


def vincular_marcas(tipo, marcas, cache):
    for nome_marca, modelos in marcas.items():
        marca = garantir_marca(nome_marca, cache)
        if not marca.suporta_tipo(tipo.id):
            marca.tipos.append(tipo)
        for nome_modelo in modelos:
            garantir_modelo(tipo, marca, nome_modelo)


def achar(nome, por_norm):
    return por_norm.get(norm(nome))


def condicao_compativel(status, condicao):
    permitidas = CONDICAO_POR_STATUS.get(status) or ()
    if not permitidas:
        return None
    legado = {'excelente': 'boa', 'inservivel': 'ruim'}
    condicao = legado.get(condicao, condicao)
    if condicao in permitidas:
        return condicao
    return permitidas[0]


def migrar_estado():
    from app.models.equipamento import Equipamento
    n = 0
    for eq in Equipamento.query.all():
        status = eq.status
        condicao = eq.condicao
        if status == 'baixado':
            status = 'inservivel'
            eq.ativo = True
        elif status == 'em_manutencao':
            status = 'disponivel_transferencia'
            condicao = 'necessita_manutencao'
        elif status == 'inservivel' or condicao == 'inservivel':
            status = 'inservivel'
        if status not in CONDICAO_POR_STATUS and status != 'inservivel' and status != 'aguardando_instalacao':
            status = 'ativo'
        nova = condicao_compativel(status, condicao)
        if eq.status != status or eq.condicao != nova:
            eq.status = status
            eq.condicao = nova
            n += 1
    return n


def aplicar(catalogo):
    tipos = TipoEquipamento.query.all()
    por_norm = {norm(t.nome): t for t in tipos}
    renomeados = criados = 0

    for origem, destino in RENOMEAR.items():
        tipo = achar(origem, por_norm)
        if not tipo or norm(tipo.nome) == norm(destino):
            continue
        ocupado = achar(destino, por_norm)
        if ocupado and ocupado.id != tipo.id:
            print(f'  pulado (nome já existe): {origem} → {destino}')
            continue
        print(f'  renomeado: {tipo.nome} → {destino}')
        por_norm.pop(norm(tipo.nome), None)
        tipo.nome = destino
        por_norm[norm(destino)] = tipo
        renomeados += 1
    db.session.flush()

    cache_marcas = {}
    for nome, info in catalogo.items():
        tipo = achar(nome, por_norm)
        if not tipo:
            tipo = TipoEquipamento(
                nome=nome,
                classificacao=info['clas'],
                tem_patrimonio=True,
                ativo=True,
                icone=ICONES.get(info['clas'], 'fas fa-box'),
            )
            db.session.add(tipo)
            db.session.flush()
            por_norm[norm(nome)] = tipo
            criados += 1
            print(f'  criado: {nome} [{info["clas"]}]')
        else:
            if tipo.nome != nome:
                por_norm.pop(norm(tipo.nome), None)
                tipo.nome = nome
                por_norm[norm(nome)] = tipo
            tipo.classificacao = info['clas']
            tipo.ativo = True
        vincular_marcas(tipo, info['marcas'], cache_marcas)
    db.session.flush()

    for tipo in TipoEquipamento.query.all():
        if tipo.nome in INFORMATICA or tipo.classificacao == 'Equipamentos de informática e telefonia':
            tipo.classificacao = 'Geral'
    return renomeados, criados


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--planilha', default=PLANILHA_PADRAO)
    args = parser.parse_args()
    if not os.path.isfile(args.planilha):
        raise SystemExit(f'Planilha não encontrada: {args.planilha}')

    catalogo = ler_planilha(args.planilha)
    print(f'{len(catalogo)} itens na planilha')

    app = create_app()
    with app.app_context():
        with db.engine.begin() as conn:
            for sql in SCHEMA:
                conn.execute(text(sql))
        print('Schema atualizado')
        n = migrar_estado()
        print(f'{n} equipamento(s) com status/condição ajustados')
        renomeados, criados = aplicar(catalogo)
        db.session.commit()
        print(f'Pronto: {renomeados} renomeados, {criados} criados, marcas e modelos vinculados.')


if __name__ == '__main__':
    main()
