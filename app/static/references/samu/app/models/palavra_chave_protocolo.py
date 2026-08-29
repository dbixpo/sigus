"""Palavra-chave que dispara um protocolo de acolhimento."""
from datetime import datetime
from app import db


class PalavraChaveProtocolo(db.Model):
    """Palavras-chave para busca/sugestão de protocolos."""
    __tablename__ = 'palavras_chave_protocolo'

    id = db.Column(db.Integer, primary_key=True)
    algoritmo_id = db.Column(db.Integer, db.ForeignKey('algoritmos_acolhimento.id', ondelete='CASCADE'), nullable=False)
    palavra = db.Column(db.String(100), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    algoritmo = db.relationship('AlgoritmoAcolhimento', backref=db.backref('palavras_chave', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<PalavraChave {self.palavra}>'
