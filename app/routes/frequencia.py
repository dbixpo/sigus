# -*- coding: utf-8 -*-
"""Planilha mensal de frequência: importação, apontamentos do profissional e da unidade."""
import calendar
import difflib
import json
import os
import re
import secrets
import time
import unicodedata
from collections import OrderedDict
from datetime import date

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required

from app import db
from app.models.frequencia import (
    FreqHoraExtra, FreqImportacao, FreqLancamento, GRUPOS_JUSTIFICATIVA, RhFuncaoCbo, RhLocal, RhServidor,
    SIGLAS_JUSTIFICATIVA, TIPOS_HORA_EXTRA, TOTAIS_CAPA, competencia_label, matriculas_do_usuario,
    normalizar_matricula, unidades_gestao_rh,
)
from app.models.matricula import MatriculaProfissional
from app.models.notificacao import Notificacao
from app.models.unidade import Unidade
from app.services.base_rh import buscar_servidores, servidores_json
from app.services.frequencia_planilha import PlanilhaInvalida, ler_planilha
from app.utils import agora_local

frequencia_bp = Blueprint('frequencia', __name__, url_prefix='/rh')

_EXTENSOES = ('.xls', '.xlsx')
_TAMANHO_MAX = 15 * 1024 * 1024
_VALIDADE_PREVIA = 2 * 3600
_STOP_LOCAL = {'SES', 'UBS', 'USF', 'PA', 'E', 'DE', 'DO', 'DA', 'DOS', 'DAS', 'ADM', 'REC',
               'ENFERMAGEM', 'ENFERM', 'MEDICOS', 'MEDICO', 'UNIDADE', 'SAUDE', 'BASICA'}


# ── Acesso ──────────────────────────────────────────────────────────────────

def _gestao():
    return unidades_gestao_rh(current_user)


def _exigir_importador():
    if not current_user.pode_importar_frequencia:
        abort(403)


def _ve_tudo():
    return _gestao() is None


def _unidades_escolha():
    ids = _gestao()
    q = Unidade.query.filter_by(status='ativa')
    if ids is not None:
        q = q.filter(Unidade.id.in_(ids or [0]))
    return q.order_by(Unidade.nome).all()


def _pode_ver_matricula(matricula):
    if matricula in matriculas_do_usuario(current_user):
        return True
    ids = _gestao()
    if ids is None:
        return True
    if not ids:
        return False
    return db.session.query(FreqLancamento.id).join(FreqImportacao).filter(
        FreqLancamento.matricula == matricula,
        FreqImportacao.status == FreqImportacao.STATUS_ATIVA,
        FreqImportacao.unidade_id.in_(ids),
    ).first() is not None


# ── Prévia temporária ───────────────────────────────────────────────────────

def _pasta_previas():
    pasta = os.path.join(current_app.instance_path, 'tmp_frequencia')
    os.makedirs(pasta, exist_ok=True)
    agora = time.time()
    for nome in os.listdir(pasta):
        caminho = os.path.join(pasta, nome)
        try:
            if agora - os.path.getmtime(caminho) > _VALIDADE_PREVIA:
                os.remove(caminho)
        except OSError:
            pass
    return pasta


def _salvar_previa(dados):
    token = secrets.token_hex(16)
    dados['_usuario_id'] = current_user.id
    with open(os.path.join(_pasta_previas(), token + '.json'), 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False)
    return token


def _carregar_previa(token):
    if not re.fullmatch(r'[0-9a-f]{32}', token or ''):
        return None, None
    caminho = os.path.join(_pasta_previas(), token + '.json')
    if not os.path.exists(caminho):
        return None, None
    with open(caminho, encoding='utf-8') as f:
        dados = json.load(f)
    if dados.get('_usuario_id') != current_user.id:
        return None, None
    return dados, caminho


# ── Sugestão de unidade para o local da planilha ───────────────────────────

def _nucleo(nome):
    s = unicodedata.normalize('NFKD', nome or '').encode('ascii', 'ignore').decode().upper()
    s = re.sub(r'[^A-Z0-9 ]', ' ', s)
    return ' '.join(p for p in s.split() if p not in _STOP_LOCAL)


def _sugerir_unidade(local, unidades):
    alvo = _nucleo(local)
    if not alvo:
        return None
    melhor, nota = None, 0.0
    for u in unidades:
        n = _nucleo(u.nome)
        if not n:
            continue
        r = difflib.SequenceMatcher(None, alvo, n).ratio()
        if n.startswith(alvo) or alvo.startswith(n):
            r += 0.15
        if r > nota:
            melhor, nota = u, r
    return melhor if nota >= 0.6 else None


# ── Importação ──────────────────────────────────────────────────────────────

def _importacoes_visiveis():
    q = FreqImportacao.query
    ids = _gestao()
    if ids is not None:
        q = q.filter(db.or_(FreqImportacao.unidade_id.in_(ids or [0]),
                            FreqImportacao.importado_por == current_user.id))
    return q


@frequencia_bp.route('/frequencia/importar', methods=['GET', 'POST'])
@login_required
def importar():
    _exigir_importador()
    if request.method == 'GET':
        historico = (_importacoes_visiveis()
                     .order_by(FreqImportacao.competencia.desc(), FreqImportacao.importado_em.desc())
                     .limit(60).all())
        return render_template('rh/frequencia_importar.html', historico=historico,
                               ve_tudo=_ve_tudo())

    arq = request.files.get('planilha')
    if not arq or not arq.filename:
        flash('Escolha a planilha de frequência (.xls ou .xlsx).', 'warning')
        return redirect(url_for('frequencia.importar'))
    nome = os.path.basename(arq.filename)
    if not nome.lower().endswith(_EXTENSOES):
        flash('Formato não aceito. Envie a planilha .xls ou .xlsx que vai para o RH.', 'warning')
        return redirect(url_for('frequencia.importar'))
    conteudo = arq.read(_TAMANHO_MAX + 1)
    if len(conteudo) > _TAMANHO_MAX:
        flash('Arquivo muito grande (máximo 15 MB).', 'warning')
        return redirect(url_for('frequencia.importar'))
    try:
        dados = ler_planilha(conteudo, nome)
    except PlanilhaInvalida as e:
        flash(str(e), 'danger')
        return redirect(url_for('frequencia.importar'))
    except Exception:
        current_app.logger.exception('Falha ao ler planilha de frequência %s', nome)
        flash('Não consegui ler essa planilha. Confira se é o modelo mensal do RH.', 'danger')
        return redirect(url_for('frequencia.importar'))
    del conteudo
    token = _salvar_previa(dados)
    return redirect(url_for('frequencia.previa', token=token))


@frequencia_bp.route('/frequencia/importar/<token>')
@login_required
def previa(token):
    _exigir_importador()
    dados, _ = _carregar_previa(token)
    if not dados:
        flash('A prévia expirou. Envie a planilha de novo.', 'warning')
        return redirect(url_for('frequencia.importar'))

    competencia = date.fromisoformat(dados['competencia'])
    unidades = _unidades_escolha()
    mapa = RhLocal.query.filter_by(nome=dados['local']).first()
    unidade_sel = None
    if mapa and mapa.unidade_id and any(u.id == mapa.unidade_id for u in unidades):
        unidade_sel = mapa.unidade_id
    sugerida = None
    if not unidade_sel:
        s = _sugerir_unidade(dados['local'], unidades)
        sugerida = s.id if s else None
    if not unidade_sel and len(unidades) == 1:
        unidade_sel = unidades[0].id

    anterior = FreqImportacao.query.filter_by(
        competencia=competencia, local=dados['local'], status=FreqImportacao.STATUS_ATIVA).first()

    mats = [l['matricula'] for l in dados['lancamentos']] + [h['matricula'] for h in dados['horas_extras']]
    no_sigus = _matriculas_no_sigus(mats)
    sem_cadastro = sorted({m for m in mats if m not in no_sigus})

    mes_ant = _mes_anterior(competencia)
    saldos_ant = _saldos_em(mes_ant, [l['matricula'] for l in dados['lancamentos']])
    divergencias = []
    for l in dados['lancamentos']:
        prev = saldos_ant.get(l['matricula'])
        if prev is not None and l['banco_saldo_anterior'] is not None \
                and abs(prev - l['banco_saldo_anterior']) > 0.01:
            divergencias.append((l, prev))

    for l in dados['lancamentos']:
        l['dias_ord'] = sorted((int(k), v) for k, v in (l['dias'] or {}).items())
        l['banco_ok'] = l['banco_saldo_atual'] is None or abs(
            (l['banco_saldo_anterior'] or 0) + (l['banco_realizadas'] or 0)
            - (l['banco_utilizadas'] or 0) - l['banco_saldo_atual']) < 0.01

    return render_template(
        'rh/frequencia_previa.html', token=token, dados=dados,
        competencia_label=competencia_label(competencia), unidades=unidades,
        unidade_sel=unidade_sel or sugerida, mapeado=bool(unidade_sel), anterior=anterior,
        sem_cadastro=sem_cadastro, divergencias=divergencias,
        mes_anterior_label=competencia_label(mes_ant), siglas=SIGLAS_JUSTIFICATIVA,
        totais_capa=TOTAIS_CAPA,
    )


@frequencia_bp.route('/frequencia/importar/<token>/confirmar', methods=['POST'])
@login_required
def confirmar(token):
    _exigir_importador()
    dados, caminho = _carregar_previa(token)
    if not dados:
        flash('A prévia expirou. Envie a planilha de novo.', 'warning')
        return redirect(url_for('frequencia.importar'))
    unidade_id = request.form.get('unidade_id', type=int)
    if not unidade_id or unidade_id not in {u.id for u in _unidades_escolha()}:
        flash('Escolha a unidade a que esta planilha pertence.', 'warning')
        return redirect(url_for('frequencia.previa', token=token))

    competencia = date.fromisoformat(dados['competencia'])
    agora = agora_local()

    mapa = RhLocal.query.filter_by(nome=dados['local']).first()
    if not mapa:
        db.session.add(RhLocal(nome=dados['local'], unidade_id=unidade_id))
    elif not mapa.unidade_id or _ve_tudo():
        mapa.unidade_id = unidade_id

    substituida = None
    for antiga in FreqImportacao.query.filter_by(
            competencia=competencia, local=dados['local'], status=FreqImportacao.STATUS_ATIVA).all():
        FreqLancamento.query.filter_by(importacao_id=antiga.id).delete(synchronize_session=False)
        FreqHoraExtra.query.filter_by(importacao_id=antiga.id).delete(synchronize_session=False)
        antiga.status = FreqImportacao.STATUS_SUBSTITUIDA
        antiga.substituida_em = agora
        substituida = antiga

    imp = FreqImportacao(
        competencia=competencia, local=dados['local'], unidade_id=unidade_id,
        arquivo=dados.get('arquivo'), status=FreqImportacao.STATUS_ATIVA,
        n_profissionais=len(dados['lancamentos']), n_horas_extras=len(dados['horas_extras']),
        n_servidores_base=len(dados['servidores']), importado_por=current_user.id, importado_em=agora,
    )
    db.session.add(imp)
    db.session.flush()

    db.session.bulk_insert_mappings(FreqLancamento, [
        dict(l, importacao_id=imp.id) for l in dados['lancamentos']])
    db.session.bulk_insert_mappings(FreqHoraExtra, [
        dict(h, importacao_id=imp.id) for h in dados['horas_extras']])

    novos_srv, atual_srv = _atualizar_base_servidores(dados['servidores'], competencia)
    n_avisados = _notificar_profissionais(dados, competencia, unidade_id)

    db.session.commit()
    try:
        os.remove(caminho)
    except OSError:
        pass

    msg = (f'Frequência de {competencia_label(competencia)} ({dados["local"]}) importada: '
           f'{imp.n_profissionais} profissionais e {imp.n_horas_extras} lançamentos de hora extra.')
    if substituida:
        msg += ' A importação anterior deste mês foi substituída.'
    if dados['servidores']:
        msg += f' Base do RH: {novos_srv} novos e {atual_srv} atualizados.'
    if n_avisados:
        msg += f' {n_avisados} profissionais foram avisados.'
    flash(msg, 'success')
    return redirect(url_for('frequencia.unidade', unidade_id=unidade_id,
                            competencia=competencia.strftime('%Y-%m')))


@frequencia_bp.route('/frequencia/importacoes/<int:imp_id>/excluir', methods=['POST'])
@login_required
def excluir_importacao(imp_id):
    _exigir_importador()
    imp = FreqImportacao.query.get_or_404(imp_id)
    ids = _gestao()
    if ids is not None and imp.unidade_id not in ids:
        abort(403)
    rotulo = f'{imp.competencia_label} ({imp.local})'
    db.session.delete(imp)
    db.session.commit()
    flash(f'Importação de {rotulo} excluída. Os apontamentos dela saíram da consulta.', 'success')
    return redirect(url_for('frequencia.importar'))


def _matriculas_no_sigus(mats):
    alvo = {normalizar_matricula(m) for m in mats}
    achadas = set()
    for (num,) in db.session.query(MatriculaProfissional.numero).filter(
            MatriculaProfissional.numero.isnot(None)).all():
        n = normalizar_matricula(num)
        if n in alvo:
            achadas.add(n)
    return achadas


def _mes_anterior(d):
    return date(d.year - 1, 12, 1) if d.month == 1 else date(d.year, d.month - 1, 1)


def _saldos_em(competencia, mats):
    if not mats:
        return {}
    rows = (db.session.query(FreqLancamento.matricula, FreqLancamento.banco_saldo_atual)
            .join(FreqImportacao)
            .filter(FreqImportacao.competencia == competencia,
                    FreqImportacao.status == FreqImportacao.STATUS_ATIVA,
                    FreqLancamento.matricula.in_(mats),
                    FreqLancamento.banco_saldo_atual.isnot(None))
            .all())
    return {m: s for m, s in rows}


def _atualizar_base_servidores(servidores, competencia):
    if not servidores:
        return 0, 0
    existentes = {s.matricula: s for s in RhServidor.query.all()}
    novos, atualizados = [], 0
    for s in servidores:
        atual = existentes.get(s['matricula'])
        if atual is None:
            novos.append(dict(s, competencia=competencia))
            existentes[s['matricula']] = True
        elif atual is not True and (atual.competencia is None or atual.competencia <= competencia):
            mudou = (atual.nome, atual.funcao, atual.local) != (s['nome'], s['funcao'], s['local'])
            atual.nome, atual.funcao, atual.local = s['nome'], s['funcao'], s['local']
            atual.competencia = competencia
            atualizados += 1 if mudou else 0
    if novos:
        db.session.bulk_insert_mappings(RhServidor, novos)
    return len(novos), atualizados


def _notificar_profissionais(dados, competencia, unidade_id):
    mats = {l['matricula'] for l in dados['lancamentos']} | {h['matricula'] for h in dados['horas_extras']}
    if not mats:
        return 0
    usuarios = set()
    for m in MatriculaProfissional.query.filter(
            MatriculaProfissional.numero.isnot(None), MatriculaProfissional.ativo.is_(True)).all():
        if normalizar_matricula(m.numero) in mats:
            usuarios.add(m.usuario_id)
    unidade = db.session.get(Unidade, unidade_id)
    titulo = f'Seus apontamentos de {competencia_label(competencia)} estão disponíveis'
    texto = f'{unidade.nome if unidade else dados["local"]} enviou a frequência do mês ao RH.'
    db.session.add_all([Notificacao(usuario_id=uid, tipo='apontamentos', titulo=titulo, texto=texto)
                        for uid in usuarios])
    return len(usuarios)


# ── Consulta ────────────────────────────────────────────────────────────────

def _parse_competencia(valor):
    try:
        a, m = (valor or '').split('-')
        return date(int(a), int(m), 1)
    except (ValueError, TypeError):
        return None


def _calendario(competencia, dias):
    """Semanas (domingo a sábado) do mês com a sigla de cada dia."""
    semanas = []
    for semana in calendar.Calendar(firstweekday=6).monthdayscalendar(competencia.year, competencia.month):
        semanas.append([(d, dias.get(str(d)) if d else None) for d in semana])
    return semanas


def _resumo_siglas(dias):
    cont = OrderedDict()
    for _, sig in sorted(((int(k), v) for k, v in (dias or {}).items())):
        cont[sig] = cont.get(sig, 0) + 1
    return [(sig, n, SIGLAS_JUSTIFICATIVA.get(sig, (sig, ''))[0], SIGLAS_JUSTIFICATIVA.get(sig, ('', ''))[1])
            for sig, n in cont.items()]


@frequencia_bp.route('/apontamentos')
@login_required
def apontamentos():
    mat_param = normalizar_matricula(request.args.get('matricula'))
    minhas = matriculas_do_usuario(current_user)
    if mat_param and mat_param not in minhas:
        if not _pode_ver_matricula(mat_param):
            abort(403)
        mats, de_outro = {mat_param}, True
    else:
        mats, de_outro = minhas, False

    lancs = []
    hes = []
    if mats:
        lancs = (FreqLancamento.query.join(FreqImportacao)
                 .filter(FreqLancamento.matricula.in_(mats),
                         FreqImportacao.status == FreqImportacao.STATUS_ATIVA)
                 .order_by(FreqImportacao.competencia.desc()).all())
        hes = (FreqHoraExtra.query.join(FreqImportacao)
               .filter(FreqHoraExtra.matricula.in_(mats),
                       FreqImportacao.status == FreqImportacao.STATUS_ATIVA)
               .order_by(FreqImportacao.competencia.desc()).all())

    competencias = sorted({l.importacao.competencia for l in lancs} | {h.importacao.competencia for h in hes},
                          reverse=True)
    comp = _parse_competencia(request.args.get('competencia'))
    if comp not in competencias:
        comp = competencias[0] if competencias else None

    nome = None
    if de_outro:
        nome = next((l.nome for l in lancs if l.nome), None) or next((h.nome for h in hes if h.nome), None)
        if not nome:
            srv = RhServidor.query.filter_by(matricula=mat_param).first()
            nome = srv.nome if srv else None

    # Uma aba por matrícula, com o que veio no mês escolhido.
    abas = []
    for m in sorted(mats):
        do_mes = [l for l in lancs if l.matricula == m and l.importacao.competencia == comp]
        he_mes = [h for h in hes if h.matricula == m and h.importacao.competencia == comp]
        historico_banco = sorted([l for l in lancs if l.matricula == m and l.tem_banco],
                                 key=lambda l: l.importacao.competencia)
        saldos = {l.importacao.competencia: l.banco_saldo_atual for l in historico_banco}
        banco_hist = []
        for l in historico_banco:
            prev = saldos.get(_mes_anterior(l.importacao.competencia))
            banco_hist.append({
                'l': l,
                'continuidade': prev is None or l.banco_saldo_anterior is None
                or abs(prev - l.banco_saldo_anterior) < 0.01,
            })
        banco_hist.reverse()
        ano_he = {k: 0.0 for k, _ in TIPOS_HORA_EXTRA}
        if comp:
            for h in hes:
                if h.matricula == m and h.importacao.competencia.year == comp.year:
                    for k, _ in TIPOS_HORA_EXTRA:
                        ano_he[k] += getattr(h, k) or 0
        if not (do_mes or he_mes or banco_hist):
            continue
        lanc_banco = next((b['l'] for b in banco_hist if b['l'].importacao.competencia <= comp), None) \
            if comp else None
        abas.append({
            'matricula': m,
            'lancamentos': [{
                'l': l,
                'calendario': _calendario(comp, l.dias or {}),
                'siglas': _resumo_siglas(l.dias),
            } for l in do_mes],
            'horas_extras': he_mes,
            'he_total_mes': sum(h.total for h in he_mes),
            'he_ano': ano_he,
            'he_ano_total': sum(ano_he.values()),
            'banco_atual': lanc_banco,
            'banco_hist': banco_hist,
            'funcao': next((l.funcao for l in do_mes if l.funcao), None)
            or next((h.funcao for h in he_mes if h.funcao), None),
        })

    return render_template(
        'rh/apontamentos.html', abas=abas, competencias=competencias, comp=comp,
        competencia_label=competencia_label, mats=mats, de_outro=de_outro, nome_outro=nome,
        matricula_outro=mat_param if de_outro else None, siglas=SIGLAS_JUSTIFICATIVA,
        grupos=GRUPOS_JUSTIFICATIVA, tipos_he=TIPOS_HORA_EXTRA, totais_capa=TOTAIS_CAPA,
        dias_semana=['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'],
    )


@frequencia_bp.route('/apontamentos/unidade')
@login_required
def unidade():
    _exigir_importador()
    ids = _gestao()
    q_imp = FreqImportacao.query.filter_by(status=FreqImportacao.STATUS_ATIVA)
    if ids is not None:
        q_imp = q_imp.filter(FreqImportacao.unidade_id.in_(ids or [0]))
    unidade_ids = sorted({i for (i,) in q_imp.with_entities(FreqImportacao.unidade_id).distinct() if i})
    unidades = Unidade.query.filter(Unidade.id.in_(unidade_ids or [0])).order_by(Unidade.nome).all()

    un_id = request.args.get('unidade_id', type=int)
    if un_id not in unidade_ids:
        logada = current_user.unidade_logada
        un_id = logada.id if logada and logada.id in unidade_ids else (unidades[0].id if unidades else None)

    imps = q_imp.filter(FreqImportacao.unidade_id == un_id).all() if un_id else []
    competencias = sorted({i.competencia for i in imps}, reverse=True)
    comp = _parse_competencia(request.args.get('competencia'))
    if comp not in competencias:
        comp = competencias[0] if competencias else None
    imps_mes = [i for i in imps if i.competencia == comp]

    linhas, hes = [], []
    for imp in imps_mes:
        for l in imp.lancamentos.order_by(FreqLancamento.nome, FreqLancamento.matricula).all():
            linhas.append({'l': l, 'imp': imp, 'siglas': _resumo_siglas(l.dias)})
        hes.extend(imp.horas_extras.order_by(FreqHoraExtra.nome).all())

    return render_template(
        'rh/apontamentos_unidade.html', unidades=unidades, un_id=un_id, competencias=competencias,
        comp=comp, competencia_label=competencia_label, imps_mes=imps_mes, linhas=linhas, hes=hes,
        tipos_he=TIPOS_HORA_EXTRA, totais_capa=TOTAIS_CAPA, siglas=SIGLAS_JUSTIFICATIVA,
        he_totais={k: sum(getattr(h, k) or 0 for h in hes) for k, _ in TIPOS_HORA_EXTRA},
        n_sem_banco_ok=sum(1 for x in linhas if not x['l'].banco_confere),
    )


# ── Base de servidores do RH ────────────────────────────────────────────────

def _pode_consultar_base():
    return (current_user.pode('cadastrar_usuario') or current_user.pode('gerenciar_usuarios')
            or current_user.pode_importar_frequencia)


@frequencia_bp.route('/servidores')
@login_required
def servidores():
    if not _pode_consultar_base():
        abort(403)
    q = (request.args.get('q') or '').strip()
    itens = servidores_json(buscar_servidores(q, limite=100)) if q else []
    total = RhServidor.query.count()
    ultima = db.session.query(db.func.max(RhServidor.competencia)).scalar()
    n_funcoes = db.session.query(db.func.count(db.distinct(RhServidor.funcao))).scalar() or 0
    n_funcoes_cbo = (db.session.query(db.func.count(db.distinct(RhServidor.funcao)))
                     .join(RhFuncaoCbo, RhFuncaoCbo.funcao == RhServidor.funcao)
                     .filter(RhFuncaoCbo.cbo.isnot(None)).scalar() or 0)
    return render_template('rh/servidores.html', q=q, itens=itens, total=total,
                           ultima=competencia_label(ultima) if ultima else None,
                           n_funcoes=n_funcoes, n_funcoes_cbo=n_funcoes_cbo,
                           pode_cbo=current_user.pode('ver_configuracoes'))


@frequencia_bp.route('/servidores/buscar')
@login_required
def buscar_servidores_json():
    if not _pode_consultar_base():
        abort(403)
    return jsonify(itens=servidores_json(
        buscar_servidores(request.args.get('q'), limite=min(request.args.get('limite', 10, type=int), 30)),
        usuario_atual_id=request.args.get('usuario_id', type=int)))


# ── De-para de locais ───────────────────────────────────────────────────────

@frequencia_bp.route('/frequencia/locais', methods=['GET', 'POST'])
@login_required
def locais():
    if not _ve_tudo():
        abort(403)
    if request.method == 'POST':
        n = 0
        for chave, valor in request.form.items():
            if not chave.startswith('local_'):
                continue
            nome = request.form.get('nome_' + chave[6:], '').strip()
            if not nome:
                continue
            uid = int(valor) if valor.isdigit() else None
            mapa = RhLocal.query.filter_by(nome=nome).first()
            if mapa is None:
                if uid:
                    db.session.add(RhLocal(nome=nome, unidade_id=uid))
                    n += 1
            elif mapa.unidade_id != uid:
                mapa.unidade_id = uid
                n += 1
        db.session.commit()
        flash(f'De-para de locais salvo ({n} alteração(ões)).', 'success')
        return redirect(url_for('frequencia.locais'))

    mapas = {m.nome: m for m in RhLocal.query.all()}
    contagem = dict(db.session.query(RhServidor.local, db.func.count(RhServidor.id))
                    .filter(RhServidor.local.isnot(None)).group_by(RhServidor.local).all())
    nomes = sorted(set(mapas) | set(contagem))
    unidades = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    linhas = []
    for i, nome in enumerate(nomes):
        m = mapas.get(nome)
        sug = None if (m and m.unidade_id) else _sugerir_unidade(nome, unidades)
        linhas.append({'i': i, 'nome': nome, 'mapa': m, 'servidores': contagem.get(nome, 0),
                       'sugerida': sug})
    return render_template('rh/frequencia_locais.html', linhas=linhas, unidades=unidades,
                           n_mapeados=sum(1 for m in mapas.values() if m.unidade_id))
