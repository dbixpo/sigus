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

TIPOS_CHAMADO = [
    'predial', 'sala', 'equipamento', 'tecnologia', 'contratual',
    'solicitacao_equipamento', 'solicitacao_administrativa', 'outro',
]
TIPOS_CHAMADO_LABELS = {
    'predial':               'Predial',
    'sala':                  'Sala',
    'equipamento':           'Equipamento',
    'tecnologia':            'Tecnologia/TI',
    'contratual':            'Contratual',
    'solicitacao_equipamento': 'Solicitação de Equipamento',
    'solicitacao_administrativa': 'Solicitação Administrativa',
    'outro':                 'Outro',
}


def prioridade_de_gut(gravidade, urgencia, tendencia):
    """Converte score GUT (G×U×T) em prioridade — 3 níveis."""
    score = gravidade * urgencia * tendencia
    if score >= 81:
        return 'alta'
    if score >= 21:
        return 'media'
    return 'baixa'


def resumo_gut(gravidade, urgencia, tendencia):
    """Texto legível da matriz GUT + prioridade resultante."""
    from app.models.planejamento import GUT_GRAVIDADE, GUT_URGENCIA, GUT_TENDENCIA
    if not all([gravidade, urgencia, tendencia]):
        return None
    prio = PRIORIDADES_LABELS.get(prioridade_de_gut(gravidade, urgencia, tendencia), '—')
    return (
        f'Gravidade: {GUT_GRAVIDADE.get(gravidade, gravidade)} · '
        f'Urgência: {GUT_URGENCIA.get(urgencia, urgencia)} · '
        f'Tendência: {GUT_TENDENCIA.get(tendencia, tendencia)} · '
        f'Prioridade: {prio}'
    )


def normalizar_prioridade(slug):
    """Compatibilidade: chamados antigos com 'urgente' → alta."""
    if slug == 'urgente':
        return 'alta'
    return slug or 'media'


PRIORIDADES = ['baixa', 'media', 'alta']
PRIORIDADES_LABELS = {
    'baixa': 'Baixa',
    'media': 'Média',
    'alta': 'Alta',
    'urgente': 'Alta',
}
PRIORIDADES_BADGE = {
    'baixa': 'success',
    'media': 'warning',
    'alta': 'danger',
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
    tipo_chamado = db.Column(db.String(30), nullable=False, default='equipamento')
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    prioridade = db.Column(db.String(10), nullable=False, default='media')
    status = db.Column(db.String(20), nullable=False, default='aberto')
    aberto_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='RESTRICT'), nullable=True)
    externo_nome = db.Column(db.String(200))
    externo_whatsapp = db.Column(db.String(20))
    externo_email = db.Column(db.String(200))
    responsavel_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    setor_id = db.Column(db.Integer, db.ForeignKey('setores_manutencao.id', ondelete='SET NULL'))
    unidade_responsavel_id = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='SET NULL'))
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

    # ── Campos para chamado de Solicitação de Equipamento ─────────────
    se_tipo_equipamento_id = db.Column(db.Integer, db.ForeignKey('tipos_equipamento.id', ondelete='SET NULL'))
    se_tipo_livre = db.Column(db.String(150))  # Quando "Tipo não listado" (ex: Mouse)

    # ── GUT do solicitante (gravado na abertura) ───────────────────────
    sa_gravidade = db.Column(db.Integer)
    sa_urgencia = db.Column(db.Integer)
    sa_tendencia = db.Column(db.Integer)
    # ── GUT do setor executante (só se revisar na gestão) ─────────────
    gut_exec_gravidade = db.Column(db.Integer)
    gut_exec_urgencia = db.Column(db.Integer)
    gut_exec_tendencia = db.Column(db.Integer)

    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    fechado_em = db.Column(db.DateTime)

    unidade = db.relationship('Unidade', back_populates='chamados', foreign_keys=[unidade_id])
    predio  = db.relationship('Predio', foreign_keys=[predio_id])
    sala = db.relationship('Sala', back_populates='chamados')
    equipamento = db.relationship('Equipamento', back_populates='chamados')
    solicitante = db.relationship('Usuario', foreign_keys=[aberto_por], back_populates='chamados_abertos')
    responsavel = db.relationship('Usuario', foreign_keys=[responsavel_id], back_populates='chamados_responsavel')
    setor = db.relationship('SetorManutencao', back_populates='chamados')
    unidade_responsavel = db.relationship('Unidade', foreign_keys=[unidade_responsavel_id])
    se_tipo_equipamento = db.relationship('TipoEquipamento', foreign_keys=[se_tipo_equipamento_id])
    itens_solicitacao = db.relationship('ChamadoSolicitacaoItem', back_populates='chamado',
                                         order_by='ChamadoSolicitacaoItem.id', lazy='dynamic',
                                         cascade='all, delete-orphan')
    historico = db.relationship('ChamadoHistorico', back_populates='chamado',
                                 order_by='ChamadoHistorico.criado_em', lazy='dynamic',
                                 cascade='all, delete-orphan')
    fotos = db.relationship('ChamadoFoto', back_populates='chamado',
                             order_by='ChamadoFoto.id', lazy='dynamic',
                             cascade='all, delete-orphan')
    atribuidos_rel = db.relationship(
        'ChamadoAtribuido', back_populates='chamado',
        cascade='all, delete-orphan', lazy='selectin',
    )

    @property
    def atribuidos_usuarios(self):
        users = [a.usuario for a in self.atribuidos_rel if a.usuario]
        return sorted(users, key=lambda u: (u.nome or '').lower())

    @property
    def atribuidos_ids(self):
        return [a.usuario_id for a in self.atribuidos_rel]

    @property
    def atribuidos_nomes(self):
        nomes = [u.nome for u in self.atribuidos_usuarios]
        if nomes:
            return nomes
        if self.responsavel:
            return [self.responsavel.nome]
        return []
    def gerar_numero(tipo_chamado='predial'):
        from datetime import date
        hoje = date.today()
        if tipo_chamado == 'equipamento':
            sigla = 'CE'
        elif tipo_chamado == 'solicitacao_equipamento':
            sigla = 'SE'
        elif tipo_chamado == 'solicitacao_administrativa':
            sigla = 'CA'
        else:
            sigla = 'CP'
        prefixo = f"{sigla}{hoje.year}{hoje.month:02d}{hoje.day:02d}"
        ultimo = Chamado.query.filter(Chamado.numero.like(f'{prefixo}%')).order_by(Chamado.numero.desc()).first()
        seq = (int(ultimo.numero[-4:]) + 1) if ultimo else 1
        return f"{prefixo}{seq:04d}"

    @property
    def tipo_label(self):
        return TIPOS_CHAMADO_LABELS.get(self.tipo_chamado, self.tipo_chamado)

    @property
    def prioridade_efetiva_slug(self):
        if self.gut_executante_preenchido:
            return prioridade_de_gut(
                self.gut_exec_gravidade, self.gut_exec_urgencia, self.gut_exec_tendencia
            )
        if self.gut_solicitante_preenchido:
            return prioridade_de_gut(self.sa_gravidade, self.sa_urgencia, self.sa_tendencia)
        return normalizar_prioridade(self.prioridade)

    @property
    def prioridade_label(self):
        slug = self.prioridade_efetiva_slug
        return PRIORIDADES_LABELS.get(slug, self.prioridade)

    @property
    def prioridade_badge(self):
        slug = self.prioridade_efetiva_slug
        return PRIORIDADES_BADGE.get(slug, 'secondary')

    @property
    def gut_solicitante_preenchido(self):
        return all([self.sa_gravidade, self.sa_urgencia, self.sa_tendencia])

    @property
    def gut_executante_preenchido(self):
        return all([self.gut_exec_gravidade, self.gut_exec_urgencia, self.gut_exec_tendencia])

    @property
    def gut_solicitante_resumo(self):
        return resumo_gut(self.sa_gravidade, self.sa_urgencia, self.sa_tendencia)

    @property
    def gut_executante_resumo(self):
        return resumo_gut(self.gut_exec_gravidade, self.gut_exec_urgencia, self.gut_exec_tendencia)

    @property
    def gut_solicitante_prioridade_label(self):
        if not self.gut_solicitante_preenchido:
            return None
        slug = prioridade_de_gut(self.sa_gravidade, self.sa_urgencia, self.sa_tendencia)
        return PRIORIDADES_LABELS.get(slug, slug)

    @property
    def gut_solicitante_prioridade_badge(self):
        if not self.gut_solicitante_preenchido:
            return 'secondary'
        slug = prioridade_de_gut(self.sa_gravidade, self.sa_urgencia, self.sa_tendencia)
        return PRIORIDADES_BADGE.get(slug, 'secondary')

    @property
    def gut_executante_prioridade_label(self):
        if not self.gut_executante_preenchido:
            return None
        slug = prioridade_de_gut(
            self.gut_exec_gravidade, self.gut_exec_urgencia, self.gut_exec_tendencia
        )
        return PRIORIDADES_LABELS.get(slug, slug)

    @property
    def gut_executante_prioridade_badge(self):
        if not self.gut_executante_preenchido:
            return 'secondary'
        slug = prioridade_de_gut(
            self.gut_exec_gravidade, self.gut_exec_urgencia, self.gut_exec_tendencia
        )
        return PRIORIDADES_BADGE.get(slug, 'secondary')

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

    @property
    def sa_gut_score(self):
        if not all([self.sa_gravidade, self.sa_urgencia, self.sa_tendencia]):
            return None
        return self.sa_gravidade * self.sa_urgencia * self.sa_tendencia

    @property
    def sa_gut_label(self):
        if not all([self.sa_gravidade, self.sa_urgencia, self.sa_tendencia]):
            return None
        return f'G{self.sa_gravidade} U{self.sa_urgencia} T{self.sa_tendencia}'

    @property
    def sa_gut_prioridade(self):
        """Alias legado — mesma prioridade final (3 níveis GUT)."""
        slug = normalizar_prioridade(self.prioridade)
        return {
            'texto': self.prioridade_label,
            'cls': f'bg-{self.prioridade_badge}',
        }

    @property
    def sa_gravidade_label(self):
        from app.models.planejamento import GUT_GRAVIDADE
        return GUT_GRAVIDADE.get(self.sa_gravidade, '—') if self.sa_gravidade else '—'

    @property
    def sa_urgencia_label(self):
        from app.models.planejamento import GUT_URGENCIA
        return GUT_URGENCIA.get(self.sa_urgencia, '—') if self.sa_urgencia else '—'

    @property
    def sa_tendencia_label(self):
        from app.models.planejamento import GUT_TENDENCIA
        return GUT_TENDENCIA.get(self.sa_tendencia, '—') if self.sa_tendencia else '—'

    @property
    def ultimo_historico(self):
        return self.historico.order_by(ChamadoHistorico.criado_em.desc()).first()

    @property
    def solicitante_nome(self):
        if self.solicitante:
            return self.solicitante.nome
        return self.externo_nome or '—'

    @property
    def aberto_por_externo(self):
        return self.aberto_por is None and bool(self.externo_nome)

    @property
    def ultimo_editor(self):
        h = self.ultimo_historico
        if h and h.usuario:
            return h.usuario
        return self.solicitante

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


# Motivos para itens de solicitação de equipamento
MOTIVOS_SOLICITACAO = [
    ('ampliacao', 'Ampliação de serviço'),
    ('substituicao', 'Substituição de equipamento'),
]
MOTIVOS_SOLICITACAO_LABELS = dict(MOTIVOS_SOLICITACAO)


class ChamadoSolicitacaoItem(db.Model):
    """Item de solicitação de equipamento (sala, motivo, equipamento a substituir, observação)."""
    __tablename__ = 'chamado_solicitacao_itens'

    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamados.id', ondelete='CASCADE'), nullable=False)
    sala_id = db.Column(db.Integer, db.ForeignKey('salas.id', ondelete='SET NULL'))
    motivo = db.Column(db.String(20), nullable=False, default='ampliacao')  # ampliacao | substituicao
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamentos.id', ondelete='SET NULL'))  # se substituicao
    observacao = db.Column(db.Text)

    chamado = db.relationship('Chamado', back_populates='itens_solicitacao')
    sala = db.relationship('Sala', foreign_keys=[sala_id])
    equipamento = db.relationship('Equipamento', foreign_keys=[equipamento_id])

    @property
    def motivo_label(self):
        return MOTIVOS_SOLICITACAO_LABELS.get(self.motivo, self.motivo)


TIPOS_ANDAMENTO = [
    ('andamento',        'Andamento'),
    ('pedido_info',      'Pedido de Informação'),
    ('alerta',           'Alerta / Pendência'),
    ('nota_encerramento','Nota de Encerramento'),
]
TIPOS_ANDAMENTO_LABELS = {k: v for k, v in TIPOS_ANDAMENTO}
TIPOS_ANDAMENTO_ICONE = {
    'andamento':         'fas fa-comment',
    'pedido_info':       'fas fa-question-circle',
    'alerta':            'fas fa-exclamation-triangle',
    'nota_encerramento': 'fas fa-file-check',
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
        return TIPOS_ANDAMENTO_ICONE.get(self.tipo_andamento, 'fas fa-comment')

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
            return 'fas fa-file-image'
        if self.is_video:
            return 'fas fa-video'
        if self.is_pdf:
            return 'fas fa-file-pdf'
        return 'fas fa-paperclip'

    @property
    def tamanho_fmt(self):
        if not self.tamanho_bytes:
            return ''
        kb = self.tamanho_bytes / 1024
        if kb < 1024:
            return f'{kb:.0f} KB'
        return f'{kb/1024:.1f} MB'


class ChamadoAtribuido(db.Model):
    """Profissionais da unidade demandada que tratam o chamado."""
    __tablename__ = 'chamado_atribuidos'

    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamados.id', ondelete='CASCADE'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    atribuido_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    chamado = db.relationship('Chamado', back_populates='atribuidos_rel')
    usuario = db.relationship('Usuario')

    __table_args__ = (db.UniqueConstraint('chamado_id', 'usuario_id'),)
