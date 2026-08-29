"""Matrículas profissionais - vínculos com CBO, conselho, etc."""
from datetime import datetime
from app import db
from app.models.usuario import CBOS, VINCULOS, TIPOS_VINCULO


class MatriculaProfissional(db.Model):
    """Cada matrícula de um profissional. Uma pessoa pode ter N matrículas."""
    __tablename__ = 'matriculas_profissionais'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    numero = db.Column(db.String(50), nullable=False)
    vinculo = db.Column(db.String(1))
    tipo_vinculo = db.Column(db.String(1))
    cbo = db.Column(db.String(10))
    reg_conselho = db.Column(db.String(30))
    orgao_emissor = db.Column(db.String(50))
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuario = db.relationship('Usuario', back_populates='matriculas')

    @property
    def cbo_label(self):
        for cod, desc in CBOS:
            if cod == self.cbo:
                return f'{cod} – {desc}'
        return self.cbo or '—'

    @property
    def vinculo_label(self):
        return VINCULOS.get(self.vinculo, '—')

    @property
    def tipo_vinculo_label(self):
        return TIPOS_VINCULO.get(self.tipo_vinculo, '—')

    def __repr__(self):
        return f'<Matricula {self.numero} u={self.usuario_id}>'
