from datetime import datetime
from app import db


class TipoUnidade(db.Model):
    __tablename__ = 'tipos_unidade'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(60), nullable=False, unique=True)
    sigla = db.Column(db.String(20), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    unidades = db.relationship('Unidade', back_populates='tipo_unidade', lazy='dynamic')

    def __repr__(self):
        return f'<TipoUnidade {self.sigla}>'
