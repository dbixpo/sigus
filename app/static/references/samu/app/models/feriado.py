"""Feriados - calendário para RH."""
from datetime import datetime
from app import db

TIPOS_FOLGA = {'feriado': 'Feriado', 'ponto_facultativo': 'Ponto Facultativo', 'data_comemorativa': 'Data Comemorativa'}
NATUREZAS = {'municipal': 'Municipal', 'nacional': 'Nacional'}


class Feriado(db.Model):
    """Feriados e datas comemorativas para cálculo de RH."""
    __tablename__ = 'feriados'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    tipo_folga = db.Column(db.String(20), nullable=False, default='feriado')
    natureza = db.Column(db.String(20), nullable=False, default='nacional')
    numero_decreto = db.Column(db.String(50))
    link_decreto = db.Column(db.String(500))
    emoji = db.Column(db.String(20))
    cor_primaria = db.Column(db.String(7))
    cor_secundaria = db.Column(db.String(7))
    cor_fonte_primaria = db.Column(db.String(7))
    cor_fonte_secundaria = db.Column(db.String(7))
    descricao = db.Column(db.String(300))
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    DIAS_SEMANA = ('Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira',
                   'Sexta-feira', 'Sábado', 'Domingo')

    @property
    def data_fmt(self):
        """Data formatada DD/MM/YYYY."""
        if not self.data:
            return '—'
        return self.data.strftime('%d/%m/%Y')

    @property
    def dia_semana(self):
        """Dia da semana a partir da data (0=segunda, 6=domingo)."""
        if not self.data:
            return '—'
        return self.DIAS_SEMANA[self.data.weekday()]

    @property
    def tipo_folga_label(self):
        return TIPOS_FOLGA.get(self.tipo_folga, self.tipo_folga or '—')

    @property
    def natureza_label(self):
        return NATUREZAS.get(self.natureza, self.natureza or '—')

    def __repr__(self):
        return f'<Feriado {self.data} {self.nome}>'
