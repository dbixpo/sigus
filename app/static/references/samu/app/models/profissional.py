"""Profissional vinculado às unidades SAMU."""
from datetime import datetime
from app import db


class Profissional(db.Model):
    """Cadastro de profissionais (médicos, enfermeiros, TARMs, condutores, etc.)."""
    __tablename__ = 'profissionais'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cpf = db.Column(db.String(14))
    cns = db.Column(db.String(20))
    matricula = db.Column(db.String(50))
    cargo = db.Column(db.String(100))
    cbo = db.Column(db.String(10))
    reg_conselho = db.Column(db.String(30))
    orgao_emissor = db.Column(db.String(50))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(200))
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    unidade_samu_id = db.Column(db.Integer, db.ForeignKey('unidades_samu.id', ondelete='SET NULL'))
    unidade_samu = db.relationship('UnidadeSamu', back_populates='profissionais')

    usuario = db.relationship('Usuario', back_populates='profissional', uselist=False)

    def __repr__(self):
        return f'<Profissional {self.nome}>'
