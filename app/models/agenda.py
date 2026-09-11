# -*- coding: utf-8 -*-
"""Agenda da unidade — eventos compartilhados no SIGUS."""
from datetime import datetime, date, timedelta
from urllib.parse import urlencode

from app import db
from app.utils import agora_local_callable


VISIBILIDADE_UNIDADE = 'unidade'
VISIBILIDADE_PESSOAL = 'pessoal'
TIPO_EVENTO = 'evento'
TIPO_REUNIAO = 'reuniao'

agenda_evento_participantes = db.Table(
    'agenda_evento_participantes',
    db.Column('evento_id', db.Integer, db.ForeignKey('agenda_eventos.id', ondelete='CASCADE'), primary_key=True),
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), primary_key=True),
)


class AgendaEvento(db.Model):
    __tablename__ = 'agenda_eventos'

    id = db.Column(db.Integer, primary_key=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='CASCADE'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    local = db.Column(db.String(300))
    inicio = db.Column(db.DateTime, nullable=False)
    fim = db.Column(db.DateTime)
    dia_inteiro = db.Column(db.Boolean, nullable=False, default=False)
    visibilidade = db.Column(db.String(20), nullable=False, default=VISIBILIDADE_UNIDADE)
    tipo = db.Column(db.String(20), nullable=False, default=TIPO_EVENTO)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable)
    atualizado_em = db.Column(db.DateTime)

    unidade = db.relationship('Unidade', foreign_keys=[unidade_id])
    criador = db.relationship('Usuario', foreign_keys=[criado_por])
    participantes = db.relationship(
        'Usuario',
        secondary=agenda_evento_participantes,
        lazy='joined',
    )

    @property
    def eh_pessoal(self):
        return self.visibilidade == VISIBILIDADE_PESSOAL

    @property
    def eh_reuniao(self):
        return self.tipo == TIPO_REUNIAO

    @property
    def inicio_date(self):
        return self.inicio.date() if isinstance(self.inicio, datetime) else self.inicio

    @property
    def fim_efetivo(self):
        if self.fim:
            return self.fim
        if self.dia_inteiro:
            return self.inicio
        return self.inicio + timedelta(hours=1)


def google_calendar_url(titulo, inicio, fim=None, descricao='', local='', dia_inteiro=False):
    """Monta o link 'Adicionar ao Google Agenda' (sem OAuth)."""
    def _date(v):
        if isinstance(v, datetime):
            return v.date()
        return v

    def _fmt_day(v):
        return _date(v).strftime('%Y%m%d')

    def _fmt_dt(v):
        if isinstance(v, date) and not isinstance(v, datetime):
            v = datetime.combine(v, datetime.min.time())
        return v.strftime('%Y%m%dT%H%M%S')

    if dia_inteiro:
        start = _date(inicio)
        end = _date(fim or inicio) + timedelta(days=1)
        dates = f'{_fmt_day(start)}/{_fmt_day(end)}'
    else:
        end = fim or (
            inicio + timedelta(hours=1) if isinstance(inicio, datetime)
            else datetime.combine(inicio, datetime.min.time()) + timedelta(hours=1)
        )
        dates = f'{_fmt_dt(inicio)}/{_fmt_dt(end)}'

    params = {
        'action': 'TEMPLATE',
        'text': titulo or 'Evento SIGUS',
        'dates': dates,
        'details': descricao or '',
        'location': local or '',
        'ctz': 'America/Sao_Paulo',
    }
    return 'https://calendar.google.com/calendar/render?' + urlencode(params)


def _ics_escape(texto):
    return (texto or '').replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')


def montar_ics(uid, titulo, inicio, fim=None, descricao='', local='', dia_inteiro=False):
    """Gera um .ics simples (Google, Outlook, Apple)."""
    agora = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

    def _date(v):
        if isinstance(v, datetime):
            return v.date()
        return v

    if dia_inteiro:
        start = _date(inicio)
        end = _date(fim or inicio) + timedelta(days=1)
        dtstart = f'DTSTART;VALUE=DATE:{start.strftime("%Y%m%d")}'
        dtend = f'DTEND;VALUE=DATE:{end.strftime("%Y%m%d")}'
    else:
        def _fmt(v):
            if isinstance(v, date) and not isinstance(v, datetime):
                v = datetime.combine(v, datetime.min.time())
            return v.strftime('%Y%m%dT%H%M%S')
        end = fim or (
            inicio + timedelta(hours=1) if isinstance(inicio, datetime)
            else datetime.combine(inicio, datetime.min.time()) + timedelta(hours=1)
        )
        dtstart = f'DTSTART;TZID=America/Sao_Paulo:{_fmt(inicio)}'
        dtend = f'DTEND;TZID=America/Sao_Paulo:{_fmt(end)}'

    linhas = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//SIGUS//Agenda//PT',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'BEGIN:VEVENT',
        f'UID:{uid}',
        f'DTSTAMP:{agora}',
        dtstart,
        dtend,
        f'SUMMARY:{_ics_escape(titulo)}',
    ]
    if descricao:
        linhas.append(f'DESCRIPTION:{_ics_escape(descricao)}')
    if local:
        linhas.append(f'LOCATION:{_ics_escape(local)}')
    linhas += [
        'END:VEVENT',
        'END:VCALENDAR',
        '',
    ]
    return '\r\n'.join(linhas)
