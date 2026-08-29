# -*- coding: utf-8 -*-
"""Planejamentos/Projetos com GUT e ações em Kanban — estilo Monday.com."""
from datetime import datetime, date
from app import db
from app.utils import prefixed_static_url
from app.utils import agora_local_callable


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


# Tabelas de relacionamento many-to-many para unidades e tipos de unidades
planejamento_unidades = db.Table(
    'planejamento_unidades',
    db.Column('planejamento_id', db.Integer, db.ForeignKey('planejamentos.id', ondelete='CASCADE'), primary_key=True),
    db.Column('unidade_id', db.Integer, db.ForeignKey('unidades.id', ondelete='CASCADE'), primary_key=True),
)

planejamento_tipos_unidade = db.Table(
    'planejamento_tipos_unidade',
    db.Column('planejamento_id', db.Integer, db.ForeignKey('planejamentos.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tipo_unidade_id', db.Integer, db.ForeignKey('tipos_unidade.id', ondelete='CASCADE'), primary_key=True),
)


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
    criado_em      = db.Column(db.DateTime, nullable=False, default=agora_local_callable)
    atualizado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    atualizado_em  = db.Column(db.DateTime, nullable=True)

    unidade  = db.relationship('Unidade', foreign_keys=[unidade_id], backref=db.backref('planejamentos', lazy='dynamic'))
    # Relacionamentos many-to-many para múltiplas unidades e tipos de unidades
    unidades = db.relationship('Unidade', secondary=planejamento_unidades, lazy='dynamic',
                               backref=db.backref('planejamentos_vinculados', lazy='dynamic'))
    tipos_unidade = db.relationship('TipoUnidade', secondary=planejamento_tipos_unidade, lazy='dynamic',
                                     backref=db.backref('planejamentos', lazy='dynamic'))
    criador       = db.relationship('Usuario', foreign_keys=[criado_por])
    ultimo_editor = db.relationship('Usuario', foreign_keys=[atualizado_por])
    acoes    = db.relationship('AcaoPlanejamento', back_populates='planejamento', order_by='AcaoPlanejamento.ordem',
                               lazy='dynamic', cascade='all, delete-orphan')
    anexos   = db.relationship('PlanejamentoAnexo', back_populates='planejamento',
                               order_by='PlanejamentoAnexo.criado_em.asc()',
                               lazy='dynamic',
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
    """Anexo (PDF, foto, audio) vinculado a um planejamento."""
    __tablename__ = 'planejamentos_anexos'

    id             = db.Column(db.Integer, primary_key=True)
    planejamento_id = db.Column(db.Integer, db.ForeignKey('planejamentos.id', ondelete='CASCADE'), nullable=False)
    filename  = db.Column(db.String(200), nullable=False)
    original  = db.Column(db.String(200), nullable=False)
    mime_type = db.Column(db.String(100))
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable)

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

    @property
    def eh_audio(self):
        return (self.mime_type or '').startswith('audio/')


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
    criado_em  = db.Column(db.DateTime, nullable=False, default=agora_local_callable)
    atualizado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    atualizado_em  = db.Column(db.DateTime, nullable=True)

    planejamento  = db.relationship('Planejamento', back_populates='acoes')
    criador       = db.relationship('Usuario', foreign_keys=[criado_por])
    ultimo_editor = db.relationship('Usuario', foreign_keys=[atualizado_por])
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
        """Retorna texto de dias até vencer ou após vencer. Não conta prazo para ações Feito/Cancelado."""
        if not self.prazo or self.status in ('concluido', 'cancelado'):
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
    criado_em  = db.Column(db.DateTime, nullable=False, default=agora_local_callable)

    acao    = db.relationship('AcaoPlanejamento', back_populates='observacoes')
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    anexos  = db.relationship('AcaoObservacaoAnexo', back_populates='observacao',
                              order_by='AcaoObservacaoAnexo.id.asc()',
                              lazy='joined',
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
    
    @property
    def eh_audio(self):
        return (self.mime_type or '').startswith('audio/')
    
    @property
    def tipo_arquivo(self):
        """Retorna o tipo de arquivo baseado no mime_type ou extensão."""
        mime = (self.mime_type or '').lower()
        original_lower = (self.original or '').lower()
        
        if mime.startswith('image/'):
            return 'imagem'
        elif mime.startswith('application/pdf'):
            return 'pdf'
        elif mime.startswith('audio/'):
            return 'audio'
        elif 'word' in mime or 'document' in mime or original_lower.endswith(('.doc', '.docx')):
            return 'word'
        elif 'excel' in mime or 'spreadsheet' in mime or original_lower.endswith(('.xls', '.xlsx', '.ods')):
            return 'excel'
        elif 'powerpoint' in mime or 'presentation' in mime or original_lower.endswith(('.ppt', '.pptx', '.odp')):
            return 'powerpoint'
        elif 'opendocument' in mime or original_lower.endswith(('.odt', '.ods', '.odp')):
            if original_lower.endswith('.odt'):
                return 'word'
            elif original_lower.endswith('.ods'):
                return 'excel'
            elif original_lower.endswith('.odp'):
                return 'powerpoint'
        elif mime.startswith('text/') or original_lower.endswith('.txt'):
            return 'texto'
        return 'arquivo'
    
    @property
    def icone_classe(self):
        """Retorna a classe do ícone Bootstrap baseado no tipo de arquivo."""
        tipo = self.tipo_arquivo
        icones = {
            'imagem': 'bi-image text-success',
            'pdf': 'bi-file-earmark-pdf text-danger',
            'word': 'bi-file-earmark-word text-primary',
            'excel': 'bi-file-earmark-excel text-success',
            'powerpoint': 'bi-file-earmark-ppt text-warning',
            'texto': 'bi-file-earmark-text text-secondary',
            'audio': 'bi-file-earmark-music text-info',
            'arquivo': 'bi-file-earmark text-muted'
        }
        return icones.get(tipo, 'bi-file-earmark text-muted')