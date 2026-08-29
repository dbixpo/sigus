"""Bases Descentralizadas — endereço completo para viaturas vinculadas."""
from datetime import datetime
from app import db


class BaseDescentralizada(db.Model):
    """Base descentralizada com endereço completo (mesmo padrão da Central)."""
    __tablename__ = 'bases_descentralizadas'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    logradouro = db.Column(db.String(300))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    uf = db.Column(db.String(2))
    cep = db.Column(db.String(9))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(200))
    link_google_maps = db.Column(db.String(500))
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    viaturas = db.relationship('UnidadeSamu', back_populates='base', foreign_keys='UnidadeSamu.base_id')

    @property
    def endereco_completo(self):
        """Monta endereço: Logradouro, Nº, Complemento, Bairro."""
        partes = []
        if self.logradouro:
            partes.append(self.logradouro)
        if self.numero:
            partes.append(f'nº {self.numero}')
        if self.complemento:
            partes.append(self.complemento)
        if self.bairro:
            partes.append(self.bairro)
        return ', '.join(partes) if partes else None

    def __repr__(self):
        return f'<BaseDescentralizada {self.nome}>'
