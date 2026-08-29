# -*- coding: utf-8 -*-
"""Código Brasileiro de Ocupação (CBO)."""
from datetime import datetime
from app import db


class CBO(db.Model):
    """Código Brasileiro de Ocupação."""
    __tablename__ = 'cbos'

    id          = db.Column(db.Integer, primary_key=True)
    codigo      = db.Column(db.String(10), nullable=False, unique=True)
    descricao   = db.Column(db.String(200), nullable=False)
    ativo       = db.Column(db.Boolean, nullable=False, default=True)
    criado_em   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CBO {self.codigo} - {self.descricao}>'

    @property
    def label(self):
        """Retorna código e descrição formatados."""
        return f'{self.codigo} – {self.descricao}'
