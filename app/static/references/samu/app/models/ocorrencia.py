"""Ocorrência (registro de ligação) para o TARM."""
from datetime import datetime
from app import db


# Status: aguardando = salvo para completar depois; em_atendimento = preenchendo;
# finalizada = encerrado pelo telefonista; enviada_medico = passada ao médico
STATUS_AGUARDANDO = 'aguardando'
STATUS_EM_ATENDIMENTO = 'em_atendimento'
STATUS_FINALIZADA = 'finalizada'
STATUS_ENVIADA_MEDICO = 'enviada_medico'
STATUS_REGULADA = 'regulada'  # médico regulou, aguardando despacho

STATUS_LABELS = {
    STATUS_AGUARDANDO: 'Aguardando',
    STATUS_EM_ATENDIMENTO: 'Em atendimento',
    STATUS_FINALIZADA: 'Finalizada',
    STATUS_ENVIADA_MEDICO: 'Enviada ao médico',
    STATUS_REGULADA: 'Regulada',
}


class Ocorrencia(db.Model):
    """Registro de ligação ao 192 - ID formato AAMMDD0000."""
    __tablename__ = 'ocorrencias'

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False, index=True)  # AAMMDD0000

    # Telefone (apenas dígitos armazenados)
    telefone = db.Column(db.String(20), nullable=False, index=True)
    nome_solicitante = db.Column(db.String(200))
    atendente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    apelido = db.Column(db.String(150))

    # Timestamps para ficha de atendimento
    iniciada_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finalizada_em = db.Column(db.DateTime)
    enviada_medico_em = db.Column(db.DateTime)

    # Algoritmo e motivo
    algoritmo_id = db.Column(db.Integer, db.ForeignKey('algoritmos_acolhimento.id', ondelete='SET NULL'))
    motivo_queixa = db.Column(db.Text)
    respostas_algoritmo = db.Column(db.JSON, default=dict)  # {pergunta_id: opcao_id ou texto}

    # Pacientes [{nome, sexo, idade}, ...]
    pacientes = db.Column(db.JSON, default=list)

    # Regulação médica: tipo/motivo da ocorrência
    tipo_ocorrencia_id = db.Column(db.Integer, db.ForeignKey('tipos_ocorrencia.id', ondelete='SET NULL'))
    motivo_ocorrencia_id = db.Column(db.Integer, db.ForeignKey('motivos_ocorrencia.id', ondelete='SET NULL'))

    # Tipo e origem (pré-preenchidos da última ligação)
    tipo_ligacao_id = db.Column(db.Integer, db.ForeignKey('tipos_ligacao.id', ondelete='SET NULL'))
    origem_ligacao_id = db.Column(db.Integer, db.ForeignKey('origens_ligacao.id', ondelete='SET NULL'))
    unidade_saude_id = db.Column(db.Integer, db.ForeignKey('unidades_saude.id', ondelete='SET NULL'))
    unidade_samu_id = db.Column(db.Integer, db.ForeignKey('unidades_samu.id', ondelete='SET NULL'))  # viatura vinculada pelo RO

    # Endereço
    end_cidade = db.Column(db.String(100))
    end_uf = db.Column(db.String(2))
    end_logradouro = db.Column(db.String(300))
    end_numero = db.Column(db.String(20))
    end_complemento = db.Column(db.String(100))
    end_bairro = db.Column(db.String(100))
    end_cep = db.Column(db.String(9))

    status = db.Column(db.String(30), nullable=False, default=STATUS_EM_ATENDIMENTO, index=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Regulação médica: avaliação e decisão
    avaliacao_medica_historico = db.Column(db.Text)  # histórico de avaliações (append-only)
    decisao_protocolo = db.Column(db.Text)  # decisão sugerida pelo protocolo
    decisoes_medicas = db.Column(db.JSON, default=list)  # [{tipo_unidade_id, classificacao_risco_id}, ...]
    regulada_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    regulada_em = db.Column(db.DateTime)

    # Despacho RO: timestamps (estilo eSUS SAMU)
    envio_viatura_em = db.Column(db.DateTime)
    saida_base_em = db.Column(db.DateTime)
    chegada_local_em = db.Column(db.DateTime)
    saida_local_em = db.Column(db.DateTime)
    chegada_destino_em = db.Column(db.DateTime)
    equipe_liberada_em = db.Column(db.DateTime)
    chegada_base_em = db.Column(db.DateTime)
    cancelamento_intercorrencia_id = db.Column(db.Integer, db.ForeignKey('intercorrencias.id', ondelete='SET NULL'))
    cancelamento_observacao = db.Column(db.Text)

    # Bloqueio de edição concorrente: quem está editando
    editando_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    editando_desde = db.Column(db.DateTime)

    atendente = db.relationship('Usuario', backref='ocorrencias_atendidas', foreign_keys=[atendente_id])
    editando_por = db.relationship('Usuario', foreign_keys=[editando_por_id])
    algoritmo = db.relationship('AlgoritmoAcolhimento', backref='ocorrencias', foreign_keys=[algoritmo_id])
    tipo_ocorrencia = db.relationship('TipoOcorrencia', backref='ocorrencias', foreign_keys=[tipo_ocorrencia_id])
    motivo_ocorrencia = db.relationship('MotivoOcorrencia', backref='ocorrencias', foreign_keys=[motivo_ocorrencia_id])
    regulada_por = db.relationship('Usuario', foreign_keys=[regulada_por_id])
    tipo_ligacao = db.relationship('TipoLigacao', backref='ocorrencias', foreign_keys=[tipo_ligacao_id])
    origem_ligacao = db.relationship('OrigemLigacao', backref='ocorrencias', foreign_keys=[origem_ligacao_id])
    unidade_saude = db.relationship('UnidadeSaude', backref='ocorrencias', foreign_keys=[unidade_saude_id])
    unidade_samu = db.relationship('UnidadeSamu', backref='ocorrencias_despachadas', foreign_keys=[unidade_samu_id])
    cancelamento_intercorrencia = db.relationship('Intercorrencia', backref='ocorrencias_canceladas', foreign_keys=[cancelamento_intercorrencia_id])

    @property
    def endereco_formatado(self):
        """Endereço completo para link Google Maps."""
        partes = []
        if self.end_logradouro:
            partes.append(self.end_logradouro)
        if self.end_numero:
            partes.append(self.end_numero)
        if self.end_complemento:
            partes.append(self.end_complemento)
        if self.end_bairro:
            partes.append(self.end_bairro)
        if self.end_cidade:
            partes.append(self.end_cidade)
        if self.end_uf:
            partes.append(self.end_uf)
        if self.end_cep:
            partes.append(self.end_cep)
        return ', '.join(partes) if partes else None

    @property
    def google_maps_url(self):
        """URL para buscar endereço no Google Maps."""
        if not self.endereco_formatado:
            return None
        import urllib.parse
        return 'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote(self.endereco_formatado)

    def __repr__(self):
        return f'<Ocorrencia {self.numero}>'
