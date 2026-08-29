"""Equipes: viatura + veículo + profissionais (Montar Equipes - Rádio Operador)."""
from datetime import datetime
from app import db


class Equipe(db.Model):
    """Equipe vinculada a uma viatura (Unidade SAMU)."""
    __tablename__ = 'equipes'

    id = db.Column(db.Integer, primary_key=True)
    unidade_samu_id = db.Column(db.Integer, db.ForeignKey('unidades_samu.id', ondelete='CASCADE'), nullable=False)
    veiculo_id = db.Column(db.Integer, db.ForeignKey('veiculos.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    unidade_samu = db.relationship('UnidadeSamu', backref=db.backref('equipe', uselist=False))
    veiculo = db.relationship('Veiculo', backref='equipes')
    membros = db.relationship('EquipeMembro', back_populates='equipe', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Equipe unidade_samu_id={self.unidade_samu_id}>'


class EquipeMembro(db.Model):
    """Membro da equipe: profissional + perfil (categoria)."""
    __tablename__ = 'equipes_membros'

    id = db.Column(db.Integer, primary_key=True)
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipes.id', ondelete='CASCADE'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    cbo = db.Column(db.String(10))  # legado
    perfil = db.Column(db.String(50))  # medico_intervencionista, enfermeiro, aux_tec_enfermagem, condutor
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    equipe = db.relationship('Equipe', back_populates='membros')
    usuario = db.relationship('Usuario', backref='equipes_membro')

    def __repr__(self):
        return f'<EquipeMembro equipe={self.equipe_id} usuario={self.usuario_id}>'
