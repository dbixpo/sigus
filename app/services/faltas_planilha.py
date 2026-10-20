# -*- coding: utf-8 -*-
"""Cruza a falta abonada do perfil com os dias FA das planilhas de frequência já importadas."""
from datetime import date

from app import db
from app.models.falta_abonada import FaltaAbonada
from app.models.frequencia import (
    FreqImportacao, FreqLancamento, matriculas_do_usuario, normalizar_matricula,
)
from app.models.matricula import MatriculaProfissional
from app.models.usuario import Usuario
from app.services.frequencia_planilha import faltas_abonadas_nos_lancamentos


def _usuarios_das_matriculas(matriculas):
    """matrícula normalizada → Usuario. A primeira pessoa encontrada fica com a matrícula."""
    alvo = {normalizar_matricula(m) for m in matriculas}
    alvo.discard('')
    if not alvo:
        return {}
    achados = {}
    consulta = (
        db.session.query(MatriculaProfissional.numero, MatriculaProfissional.usuario_id)
        .filter(MatriculaProfissional.ativo.is_(True), MatriculaProfissional.numero.isnot(None))
        .all()
    )
    ids = set()
    por_id = {}
    for numero, usuario_id in consulta:
        n = normalizar_matricula(numero)
        if n in alvo and n not in por_id:
            por_id[n] = usuario_id
            ids.add(usuario_id)
    for (numero, usuario_id) in (
        db.session.query(Usuario.matricula, Usuario.id)
        .filter(Usuario.matricula.isnot(None))
        .all()
    ):
        n = normalizar_matricula(numero)
        if n in alvo and n not in por_id:
            por_id[n] = usuario_id
            ids.add(usuario_id)
    if not ids:
        return {}
    pessoas = {u.id: u for u in Usuario.query.filter(Usuario.id.in_(ids)).all()}
    for matricula, usuario_id in por_id.items():
        pessoa = pessoas.get(usuario_id)
        if pessoa:
            achados[matricula] = pessoa
    return achados


def ocorrencias_da_frequencia(matriculas, ano=None):
    """FA gravada em importações ativas. Cada item: data (ou None), quantidade, local, competencia, matricula, nome."""
    mats = sorted({normalizar_matricula(m) for m in matriculas} - {''})
    if not mats:
        return []
    q = (
        db.session.query(FreqLancamento, FreqImportacao)
        .join(FreqImportacao)
        .filter(
            FreqImportacao.status == FreqImportacao.STATUS_ATIVA,
            FreqLancamento.matricula.in_(mats),
        )
    )
    if ano:
        q = q.filter(db.extract('year', FreqImportacao.competencia) == int(ano))
    saida = []
    for lanc, imp in q.all():
        bruto = {
            'matricula': lanc.matricula,
            'nome': lanc.nome,
            'dias': lanc.dias or {},
            'totais': lanc.totais or {},
        }
        for item in faltas_abonadas_nos_lancamentos([bruto], imp.competencia):
            item['local'] = imp.local
            item['competencia'] = imp.competencia
            saida.append(item)
    saida.sort(key=lambda i: (i['data'] or i['competencia'], i['matricula']))
    return saida


def classificar_fa_previa(lancamentos, competencia):
    """Para a tela de conferência, antes de gravar: cada FA da planilha e se já existe no perfil."""
    if isinstance(competencia, str):
        competencia = date.fromisoformat(competencia)
    itens = faltas_abonadas_nos_lancamentos(lancamentos, competencia)
    pessoas = _usuarios_das_matriculas([i['matricula'] for i in itens])
    ids = {p.id for p in pessoas.values()}
    registros = []
    if ids:
        registros = (
            FaltaAbonada.query
            .filter(
                FaltaAbonada.usuario_id.in_(ids),
                FaltaAbonada.status == FaltaAbonada.STATUS_ATIVA,
                db.extract('year', FaltaAbonada.data_falta) == competencia.year,
                db.extract('month', FaltaAbonada.data_falta) == competencia.month,
            )
            .all()
        )
    por_usuario = {}
    for falta in registros:
        por_usuario.setdefault(falta.usuario_id, []).append(falta)

    linhas = []
    for item in itens:
        pessoa = pessoas.get(item['matricula'])
        faltas = por_usuario.get(pessoa.id, []) if pessoa else []
        mesma_data = next((f for f in faltas if item['data'] and f.data_falta == item['data']), None)
        if not pessoa:
            situacao = 'sem_cadastro'
        elif mesma_data:
            situacao = 'confirmada'
        elif faltas:
            situacao = 'outra_data'
        else:
            situacao = 'sem_registro'
        linhas.append({
            **item,
            'pessoa': pessoa.nome if pessoa else None,
            'situacao': situacao,
            'registro': mesma_data.data_falta if mesma_data else (faltas[0].data_falta if faltas else None),
        })
    return linhas


def painel_faltas(usuario, ano):
    """O que a tela de faltas abonadas mostra além dos registros do perfil."""
    mats = matriculas_do_usuario(usuario)
    todas = ocorrencias_da_frequencia(mats)
    do_ano = [o for o in todas if (o['data'] or o['competencia']).year == int(ano)]
    ativas = (
        FaltaAbonada.query
        .filter_by(usuario_id=usuario.id, status=FaltaAbonada.STATUS_ATIVA)
        .all()
    )
    datas_registro = {f.data_falta for f in ativas}
    meses = {}
    for falta in ativas:
        meses[(falta.ano, falta.mes)] = 'registro'
    for item in todas:
        ref = item['data'] or item['competencia']
        chave = (ref.year, ref.month)
        if chave in meses:
            if item['data'] and item['data'] in datas_registro:
                meses[chave] = 'ambos'
            elif meses[chave] == 'registro':
                meses[chave] = 'ambos'
        else:
            meses[chave] = 'planilha'

    so_planilha = []
    for item in do_ano:
        if item['data'] and item['data'] in datas_registro:
            continue
        so_planilha.append(item)

    meses_ano = {mes: origem for (a, mes), origem in meses.items() if a == int(ano)}
    return {
        'ocorrencias': do_ano,
        'so_planilha': so_planilha,
        'datas_planilha': {o['data']: o for o in do_ano if o['data']},
        'meses': meses,
        'usadas': len(meses_ano),
        'tem_planilha_sem_registro': any(origem == 'planilha' for origem in meses_ano.values()),
    }
