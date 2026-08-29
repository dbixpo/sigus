from datetime import datetime
from app import db

STATUS_EQUIPAMENTO = ['ativo', 'em_manutencao', 'baixado']
STATUS_LABELS = {
    'ativo': 'Ativo',
    'em_manutencao': 'Em Manutenção',
    'baixado': 'Baixado',
}
STATUS_BADGE = {
    'ativo': 'success',
    'em_manutencao': 'warning',
    'baixado': 'secondary',
}

CONDICAO_EQUIPAMENTO = ['excelente', 'boa', 'regular', 'ruim', 'inservivel']
CONDICAO_LABELS = {
    'excelente': 'Excelente',
    'boa': 'Boa',
    'regular': 'Regular',
    'ruim': 'Ruim',
    'inservivel': 'Inservível',
}
CONDICAO_BADGE = {
    'excelente': 'success',
    'boa': 'info',
    'regular': 'primary',
    'ruim': 'warning',
    'inservivel': 'danger',
}


class TipoEquipamento(db.Model):
    __tablename__ = 'tipos_equipamento'

    id             = db.Column(db.Integer, primary_key=True)
    nome           = db.Column(db.String(150), nullable=False, unique=True)
    descricao      = db.Column(db.Text)
    tem_patrimonio = db.Column(db.Boolean, nullable=False, default=True)
    icone          = db.Column(db.String(80), default='bi-box')
    ativo          = db.Column(db.Boolean, nullable=False, default=True)
    criado_em      = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    campos = db.relationship('CampoTipoEquipamento', back_populates='tipo_equipamento',
                             order_by='CampoTipoEquipamento.ordem', lazy='dynamic',
                             cascade='all, delete-orphan')
    equipamentos = db.relationship('Equipamento', back_populates='tipo_equipamento', lazy='dynamic')
    contratos = db.relationship('ContratoTipoEquipamento', back_populates='tipo_equipamento', lazy='dynamic')

    def __repr__(self):
        return f'<TipoEquipamento {self.nome}>'


class CampoTipoEquipamento(db.Model):
    __tablename__ = 'campos_tipo_equipamento'

    id = db.Column(db.Integer, primary_key=True)
    tipo_equipamento_id = db.Column(db.Integer, db.ForeignKey('tipos_equipamento.id', ondelete='CASCADE'), nullable=False)
    nome_campo = db.Column(db.String(100), nullable=False)
    tipo_dado = db.Column(db.String(20), nullable=False, default='texto')
    obrigatorio = db.Column(db.Boolean, nullable=False, default=False)
    opcoes_selecao = db.Column(db.JSON)
    ordem = db.Column(db.Integer, default=0)
    # Quando True, o valor deste campo compõe o nome de exibição do equipamento
    # Ex: Ar-condicionado + "18.000 BTU" → "Ar-condicionado 18.000 BTU"
    campo_destaque = db.Column(db.Boolean, nullable=False, default=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    tipo_equipamento = db.relationship('TipoEquipamento', back_populates='campos')
    valores = db.relationship('EquipamentoCampoValor', back_populates='campo', lazy='dynamic',
                               cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Campo {self.nome_campo} [{self.tipo_equipamento_id}]>'


# Tabela de associação Marca ↔ TipoEquipamento
marca_tipo_equipamento = db.Table(
    'marca_tipo_equipamento',
    db.Column('marca_id',            db.Integer, db.ForeignKey('marcas.id',            ondelete='CASCADE'), primary_key=True),
    db.Column('tipo_equipamento_id', db.Integer, db.ForeignKey('tipos_equipamento.id', ondelete='CASCADE'), primary_key=True),
)


class Marca(db.Model):
    __tablename__ = 'marcas'

    id            = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(100), nullable=False, unique=True)
    criado_em     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    modelos      = db.relationship('Modelo', back_populates='marca', lazy='dynamic')
    equipamentos = db.relationship('Equipamento', back_populates='marca', lazy='dynamic')
    tipos        = db.relationship('TipoEquipamento', secondary=marca_tipo_equipamento,
                                   backref=db.backref('marcas', lazy='dynamic'), lazy='dynamic')

    def suporta_tipo(self, tipo_id):
        return self.tipos.filter_by(id=tipo_id).count() > 0

    def __repr__(self):
        return f'<Marca {self.nome}>'


class Modelo(db.Model):
    __tablename__ = 'modelos'

    id                  = db.Column(db.Integer, primary_key=True)
    tipo_equipamento_id = db.Column(db.Integer, db.ForeignKey('tipos_equipamento.id', ondelete='SET NULL'))
    marca_id            = db.Column(db.Integer, db.ForeignKey('marcas.id', ondelete='SET NULL'))
    nome                = db.Column(db.String(150), nullable=False)
    criado_em           = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em       = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    tipo_equipamento = db.relationship('TipoEquipamento', foreign_keys=[tipo_equipamento_id])
    marca            = db.relationship('Marca', back_populates='modelos')
    equipamentos     = db.relationship('Equipamento', back_populates='modelo', lazy='dynamic')

    __table_args__ = (db.UniqueConstraint('tipo_equipamento_id', 'marca_id', 'nome'),)

    def __repr__(self):
        return f'<Modelo {self.nome}>'


class Equipamento(db.Model):
    __tablename__ = 'equipamentos'

    id = db.Column(db.Integer, primary_key=True)
    sala_id = db.Column(db.Integer, db.ForeignKey('salas.id', ondelete='RESTRICT'), nullable=False)
    tipo_equipamento_id = db.Column(db.Integer, db.ForeignKey('tipos_equipamento.id', ondelete='RESTRICT'), nullable=False)
    numero_patrimonio = db.Column(db.String(80))
    numero_serie = db.Column(db.String(150))
    marca_id = db.Column(db.Integer, db.ForeignKey('marcas.id', ondelete='SET NULL'))
    modelo_id = db.Column(db.Integer, db.ForeignKey('modelos.id', ondelete='SET NULL'))
    data_aquisicao = db.Column(db.Date)
    valor_estimado = db.Column(db.Numeric(12, 2))
    tempo_uso_anos = db.Column(db.Numeric(5, 1))
    status = db.Column(db.String(20), nullable=False, default='ativo')
    condicao = db.Column(db.String(20), nullable=False, default='boa')
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    sala = db.relationship('Sala', back_populates='equipamentos')
    tipo_equipamento = db.relationship('TipoEquipamento', back_populates='equipamentos')
    marca = db.relationship('Marca', back_populates='equipamentos')
    modelo = db.relationship('Modelo', back_populates='equipamentos')
    campos_valores = db.relationship('EquipamentoCampoValor', back_populates='equipamento',
                                      lazy='dynamic', cascade='all, delete-orphan')
    chamados = db.relationship('Chamado', back_populates='equipamento', lazy='dynamic')
    transferencias = db.relationship('TransferenciaEquipamento', foreign_keys='TransferenciaEquipamento.equipamento_id',
                                      back_populates='equipamento', lazy='dynamic',
                                      order_by='TransferenciaEquipamento.criado_em.desc()')
    itens_documento_transferencia = db.relationship(
        'ItemDocumentoTransferencia', foreign_keys='ItemDocumentoTransferencia.equipamento_id',
        back_populates='equipamento', lazy='dynamic',
    )
    historico      = db.relationship('HistoricoEquipamento', back_populates='equipamento',
                                      lazy='dynamic', order_by='HistoricoEquipamento.criado_em.desc()',
                                      cascade='all, delete-orphan')
    usuarios_vinculados = db.relationship('EquipamentoUsuario', back_populates='equipamento',
                                          lazy='dynamic', cascade='all, delete-orphan',
                                          order_by='EquipamentoUsuario.vinculado_em')

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)

    @property
    def status_badge(self):
        return STATUS_BADGE.get(self.status, 'secondary')

    @property
    def condicao_label(self):
        return CONDICAO_LABELS.get(self.condicao, self.condicao)

    @property
    def condicao_badge(self):
        return CONDICAO_BADGE.get(self.condicao, 'secondary')

    @property
    def nome_display(self):
        """Nome de exibição: Tipo [+ valor do campo destaque] [+ Marca/Modelo]."""
        tipo_nome = self.tipo_equipamento.nome if self.tipo_equipamento else 'Equipamento'

        # Busca o valor do campo marcado como destaque
        destaque_val = None
        if self.tipo_equipamento:
            campo_dest = self.tipo_equipamento.campos.filter_by(campo_destaque=True).first()
            if campo_dest:
                cv = self.campos_valores.filter_by(campo_id=campo_dest.id).first()
                if cv and cv.valor:
                    destaque_val = cv.valor

        partes = [tipo_nome]
        if destaque_val:
            partes.append(destaque_val)
        if self.marca:
            partes.append(self.marca.nome)
        if self.modelo:
            partes.append(self.modelo.nome)
        return ' '.join(partes) if destaque_val else ' - '.join(partes)

    @property
    def identificacao(self):
        """Patrimônio ou, na falta, número de série."""
        return self.numero_patrimonio or self.numero_serie or '—'

    @property
    def usuario_vinculado_nome(self):
        """Retorna o nome do primeiro usuário vinculado, se houver."""
        ev = self.usuarios_vinculados.first()
        return ev.usuario.nome if ev and ev.usuario else None

    @property
    def contrato_vigente(self):
        """Contrato vigente que cobre este equipamento (tipo, marca, modelo conforme cobertura)."""
        from app.models.contrato import Contrato, ContratoTipoEquipamento
        from datetime import date
        from sqlalchemy import or_
        if not self.tipo_equipamento:
            return None
        q = ContratoTipoEquipamento.query.join(Contrato).filter(
            ContratoTipoEquipamento.tipo_equipamento_id == self.tipo_equipamento_id,
            or_(ContratoTipoEquipamento.marca_id.is_(None),
                ContratoTipoEquipamento.marca_id == self.marca_id),
            or_(ContratoTipoEquipamento.modelo_id.is_(None),
                ContratoTipoEquipamento.modelo_id == self.modelo_id),
            Contrato.status.in_(('vigente', 'a_vencer')),
            Contrato.data_fim >= date.today()
        )
        cte = q.first()
        return cte.contrato if cte else None

    def __repr__(self):
        return f'<Equipamento {self.id} [{self.tipo_equipamento.nome if self.tipo_equipamento else "?"}]>'


class EquipamentoUsuario(db.Model):
    """Vínculo entre um equipamento e o(s) usuário(s) que o utilizam."""
    __tablename__ = 'equipamento_usuarios'

    id             = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamentos.id', ondelete='CASCADE'), nullable=False)
    usuario_id     = db.Column(db.Integer, db.ForeignKey('usuarios.id',     ondelete='CASCADE'), nullable=False)
    observacao     = db.Column(db.String(200))
    vinculado_em   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    equipamento = db.relationship('Equipamento', back_populates='usuarios_vinculados')
    usuario     = db.relationship('Usuario')

    __table_args__ = (db.UniqueConstraint('equipamento_id', 'usuario_id'),)

    def __repr__(self):
        return f'<EquipamentoUsuario eq={self.equipamento_id} usr={self.usuario_id}>'


class EquipamentoCampoValor(db.Model):
    __tablename__ = 'equipamento_campo_valores'

    id = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamentos.id', ondelete='CASCADE'), nullable=False)
    campo_id = db.Column(db.Integer, db.ForeignKey('campos_tipo_equipamento.id', ondelete='CASCADE'), nullable=False)
    valor = db.Column(db.Text)

    equipamento = db.relationship('Equipamento', back_populates='campos_valores')
    campo = db.relationship('CampoTipoEquipamento', back_populates='valores')

    __table_args__ = (db.UniqueConstraint('equipamento_id', 'campo_id'),)
