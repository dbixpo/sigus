"""Classificação Internacional de Doenças - CID-10."""
from datetime import datetime
from app import db


class CID10(db.Model):
    """Tabela CID-10 para diagnóstico."""
    __tablename__ = 'cid10'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), nullable=False, index=True)
    descricao = db.Column(db.String(300), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CID10 {self.codigo}>'
