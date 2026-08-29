from datetime import datetime
from app import db
from app.utils import prefixed_static_url

TIPOS_NOTIFICACAO = {
    'chamado_aberto':      ('Chamado aberto na sua unidade',          'bi-wrench-adjustable',      'primary'),
    'novo_andamento':      ('Novo andamento no chamado',              'bi-chat-left-text',         'info'),
    'alerta_chamado':      ('Alerta em chamado',                      'bi-exclamation-triangle',   'danger'),
    'pedido_info':         ('Pedido de informação',                   'bi-question-circle',        'warning'),
    'chamado_concluido':   ('Chamado concluído',                      'bi-check-circle',           'success'),
    'chamado_cancelado':   ('Chamado cancelado',                      'bi-x-circle',               'secondary'),
    # Alertas de Planejamento (ações vencendo hoje ou em 3 dias)
    'alerta_planejamento': ('Ação de planejamento próxima do prazo',  'bi-clipboard2-check',       'warning'),
}


class Notificacao(db.Model):
    __tablename__ = 'notificacoes'

    id          = db.Column(db.Integer, primary_key=True)
    usuario_id  = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    tipo        = db.Column(db.String(30), nullable=False)
    titulo      = db.Column(db.String(200), nullable=False)
    texto       = db.Column(db.Text)
    chamado_id  = db.Column(db.Integer, db.ForeignKey('chamados.id', ondelete='CASCADE'))
    lida        = db.Column(db.Boolean, nullable=False, default=False)
    criado_em   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    chamado = db.relationship('Chamado', foreign_keys=[chamado_id])

    @property
    def icone(self):
        return TIPOS_NOTIFICACAO.get(self.tipo, ('', 'bi-bell', 'secondary'))[1]

    @property
    def cor(self):
        return TIPOS_NOTIFICACAO.get(self.tipo, ('', 'bi-bell', 'secondary'))[2]

    @property
    def url(self):
        if self.chamado_id:
            return prefixed_static_url(f'/chamados/{self.chamado_id}')
        return '#'
