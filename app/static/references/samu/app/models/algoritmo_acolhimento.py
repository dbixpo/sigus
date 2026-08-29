"""Algoritmo de acolhimento (protocolo configurável com perguntas e palavras-chave)."""
from datetime import datetime
from app import db


class AlgoritmoAcolhimento(db.Model):
    """Protocolo de acolhimento com palavras-chave e perguntas guiadas."""
    __tablename__ = 'algoritmos_acolhimento'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    cor = db.Column(db.String(20))
    ordem = db.Column(db.SmallInteger, nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    graus_risco = db.Column(db.JSON, nullable=True)  # [{"min":0,"max":3,"grau":"Baixo"},...]
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<AlgoritmoAcolhimento {self.codigo}>'
