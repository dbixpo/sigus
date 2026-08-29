from datetime import datetime
from app import db

STATUS_TRANSFERENCIA = {
    'pendente':  ('Aguardando aceite', 'warning'),
    'aceita':    ('Aceita',            'success'),
    'recusada':  ('Recusada',          'danger'),
    'cancelada': ('Cancelada',         'secondary'),
}

TIPO_DOCUMENTO = {
    'doacao':        'Doação',
    'emprestimo':    'Empréstimo',
    'transferencia': 'Transferência',
}

TIPO_TITULO_IMPRESSAO = {
    'doacao':        'TERMO DE DOAÇÃO DE EQUIPAMENTO',
    'emprestimo':    'TERMO DE EMPRÉSTIMO DE EQUIPAMENTO',
    'transferencia': 'TERMO DE TRANSFERÊNCIA DE EQUIPAMENTO',
}

CLASSIFICACAO_ITEM = {
    'A': 'Os materiais estão inservíveis a este setor, porém tem plenas condições de uso.',
    'B': 'Os materiais estão inservíveis a este setor e tem condições de uso, porém necessita de reparos.',
}


class HistoricoEquipamento(db.Model):
    """Registro imutável de eventos de ciclo de vida de um equipamento
    (transferências, baixas, alterações de status, etc.)."""
    __tablename__ = 'historico_equipamento'

    id             = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamentos.id', ondelete='CASCADE'), nullable=False)
    usuario_id     = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    acao           = db.Column(db.String(300), nullable=False)
    observacao     = db.Column(db.Text)
    criado_em      = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    equipamento = db.relationship('Equipamento', back_populates='historico')
    usuario     = db.relationship('Usuario')

    def __repr__(self):
        return f'<HistoricoEquipamento equip={self.equipamento_id} acao={self.acao[:30]}>'


# alias interno usado pelo blueprint de transferências
_HistoricoMovimentacao = HistoricoEquipamento


class DocumentoTransferencia(db.Model):
    """Termo de Transferência ou Empréstimo — documento com múltiplos itens entre unidades."""
    __tablename__ = 'documentos_transferencia'

    id                  = db.Column(db.Integer, primary_key=True)
    tipo                = db.Column(db.String(20), nullable=False)  # emprestimo | transferencia
    unidade_origem_id   = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='RESTRICT'), nullable=False)
    unidade_destino_id  = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='RESTRICT'), nullable=False)
    criado_por          = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    aceito_por          = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    sala_destino_id     = db.Column(db.Integer, db.ForeignKey('salas.id', ondelete='SET NULL'))
    status              = db.Column(db.String(20), nullable=False, default='pendente')
    observacao          = db.Column(db.Text)
    observacao_aceite   = db.Column(db.Text)
    criado_em           = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resolvido_em        = db.Column(db.DateTime)

    unidade_origem   = db.relationship('Unidade', foreign_keys=[unidade_origem_id])
    unidade_destino  = db.relationship('Unidade', foreign_keys=[unidade_destino_id])
    criador          = db.relationship('Usuario', foreign_keys=[criado_por])
    aceitador        = db.relationship('Usuario', foreign_keys=[aceito_por])
    sala_destino     = db.relationship('Sala', foreign_keys=[sala_destino_id])
    itens            = db.relationship('ItemDocumentoTransferencia', back_populates='documento',
                                       lazy='dynamic', cascade='all, delete-orphan')

    @property
    def tipo_label(self):
        # Documentos antigos da Lojinha tinham tipo=transferencia
        if self.tipo == 'transferencia' and self.observacao and 'Lojinha' in (self.observacao or ''):
            return TIPO_DOCUMENTO['doacao']
        return TIPO_DOCUMENTO.get(self.tipo, self.tipo)

    @property
    def tipo_titulo_impressao(self):
        # Documentos antigos da Lojinha tinham tipo=transferencia
        if self.tipo == 'transferencia' and self.observacao and 'Lojinha' in (self.observacao or ''):
            return TIPO_TITULO_IMPRESSAO['doacao']
        return TIPO_TITULO_IMPRESSAO.get(self.tipo, f'TERMO DE {self.tipo_label.upper()} DE EQUIPAMENTO')

    @property
    def status_label(self):
        return STATUS_TRANSFERENCIA.get(self.status, (self.status, 'secondary'))[0]

    @property
    def status_badge(self):
        return STATUS_TRANSFERENCIA.get(self.status, (self.status, 'secondary'))[1]

    def __repr__(self):
        return f'<DocumentoTransferencia {self.id} {self.tipo} status={self.status}>'


class ItemDocumentoTransferencia(db.Model):
    """Item de um termo — pode ser equipamento do inventário ou item manual (teclado, mouse, etc.)."""
    __tablename__ = 'itens_documento_transferencia'

    id                = db.Column(db.Integer, primary_key=True)
    documento_id      = db.Column(db.Integer, db.ForeignKey('documentos_transferencia.id', ondelete='CASCADE'), nullable=False)
    equipamento_id    = db.Column(db.Integer, db.ForeignKey('equipamentos.id', ondelete='SET NULL'))  # null = item manual
    quantidade        = db.Column(db.Integer, nullable=False, default=1)
    descricao         = db.Column(db.String(500))  # para itens manuais ou exibição
    classificacao     = db.Column(db.String(1), nullable=False)  # A | B
    numero_patrimonio = db.Column(db.String(80))   # para itens manuais
    numero_serie      = db.Column(db.String(150))  # para itens manuais ou quando sem patrimônio

    documento   = db.relationship('DocumentoTransferencia', back_populates='itens')
    equipamento = db.relationship('Equipamento', foreign_keys=[equipamento_id],
                                   back_populates='itens_documento_transferencia')

    @property
    def classificacao_label(self):
        return CLASSIFICACAO_ITEM.get(self.classificacao, '')

    def descricao_exibicao(self):
        """Retorna a descrição para exibição (do equipamento ou campo manual)."""
        if self.equipamento:
            return self.equipamento.nome_display or self.equipamento.tipo_equipamento.nome if self.equipamento.tipo_equipamento else 'Equipamento'
        return self.descricao or '—'

    def numero_patrimonio_ou_serie(self):
        """Retorna nº patrimônio ou nº série conforme disponível."""
        if self.equipamento:
            return self.equipamento.numero_patrimonio or self.equipamento.numero_serie
        return self.numero_patrimonio or self.numero_serie


class ItemLojinha(db.Model):
    """Item à disposição na 'Lojinha Interna' — equipamentos que unidades não precisam mais."""
    __tablename__ = 'itens_lojinha'

    id                = db.Column(db.Integer, primary_key=True)
    unidade_id        = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='CASCADE'), nullable=False)
    equipamento_id   = db.Column(db.Integer, db.ForeignKey('equipamentos.id', ondelete='SET NULL'))
    quantidade        = db.Column(db.Integer, nullable=False, default=1)
    descricao         = db.Column(db.String(500))
    classificacao     = db.Column(db.String(1), nullable=False)  # A | B
    numero_patrimonio = db.Column(db.String(80))
    numero_serie      = db.Column(db.String(150))
    criado_por        = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em         = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ativo             = db.Column(db.Boolean, nullable=False, default=True)

    unidade   = db.relationship('Unidade', foreign_keys=[unidade_id])
    equipamento = db.relationship('Equipamento', foreign_keys=[equipamento_id])
    criador    = db.relationship('Usuario', foreign_keys=[criado_por])

    def descricao_exibicao(self):
        if self.equipamento:
            return self.equipamento.nome_display or (self.equipamento.tipo_equipamento.nome if self.equipamento.tipo_equipamento else 'Equipamento')
        return self.descricao or '—'

    def numero_patrimonio_ou_serie(self):
        if self.equipamento:
            return self.equipamento.numero_patrimonio or self.equipamento.numero_serie
        return self.numero_patrimonio or self.numero_serie


class TransferenciaEquipamento(db.Model):
    __tablename__ = 'transferencias_equipamento'

    id                  = db.Column(db.Integer, primary_key=True)
    equipamento_id      = db.Column(db.Integer, db.ForeignKey('equipamentos.id', ondelete='CASCADE'), nullable=False)
    sala_origem_id      = db.Column(db.Integer, db.ForeignKey('salas.id', ondelete='SET NULL'))
    sala_destino_id     = db.Column(db.Integer, db.ForeignKey('salas.id', ondelete='SET NULL'))
    unidade_origem_id   = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='RESTRICT'), nullable=False)
    unidade_destino_id  = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='RESTRICT'), nullable=False)
    solicitado_por      = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    aceito_por          = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    status              = db.Column(db.String(20), nullable=False, default='pendente')
    observacao          = db.Column(db.Text)
    observacao_aceite   = db.Column(db.Text)
    criado_em           = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resolvido_em        = db.Column(db.DateTime)

    equipamento      = db.relationship('Equipamento',  foreign_keys=[equipamento_id],     back_populates='transferencias')
    sala_origem      = db.relationship('Sala',          foreign_keys=[sala_origem_id])
    sala_destino     = db.relationship('Sala',          foreign_keys=[sala_destino_id])
    unidade_origem   = db.relationship('Unidade',       foreign_keys=[unidade_origem_id])
    unidade_destino  = db.relationship('Unidade',       foreign_keys=[unidade_destino_id])
    solicitante      = db.relationship('Usuario',       foreign_keys=[solicitado_por])
    resolvente       = db.relationship('Usuario',       foreign_keys=[aceito_por])

    @property
    def status_label(self):
        return STATUS_TRANSFERENCIA.get(self.status, (self.status, 'secondary'))[0]

    @property
    def status_badge(self):
        return STATUS_TRANSFERENCIA.get(self.status, (self.status, 'secondary'))[1]

    def __repr__(self):
        return f'<Transferencia equip={self.equipamento_id} status={self.status}>'
