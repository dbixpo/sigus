"""Classificação de risco (Manchester: 1 vermelho, 2 laranja, 3 verde, 4 azul, 5 cinza)."""
from datetime import datetime
from app import db


class ClassificacaoRisco(db.Model):
    """Classificação de risco para priorização (protocolo Manchester)."""
    __tablename__ = 'classificacoes_risco'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    cor = db.Column(db.String(20), nullable=False)  # hex ou nome Bootstrap
    ordem = db.Column(db.Integer, nullable=False, default=0)  # 1=maior prioridade
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ClassificacaoRisco {self.nome}>'
