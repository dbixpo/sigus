"""Intercorrências durante o atendimento."""
from datetime import datetime
from app import db


class Intercorrencia(db.Model):
    """Intercorrências que podem ocorrer no atendimento."""
    __tablename__ = 'intercorrencias'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.String(300))
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    disponivel_cancelamento = db.Column(db.Boolean, nullable=False, default=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Intercorrencia {self.nome}>'
