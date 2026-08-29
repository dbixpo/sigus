from datetime import datetime
from app import db


class FaltaAbonada(db.Model):
    """Registro de falta abonada de um profissional.

    Regras:
    - Máximo de 6 ativas por ano civil.
    - Apenas 1 ativa por mês.
    - Canceladas não contam para o limite, mas o histórico é preservado.
    """
    __tablename__ = 'faltas_abonadas'

    STATUS_ATIVA     = 'ativa'
    STATUS_CANCELADA = 'cancelada'

    id          = db.Column(db.Integer, primary_key=True)
    usuario_id  = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    unidade_id  = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='SET NULL'))

    data_falta  = db.Column(db.Date, nullable=False)
    funcao      = db.Column(db.String(200), nullable=False)

    status          = db.Column(db.String(20), nullable=False, default='ativa')  # ativa | cancelada
    motivo_cancelamento = db.Column(db.Text)
    cancelado_em    = db.Column(db.DateTime)
    cancelado_por   = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))

    criado_em   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    criado_por  = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))

    usuario          = db.relationship('Usuario', foreign_keys=[usuario_id], backref=db.backref('faltas_abonadas', lazy='dynamic'))
    unidade          = db.relationship('Unidade', foreign_keys=[unidade_id])
    criador          = db.relationship('Usuario', foreign_keys=[criado_por])
    cancelador       = db.relationship('Usuario', foreign_keys=[cancelado_por])

    @property
    def ativa(self):
        return self.status == self.STATUS_ATIVA

    @property
    def ano(self):
        return self.data_falta.year

    @property
    def mes(self):
        return self.data_falta.month

    @property
    def status_label(self):
        return {'ativa': 'Ativa', 'cancelada': 'Cancelada'}.get(self.status, self.status)

    @property
    def status_badge(self):
        return {'ativa': 'success', 'cancelada': 'secondary'}.get(self.status, 'secondary')

    def __repr__(self):
        return f'<FaltaAbonada {self.data_falta} [{self.status}] u={self.usuario_id}>'
