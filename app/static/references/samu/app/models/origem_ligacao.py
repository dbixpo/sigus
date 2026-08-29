"""Origem da ligação (linha telefônica, WhatsApp, etc.)."""
from datetime import datetime
from app import db


class OrigemLigacao(db.Model):
    """Origem/canal da ligação."""
    __tablename__ = 'origens_ligacao'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(300))
    preenche_endereco_unidade_saude = db.Column(db.Boolean, nullable=False, default=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<OrigemLigacao {self.nome}>'
