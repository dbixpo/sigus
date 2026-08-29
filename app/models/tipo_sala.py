from datetime import datetime
from app import db


class TipoSala(db.Model):
    __tablename__ = 'tipos_sala'

    id        = db.Column(db.Integer, primary_key=True)
    nome      = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    icone     = db.Column(db.String(50), nullable=False, default='fas fa-door-open')
    ativo     = db.Column(db.Boolean, nullable=False, default=True)
    criado_em     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    salas = db.relationship('Sala', back_populates='tipo_sala', lazy='dynamic')

    def __repr__(self):
        return f'<TipoSala {self.nome}>'
