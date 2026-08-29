from datetime import datetime, date
from app import db
from app.utils import prefixed_static_url

MODALIDADE_OPCOES = [
    'Compra Eletrônica', 'Comunicados', 'Concorrência', 'Concurso', 'Convite',
    'Dispensa de Licitação', 'Inexigibilidade', 'Leilão', 'Outros/Não Aplicável',
    'Pregão Eletrônico', 'Pregão Presencial', 'Tomada de Preços',
]

STATUS_CONTRATO_LABELS = {
    'vigente': 'Vigente',
    'a_vencer': 'A Vencer',
    'vencido': 'Vencido',
    'encerrado': 'Encerrado',
}
STATUS_CONTRATO_BADGE = {
    'vigente': 'success',
    'a_vencer': 'warning',
    'vencido': 'danger',
    'encerrado': 'secondary',
}

class Contrato(db.Model):
    __tablename__ = 'contratos'

    id = db.Column(db.Integer, primary_key=True)
    numero_sei = db.Column(db.String(100), unique=True)  # Nº do Processo SEI; CPL ou SEI obrigatório
    link_sei = db.Column(db.String(500))  # Link de Acesso Direto do Processo SEI
    cpl = db.Column(db.String(30))  # formato numero/AAAA (ex: 424/2020)
    empresa = db.Column(db.String(200))  # texto legado; quando empresa_id setado, exibimos a empresa vinculada
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas_contratadas.id', ondelete='SET NULL'))
    modalidade = db.Column(db.String(80))  # Compra Eletrônica, Concorrência, Pregão, etc.
    tipo_contrato = db.Column(db.String(100))
    objeto = db.Column(db.Text)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    valor_total = db.Column(db.Numeric(14, 2))
    status = db.Column(db.String(20), nullable=False, default='vigente')
    observacoes = db.Column(db.Text)
    # Campos da planilha CONTRATOS ATUAL
    secao = db.Column(db.String(100))
    numero_contrato = db.Column(db.String(50))  # Nº do contrato (diferente de CPL/SEI)
    data_assinatura = db.Column(db.Date)
    vigencia = db.Column(db.String(100))
    fonte = db.Column(db.String(150))
    valor_inicial = db.Column(db.Numeric(14, 2))
    valor_atual = db.Column(db.Numeric(14, 2))
    valor_mensal_atual = db.Column(db.Numeric(14, 2))
    aditivo_data_pct = db.Column(db.String(200))  # Aditivo (Data e %)
    reajuste_data_base_pct = db.Column(db.String(200))  # Reajuste (Data base e %)
    fiscalizacao = db.Column(db.String(200))
    supressao_data_pct = db.Column(db.String(200))  # Supressão (Data e %)
    contato_nome_telefone = db.Column(db.String(300))
    empenhos = db.Column(db.Text)
    mandado_judicial = db.Column(db.Boolean, nullable=False, default=False)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    tipos_equipamento = db.relationship('ContratoTipoEquipamento', back_populates='contrato',
                                        lazy='dynamic', cascade='all, delete-orphan')
    acoes = db.relationship('ContratoAcao', back_populates='contrato',
                            lazy='dynamic', cascade='all, delete-orphan')
    empresa_contratada = db.relationship('EmpresaContratada', back_populates='contratos',
                                         foreign_keys=[empresa_id])
    criador = db.relationship('Usuario')

    def atualizar_status(self):
        # Se houve Termo de Encerramento, contrato está encerrado (não "vencido")
        if self.acoes.filter_by(tipo='termo_encerramento').first():
            self.status = 'encerrado'
            return
        hoje = date.today()
        dias_restantes = (self.data_fim - hoje).days
        if dias_restantes < 0:
            self.status = 'vencido'
        elif dias_restantes <= 60:
            self.status = 'a_vencer'
        else:
            self.status = 'vigente'

    @property
    def dias_restantes(self):
        return (self.data_fim - date.today()).days

    @property
    def status_label(self):
        return STATUS_CONTRATO_LABELS.get(self.status, self.status)

    @property
    def status_badge(self):
        return STATUS_CONTRATO_BADGE.get(self.status, 'secondary')

    @property
    def total_itens(self):
        return self.tipos_equipamento.count()

    @property
    def equipamentos_cobertos_display(self):
        """Texto resumido dos equipamentos cobertos (ex: Notebook | Dell | todos; Ar-condicionado | todas | todos)."""
        itens = list(self.tipos_equipamento.all())
        if not itens:
            return ''
        return '; '.join(i.cobertura_resumo for i in itens)

    @property
    def identificador(self):
        """CPL ou Nº do Processo SEI — para exibição em título, breadcrumb, etc."""
        return self.numero_sei or self.cpl or '—'

    @property
    def empresa_display(self):
        """Nome da empresa para exibição (dados administrativos: razão social)."""
        if self.empresa_contratada:
            return self.empresa_contratada.razao_social
        return self.empresa or '—'

    @property
    def cnpj_display(self):
        """CNPJ da empresa vinculada (planilha CONTRATOS ATUAL)."""
        if self.empresa_contratada and self.empresa_contratada.cnpj:
            return self.empresa_contratada.cnpj
        return ''

    @property
    def cpl_url_transparencia(self):
        """URL do portal de transparência para consulta da CPL (ex: 424/2020)."""
        if not self.cpl or '/' not in str(self.cpl):
            return None
        cpl = str(self.cpl).strip()
        enc = f'codigoProcesso%2a{cpl.replace("/", "%2F")}'
        return f'https://api.sorocaba.sp.gov.br/pub-consulta/#/publicacoes?filter_fields={enc}'

    def __repr__(self):
        return f'<Contrato {self.identificador}>'


class ContratoTipoEquipamento(db.Model):
    """
    Equipamentos cobertos pelo contrato com granularidade tipo / marca / modelo.
    - Só tipo: cobre todos (qualquer marca e modelo).
    - Tipo + marca: cobre todos os modelos daquela marca.
    - Tipo + marca + modelo: cobre especificamente esse modelo.
    """
    __tablename__ = 'contrato_tipos_equipamento'

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id', ondelete='CASCADE'), nullable=False)
    tipo_equipamento_id = db.Column(db.Integer, db.ForeignKey('tipos_equipamento.id', ondelete='CASCADE'), nullable=False)
    marca_id = db.Column(db.Integer, db.ForeignKey('marcas.id', ondelete='CASCADE'))
    modelo_id = db.Column(db.Integer, db.ForeignKey('modelos.id', ondelete='CASCADE'))
    descricao_cobertura = db.Column(db.Text)

    contrato = db.relationship('Contrato', back_populates='tipos_equipamento')
    tipo_equipamento = db.relationship('TipoEquipamento', back_populates='contratos')
    marca = db.relationship('Marca', backref='contrato_itens')
    modelo = db.relationship('Modelo', backref='contrato_itens')

    # Unique: (contrato, tipo, marca, modelo). Duplicatas (tipo only etc.) checadas na aplicação.
    __table_args__ = (db.UniqueConstraint('contrato_id', 'tipo_equipamento_id', 'marca_id', 'modelo_id',
                                          name='uq_contrato_tipo_marca_modelo'),)

    def cobre_equipamento(self, equipamento):
        """Verifica se este item cobre o equipamento dado."""
        if equipamento.tipo_equipamento_id != self.tipo_equipamento_id:
            return False
        if self.marca_id is not None and equipamento.marca_id != self.marca_id:
            return False
        if self.modelo_id is not None and equipamento.modelo_id != self.modelo_id:
            return False
        return True

    @property
    def cobertura_resumo(self):
        """Texto resumido: Notebook | Dell | Latitude 5420 ou Notebook | Dell | todos etc."""
        partes = [self.tipo_equipamento.nome if self.tipo_equipamento else '?']
        partes.append(self.marca.nome if self.marca else 'todas')
        partes.append(self.modelo.nome if self.modelo else 'todos')
        return ' | '.join(partes)


# Tipos de ação do contrato
ACAO_TIPOS = [
    ('prorrogacao', 'Prorrogação'),
    ('prorrogacao_excepcional', 'Prorrogação Excepcional'),
    ('renovacao', 'Renovação'),
    ('termo_aditivo', 'Termo Aditivo'),
    ('notificacao', 'Notificação'),
    ('multa', 'Multa'),
    ('termo_encerramento', 'Termo de Encerramento'),
]


class ContratoAcao(db.Model):
    """Ação registrada no contrato (prorrogação, aditivo, notificação, multa, etc.)."""
    __tablename__ = 'contrato_acoes'

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id', ondelete='CASCADE'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    data_acao = db.Column(db.Date, nullable=False)
    observacao = db.Column(db.Text)
    # Prorrogação / Renovação: período em meses OU nova data de vencimento
    periodo_meses = db.Column(db.Integer)
    nova_data_fim = db.Column(db.Date)
    # Termo Aditivo: valor fixo OU porcentagem
    valor_adicional = db.Column(db.Numeric(14, 2))
    porcentagem_adicional = db.Column(db.Numeric(6, 2))
    # Multa: porcentagem (calcula sobre valor do contrato)
    porcentagem_multa = db.Column(db.Numeric(6, 2))
    # Notificação: anexo
    anexo_filename = db.Column(db.String(200))
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    contrato = db.relationship('Contrato', back_populates='acoes')
    criador = db.relationship('Usuario')

    @property
    def tipo_label(self):
        return dict(ACAO_TIPOS).get(self.tipo, self.tipo)

    @property
    def anexo_url(self):
        if self.anexo_filename:
            return prefixed_static_url(f'/static/uploads/contrato_acoes/{self.anexo_filename}')
        return None

    @property
    def valor_multa_calculado(self):
        """Valor da multa = valor_total do contrato * (porcentagem_multa/100)."""
        if not self.porcentagem_multa or not self.contrato or not self.contrato.valor_total:
            return None
        from decimal import Decimal
        return (self.contrato.valor_total * self.porcentagem_multa / Decimal(100))

    @property
    def novo_valor_total(self):
        """Para termo aditivo: valor_total + valor_adicional ou valor_total * (1 + %/100)."""
        if not self.contrato:
            return None
        from decimal import Decimal
        v = self.contrato.valor_total or Decimal(0)
        if self.valor_adicional:
            return v + self.valor_adicional
        if self.porcentagem_adicional:
            return v * (1 + self.porcentagem_adicional / Decimal(100))
        return None
