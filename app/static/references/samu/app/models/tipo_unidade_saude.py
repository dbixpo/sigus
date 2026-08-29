"""Tipos de Unidade de Saúde (APS, AES, HOS, UPA, UPH, PA)."""
from datetime import datetime
from app import db


class TipoUnidadeSaude(db.Model):
    """Tipo de unidade de saúde: APS, AES, HOS, UPA, UPH, PA."""
    __tablename__ = 'tipos_unidade_saude'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    sigla = db.Column(db.String(20), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TipoUnidadeSaude {self.sigla}>'
