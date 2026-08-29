"""Tipos de ligação para registro no TARM."""
from datetime import datetime
from app import db


class TipoLigacao(db.Model):
    """Tipos de ligação recebidas pela central."""
    __tablename__ = 'tipos_ligacao'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(300))
    permite_encerrar_direto = db.Column(db.Boolean, nullable=False, default=False)
    eh_trote = db.Column(db.Boolean, nullable=False, default=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TipoLigacao {self.nome}>'
