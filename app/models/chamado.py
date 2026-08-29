from datetime import datetime
from app import db
from app.utils import prefixed_static_url

# Categorias do form de bem permanente (espelha o Google Form)
CATEGORIAS_BP = [
    ('eletroeletronico',      'Eletroeletrônico'),
    ('equip_medico',          'Equipamento médico/odontológico'),
    ('mobiliario_medico',     'Mobiliário médico'),
    ('mobiliario_geral',      'Mobiliário geral'),
    ('outro',                 'Outro'),
]

SERVICOS_BP = [
    ('corretiva',     'Manutenção corretiva'),
    ('preventiva',    'Manutenção preventiva'),
    ('instalacao',    'Instalação'),
    ('desinstalacao', 'Desinstalação'),
    ('treinamento',   'Treinamento'),
    ('calibracao',    'Calibração'),
    ('outro',         'Outro'),
]

PROBLEMA_EM = [
    ('bem',       'No bem permanente'),
    ('acessorio', 'No acessório'),
]

TIPOS_CHAMADO = ['predial', 'sala', 'equipamento', 'tecnologia', 'contratual', 'outro']
TIPOS_CHAMADO_LABELS = {
    'predial':    'Predial',
    'sala':       'Sala',
    'equipamento': 'Equipamento',
    'tecnologia': 'Tecnologia/TI',
    'contratual': 'Contratual',
    'outro':      'Outro',
}

PRIORIDADES = ['baixa', 'media', 'alta', 'urgente']
PRIORIDADES_LABELS = {
    'baixa': 'Baixa',
    'media': 'Média',
    'alta': 'Alta',
    'urgente': 'Urgente',
}
PRIORIDADES_BADGE = {
    'baixa': 'secondary',
    'media': 'info',
    'alta': 'warning',
    'urgente': 'danger',
}

STATUS_CHAMADO = ['aberto', 'em_andamento', 'aguardando_peca', 'concluido', 'cancelado']
STATUS_CHAMADO_LABELS = {
    'aberto': 'Aberto',
    'em_andamento': 'Em Andamento',
    'aguardando_peca': 'Aguardando Peça',
    'concluido': 'Concluído',
    'cancelado': 'Cancelado',
}
STATUS_CHAMADO_BADGE = {
    'aberto': 'danger',
    'em_andamento': 'warning',
    'aguardando_peca': 'info',
    'concluido': 'success',
    'cancelado': 'secondary',
}


class Divisao(db.Model):
    """Divisão que agrupa setores e define quais chamados a divisão 'cuida'.
    Ex.: SUEQ Predial (tipos_chamado=[predial]), Divisão APS (tipos_unidade_ids=[USF, UBS]).
    Membros da divisão VEEM os chamados; só o setor atribuído TRABALHA neles."""
    __tablename__ = 'divisoes'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    tipos_chamado = db.Column(db.JSON, default=list)   # ex: ['predial', 'equipamento']
    tipos_unidade_ids = db.Column(db.JSON, default=list)  # ex: [1, 2] (ids de TipoUnidade)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    setores = db.relationship('SetorManutencao', back_populates='divisao', lazy='dynamic')

    def __repr__(self):
        return f'<Divisao {self.nome}>'


class SetorManutencao(db.Model):
    __tablename__ = 'setores_manutencao'

    id = db.Column(db.Integer, primary_key=True)
    divisao_id = db.Column(db.Integer, db.ForeignKey('divisoes.id', ondelete='SET NULL'))
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    tipos_chamado = db.Column(db.JSON, default=list)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    divisao = db.relationship('Divisao', back_populates='setores')
    usuarios = db.relationship('UsuarioSetor', back_populates='setor', lazy='dynamic')
    chamados = db.relationship('Chamado', back_populates='setor', lazy='dynamic')

    def __repr__(self):
        return f'<SetorManutencao {self.nome}>'


class UsuarioSetor(db.Model):
    __tablename__ = 'usuario_setor'

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), primary_key=True)
    setor_id = db.Column(db.Integer, db.ForeignKey('setores_manutencao.id', ondelete='CASCADE'), primary_key=True)

    usuario = db.relationship('Usuario')
    setor = db.relationship('SetorManutencao', back_populates='usuarios')


class Chamado(db.Model):
    __tablename__ = 'chamados'

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False, unique=True)
    # Para chamados de equipamento/TI: unidade_id é obrigatório
    # Para chamados prediais em prédio compartilhado: predio_id pode ser preenchido
    # e unidade_id aponta para a unidade solicitante dentro do prédio
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='RESTRICT'), nullable=False)
    predio_id  = db.Column(db.Integer, db.ForeignKey('predios.id',   ondelete='SET NULL'))
    sala_id = db.Column(db.Integer, db.ForeignKey('salas.id', ondelete='SET NULL'))
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamentos.id', ondelete='SET NULL'))
    tipo_chamado = db.Column(db.String(20), nullable=False, default='equipamento')
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    prioridade = db.Column(db.String(10), nullable=False, default='media')
    status = db.Column(db.String(20), nullable=False, default='aberto')
    aberto_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='RESTRICT'), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    setor_id = db.Column(db.Integer, db.ForeignKey('setores_manutencao.id', ondelete='SET NULL'))
    observacao_conclusao = db.Column(db.Text)

    # ── Campos extras para chamado de Bem Permanente ──────────────
    # Dados do equipamento quando não há cadastro no sistema
    bp_num_patrimonio    = db.Column(db.String(60))   # preenchido manualmente se sem cadastro
    bp_nome_equip        = db.Column(db.String(200))  # nome livre
    bp_fabricante_modelo = db.Column(db.String(200))  # fabricante/modelo livre
    bp_num_serie         = db.Column(db.String(100))  # nº de série livre
    bp_categoria         = db.Column(db.String(30))   # CATEGORIAS_BP
    bp_servico           = db.Column(db.String(20))   # SERVICOS_BP
    bp_problema_em       = db.Column(db.String(20))   # PROBLEMA_EM
    bp_rechamado         = db.Column(db.Boolean, default=False)
    bp_data_rechamado    = db.Column(db.Date)

    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    fechado_em = db.Column(db.DateTime)

    unidade = db.relationship('Unidade', back_populates='chamados')
    predio  = db.relationship('Predio', foreign_keys=[predio_id])
    sala = db.relationship('Sala', back_populates='chamados')
    equipamento = db.relationship('Equipamento', back_populates='chamados')
    solicitante = db.relationship('Usuario', foreign_keys=[aberto_por], back_populates='chamados_abertos')
    responsavel = db.relationship('Usuario', foreign_keys=[responsavel_id], back_populates='chamados_responsavel')
    setor = db.relationship('SetorManutencao', back_populates='chamados')
    historico = db.relationship('ChamadoHistorico', back_populates='chamado',
                                 order_by='ChamadoHistorico.criado_em', lazy='dynamic',
                                 cascade='all, delete-orphan')
    fotos = db.relationship('ChamadoFoto', back_populates='chamado',
                             order_by='ChamadoFoto.id', lazy='dynamic',
                             cascade='all, delete-orphan')

    @staticmethod
    def gerar_numero(tipo_chamado='predial'):
        from datetime import date
        hoje = date.today()
        sigla = 'CE' if tipo_chamado == 'equipamento' else 'CP'
        prefixo = f"{sigla}{hoje.year}{hoje.month:02d}{hoje.day:02d}"
        ultimo = Chamado.query.filter(Chamado.numero.like(f'{prefixo}%')).order_by(Chamado.numero.desc()).first()
        seq = (int(ultimo.numero[-4:]) + 1) if ultimo else 1
        return f"{prefixo}{seq:04d}"

    @property
    def tipo_label(self):
        return TIPOS_CHAMADO_LABELS.get(self.tipo_chamado, self.tipo_chamado)

    @property
    def prioridade_label(self):
        return PRIORIDADES_LABELS.get(self.prioridade, self.prioridade)

    @property
    def prioridade_badge(self):
        return PRIORIDADES_BADGE.get(self.prioridade, 'secondary')

    @property
    def status_label(self):
        try:
            from app.models.status_chamado import StatusChamado
            s = StatusChamado.query.filter_by(slug=self.status).first()
            if s:
                return s.label
        except Exception:
            pass
        return STATUS_CHAMADO_LABELS.get(self.status, self.status)

    @property
    def status_badge(self):
        try:
            from app.models.status_chamado import StatusChamado
            s = StatusChamado.query.filter_by(slug=self.status).first()
            if s:
                return s.badge_cor
        except Exception:
            pass
        return STATUS_CHAMADO_BADGE.get(self.status, 'secondary')

    def __repr__(self):
        return f'<Chamado {self.numero}>'


class ChamadoFoto(db.Model):
    """Foto ou vídeo anexado a um chamado de Bem Permanente."""
    __tablename__ = 'chamado_fotos'

    id          = db.Column(db.Integer, primary_key=True)
    chamado_id  = db.Column(db.Integer, db.ForeignKey('chamados.id', ondelete='CASCADE'), nullable=False)
    filename    = db.Column(db.String(200), nullable=False)   # nome salvo em disco
    original    = db.Column(db.String(200))                   # nome original do upload
    mime_type   = db.Column(db.String(80))
    criado_em   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    chamado = db.relationship('Chamado', back_populates='fotos')

    @property
    def url(self):
        return prefixed_static_url(f'/static/uploads/chamados/{self.filename}')

    @property
    def is_video(self):
        return self.mime_type and self.mime_type.startswith('video/')


TIPOS_ANDAMENTO = [
    ('andamento',        'Andamento'),
    ('pedido_info',      'Pedido de Informação'),
    ('alerta',           'Alerta / Pendência'),
    ('nota_encerramento','Nota de Encerramento'),
]
TIPOS_ANDAMENTO_LABELS = {k: v for k, v in TIPOS_ANDAMENTO}
TIPOS_ANDAMENTO_ICONE = {
    'andamento':         'bi-chat-left-text',
    'pedido_info':       'bi-question-circle',
    'alerta':            'bi-exclamation-triangle',
    'nota_encerramento': 'bi-file-check',
}
TIPOS_ANDAMENTO_COR = {
    'andamento':         'primary',
    'pedido_info':       'warning',
    'alerta':            'danger',
    'nota_encerramento': 'success',
}


class ChamadoHistorico(db.Model):
    __tablename__ = 'chamado_historico'

    id            = db.Column(db.Integer, primary_key=True)
    chamado_id    = db.Column(db.Integer, db.ForeignKey('chamados.id', ondelete='CASCADE'), nullable=False)
    usuario_id    = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    acao          = db.Column(db.String(200), nullable=False)
    observacao    = db.Column(db.Text)
    tipo_andamento = db.Column(db.String(30), nullable=False, default='andamento')
    requer_resposta = db.Column(db.Boolean, nullable=False, default=False)
    respondido_em  = db.Column(db.DateTime)
    contrato_id   = db.Column(db.Integer, db.ForeignKey('contratos.id', ondelete='SET NULL'))
    criado_em     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    chamado  = db.relationship('Chamado', back_populates='historico')
    usuario  = db.relationship('Usuario')
    contrato = db.relationship('Contrato', foreign_keys=[contrato_id])
    anexos   = db.relationship('AnexoAndamento', back_populates='andamento',
                                lazy='dynamic', cascade='all, delete-orphan')

    @property
    def tipo_label(self):
        return TIPOS_ANDAMENTO_LABELS.get(self.tipo_andamento, self.tipo_andamento)

    @property
    def tipo_icone(self):
        return TIPOS_ANDAMENTO_ICONE.get(self.tipo_andamento, 'bi-chat-left-text')

    @property
    def tipo_cor(self):
        return TIPOS_ANDAMENTO_COR.get(self.tipo_andamento, 'primary')

    @property
    def pendente(self):
        return self.requer_resposta and self.respondido_em is None


class AnexoAndamento(db.Model):
    __tablename__ = 'andamento_anexos'

    id            = db.Column(db.Integer, primary_key=True)
    andamento_id  = db.Column(db.Integer, db.ForeignKey('chamado_historico.id', ondelete='CASCADE'), nullable=False)
    filename      = db.Column(db.String(200), nullable=False)
    original      = db.Column(db.String(200))
    mime_type     = db.Column(db.String(80))
    tamanho_bytes = db.Column(db.Integer)
    criado_em     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    andamento = db.relationship('ChamadoHistorico', back_populates='anexos')

    @property
    def url(self):
        return prefixed_static_url(f'/static/uploads/andamentos/{self.filename}')

    @property
    def is_imagem(self):
        return self.mime_type and self.mime_type.startswith('image/')

    @property
    def is_video(self):
        return self.mime_type and self.mime_type.startswith('video/')

    @property
    def is_pdf(self):
        return self.mime_type == 'application/pdf'

    @property
    def icone(self):
        if self.is_imagem:
            return 'bi-file-image'
        if self.is_video:
            return 'bi-camera-video'
        if self.is_pdf:
            return 'bi-file-pdf'
        return 'bi-paperclip'

    @property
    def tamanho_fmt(self):
        if not self.tamanho_bytes:
            return ''
        kb = self.tamanho_bytes / 1024
        if kb < 1024:
            return f'{kb:.0f} KB'
        return f'{kb/1024:.1f} MB'
