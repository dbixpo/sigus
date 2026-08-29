"""Classificação Internacional de Doenças para Oncologia - CID-O (morfologia de neoplasias)."""
from datetime import datetime
from app import db


class CidO(db.Model):
    """Tabela CID-O para morfologia de neoplasias."""
    __tablename__ = 'cido'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, index=True)
    descricao = db.Column(db.String(300), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CidO {self.codigo}>'
