# -*- coding: utf-8 -*-
"""Agenda da unidade: eventos do SIGUS + prazos de planejamento + Google Agenda."""
from datetime import datetime, date, timedelta

from flask import (
    Blueprint, abort, flash, jsonify, redirect, render_template,
    request, url_for, Response,
)
from flask_login import current_user, login_required
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload, selectinload

from app import db
from app.models.agenda import (
    AgendaEvento, VISIBILIDADE_UNIDADE, VISIBILIDADE_PESSOAL,
    TIPO_EVENTO, TIPO_REUNIAO, google_calendar_url, montar_ics,
)
from app.models.planejamento import (
    Planejamento, AcaoPlanejamento, planejamento_unidades,
    planejamento_tipos_unidade, STATUS_ACAO_LABELS,
)
from app.models.unidade import Unidade, UsuarioUnidade
from app.models.usuario import Usuario
from app.models.feriado import Feriado, expediente_no_dia, feriados_no_periodo
from app.utils import agora_local, agora_brasilia

agenda_bp = Blueprint('agenda', __name__, url_prefix='/agenda')

COR_EVENTO = '#1A82B8'
COR_PESSOAL = '#19A88B'
COR_REUNIAO = '#0D3B5E'
COR_PRAZO = '#F5C500'
COR_PRAZO_VENCIDO = '#E63030'
COR_PRAZO_FEITO = '#718096'
COR_FERIADO = '#E63030'

EXPEDIENTE_INI = 8
EXPEDIENTE_FIM = 17
ALMOCO_INI = 12
ALMOCO_FIM = 13
DIAS_SEMANA_PT = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']


def _exige(*acoes):
    if not any(current_user.pode(a) for a in acoes):
        abort(403)


def _ids_unidades():
    ids = [u.id for u in current_user.unidades_ativas]
    if ids:
        return ids
    if current_user.perfil == 'administrador' or current_user.pode('ver_todas_unidades'):
        return [u.id for u in Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()]
    return []


def _unidades():
    ids = _ids_unidades()
    if not ids:
        return []
    return Unidade.query.filter(Unidade.id.in_(ids), Unidade.status == 'ativa').order_by(Unidade.nome).all()


def _unidade_padrao(unidades):
    uid = request.args.get('unidade_id', type=int) or request.form.get('unidade_id', type=int)
    ids = {u.id for u in unidades}
    if uid in ids:
        return uid
    padrao = getattr(current_user, 'unidade_padrao', None)
    if padrao and padrao.id in ids:
        return padrao.id
    return unidades[0].id if unidades else None


def _usuarios_agenda(ids_unidades):
    if not ids_unidades:
        lista = []
    else:
        lista = (
            Usuario.query
            .join(UsuarioUnidade, UsuarioUnidade.usuario_id == Usuario.id)
            .filter(
                UsuarioUnidade.unidade_id.in_(ids_unidades),
                UsuarioUnidade.ativo.is_(True),
                Usuario.ativo.is_(True),
            )
            .distinct()
            .order_by(Usuario.nome)
            .all()
        )
    ids_seen = {u.id for u in lista}
    if current_user.is_authenticated and current_user.id not in ids_seen:
        lista = [current_user] + lista
    return lista


def _ids_participantes_form(form, unidades):
    ids_ok = {u.id for u in _usuarios_agenda([x.id for x in unidades])}
    ids_ok.add(current_user.id)
    escolhidos = []
    for raw in form.getlist('participantes'):
        try:
            uid = int(raw)
        except (TypeError, ValueError):
            continue
        if uid in ids_ok and uid not in escolhidos:
            escolhidos.append(uid)
    if current_user.id not in escolhidos:
        escolhidos.append(current_user.id)
    return escolhidos


def _fim_evento(ev):
    if ev.dia_inteiro:
        ini = ev.inicio.date() if isinstance(ev.inicio, datetime) else ev.inicio
        fim_d = ev.fim.date() if ev.fim else ini
        if isinstance(fim_d, datetime):
            fim_d = fim_d.date()
        return datetime.combine(fim_d + timedelta(days=1), datetime.min.time())
    if ev.fim:
        return ev.fim
    return ev.inicio + timedelta(hours=1)


def _intervalos_pessoa(usuario_id, janela_ini, janela_fim, ignorar_id=None):
    q = AgendaEvento.query.filter(
        AgendaEvento.inicio < janela_fim,
        or_(
            AgendaEvento.criado_por == usuario_id,
            AgendaEvento.participantes.any(Usuario.id == usuario_id),
        ),
    )
    if ignorar_id:
        q = q.filter(AgendaEvento.id != ignorar_id)
    intervalos = []
    for ev in q.all():
        if ev.eh_pessoal and ev.criado_por != usuario_id:
            continue
        fim = _fim_evento(ev)
        if fim <= janela_ini or ev.inicio >= janela_fim:
            continue
        intervalos.append((ev.inicio, fim, ev.titulo or 'Compromisso'))
    return intervalos


def _livre_em(usuario_id, slot_ini, slot_fim, ignorar_id=None):
    for ini, fim, _titulo in _intervalos_pessoa(usuario_id, slot_ini, slot_fim, ignorar_id):
        if ini < slot_fim and fim > slot_ini:
            return False, _titulo
    return True, None


def _sugerir_horarios(usuario_ids, duracao_min=60, ignorar_id=None, quantidade=5):
    duracao = timedelta(minutes=max(30, min(240, int(duracao_min or 60))))
    agora = agora_brasilia().replace(second=0, microsecond=0)
    janela_fim = datetime.combine(agora.date() + timedelta(days=60), datetime.min.time())
    ocupado = {
        uid: _intervalos_pessoa(uid, agora, janela_fim, ignorar_id)
        for uid in usuario_ids
    }
    feriados = feriados_no_periodo(agora.date(), janela_fim.date())

    def _livre(uid, a, b):
        for ini, fim, _titulo in ocupado.get(uid, []):
            if ini < b and fim > a:
                return False
        return True

    sugestoes = []
    dia = agora.date()
    tentativas = 0
    while len(sugestoes) < quantidade and tentativas < 80:
        tentativas += 1
        janela = expediente_no_dia(dia, feriados)
        if not janela:
            dia += timedelta(days=1)
            continue
        exp_ini, exp_fim = janela
        exp_ini = max(EXPEDIENTE_INI, exp_ini)
        exp_fim = min(EXPEDIENTE_FIM, exp_fim)
        if exp_ini >= exp_fim:
            dia += timedelta(days=1)
            continue
        fim_expediente = datetime.combine(dia, datetime.min.time()).replace(hour=exp_fim)
        almoco = datetime.combine(dia, datetime.min.time()).replace(hour=ALMOCO_INI)
        almoco_fim = datetime.combine(dia, datetime.min.time()).replace(hour=ALMOCO_FIM)
        for hora in range(exp_ini, exp_fim):
            if ALMOCO_INI <= hora < ALMOCO_FIM:
                continue
            slot_ini = datetime.combine(dia, datetime.min.time()).replace(hour=hora)
            slot_fim = slot_ini + duracao
            if slot_ini < agora or slot_fim > fim_expediente:
                continue
            if slot_ini < almoco_fim and slot_fim > almoco:
                continue
            if all(_livre(uid, slot_ini, slot_fim) for uid in usuario_ids):
                sugestoes.append({
                    'inicio': slot_ini.strftime('%Y-%m-%dT%H:%M'),
                    'fim': slot_fim.strftime('%Y-%m-%dT%H:%M'),
                    'label': (
                        f'{DIAS_SEMANA_PT[slot_ini.weekday()]} {slot_ini.strftime("%d/%m")} · '
                        f'{slot_ini.strftime("%H:%M")}–{slot_fim.strftime("%H:%M")}'
                    ),
                })
                if len(sugestoes) >= quantidade:
                    break
        dia += timedelta(days=1)
    return sugestoes


def _ids_planejamentos(ids_unidades, unidade_id=None):
    if not ids_unidades:
        return set()
    alvo = [unidade_id] if unidade_id else list(ids_unidades)
    p_ids = set()
    for pid, in db.session.query(Planejamento.id).filter(Planejamento.unidade_id.in_(alvo)).all():
        p_ids.add(pid)
    for pid, in db.session.query(planejamento_unidades.c.planejamento_id).filter(
        planejamento_unidades.c.unidade_id.in_(alvo)
    ).all():
        p_ids.add(pid)
    tipos = [
        t[0] for t in db.session.query(Unidade.tipo_unidade_id).filter(
            Unidade.id.in_(alvo), Unidade.tipo_unidade_id.isnot(None)
        ).distinct().all() if t[0]
    ]
    if tipos:
        for pid, in db.session.query(planejamento_tipos_unidade.c.planejamento_id).filter(
            planejamento_tipos_unidade.c.tipo_unidade_id.in_(tipos)
        ).all():
            p_ids.add(pid)
    return p_ids


def _parse_iso(valor):
    if not valor:
        return None
    texto = valor.strip().replace('Z', '')
    if texto.endswith('+00:00'):
        texto = texto[:-6]
    try:
        if 'T' in texto:
            if len(texto) == 16:
                return datetime.strptime(texto, '%Y-%m-%dT%H:%M')
            return datetime.fromisoformat(texto[:19])
        return datetime.strptime(texto[:10], '%Y-%m-%d')
    except ValueError:
        return None


def _ics_response(conteudo, filename):
    return Response(
        conteudo,
        mimetype='text/calendar; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


def _evento_visivel(ev):
    if ev.criado_por == current_user.id:
        return True
    if any(p.id == current_user.id for p in (ev.participantes or [])):
        return True
    ids = set(_ids_unidades())
    if ev.unidade_id not in ids:
        return False
    if ev.eh_pessoal:
        return False
    return True


def _pode_editar_evento(ev):
    if not _evento_visivel(ev):
        return False
    if current_user.pode('editar_agenda'):
        return True
    return ev.criado_por == current_user.id


def _primeiro_nome(nome):
    return (nome or '').split()[0] if nome else ''


def _pessoa_json(usuario=None, empresa=None):
    if empresa:
        nome = empresa.nome_comum or empresa.razao_social or 'Empresa'
        return {
            'nome': nome,
            'primeiro': _primeiro_nome(nome),
            'foto_url': empresa.foto_url,
            'inicial': (nome[0] if nome else '?').upper(),
            'empresa': True,
        }
    nome = (usuario.nome if usuario else '') or ''
    return {
        'nome': nome,
        'primeiro': _primeiro_nome(nome),
        'foto_url': usuario.foto_url if usuario else None,
        'inicial': (nome[0] if nome else '?').upper(),
        'empresa': False,
    }


def _fc_evento(ev):
    inicio = ev.inicio
    fim = ev.fim
    if ev.dia_inteiro:
        start = inicio.date().isoformat() if isinstance(inicio, datetime) else inicio.isoformat()
        if fim:
            fim_d = fim.date() if isinstance(fim, datetime) else fim
            end = (fim_d + timedelta(days=1)).isoformat()
        else:
            end = None
    else:
        start = inicio.isoformat(timespec='seconds')
        end = fim.isoformat(timespec='seconds') if fim else None
    if ev.eh_reuniao:
        cor = COR_REUNIAO
        pessoas = [_pessoa_json(u) for u in (ev.participantes or [])]
        if ev.criador and ev.criador.id not in [p.id for p in (ev.participantes or [])]:
            pessoas = [_pessoa_json(ev.criador)] + pessoas
        pessoas_label = 'Participantes'
        tipo_ui = 'reuniao'
    else:
        cor = COR_PESSOAL if ev.eh_pessoal else COR_EVENTO
        pessoas = [_pessoa_json(ev.criador)] if ev.criador else []
        pessoas_label = 'Criado por'
        tipo_ui = 'evento'
    payload = {
        'id': f'evt-{ev.id}',
        'title': ev.titulo,
        'start': start,
        'allDay': ev.dia_inteiro,
        'backgroundColor': cor,
        'borderColor': cor,
        'extendedProps': {
            'tipo': tipo_ui,
            'evento_id': ev.id,
            'descricao': ev.descricao or '',
            'local': ev.local or '',
            'unidade': ev.unidade.nome if ev.unidade else '',
            'unidade_id': ev.unidade_id,
            'criador': ev.criador.nome if ev.criador else '',
            'pessoas_label': pessoas_label,
            'pessoas': pessoas,
            'participante_ids': [u.id for u in (ev.participantes or [])],
            'visibilidade': ev.visibilidade,
            'pode_editar': _pode_editar_evento(ev),
            'google_url': google_calendar_url(
                ev.titulo, ev.inicio, ev.fim, ev.descricao or '', ev.local or '', ev.dia_inteiro,
            ),
            'ics_url': url_for('agenda.evento_ics', id=ev.id),
        },
    }
    if end:
        payload['end'] = end
    return payload


def _fc_prazo(acao, hoje):
    prazo = acao.prazo
    if acao.status == 'concluido':
        cor = COR_PRAZO_FEITO
    elif prazo < hoje:
        cor = COR_PRAZO_VENCIDO
    else:
        cor = COR_PRAZO
    titulo = acao.titulo
    plano = acao.planejamento.titulo if acao.planejamento else ''
    if plano:
        titulo = f'{acao.titulo} · {plano}'
    descricao = (
        f'Prazo da ação "{acao.titulo}" no planejamento "{plano}". '
        f'Status: {STATUS_ACAO_LABELS.get(acao.status, acao.status)}.'
    )
    pessoas = [_pessoa_json(u) for u in (acao.responsaveis or [])]
    if not pessoas:
        pessoas = [_pessoa_json(empresa=e) for e in (acao.empresas or [])]
    return {
        'id': f'prazo-{acao.id}',
        'title': titulo,
        'start': prazo.isoformat(),
        'allDay': True,
        'backgroundColor': cor,
        'borderColor': cor,
        'extendedProps': {
            'tipo': 'prazo',
            'acao_id': acao.id,
            'descricao': descricao,
            'local': '',
            'unidade': acao.planejamento.unidade.nome if acao.planejamento and acao.planejamento.unidade else '',
            'status': STATUS_ACAO_LABELS.get(acao.status, acao.status),
            'pessoas_label': 'Quem resolve',
            'pessoas': pessoas,
            'pode_editar': False,
            'plano_url': url_for('planejamentos.listar', expand=acao.planejamento_id),
            'google_url': google_calendar_url(
                f'Prazo: {acao.titulo}', prazo, None, descricao, '', True,
            ),
            'ics_url': url_for('agenda.prazo_ics', id=acao.id),
        },
    }


def _fc_feriado(f):
    start = f.data.isoformat()
    partes = [f.tipo_label]
    if f.natureza_label:
        partes.append(f.natureza_label)
    if not f.dia_inteiro:
        ini = f.expediente_inicio.strftime('%H:%M') if f.expediente_inicio else '08:00'
        fimh = f.expediente_fim.strftime('%H:%M') if f.expediente_fim else '17:00'
        partes.append(f'Expediente {ini}–{fimh}')
    if f.observacao:
        partes.append(f.observacao)
    if f.numero_decreto:
        partes.append(f.numero_decreto)
    chip = {
        'id': f'feriado-{f.id}',
        'title': f.nome,
        'start': start,
        'allDay': True,
        'backgroundColor': COR_FERIADO,
        'borderColor': COR_FERIADO,
        'classNames': ['agenda-ev-feriado'],
        'extendedProps': {
            'tipo': 'feriado',
            'descricao': ' · '.join(partes),
            'local': '',
            'pessoas': [],
            'pessoas_label': '',
            'pode_editar': False,
            'decreto_url': f.link_decreto or '',
            'decreto': f.numero_decreto or '',
        },
    }
    fundo = {
        'id': f'feriado-bg-{f.id}',
        'start': start,
        'allDay': True,
        'display': 'background',
        'backgroundColor': 'rgba(230, 48, 48, 0.18)',
        'classNames': ['agenda-feriado-bg'],
        'extendedProps': {'tipo': 'feriado-bg'},
    }
    return fundo, chip


def _dados_formulario(form, unidades):
    titulo = (form.get('titulo') or '').strip()
    unidade_id = form.get('unidade_id', type=int)
    ids = {u.id for u in unidades}
    if unidade_id not in ids:
        unidade_id = _unidade_padrao(unidades)
    dia_inteiro = form.get('dia_inteiro') in ('1', 'true', 'on', True)
    visibilidade = form.get('visibilidade') or VISIBILIDADE_UNIDADE
    if visibilidade not in (VISIBILIDADE_UNIDADE, VISIBILIDADE_PESSOAL):
        visibilidade = VISIBILIDADE_UNIDADE
    descricao = (form.get('descricao') or '').strip() or None
    local = (form.get('local') or '').strip() or None
    tipo = form.get('tipo') or TIPO_EVENTO
    if tipo not in (TIPO_EVENTO, TIPO_REUNIAO):
        tipo = TIPO_EVENTO
    if tipo == TIPO_REUNIAO:
        dia_inteiro = False
        visibilidade = VISIBILIDADE_UNIDADE
    duracao = form.get('duracao', type=int) or 60
    if duracao not in (30, 60, 90, 120):
        duracao = 60
    if dia_inteiro:
        inicio = _parse_iso(form.get('inicio_data') or form.get('inicio'))
        fim = _parse_iso(form.get('fim_data') or form.get('fim'))
        if inicio:
            inicio = datetime.combine(inicio.date() if isinstance(inicio, datetime) else inicio, datetime.min.time())
        if fim:
            fim = datetime.combine(fim.date() if isinstance(fim, datetime) else fim, datetime.min.time())
            if inicio and fim.date() == inicio.date():
                fim = None
    else:
        inicio = _parse_iso(form.get('inicio'))
        fim = _parse_iso(form.get('fim'))
        if tipo == TIPO_REUNIAO and inicio:
            fim = inicio + timedelta(minutes=duracao)
        elif inicio and not fim:
            fim = inicio + timedelta(minutes=duracao)
    return {
        'titulo': titulo,
        'unidade_id': unidade_id,
        'dia_inteiro': dia_inteiro,
        'visibilidade': visibilidade,
        'descricao': descricao,
        'local': local,
        'inicio': inicio,
        'fim': fim,
        'tipo': tipo,
    }


@agenda_bp.route('/')
@login_required
def index():
    _exige('ver_agenda', 'adicionar_agenda', 'editar_agenda')
    unidades = _unidades()
    if not unidades:
        flash('Você precisa estar vinculado a pelo menos uma unidade para acessar a agenda.', 'warning')
        return redirect(url_for('dashboard.index'))
    unidade_id = _unidade_padrao(unidades)
    usuarios = _usuarios_agenda([u.id for u in unidades])
    return render_template(
        'agenda/calendario.html',
        unidades=unidades,
        unidade_id=unidade_id,
        usuarios=usuarios,
        pode_adicionar=current_user.pode('adicionar_agenda'),
    )


@agenda_bp.route('/eventos.json')
@login_required
def eventos_json():
    _exige('ver_agenda', 'adicionar_agenda', 'editar_agenda')
    unidades = _unidades()
    ids = [u.id for u in unidades]
    if not ids:
        return jsonify([])
    unidade_id = request.args.get('unidade_id', type=int)
    if unidade_id and unidade_id in ids:
        ids_filtro = [unidade_id]
    else:
        ids_filtro = ids
    start = _parse_iso(request.args.get('start')) or datetime.now().replace(day=1)
    end = _parse_iso(request.args.get('end')) or (start + timedelta(days=40))
    mostrar_eventos = request.args.get('eventos', '1') != '0'
    mostrar_prazos = request.args.get('prazos', '1') != '0'
    mostrar_feriados = request.args.get('feriados', '1') != '0'

    itens = []
    if mostrar_eventos:
        q = AgendaEvento.query.options(
            joinedload(AgendaEvento.unidade),
            joinedload(AgendaEvento.criador),
            selectinload(AgendaEvento.participantes),
        ).filter(
            AgendaEvento.inicio < end,
            or_(AgendaEvento.fim >= start, and_(AgendaEvento.fim.is_(None), AgendaEvento.inicio >= start)),
        )
        q = q.filter(or_(
            and_(
                AgendaEvento.visibilidade == VISIBILIDADE_UNIDADE,
                AgendaEvento.unidade_id.in_(ids_filtro),
            ),
            AgendaEvento.criado_por == current_user.id,
            AgendaEvento.participantes.any(Usuario.id == current_user.id),
        ))
        for ev in q.all():
            itens.append(_fc_evento(ev))

    if mostrar_prazos:
        p_ids = _ids_planejamentos(ids, unidade_id if unidade_id in ids else None)
        if p_ids:
            hoje = date.today()
            acoes = (
                AcaoPlanejamento.query
                .options(
                    joinedload(AcaoPlanejamento.planejamento).joinedload(Planejamento.unidade),
                    joinedload(AcaoPlanejamento.responsaveis),
                    joinedload(AcaoPlanejamento.empresas),
                )
                .filter(
                    AcaoPlanejamento.planejamento_id.in_(p_ids),
                    AcaoPlanejamento.prazo.isnot(None),
                    AcaoPlanejamento.prazo >= start.date(),
                    AcaoPlanejamento.prazo < end.date(),
                    AcaoPlanejamento.status != 'cancelado',
                )
                .all()
            )
            for acao in acoes:
                itens.append(_fc_prazo(acao, hoje))

    if mostrar_feriados:
        ini_d = start.date() if isinstance(start, datetime) else start
        fim_d = end.date() if isinstance(end, datetime) else end
        for feriado in Feriado.query.filter(
            Feriado.ativo.is_(True),
            Feriado.data >= ini_d,
            Feriado.data < fim_d,
        ).order_by(Feriado.data).all():
            fundo, chip = _fc_feriado(feriado)
            itens.append(fundo)
            itens.append(chip)
    return jsonify(itens)


@agenda_bp.route('/eventos', methods=['POST'])
@login_required
def criar():
    _exige('adicionar_agenda')
    unidades = _unidades()
    dados = _dados_formulario(request.form, unidades)
    if not dados['titulo'] or not dados['inicio']:
        return jsonify({'ok': False, 'erro': 'Informe o título e a data.'}), 400
    ev = AgendaEvento(
        unidade_id=dados['unidade_id'],
        titulo=dados['titulo'],
        descricao=dados['descricao'],
        local=dados['local'],
        inicio=dados['inicio'],
        fim=dados['fim'],
        dia_inteiro=dados['dia_inteiro'],
        visibilidade=dados['visibilidade'],
        tipo=dados['tipo'],
        criado_por=current_user.id,
        criado_em=agora_local(),
    )
    if dados['tipo'] == TIPO_REUNIAO:
        ids_p = _ids_participantes_form(request.form, unidades)
        ev.participantes = Usuario.query.filter(Usuario.id.in_(ids_p)).all()
    db.session.add(ev)
    db.session.commit()
    return jsonify({
        'ok': True,
        'evento': _fc_evento(ev),
        'google_url': google_calendar_url(
            ev.titulo, ev.inicio, ev.fim, ev.descricao or '', ev.local or '', ev.dia_inteiro,
        ),
    })


@agenda_bp.route('/eventos/<int:id>', methods=['POST'])
@login_required
def editar(id):
    ev = AgendaEvento.query.get_or_404(id)
    if not _pode_editar_evento(ev):
        abort(403)
    unidades = _unidades()
    dados = _dados_formulario(request.form, unidades)
    if not dados['titulo'] or not dados['inicio']:
        return jsonify({'ok': False, 'erro': 'Informe o título e a data.'}), 400
    ev.unidade_id = dados['unidade_id']
    ev.titulo = dados['titulo']
    ev.descricao = dados['descricao']
    ev.local = dados['local']
    ev.inicio = dados['inicio']
    ev.fim = dados['fim']
    ev.dia_inteiro = dados['dia_inteiro']
    ev.visibilidade = dados['visibilidade']
    ev.tipo = dados['tipo']
    ev.atualizado_em = agora_local()
    if dados['tipo'] == TIPO_REUNIAO:
        ids_p = _ids_participantes_form(request.form, unidades)
        ev.participantes = Usuario.query.filter(Usuario.id.in_(ids_p)).all()
    else:
        ev.participantes = []
    db.session.commit()
    return jsonify({
        'ok': True,
        'evento': _fc_evento(ev),
        'google_url': google_calendar_url(
            ev.titulo, ev.inicio, ev.fim, ev.descricao or '', ev.local or '', ev.dia_inteiro,
        ),
    })


@agenda_bp.route('/eventos/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    ev = AgendaEvento.query.get_or_404(id)
    if not _pode_editar_evento(ev):
        abort(403)
    db.session.delete(ev)
    db.session.commit()
    return jsonify({'ok': True})


@agenda_bp.route('/sugerir', methods=['POST'])
@login_required
def sugerir():
    _exige('ver_agenda', 'adicionar_agenda', 'editar_agenda')
    unidades = _unidades()
    ids = _ids_participantes_form(request.form, unidades)
    duracao = request.form.get('duracao', type=int) or 60
    ignorar = request.form.get('evento_id', type=int)
    return jsonify({
        'ok': True,
        'sugestoes': _sugerir_horarios(ids, duracao, ignorar, 5),
    })


@agenda_bp.route('/disponibilidade', methods=['POST'])
@login_required
def disponibilidade():
    _exige('ver_agenda', 'adicionar_agenda', 'editar_agenda')
    unidades = _unidades()
    ids = _ids_participantes_form(request.form, unidades)
    inicio = _parse_iso(request.form.get('inicio'))
    duracao = request.form.get('duracao', type=int) or 60
    if duracao not in (30, 60, 90, 120):
        duracao = 60
    fim = _parse_iso(request.form.get('fim'))
    if inicio and not fim:
        fim = inicio + timedelta(minutes=duracao)
    if not inicio or not fim:
        return jsonify({'ok': True, 'todos_livres': True, 'pessoas': []})
    ignorar = request.form.get('evento_id', type=int)
    usuarios = {u.id: u for u in Usuario.query.filter(Usuario.id.in_(ids)).all()}
    pessoas = []
    for uid in ids:
        livre, titulo = _livre_em(uid, inicio, fim, ignorar)
        u = usuarios.get(uid)
        pessoas.append({
            'id': uid,
            'nome': u.nome if u else '',
            'primeiro': _primeiro_nome(u.nome if u else ''),
            'livre': livre,
            'conflito': None if livre else titulo,
        })
    return jsonify({
        'ok': True,
        'todos_livres': all(p['livre'] for p in pessoas),
        'pessoas': pessoas,
    })


@agenda_bp.route('/eventos/<int:id>.ics')
@login_required
def evento_ics(id):
    _exige('ver_agenda', 'adicionar_agenda', 'editar_agenda')
    ev = AgendaEvento.query.get_or_404(id)
    if not _evento_visivel(ev):
        abort(403)
    ics = montar_ics(
        f'sigus-evento-{ev.id}@sorocaba.sp.gov.br',
        ev.titulo, ev.inicio, ev.fim, ev.descricao or '', ev.local or '', ev.dia_inteiro,
    )
    return _ics_response(ics, f'sigus-evento-{ev.id}.ics')


@agenda_bp.route('/prazos/<int:id>.ics')
@login_required
def prazo_ics(id):
    _exige('ver_agenda', 'adicionar_agenda', 'editar_agenda')
    acao = AcaoPlanejamento.query.get_or_404(id)
    if not acao.prazo:
        abort(404)
    p_ids = _ids_planejamentos(_ids_unidades())
    if acao.planejamento_id not in p_ids:
        abort(403)
    plano = acao.planejamento.titulo if acao.planejamento else ''
    descricao = f'Prazo da ação no planejamento {plano}.'
    ics = montar_ics(
        f'sigus-prazo-{acao.id}@sorocaba.sp.gov.br',
        f'Prazo: {acao.titulo}', acao.prazo, None, descricao, '', True,
    )
    return _ics_response(ics, f'sigus-prazo-{acao.id}.ics')
