"""Pergunta de um protocolo de acolhimento."""
from datetime import datetime
from app import db
from app.models.opcao_resposta import OpcaoResposta


class PerguntaProtocolo(db.Model):
    """Perguntas do protocolo (texto livre, sim/não, múltipla escolha)."""
    __tablename__ = 'perguntas_protocolo'

    TIPO_SELECTBOX = 'selectbox'   # uma opção (botões, escolhe 1 e avança)
    TIPO_MULTIPLA = 'multipla_escolha'  # várias opções (checkboxes, escolhe N e avança)
    TIPO_TEXTO = 'texto'  # bloco informativo (descrição, procedimento) — sem opções, avança automaticamente
    TIPOS = [
        (TIPO_SELECTBOX, 'Uma opção (selectbox)'),
        (TIPO_MULTIPLA, 'Múltipla escolha'),
        (TIPO_TEXTO, 'Texto informativo (descrição/procedimento)'),
    ]

    id = db.Column(db.Integer, primary_key=True)
    algoritmo_id = db.Column(db.Integer, db.ForeignKey('algoritmos_acolhimento.id', ondelete='CASCADE'), nullable=False)
    secao = db.Column(db.String(100))
    enunciado = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(30), nullable=False, default=TIPO_SELECTBOX)
    ordem = db.Column(db.SmallInteger, nullable=False, default=0)
    obrigatoria = db.Column(db.Boolean, nullable=False, default=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    algoritmo = db.relationship('AlgoritmoAcolhimento', backref=db.backref('perguntas', lazy='dynamic', cascade='all, delete-orphan', order_by='PerguntaProtocolo.ordem'))
    opcoes = db.relationship('OpcaoResposta', foreign_keys=[OpcaoResposta.pergunta_id], backref=db.backref('pergunta', foreign_keys=[OpcaoResposta.pergunta_id]), lazy='dynamic', cascade='all, delete-orphan', order_by='OpcaoResposta.ordem')

    def __repr__(self):
        return f'<PerguntaProtocolo {self.enunciado[:40]}>'
