# -*- coding: utf-8 -*-
"""Segurança do Paciente — notificações internas do NSP da unidade.

Inspirado no MedicSys (Eventos Adversos) e na RDC 36/2013 / ICPS-OMS / NT Anvisa 09/2025.
Os selects vêm de nsp_catalogos e são gerenciados em Configurações.
"""
from datetime import datetime
from app import db
from app.utils import prefixed_static_url


GRUPOS_CATALOGO = [
    ('status', 'Status da ocorrência'),
    ('classificacao', 'Classificação da ocorrência'),
    ('tipo_incidente', 'Tipo de incidente'),
    ('tipo_setor', 'Tipo de setor'),
    ('setor', 'Setor'),
    ('departamento', 'Departamento'),
    ('tipo_pessoa', 'Tipo de pessoa afetada'),
    ('setor_destino', 'Destino de encaminhamento'),
]
GRUPOS_LABELS = dict(GRUPOS_CATALOGO)

BADGE_CORES = [
    ('danger', 'Vermelho'),
    ('warning', 'Amarelo'),
    ('info', 'Azul claro'),
    ('primary', 'Azul'),
    ('success', 'Verde'),
    ('secondary', 'Cinza'),
    ('dark', 'Preto'),
]

TIPOS_ANDAMENTO = {
    'registro': 'Registro',
    'comentario': 'Comentário',
    'analise': 'Análise / investigação',
    'encaminhamento': 'Encaminhamento',
    'status': 'Mudança de status',
    'anexo': 'Anexo',
    'acao': 'Plano de ação',
    'notivisa': 'Notivisa',
}

# Seed inicial (grupo, slug, nome, ordem, cor, exige_texto, never_event, encerra, padrao)
CATALOGOS_INICIAIS = [
    # Status
    ('status', 'aberto', 'Aberto', 1, 'danger', False, False, False, True),
    ('status', 'em_analise', 'Em análise', 2, 'warning', False, False, False, True),
    ('status', 'encaminhado', 'Encaminhado', 3, 'info', False, False, False, True),
    ('status', 'plano_acao', 'Plano de ação', 4, 'primary', False, False, False, True),
    ('status', 'concluido', 'Concluído', 5, 'success', False, False, True, False),
    ('status', 'arquivado', 'Arquivado', 6, 'secondary', False, False, True, False),
    # Classificação (MedicSys + ICPS)
    ('classificacao', 'circunstancia_risco', 'Circunstância de risco', 1, 'secondary', False, False, False, False),
    ('classificacao', 'near_miss', 'Quase erro', 2, 'info', False, False, False, False),
    ('classificacao', 'nao_conformidade', 'Não conformidade', 3, 'dark', False, False, False, False),
    ('classificacao', 'sem_dano', 'Sem dano', 4, 'success', False, False, False, False),
    ('classificacao', 'dano_leve', 'Dano leve', 5, 'primary', False, False, False, False),
    ('classificacao', 'dano_moderado', 'Dano moderado', 6, 'warning', False, False, False, False),
    ('classificacao', 'dano_grave', 'Dano grave', 7, 'danger', False, False, False, False),
    ('classificacao', 'obito', 'Óbito', 8, 'danger', False, False, False, False),
    # Tipo de incidente (ICPS-OMS / Anvisa, adaptado à APS)
    ('tipo_incidente', 'medicacao', 'Erro / falha de medicação', 1, 'danger', False, False, False, False),
    ('tipo_incidente', 'imunizacao', 'Erro de imunização / vacinação', 2, 'danger', False, False, False, False),
    ('tipo_incidente', 'queda', 'Queda', 3, 'warning', False, False, False, False),
    ('tipo_incidente', 'identificacao', 'Falha de identificação do paciente', 4, 'warning', False, False, False, False),
    ('tipo_incidente', 'comunicacao', 'Falha de comunicação', 5, 'info', False, False, False, False),
    ('tipo_incidente', 'processo_clinico', 'Falha em processo ou procedimento clínico', 6, 'primary', False, False, False, False),
    ('tipo_incidente', 'equipamento', 'Falha de equipamento / dispositivo', 7, 'secondary', False, False, False, False),
    ('tipo_incidente', 'sistema_energia', 'Falta de sistema, energia ou internet', 8, 'dark', False, False, False, False),
    ('tipo_incidente', 'infraestrutura', 'Infraestrutura / instalações (água, estrutura)', 9, 'secondary', False, False, False, False),
    ('tipo_incidente', 'recursos', 'Recursos / gestão organizacional', 10, 'warning', False, False, False, False),
    ('tipo_incidente', 'amostra', 'Perda, troca ou extravio de amostra', 11, 'info', False, False, False, False),
    ('tipo_incidente', 'documentacao', 'Falha de documentação / prontuário', 12, 'secondary', False, False, False, False),
    ('tipo_incidente', 'atraso', 'Atraso no atendimento', 13, 'warning', False, False, False, False),
    ('tipo_incidente', 'violencia', 'Violência / agressão', 14, 'danger', False, False, False, False),
    ('tipo_incidente', 'fuga', 'Fuga / evasão', 15, 'danger', False, True, False, False),
    ('tipo_incidente', 'queimadura', 'Queimadura / mecanismo térmico', 16, 'danger', False, True, False, False),
    ('tipo_incidente', 'lesao_pressao', 'Lesão por pressão', 17, 'warning', False, False, False, False),
    ('tipo_incidente', 'outro', 'Outro', 99, 'secondary', True, False, False, False),
    # Tipo de setor (MedicSys)
    ('tipo_setor', 'administrativo', 'Administrativo', 1, 'secondary', False, False, False, False),
    ('tipo_setor', 'assistencial', 'Assistencial', 2, 'primary', False, False, False, False),
    # Setores típicos de UBS/USF/UPA
    ('setor', 'recepcao', 'Recepção', 1, 'secondary', False, False, False, False),
    ('setor', 'acolhimento', 'Acolhimento / triagem', 2, 'info', False, False, False, False),
    ('setor', 'consultorio_medico', 'Consultório médico', 3, 'primary', False, False, False, False),
    ('setor', 'consultorio_enfermagem', 'Consultório de enfermagem', 4, 'primary', False, False, False, False),
    ('setor', 'vacina', 'Sala de vacina', 5, 'success', False, False, False, False),
    ('setor', 'curativo', 'Sala de curativo', 6, 'warning', False, False, False, False),
    ('setor', 'farmacia', 'Farmácia', 7, 'info', False, False, False, False),
    ('setor', 'odontologia', 'Odontologia', 8, 'primary', False, False, False, False),
    ('setor', 'coleta', 'Coleta / laboratório', 9, 'secondary', False, False, False, False),
    ('setor', 'observacao', 'Observação', 10, 'warning', False, False, False, False),
    ('setor', 'urgencia', 'Urgência / emergência', 11, 'danger', False, False, False, False),
    ('setor', 'administracao', 'Administração', 12, 'dark', False, False, False, False),
    ('setor', 'almoxarifado', 'Almoxarifado', 13, 'secondary', False, False, False, False),
    ('setor', 'higienizacao', 'Higienização', 14, 'secondary', False, False, False, False),
    ('setor', 'outro', 'Outro', 99, 'secondary', True, False, False, False),
    # Departamento
    ('departamento', 'aps', 'Atenção primária', 1, 'primary', False, False, False, False),
    ('departamento', 'urgencia', 'Urgência e emergência', 2, 'danger', False, False, False, False),
    ('departamento', 'saude_bucal', 'Saúde bucal', 3, 'info', False, False, False, False),
    ('departamento', 'farmacia', 'Farmácia', 4, 'success', False, False, False, False),
    ('departamento', 'vigilancia', 'Vigilância em saúde', 5, 'warning', False, False, False, False),
    ('departamento', 'administracao', 'Administração', 6, 'secondary', False, False, False, False),
    ('departamento', 'outro', 'Outro', 99, 'secondary', True, False, False, False),
    # Tipo de pessoa (MedicSys)
    ('tipo_pessoa', 'paciente', 'Paciente', 1, 'primary', False, False, False, False),
    ('tipo_pessoa', 'acompanhante', 'Acompanhante', 2, 'info', False, False, False, False),
    ('tipo_pessoa', 'colaborador', 'Colaborador', 3, 'warning', False, False, False, False),
    ('tipo_pessoa', 'visitante', 'Visitante', 4, 'secondary', False, False, False, False),
    ('tipo_pessoa', 'outros', 'Outros', 99, 'secondary', True, False, False, False),
    # Destinos de encaminhamento
    ('setor_destino', 'nsp_unidade', 'NSP da unidade', 1, 'primary', False, False, False, False),
    ('setor_destino', 'coordenacao', 'Coordenação da unidade', 2, 'info', False, False, False, False),
    ('setor_destino', 'nsp_central', 'NSP central / qualidade', 3, 'dark', False, False, False, False),
    ('setor_destino', 'vigilancia_saude', 'Vigilância em saúde', 4, 'warning', False, False, False, False),
    ('setor_destino', 'farmacia_central', 'Farmácia central', 5, 'success', False, False, False, False),
    ('setor_destino', 'diretoria', 'Diretoria / gestão', 6, 'danger', False, False, False, False),
    ('setor_destino', 'visa', 'Vigilância sanitária', 7, 'warning', False, False, False, False),
    ('setor_destino', 'outro', 'Outro', 99, 'secondary', True, False, False, False),
]


class NspCatalogo(db.Model):
    """Opção configurável dos selects da Segurança do Paciente."""
    __tablename__ = 'nsp_catalogos'
    __table_args__ = (
        db.UniqueConstraint('grupo', 'slug', name='uq_nsp_catalogo_grupo_slug'),
    )

    id = db.Column(db.Integer, primary_key=True)
    grupo = db.Column(db.String(40), nullable=False, index=True)
    slug = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text)
    ordem = db.Column(db.Integer, nullable=False, default=0)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    cor = db.Column(db.String(20), nullable=False, default='secondary')
    exige_texto = db.Column(db.Boolean, nullable=False, default=False)
    never_event = db.Column(db.Boolean, nullable=False, default=False)
    encerra = db.Column(db.Boolean, nullable=False, default=False)
    padrao = db.Column(db.Boolean, nullable=False, default=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<NspCatalogo {self.grupo}:{self.slug}>'

    @classmethod
    def ativos(cls, grupo):
        return cls.query.filter_by(grupo=grupo, ativo=True).order_by(cls.ordem, cls.nome).all()

    @classmethod
    def por_slug(cls, grupo, slug):
        return cls.query.filter_by(grupo=grupo, slug=slug).first()

    @property
    def grupo_label(self):
        return GRUPOS_LABELS.get(self.grupo, self.grupo)


class NspOcorrencia(db.Model):
    """Notificação de incidente / evento adverso da unidade."""
    __tablename__ = 'nsp_ocorrencias'

    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(20), nullable=False, unique=True, index=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='CASCADE'), nullable=False, index=True)

    notificante_nome = db.Column(db.String(150), nullable=False)
    tipo_setor_notificante_id = db.Column(db.Integer, db.ForeignKey('nsp_catalogos.id', ondelete='SET NULL'))
    setor_notificante_id = db.Column(db.Integer, db.ForeignKey('nsp_catalogos.id', ondelete='SET NULL'))
    setor_notificante_outro = db.Column(db.String(150))

    nome_afetado = db.Column(db.String(150))
    data_nascimento = db.Column(db.Date)
    prontuario = db.Column(db.String(40))
    cpf = db.Column(db.String(14))
    cns = db.Column(db.String(20))
    tipo_pessoa_id = db.Column(db.Integer, db.ForeignKey('nsp_catalogos.id', ondelete='SET NULL'))
    tipo_pessoa_outro = db.Column(db.String(150))

    data_ocorrencia = db.Column(db.Date, nullable=False)
    hora_ocorrencia = db.Column(db.Time)

    tipo_setor_ocorrencia_id = db.Column(db.Integer, db.ForeignKey('nsp_catalogos.id', ondelete='SET NULL'))
    setor_ocorrencia_id = db.Column(db.Integer, db.ForeignKey('nsp_catalogos.id', ondelete='SET NULL'))
    setor_ocorrencia_outro = db.Column(db.String(150))
    departamento_id = db.Column(db.Integer, db.ForeignKey('nsp_catalogos.id', ondelete='SET NULL'))
    tipo_incidente_id = db.Column(db.Integer, db.ForeignKey('nsp_catalogos.id', ondelete='SET NULL'))
    classificacao_id = db.Column(db.Integer, db.ForeignKey('nsp_catalogos.id', ondelete='SET NULL'))
    never_event = db.Column(db.Boolean, nullable=False, default=False)

    descricao = db.Column(db.Text, nullable=False)
    acao_imediata = db.Column(db.Text, nullable=False)

    tipo_setor_notificado_id = db.Column(db.Integer, db.ForeignKey('nsp_catalogos.id', ondelete='SET NULL'))
    setor_notificado_id = db.Column(db.Integer, db.ForeignKey('nsp_catalogos.id', ondelete='SET NULL'))
    setor_notificado_outro = db.Column(db.String(150))

    status_id = db.Column(db.Integer, db.ForeignKey('nsp_catalogos.id', ondelete='SET NULL'), index=True)
    responsavel_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))

    fatores_contribuintes = db.Column(db.Text)
    consequencias_organizacionais = db.Column(db.Text)
    deteccao = db.Column(db.Text)
    fatores_atenuantes = db.Column(db.Text)
    acoes_melhoria = db.Column(db.Text)
    acoes_reducao_risco = db.Column(db.Text)
    analise_resumo = db.Column(db.Text)
    analise_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    analise_em = db.Column(db.DateTime)

    notivisa_notificado = db.Column(db.Boolean, nullable=False, default=False)
    notivisa_numero = db.Column(db.String(40))
    notivisa_em = db.Column(db.Date)

    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    encerrado_em = db.Column(db.DateTime)

    unidade = db.relationship('Unidade', foreign_keys=[unidade_id])
    tipo_setor_notificante = db.relationship('NspCatalogo', foreign_keys=[tipo_setor_notificante_id])
    setor_notificante = db.relationship('NspCatalogo', foreign_keys=[setor_notificante_id])
    tipo_pessoa = db.relationship('NspCatalogo', foreign_keys=[tipo_pessoa_id])
    tipo_setor_ocorrencia = db.relationship('NspCatalogo', foreign_keys=[tipo_setor_ocorrencia_id])
    setor_ocorrencia = db.relationship('NspCatalogo', foreign_keys=[setor_ocorrencia_id])
    departamento = db.relationship('NspCatalogo', foreign_keys=[departamento_id])
    tipo_incidente = db.relationship('NspCatalogo', foreign_keys=[tipo_incidente_id])
    classificacao = db.relationship('NspCatalogo', foreign_keys=[classificacao_id])
    tipo_setor_notificado = db.relationship('NspCatalogo', foreign_keys=[tipo_setor_notificado_id])
    setor_notificado = db.relationship('NspCatalogo', foreign_keys=[setor_notificado_id])
    status = db.relationship('NspCatalogo', foreign_keys=[status_id])
    responsavel = db.relationship('Usuario', foreign_keys=[responsavel_id])
    autor = db.relationship('Usuario', foreign_keys=[criado_por])
    analista = db.relationship('Usuario', foreign_keys=[analise_por])
    anexos = db.relationship('NspAnexo', back_populates='ocorrencia', cascade='all, delete-orphan',
                             order_by='NspAnexo.criado_em')
    andamentos = db.relationship('NspAndamento', back_populates='ocorrencia', cascade='all, delete-orphan',
                                 order_by='NspAndamento.criado_em.desc()')
    encaminhamentos = db.relationship('NspEncaminhamento', back_populates='ocorrencia', cascade='all, delete-orphan',
                                      order_by='NspEncaminhamento.criado_em.desc()')
    acoes = db.relationship('NspAcao', back_populates='ocorrencia', cascade='all, delete-orphan',
                            order_by='NspAcao.prazo')

    def __repr__(self):
        return f'<NspOcorrencia {self.protocolo}>'

    @property
    def encerrada(self):
        return bool(self.status and self.status.encerra)

    @property
    def classificacao_nome(self):
        return self.classificacao.nome if self.classificacao else '—'

    @property
    def classificacao_cor(self):
        return (self.classificacao.cor if self.classificacao else 'secondary') or 'secondary'

    @property
    def status_nome(self):
        return self.status.nome if self.status else '—'

    @property
    def status_cor(self):
        return (self.status.cor if self.status else 'secondary') or 'secondary'

    @property
    def tipo_incidente_nome(self):
        return self.tipo_incidente.nome if self.tipo_incidente else '—'

    @property
    def setor_ocorrencia_nome(self):
        if self.setor_ocorrencia and self.setor_ocorrencia.exige_texto and self.setor_ocorrencia_outro:
            return self.setor_ocorrencia_outro
        if self.setor_ocorrencia:
            return self.setor_ocorrencia.nome
        return self.setor_ocorrencia_outro or '—'

    @property
    def exige_investigacao(self):
        slug = self.classificacao.slug if self.classificacao else ''
        return self.never_event or slug in ('obito', 'dano_grave')

    @property
    def investigacao_preenchida(self):
        campos = (
            self.fatores_contribuintes, self.consequencias_organizacionais, self.deteccao,
            self.fatores_atenuantes, self.acoes_melhoria, self.acoes_reducao_risco,
        )
        return all(bool(c and c.strip()) for c in campos)


class NspAnexo(db.Model):
    __tablename__ = 'nsp_anexos'

    id = db.Column(db.Integer, primary_key=True)
    ocorrencia_id = db.Column(db.Integer, db.ForeignKey('nsp_ocorrencias.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(80), nullable=False)
    original = db.Column(db.String(200))
    mime_type = db.Column(db.String(100))
    tamanho_bytes = db.Column(db.Integer)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    ocorrencia = db.relationship('NspOcorrencia', back_populates='anexos')
    autor = db.relationship('Usuario', foreign_keys=[criado_por])

    @property
    def url(self):
        return prefixed_static_url(f'/static/uploads/nsp/{self.filename}')

    @property
    def is_image(self):
        return (self.mime_type or '').startswith('image/')

    @property
    def tamanho_label(self):
        n = self.tamanho_bytes or 0
        if n < 1024:
            return f'{n} B'
        if n < 1024 * 1024:
            return f'{n / 1024:.0f} KB'
        return f'{n / (1024 * 1024):.1f} MB'


class NspAndamento(db.Model):
    __tablename__ = 'nsp_andamentos'

    id = db.Column(db.Integer, primary_key=True)
    ocorrencia_id = db.Column(db.Integer, db.ForeignKey('nsp_ocorrencias.id', ondelete='CASCADE'), nullable=False, index=True)
    tipo = db.Column(db.String(30), nullable=False, default='comentario')
    texto = db.Column(db.Text, nullable=False)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    ocorrencia = db.relationship('NspOcorrencia', back_populates='andamentos')
    autor = db.relationship('Usuario', foreign_keys=[criado_por])

    @property
    def tipo_label(self):
        return TIPOS_ANDAMENTO.get(self.tipo, self.tipo)


class NspEncaminhamento(db.Model):
    __tablename__ = 'nsp_encaminhamentos'

    id = db.Column(db.Integer, primary_key=True)
    ocorrencia_id = db.Column(db.Integer, db.ForeignKey('nsp_ocorrencias.id', ondelete='CASCADE'), nullable=False, index=True)
    destino_id = db.Column(db.Integer, db.ForeignKey('nsp_catalogos.id', ondelete='SET NULL'))
    destino_outro = db.Column(db.String(150))
    unidade_destino_id = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='SET NULL'))
    texto = db.Column(db.Text)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    ocorrencia = db.relationship('NspOcorrencia', back_populates='encaminhamentos')
    destino = db.relationship('NspCatalogo', foreign_keys=[destino_id])
    unidade_destino = db.relationship('Unidade', foreign_keys=[unidade_destino_id])
    autor = db.relationship('Usuario', foreign_keys=[criado_por])

    @property
    def destino_nome(self):
        if self.destino and self.destino.exige_texto and self.destino_outro:
            return self.destino_outro
        if self.destino:
            return self.destino.nome
        return self.destino_outro or '—'


class NspAcao(db.Model):
    __tablename__ = 'nsp_acoes'

    id = db.Column(db.Integer, primary_key=True)
    ocorrencia_id = db.Column(db.Integer, db.ForeignKey('nsp_ocorrencias.id', ondelete='CASCADE'), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    responsavel_nome = db.Column(db.String(150))
    prazo = db.Column(db.Date)
    concluida = db.Column(db.Boolean, nullable=False, default=False)
    concluida_em = db.Column(db.DateTime)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    ocorrencia = db.relationship('NspOcorrencia', back_populates='acoes')
    autor = db.relationship('Usuario', foreign_keys=[criado_por])
