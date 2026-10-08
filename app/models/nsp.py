# -*- coding: utf-8 -*-
"""Segurança do Paciente — notificação e gestão de incidentes (SNI-SGQSP).

Fluxo do Regimento Interno do SGQSP (RI-SGQSP-001): a notificação vai primeiro ao
Núcleo de Segurança do Paciente, que qualifica e encaminha às comissões das unidades.
A coordenação da unidade só vê o caso se o Núcleo liberar. Cultura justa e não punitiva
(Art. 8º, VI e Art. 82): a notificação pode ser anônima e nunca guarda quem a registrou.
"""
from datetime import datetime
from app import db
from app.utils import prefixed_static_url, agora_local


TIPOLOGIAS = ['Atenção Primária', 'Urgência e Emergência', 'Atenção Especializada',
              'Atenção Psicossocial', 'Atenção Domiciliar']
TURNOS = ['Manhã', 'Tarde', 'Noite', 'Plantão noturno']
FAIXAS_ETARIAS = ['0-1', '2-11', '12-17', '18-59', '60+']
CLASSIFICACOES = ['Circunstância notificável', 'Quase falha (near miss)', 'Incidente sem dano',
                  'Incidente com dano / evento adverso', 'Evento sentinela']
GRAUS_DANO = ['Sem dano', 'Leve', 'Moderado', 'Grave', 'Óbito']
CRITICIDADES = ['Baixa', 'Moderada', 'Alta', 'Crítica']
METODOLOGIAS = ['Análise de barreiras', '5 Porquês', 'Ishikawa', 'Análise de causa raiz', 'Revisão de processo']
INV_STATUS = ['Não iniciada', 'Em investigação', 'Concluída']
ACAO_STATUS = ['Aberta', 'Em andamento', 'Concluída']

ETAPAS = [
    ('em_qualificacao', 'Em qualificação', 'warning'),
    ('qualificada', 'Qualificada', 'info'),
    ('encaminhada', 'Encaminhada', 'primary'),
    ('em_investigacao', 'Em investigação', 'danger'),
    ('concluida', 'Concluída', 'success'),
    ('arquivada', 'Arquivada', 'secondary'),
]
ETAPAS_LABEL = {s: l for s, l, _ in ETAPAS}
ETAPAS_COR = {s: c for s, _, c in ETAPAS}
ETAPAS_ENCERRADAS = ('concluida', 'arquivada')

CRITICIDADE_COR = {'Baixa': 'success', 'Moderada': 'warning', 'Alta': 'danger', 'Crítica': 'danger'}


def sugestao_preliminar(descricao, acoes):
    """Apoio técnico à qualificação (não substitui a análise humana do Núcleo)."""
    t = f'{descricao or ""} {acoes or ""}'.lower()
    if any(p in t for p in ('quase', 'interceptad', 'não chegou', 'nao chegou')):
        return {'classificacao': 'Quase falha (near miss)', 'dano': 'Sem dano', 'criticidade': 'Moderada',
                'investigar': 'Avaliar'}
    if any(p in t for p in ('óbito', 'obito', 'morte', 'grave', 'dano', 'lesão', 'lesao')):
        alta = any(p in t for p in ('óbito', 'obito', 'morte', 'grave'))
        return {'classificacao': 'Incidente com dano / evento adverso', 'dano': 'Validar',
                'criticidade': 'Alta' if alta else 'Moderada', 'investigar': 'Sim'}
    return {'classificacao': 'Incidente sem dano ou circunstância notificável', 'dano': 'Pendente',
            'criticidade': 'Baixa', 'investigar': 'Avaliar'}


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
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local)

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
    """Notificação de incidente; unidade_id é a unidade notificante."""
    __tablename__ = 'nsp_ocorrencias'

    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(20), nullable=False, unique=True, index=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='CASCADE'), nullable=False, index=True)

    etapa = db.Column(db.String(20), nullable=False, default='em_qualificacao', index=True)
    origem = db.Column(db.String(10), nullable=False, default='sigus')
    anonimo = db.Column(db.Boolean, nullable=False, default=True)
    tipologia = db.Column(db.String(60))
    local_incidente = db.Column(db.String(150))
    turno = db.Column(db.String(30))
    ocorrencia_em = db.Column(db.DateTime)
    identificacao_em = db.Column(db.DateTime)
    paciente_codigo = db.Column(db.String(60))
    faixa_etaria = db.Column(db.String(10))
    notificante_cargo = db.Column(db.String(120))

    qual_classificacao = db.Column(db.String(60))
    qual_dano = db.Column(db.String(20))
    qual_criticidade = db.Column(db.String(20))
    qual_diagnostico = db.Column(db.Text)
    qual_fundamentacao = db.Column(db.Text)
    qualificado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    qualificado_em = db.Column(db.DateTime)

    inv_metodologia = db.Column(db.String(40))
    inv_status = db.Column(db.String(20))
    inv_barreiras = db.Column(db.Text)
    inv_causas = db.Column(db.Text)
    inv_conclusao = db.Column(db.Text)
    inv_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    inv_em = db.Column(db.DateTime)

    notificante_nome = db.Column(db.String(150))
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
    acao_imediata = db.Column(db.Text)

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
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=agora_local, onupdate=agora_local)
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
    qualificador = db.relationship('Usuario', foreign_keys=[qualificado_por])
    investigador = db.relationship('Usuario', foreign_keys=[inv_por])
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
        return self.etapa in ETAPAS_ENCERRADAS

    @property
    def etapa_label(self):
        return ETAPAS_LABEL.get(self.etapa, self.etapa or '—')

    @property
    def etapa_cor(self):
        return ETAPAS_COR.get(self.etapa, 'secondary')

    @property
    def criticidade_label(self):
        return self.qual_criticidade or 'Pendente'

    @property
    def criticidade_cor(self):
        return CRITICIDADE_COR.get(self.qual_criticidade, 'secondary')

    @property
    def data_referencia(self):
        return self.ocorrencia_em or self.criado_em

    @property
    def unidades_encaminhadas(self):
        vistos, lista = set(), []
        for e in sorted(self.encaminhamentos, key=lambda x: x.criado_em or datetime.min):
            if e.unidade_destino_id and e.unidade_destino_id not in vistos:
                vistos.add(e.unidade_destino_id)
                lista.append(e)
        return lista

    @property
    def acoes_vencidas(self):
        from app.utils import hoje_brasilia
        hoje = hoje_brasilia()
        return [a for a in self.acoes if a.prazo and a.prazo < hoje and a.status_label != 'Concluída']

    @property
    def tem_dados_paciente(self):
        return any((self.nome_afetado, self.data_nascimento, self.prontuario, self.cpf, self.cns))

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
        return (self.never_event or self.qual_dano in ('Grave', 'Óbito')
                or self.qual_classificacao == 'Evento sentinela'
                or self.qual_criticidade == 'Crítica')

    @property
    def investigacao_preenchida(self):
        return self.inv_status == 'Concluída' and bool((self.inv_conclusao or '').strip())


class NspAnexo(db.Model):
    __tablename__ = 'nsp_anexos'

    id = db.Column(db.Integer, primary_key=True)
    ocorrencia_id = db.Column(db.Integer, db.ForeignKey('nsp_ocorrencias.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(80), nullable=False)
    original = db.Column(db.String(200))
    mime_type = db.Column(db.String(100))
    tamanho_bytes = db.Column(db.Integer)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local)

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
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local)

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
    liberado_coordenacao = db.Column(db.Boolean, nullable=False, default=False)
    liberado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    liberado_em = db.Column(db.DateTime)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local)

    ocorrencia = db.relationship('NspOcorrencia', back_populates='encaminhamentos')
    destino = db.relationship('NspCatalogo', foreign_keys=[destino_id])
    unidade_destino = db.relationship('Unidade', foreign_keys=[unidade_destino_id])
    autor = db.relationship('Usuario', foreign_keys=[criado_por])
    liberador = db.relationship('Usuario', foreign_keys=[liberado_por])

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
    indicador = db.Column(db.String(255))
    status = db.Column(db.String(20))
    concluida = db.Column(db.Boolean, nullable=False, default=False)
    concluida_em = db.Column(db.DateTime)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local)

    ocorrencia = db.relationship('NspOcorrencia', back_populates='acoes')
    autor = db.relationship('Usuario', foreign_keys=[criado_por])

    @property
    def status_label(self):
        if self.status:
            return self.status
        return 'Concluída' if self.concluida else 'Aberta'

    @property
    def vencida(self):
        from app.utils import hoje_brasilia
        return bool(self.prazo and self.prazo < hoje_brasilia() and self.status_label != 'Concluída')


class NspMembro(db.Model):
    """Quem atua na Segurança do Paciente: Núcleo (rede toda) ou comissão de uma unidade."""
    __tablename__ = 'nsp_membros'
    __table_args__ = (
        db.UniqueConstraint('usuario_id', 'papel', 'unidade_id', name='uq_nsp_membro'),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, index=True)
    papel = db.Column(db.String(20), nullable=False)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='CASCADE'), index=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local)

    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    unidade = db.relationship('Unidade', foreign_keys=[unidade_id])

    PAPEIS = {'nucleo': 'Núcleo de Segurança do Paciente', 'comissao': 'Comissão da unidade'}

    @property
    def papel_label(self):
        return self.PAPEIS.get(self.papel, self.papel)


def eh_nucleo(usuario):
    if not getattr(usuario, 'is_authenticated', False):
        return False
    return db.session.query(NspMembro.id).filter_by(
        usuario_id=usuario.id, papel='nucleo', ativo=True).first() is not None


def unidades_comissao(usuario):
    if not getattr(usuario, 'is_authenticated', False):
        return set()
    rows = db.session.query(NspMembro.unidade_id).filter(
        NspMembro.usuario_id == usuario.id, NspMembro.papel == 'comissao',
        NspMembro.ativo.is_(True), NspMembro.unidade_id.isnot(None)).all()
    return {r[0] for r in rows}


def unidades_coordenacao(usuario):
    """Unidades em que o usuário é coordenação: gestor principal/secundário ou perfil Gestor de Área vinculado."""
    if not getattr(usuario, 'is_authenticated', False):
        return set()
    from app.models.unidade import UsuarioUnidade
    q = db.session.query(UsuarioUnidade.unidade_id).filter(
        UsuarioUnidade.usuario_id == usuario.id, UsuarioUnidade.ativo.is_(True))
    if usuario.perfil != 'coordenador':
        q = q.filter(UsuarioUnidade.papel.in_(['gestor_principal', 'gestor_secundario']))
    return {r[0] for r in q.all()}
