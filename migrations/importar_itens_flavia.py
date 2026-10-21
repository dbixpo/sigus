# -*- coding: utf-8 -*-
"""Cadastra os itens da planilha da Flávia: classificação RENEM, marca e modelo.

Não cria equipamento físico (patrimônio em sala). Não altera o que já é de TI.
"""
import os
import sys
import unicodedata
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import openpyxl
from app import create_app, db
from app.models.equipamento import (
    Marca, Modelo, TipoEquipamento, vincular_categoria,
)

PLANILHA = r'C:\Users\dbixpo\Desktop\Flavia\Itens SIGUS.xlsx'

# O que já está de informática fica como está. Se a planilha repetir, não cadastra.
NAO_CADASTRAR = {
    'computador (gabinete)',
    'computador all-in-one',
    'notebook',
    'tablet',
    'impressora',
    'monitor',
    'tv',
    'projetor',
    'no-break (para servidor)',
    'sistema de senha para atendimento',
    'tela de projecao',
    'aparelho de telefone',
}

ICONES = {
    'Médico-Assistencial': 'fas fa-stethoscope',
    'Apoio': 'fas fa-hand-holding-medical',
    'Infraestrutura': 'fas fa-screwdriver-wrench',
    'Geral': 'fas fa-box',
}


def norm(texto):
    texto = unicodedata.normalize('NFD', texto or '')
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return ' '.join(texto.lower().split())


def limpar(valor):
    if valor is None:
        return ''
    return ' '.join(str(valor).replace('\xa0', ' ').split())


def ler(caminho):
    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb.active
    itens = OrderedDict()
    for row in ws.iter_rows(min_row=3, values_only=True):
        nome = limpar(row[0] if row else '')
        if not nome or norm(nome) == 'descricao':
            continue
        clas = limpar(row[1] if len(row) > 1 else '')
        marca = limpar(row[2] if len(row) > 2 else '')
        modelo = limpar(row[3] if len(row) > 3 else '')
        item = itens.setdefault(nome, {'clas': clas, 'marcas': OrderedDict()})
        if clas:
            item['clas'] = clas
        if not marca:
            continue
        modelos = item['marcas'].setdefault(marca, [])
        if modelo and modelo not in modelos:
            modelos.append(modelo)
    return itens


def marca_por_nome(nome, cache):
    chave = norm(nome)
    if chave in cache:
        return cache[chave]
    marca = Marca.query.filter(db.func.lower(Marca.nome) == nome.lower()).first()
    if not marca:
        marca = Marca(nome=nome[:100], pendente=False)
        db.session.add(marca)
        db.session.flush()
    cache[chave] = marca
    return marca


def aplicar(itens):
    por_norm = {norm(t.nome): t for t in TipoEquipamento.query.all()}
    cache_marcas = {}
    pulados = []
    criados = reusados = marcas_novas = modelos_novos = 0
    antes_marcas = Marca.query.count()
    antes_modelos = Modelo.query.count()
    for nome, info in itens.items():
        if norm(nome) in NAO_CADASTRAR:
            pulados.append(nome)
            continue
        tipo = por_norm.get(norm(nome))
        if tipo and norm(tipo.nome) in NAO_CADASTRAR:
            pulados.append(nome)
            continue
        if not tipo:
            tipo = TipoEquipamento(
                nome=nome[:150],
                tem_patrimonio=True,
                ativo=True,
                icone=ICONES.get(info['clas'], 'fas fa-box'),
            )
            db.session.add(tipo)
            db.session.flush()
            por_norm[norm(tipo.nome)] = tipo
            criados += 1
        else:
            reusados += 1
        if info['clas']:
            vincular_categoria(tipo, info['clas'])
        for nome_marca, modelos in info['marcas'].items():
            marca = marca_por_nome(nome_marca, cache_marcas)
            if not tipo.marcas.filter_by(id=marca.id).first():
                tipo.marcas.append(marca)
            for nome_modelo in modelos:
                existe = Modelo.query.filter(
                    Modelo.tipo_equipamento_id == tipo.id,
                    Modelo.marca_id == marca.id,
                    db.func.lower(Modelo.nome) == nome_modelo.lower(),
                ).first()
                if existe:
                    continue
                db.session.add(Modelo(
                    tipo_equipamento_id=tipo.id,
                    marca_id=marca.id,
                    nome=nome_modelo[:150],
                    pendente=False,
                ))
                modelos_novos += 1
    db.session.flush()
    marcas_novas = Marca.query.count() - antes_marcas
    return pulados, criados, reusados, marcas_novas, modelos_novos


def main():
    if not os.path.isfile(PLANILHA):
        raise SystemExit(f'Planilha não encontrada: {PLANILHA}')
    itens = ler(PLANILHA)
    app = create_app()
    with app.app_context():
        pulados, criados, reusados, marcas, modelos = aplicar(itens)
        db.session.commit()
        print(f'itens na planilha: {len(itens)}')
        print(f'tipos criados: {criados}')
        print(f'tipos que ja existiam e receberam marca/modelo: {reusados}')
        print(f'marcas novas: {marcas}')
        print(f'modelos novos: {modelos}')
        print('NAO CADASTRADOS:')
        for nome in pulados:
            print(f'- {nome}')


if __name__ == '__main__':
    main()
