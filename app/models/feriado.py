# -*- coding: utf-8 -*-
"""Feriados e pontos facultativos da Prefeitura (expediente da agenda)."""
from datetime import date, time, datetime

from app import db


TIPO_FERIADO = 'feriado'
TIPO_PONTO_FACULTATIVO = 'ponto_facultativo'
TIPOS_FOLGA = {
    TIPO_FERIADO: 'Feriado',
    TIPO_PONTO_FACULTATIVO: 'Ponto facultativo',
}

NATUREZA_NACIONAL = 'nacional'
NATUREZA_ESTADUAL = 'estadual'
NATUREZA_MUNICIPAL = 'municipal'
NATUREZAS = {
    NATUREZA_NACIONAL: 'Nacional',
    NATUREZA_ESTADUAL: 'Estadual',
    NATUREZA_MUNICIPAL: 'Municipal',
}

DIAS_SEMANA = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']

EXPEDIENTE_INI = 8
EXPEDIENTE_FIM = 17


class Feriado(db.Model):
    __tablename__ = 'feriados'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, unique=True)
    nome = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(30), nullable=False, default=TIPO_FERIADO)
    natureza = db.Column(db.String(20), nullable=False, default=NATUREZA_NACIONAL)
    numero_decreto = db.Column(db.String(120))
    link_decreto = db.Column(db.String(500))
    dia_inteiro = db.Column(db.Boolean, nullable=False, default=True)
    expediente_inicio = db.Column(db.Time)
    expediente_fim = db.Column(db.Time)
    observacao = db.Column(db.String(400))
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    @property
    def tipo_label(self):
        return TIPOS_FOLGA.get(self.tipo, self.tipo)

    @property
    def natureza_label(self):
        return NATUREZAS.get(self.natureza, self.natureza)

    @property
    def dia_semana(self):
        if not self.data:
            return ''
        return DIAS_SEMANA[self.data.weekday()]

    @property
    def data_fmt(self):
        return self.data.strftime('%d/%m/%Y') if self.data else ''

    def janela_expediente(self):
        """(hora_ini, hora_fim) ou None se não houver expediente no dia."""
        if not self.ativo:
            return (EXPEDIENTE_INI, EXPEDIENTE_FIM)
        if self.dia_inteiro:
            return None
        ini = self.expediente_inicio.hour if self.expediente_inicio else EXPEDIENTE_INI
        fim = self.expediente_fim.hour if self.expediente_fim else EXPEDIENTE_FIM
        ini = max(EXPEDIENTE_INI, min(EXPEDIENTE_FIM, ini))
        fim = max(ini, min(EXPEDIENTE_FIM, fim))
        if ini >= fim:
            return None
        return ini, fim


def expediente_no_dia(dia, feriados_por_data=None):
    """Janela 8h–17h em dia útil, ou None (fim de semana / sem expediente)."""
    if isinstance(dia, datetime):
        dia = dia.date()
    if dia.weekday() >= 5:
        return None
    feriado = None
    if feriados_por_data is not None:
        feriado = feriados_por_data.get(dia)
    else:
        feriado = Feriado.query.filter_by(data=dia, ativo=True).first()
    if feriado:
        return feriado.janela_expediente()
    return EXPEDIENTE_INI, EXPEDIENTE_FIM


def feriados_no_periodo(inicio, fim):
    if isinstance(inicio, datetime):
        inicio = inicio.date()
    if isinstance(fim, datetime):
        fim = fim.date()
    rows = (
        Feriado.query
        .filter(Feriado.ativo.is_(True), Feriado.data >= inicio, Feriado.data < fim)
        .all()
    )
    return {f.data: f for f in rows}
