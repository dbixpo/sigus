"""Aviso para o Quadro de Avisos."""
from datetime import datetime
from app import db


class Aviso(db.Model):
    """Aviso exibido no Quadro de Avisos."""
    __tablename__ = 'avisos'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    mensagem = db.Column(db.Text)  # HTML
    anexo = db.Column(db.String(255))  # nome do arquivo armazenado
    ordem = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    criado_por = db.relationship('Usuario', foreign_keys=[criado_por_id])

    def __repr__(self):
        return f'<Aviso {self.titulo}>'
