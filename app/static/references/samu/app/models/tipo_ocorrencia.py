"""Tipo de ocorrência."""
from datetime import datetime
from app import db


class TipoOcorrencia(db.Model):
    """Tipos de ocorrência atendidas pelo SAMU."""
    __tablename__ = 'tipos_ocorrencia'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(300))
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TipoOcorrencia {self.nome}>'
