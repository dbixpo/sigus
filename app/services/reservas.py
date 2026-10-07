# -*- coding: utf-8 -*-
"""Reserva de salas e veículos na agenda: conflitos, salas livres e situação da frota."""
import re
import unicodedata
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app import db
from app.models.agenda import AgendaEvento
from app.models.sala import Sala
from app.models.tipo_sala import TipoSala
from app.models.unidade import Unidade
from app.models.veiculo import Veiculo


# ── Intervalos e conflitos ─────────────────────────────────────────────

def intervalo(inicio, fim, dia_inteiro):
    """Intervalo real ocupado [ini, fim). Dia inteiro vai até a meia-noite do último dia."""
    if dia_inteiro:
        ini_d = inicio.date() if isinstance(inicio, datetime) else inicio
        fim_d = fim.date() if isinstance(fim, datetime) else (fim or ini_d)
        return (datetime.combine(ini_d, datetime.min.time()),
                datetime.combine(max(fim_d, ini_d) + timedelta(days=1), datetime.min.time()))
    return inicio, fim or inicio + timedelta(hours=1)


def intervalo_evento(ev):
    return intervalo(ev.inicio, ev.fim, ev.dia_inteiro)


def _reservas(coluna, ids, ini, fim, ignorar_id=None):
    if not ids:
        return []
    q = AgendaEvento.query.options(
        joinedload(AgendaEvento.unidade), joinedload(AgendaEvento.criador), joinedload(AgendaEvento.condutor),
    ).filter(coluna.in_(list(ids)), AgendaEvento.inicio < fim,
             AgendaEvento.inicio >= ini - timedelta(days=62))
    if ignorar_id:
        q = q.filter(AgendaEvento.id != ignorar_id)
    return [ev for ev in q.order_by(AgendaEvento.inicio).all() if intervalo_evento(ev)[1] > ini]


def conflitos(ini, fim, sala_id=None, veiculo_id=None, ignorar_id=None):
    if sala_id:
        return _reservas(AgendaEvento.sala_id, [sala_id], ini, fim, ignorar_id)
    if veiculo_id:
        return _reservas(AgendaEvento.veiculo_id, [veiculo_id], ini, fim, ignorar_id)
    return []


def _hora(dt):
    return dt.strftime('%H:%M')


def texto_periodo(ev):
    ini, fim = intervalo_evento(ev)
    if ev.dia_inteiro:
        ultimo = fim - timedelta(days=1)
        if ultimo.date() == ini.date():
            return f'o dia todo em {ini.strftime("%d/%m")}'
        return f'de {ini.strftime("%d/%m")} a {ultimo.strftime("%d/%m")}'
    if ini.date() == fim.date():
        return f'das {_hora(ini)} às {_hora(fim)} de {ini.strftime("%d/%m")}'
    return f'de {ini.strftime("%d/%m %H:%M")} a {fim.strftime("%d/%m %H:%M")}'


def texto_ocupacao(ev, mostrar_titulo=True):
    quem = ev.criador.nome if ev.criador else 'alguém'
    unidade = f' ({ev.unidade.nome})' if ev.unidade else ''
    texto = f'Reservado {texto_periodo(ev)} por {quem}{unidade}'
    if mostrar_titulo and ev.titulo and not ev.eh_pessoal:
        texto += f': {ev.titulo}'
    return texto


# ── Salas reserváveis ──────────────────────────────────────────────────

def _normalizar(texto):
    texto = unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode().lower()
    texto = re.sub(r'\b(rua|r|avenida|av|praca|pca|alameda|al|rodovia|rod|travessa|tv|estrada|est)\b\.?', ' ', texto)
    return ' '.join(re.findall(r'[a-z0-9]+', texto))


def chave_endereco(unidade):
    """Unidades no mesmo prédio (ou, sem prédio, no mesmo endereço + número) dividem as salas com facilidade."""
    if unidade is None:
        return None
    if unidade.predio_id:
        return ('predio', unidade.predio_id)
    rua = _normalizar(unidade.endereco)
    if not rua:
        return None
    numero = ''.join(re.findall(r'\d+', unidade.numero or '')) or _normalizar(unidade.numero)
    return ('endereco', f'{rua}|{numero}')


def rotulo_endereco(unidade):
    if unidade is None:
        return ''
    if unidade.predio:
        return unidade.predio.nome
    partes = [unidade.endereco or '']
    if unidade.numero:
        partes.append(unidade.numero)
    return ', '.join(p for p in partes if p)


def salas_reservaveis(ids_proprias):
    """Salas que o usuário pode reservar: as reserváveis das unidades dele e as compartilhadas da rede."""
    filtro = Sala.uso_compartilhado.is_(True)
    if ids_proprias:
        filtro = or_(filtro, Sala.unidade_id.in_(list(ids_proprias)))
    return (Sala.query
            .join(TipoSala, TipoSala.id == Sala.tipo_sala_id)
            .join(Unidade, Unidade.id == Sala.unidade_id)
            .options(joinedload(Sala.unidade).joinedload(Unidade.predio), joinedload(Sala.tipo_sala))
            .filter(Sala.ativo.is_(True), TipoSala.reservavel.is_(True), Unidade.status == 'ativa', filtro)
            .all())


def pode_reservar_sala(sala, ids_proprias):
    return bool(sala and sala.reservavel and (sala.uso_compartilhado or sala.unidade_id in set(ids_proprias or [])))


def salas_livres(unidade_base, ini, fim, ids_proprias, ignorar_id=None, ids_visiveis=None):
    """Três grupos: unidade do evento, mesmo prédio/endereço e o resto da rede. Livres primeiro."""
    salas = salas_reservaveis(ids_proprias)
    ocupacao = {}
    for ev in _reservas(AgendaEvento.sala_id, [s.id for s in salas], ini, fim, ignorar_id):
        ocupacao.setdefault(ev.sala_id, []).append(ev)
    chave_base = chave_endereco(unidade_base)
    ids_visiveis = set(ids_visiveis or [])
    grupos = {'unidade': [], 'predio': [], 'rede': []}
    for s in salas:
        evs = ocupacao.get(s.id, [])
        item = {
            'id': s.id,
            'nome': s.nome,
            'tipo': s.tipo_sala.nome if s.tipo_sala else '',
            'icone': s.tipo_sala.icone if s.tipo_sala else 'fas fa-door-open',
            'unidade': s.unidade.nome,
            'unidade_id': s.unidade_id,
            'endereco': rotulo_endereco(s.unidade),
            'capacidade': s.capacidade_maxima or 0,
            'compartilhada': bool(s.uso_compartilhado),
            'livre': not evs,
            'ocupacao': [texto_ocupacao(ev, ev.unidade_id in ids_visiveis) for ev in evs],
        }
        if unidade_base and s.unidade_id == unidade_base.id:
            grupos['unidade'].append(item)
        elif chave_base and chave_endereco(s.unidade) == chave_base:
            grupos['predio'].append(item)
        else:
            grupos['rede'].append(item)
    for lista in grupos.values():
        lista.sort(key=lambda i: (not i['livre'], i['unidade'].lower(), i['nome'].lower()))
    return {
        'grupos': grupos,
        'predio': rotulo_endereco(unidade_base) if chave_base else '',
    }


# ── Veículos ───────────────────────────────────────────────────────────

def query_veiculos(ids_unidades):
    if not ids_unidades:
        return Veiculo.query.filter(db.false())
    return (Veiculo.query
            .options(joinedload(Veiculo.unidade))
            .filter(Veiculo.ativo.is_(True), Veiculo.unidade_id.in_(list(ids_unidades))))


def km_atual(veiculo):
    """Último km de chegada registrado; sem nenhum, o km informado no cadastro."""
    ultimo = (db.session.query(AgendaEvento.km_chegada)
              .filter(AgendaEvento.veiculo_id == veiculo.id, AgendaEvento.km_chegada.isnot(None))
              .order_by(AgendaEvento.inicio.desc()).first())
    return ultimo[0] if ultimo else veiculo.km_cadastro


def situacao_veiculos(veiculos, agora):
    """{veiculo_id: {'em_uso': ev|None, 'proxima': ev|None, 'pendentes': n}}"""
    ids = [v.id for v in veiculos]
    situacao = {vid: {'em_uso': None, 'proxima': None, 'pendentes': 0} for vid in ids}
    if not ids:
        return situacao
    for ev in _reservas(AgendaEvento.veiculo_id, ids, agora, agora + timedelta(days=60)):
        ini, fim = intervalo_evento(ev)
        s = situacao[ev.veiculo_id]
        if ini <= agora < fim and s['em_uso'] is None:
            s['em_uso'] = ev
        elif ini > agora and s['proxima'] is None:
            s['proxima'] = ev
    for vid, n in (db.session.query(AgendaEvento.veiculo_id, db.func.count(AgendaEvento.id))
                   .filter(AgendaEvento.veiculo_id.in_(ids), AgendaEvento.inicio < agora,
                           AgendaEvento.km_chegada.is_(None))
                   .group_by(AgendaEvento.veiculo_id).all()):
        situacao[vid]['pendentes'] = n
    return situacao
