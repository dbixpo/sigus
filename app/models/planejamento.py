# -*- coding: utf-8 -*-
"""Planejamentos/Projetos com GUT e ações em Kanban — estilo Monday.com."""
from datetime import datetime, date
from app import db
from app.utils import prefixed_static_url


STATUS_ACAO = ['backlog', 'em_andamento', 'concluido', 'cancelado']
STATUS_ACAO_LABELS = {
    'backlog': 'Pendente',
    'em_andamento': 'Em andamento',
    'concluido': 'Feito',
    'cancelado': 'Cancelado',
}
STATUS_ACAO_BADGE = {
    'backlog': 'status-pendente',
    'em_andamento': 'status-andamento',
    'concluido': 'status-feito',
    'cancelado': 'status-cancelado',
}

GUT_GRAVIDADE = {1: 'Muito baixo', 2: 'Baixo', 3: 'Médio', 4: 'Alto', 5: 'Crítico'}
GUT_URGENCIA = {1: 'Pode esperar', 2: 'Pouco urgente', 3: 'Urgente', 4: 'Muito urgente', 5: 'Imediato'}
GUT_TENDENCIA = {1: 'Estável', 2: 'Leve piora', 3: 'Piora moderada', 4: 'Piora rápida', 5: 'Piora iminente'}


class Planejamento(db.Model):
    """Projeto/Planejamento de uma unidade. Tem GUT (Gravidade, Urgência, Tendência) para priorização."""
    __tablename__ = 'planejamentos'

    id          = db.Column(db.Integer, primary_key=True)
    unidade_id  = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='CASCADE'), nullable=False)
    titulo      = db.Column(db.String(200), nullable=False)
    descricao   = db.Column(db.Text)
    gravidade   = db.Column(db.Integer, nullable=False, default=1)  # 1-5
    urgencia    = db.Column(db.Integer, nullable=False, default=1)  # 1-5
    tendencia   = db.Column(db.Integer, nullable=False, default=1)  # 1-5
    criado_por     = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em      = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    atualizado_em  = db.Column(db.DateTime, nullable=True)

    unidade  = db.relationship('Unidade', backref=db.backref('planejamentos', lazy='dynamic'))
    criador       = db.relationship('Usuario', foreign_keys=[criado_por])
    ultimo_editor = db.relationship('Usuario', foreign_keys=[atualizado_por])
    acoes    = db.relationship('AcaoPlanejamento', back_populates='planejamento', order_by='AcaoPlanejamento.ordem',
                               lazy='dynamic', cascade='all, delete-orphan')
    anexos   = db.relationship('PlanejamentoAnexo', back_populates='planejamento', lazy='dynamic',
                               cascade='all, delete-orphan')

    @property
    def gut_score(self):
        """G × U × T — priorização GUT."""
        return self.gravidade * self.urgencia * self.tendencia

    @property
    def gut_label(self):
        return f'G{self.gravidade} U{self.urgencia} T{self.tendencia}'

    @property
    def gut_prioridade(self):
        """Retorna {'texto': str, 'cls': str} para badge de prioridade — mesma lógica do form."""
        score = self.gut_score
        if score >= 81:
            return {'texto': 'Prioridade crítica', 'cls': 'bg-danger'}
        if score >= 51:
            return {'texto': 'Alta prioridade', 'cls': 'bg-warning text-dark'}
        if score >= 21:
            return {'texto': 'Prioridade moderada', 'cls': 'bg-info text-dark'}
        return {'texto': 'Baixa prioridade', 'cls': 'bg-success'}

    @property
    def gut_gravidade_label(self):
        return GUT_GRAVIDADE.get(self.gravidade, '-')

    @property
    def gut_urgencia_label(self):
        return GUT_URGENCIA.get(self.urgencia, '-')

    @property
    def gut_tendencia_label(self):
        return GUT_TENDENCIA.get(self.tendencia, '-')


class PlanejamentoAnexo(db.Model):
    """Anexo (PDF, foto) vinculado a um planejamento."""
    __tablename__ = 'planejamentos_anexos'

    id             = db.Column(db.Integer, primary_key=True)
    planejamento_id = db.Column(db.Integer, db.ForeignKey('planejamentos.id', ondelete='CASCADE'), nullable=False)
    filename  = db.Column(db.String(200), nullable=False)
    original  = db.Column(db.String(200), nullable=False)
    mime_type = db.Column(db.String(100))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    planejamento = db.relationship('Planejamento', back_populates='anexos', foreign_keys=[planejamento_id])

    @property
    def url(self):
        return prefixed_static_url(f'/static/uploads/planos/{self.filename}')

    @property
    def eh_pdf(self):
        return (self.mime_type or '').startswith('application/pdf')

    @property
    def eh_imagem(self):
        return (self.mime_type or '').startswith('image/')


acacao_planejamento_responsaveis = db.Table(
    'acao_planejamento_responsaveis',
    db.Column('acao_id', db.Integer, db.ForeignKey('acoes_planejamento.id', ondelete='CASCADE'), primary_key=True),
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), primary_key=True),
)

acacao_planejamento_empresas = db.Table(
    'acao_planejamento_empresas',
    db.Column('acao_id', db.Integer, db.ForeignKey('acoes_planejamento.id', ondelete='CASCADE'), primary_key=True),
    db.Column('empresa_id', db.Integer, db.ForeignKey('empresas_contratadas.id', ondelete='CASCADE'), primary_key=True),
)


class AcaoPlanejamento(db.Model):
    """Ação pertencente a um planejamento — estilo Monday.com (planilha)."""
    __tablename__ = 'acoes_planejamento'

    id              = db.Column(db.Integer, primary_key=True)
    planejamento_id = db.Column(db.Integer, db.ForeignKey('planejamentos.id', ondelete='CASCADE'), nullable=False)
    titulo     = db.Column(db.String(300), nullable=False)
    descricao  = db.Column(db.Text)
    status     = db.Column(db.String(20), nullable=False, default='backlog')
    ordem      = db.Column(db.Integer, nullable=False, default=0)
    prazo      = db.Column(db.Date, nullable=True)  # data prevista de conclusão
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    planejamento  = db.relationship('Planejamento', back_populates='acoes')
    criador       = db.relationship('Usuario', foreign_keys=[criado_por])
    responsaveis  = db.relationship(
        'Usuario',
        secondary=acacao_planejamento_responsaveis,
        backref=db.backref('acoes_planejamento_responsavel', lazy='dynamic'),
        lazy='joined',
    )
    empresas = db.relationship(
        'EmpresaContratada',
        secondary=acacao_planejamento_empresas,
        backref=db.backref('acoes_planejamento', lazy='dynamic'),
        lazy='joined',
    )
    observacoes   = db.relationship(
        'AcaoObservacao',
        back_populates='acao',
        order_by='AcaoObservacao.criado_em',
        lazy='selectin',
        cascade='all, delete-orphan',
    )

    @property
    def status_label(self):
        return STATUS_ACAO_LABELS.get(self.status, self.status)

    @property
    def status_badge_cls(self):
        return STATUS_ACAO_BADGE.get(self.status, '')

    @property
    def prazo_dias_texto(self):
        """Retorna texto de dias até vencer ou após vencer."""
        if not self.prazo:
            return None
        hoje = date.today()
        delta = (self.prazo - hoje).days
        if delta > 0:
            d = 'dia' if delta == 1 else 'dias'
            return f'{delta} {d} para vencer'
        if delta == 0:
            return 'Vence hoje'
        d = 'dia' if abs(delta) == 1 else 'dias'
        return f'Venceu há {abs(delta)} {d}'


class AcaoObservacao(db.Model):
    """Observação/anotação feita por responsável em uma ação — registro do desenrolar."""
    __tablename__ = 'acoes_planejamento_observacoes'

    id         = db.Column(db.Integer, primary_key=True)
    acao_id    = db.Column(db.Integer, db.ForeignKey('acoes_planejamento.id', ondelete='CASCADE'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    texto      = db.Column(db.Text, nullable=False)  # HTML (Quill)
    criado_em  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    acao    = db.relationship('AcaoPlanejamento', back_populates='observacoes')
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    anexos  = db.relationship('AcaoObservacaoAnexo', back_populates='observacao', lazy='joined',
                              cascade='all, delete-orphan')


class AcaoObservacaoAnexo(db.Model):
    """Anexo em uma observação de ação."""
    __tablename__ = 'acoes_planejamento_obs_anexos'

    id             = db.Column(db.Integer, primary_key=True)
    observacao_id  = db.Column(db.Integer, db.ForeignKey('acoes_planejamento_observacoes.id', ondelete='CASCADE'), nullable=False)
    filename    = db.Column(db.String(200), nullable=False)
    original    = db.Column(db.String(200), nullable=False)
    mime_type   = db.Column(db.String(100))

    observacao = db.relationship('AcaoObservacao', back_populates='anexos')

    @property
    def url(self):
        return prefixed_static_url(f'/static/uploads/obs_acoes/{self.filename}')

    @property
    def eh_imagem(self):
        return (self.mime_type or '').startswith('image/')

    @property
    def eh_pdf(self):
        return (self.mime_type or '').startswith('application/pdf')
