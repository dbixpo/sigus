"""Opção de resposta para pergunta (selectbox ou múltipla escolha)."""
from app import db


class OpcaoResposta(db.Model):
    """Opções de resposta. proxima_pergunta_id indica qual pergunta virá ao escolher esta opção."""
    __tablename__ = 'opcoes_resposta'

    id = db.Column(db.Integer, primary_key=True)
    pergunta_id = db.Column(db.Integer, db.ForeignKey('perguntas_protocolo.id', ondelete='CASCADE'), nullable=False)
    texto = db.Column(db.String(200), nullable=False)
    pontuacao = db.Column(db.SmallInteger, nullable=False, default=0)  # para cálculo de grau de risco
    ordem = db.Column(db.SmallInteger, nullable=False, default=0)
    proxima_pergunta_id = db.Column(db.Integer, db.ForeignKey('perguntas_protocolo.id', ondelete='SET NULL'))

    proxima_pergunta = db.relationship('PerguntaProtocolo', foreign_keys=[proxima_pergunta_id])

    def __repr__(self):
        return f'<OpcaoResposta {self.texto}>'
