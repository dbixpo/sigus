# -*- coding: utf-8 -*-
"""Tabelas do dashboard-emendas (Patrick) no schema PostgreSQL `sueq`."""
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app import db

SCHEMA = {'schema': 'sueq'}


class SueqParlamentar(db.Model):
    __tablename__ = 'parlamentares'
    __table_args__ = SCHEMA
    id = db.Column(db.BigInteger, primary_key=True)
    nome = db.Column(db.Text, nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)


class SueqUnidade(db.Model):
    __tablename__ = 'unidades'
    __table_args__ = SCHEMA
    id = db.Column(db.BigInteger, primary_key=True)
    nome = db.Column(db.Text)
    nome_chave = db.Column(db.Text)
    endereco = db.Column(db.Text)
    telefone = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)


class SueqProcesso(db.Model):
    __tablename__ = 'processos'
    __table_args__ = SCHEMA
    id = db.Column(db.BigInteger, primary_key=True)
    identificador = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.Text)
    natureza = db.Column(db.Text)
    objeto = db.Column(db.Text)
    modalidade = db.Column(db.Text)
    status = db.Column(db.Text)
    secao = db.Column(db.Text)
    valor_estimado = db.Column(db.Numeric)
    observacao = db.Column(db.Text)
    sc = db.Column(db.Text)
    link_publico_sei = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    @property
    def link_sei_url(self):
        t = (self.link_publico_sei or '').strip()
        if t.lower().startswith(('http://', 'https://')):
            return t
        return None


class SueqEmenda(db.Model):
    __tablename__ = 'emendas'
    __table_args__ = SCHEMA
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo = db.Column(db.Text)
    emenda = db.Column(db.Text)
    parlamentar = db.Column(db.Text)
    sei_emenda = db.Column(db.Text)
    sei = db.Column(db.Text)
    link_sei = db.Column(db.Text)
    valor_cedido = db.Column(db.Numeric)
    unidade = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ano = db.Column(db.Integer)
    numero = db.Column(db.Text)
    objeto = db.Column(db.Text)
    unidade_id = db.Column(db.BigInteger, db.ForeignKey('sueq.unidades.id'))

    unidade_ref = db.relationship('SueqUnidade', foreign_keys=[unidade_id])
    itens = db.relationship('SueqEmendaItem', back_populates='emenda_ref', lazy='dynamic')

    @property
    def link_sei_url(self):
        """URL pública do processo SEI, se houver (igual aos contratos)."""
        for valor in (self.link_sei, self.sei, self.sei_emenda):
            t = (valor or '').strip()
            if t.lower().startswith(('http://', 'https://')):
                return t
        return None

    @property
    def sei_display(self):
        for valor in (self.sei_emenda, self.sei):
            t = (valor or '').strip()
            if t and not t.lower().startswith(('http://', 'https://')):
                return t
        t = (self.sei_emenda or self.sei or '').strip()
        if t.lower().startswith(('http://', 'https://')):
            return 'Abrir processo no SEI'
        return t or None

    @property
    def total_planejado(self):
        return sum((i.vl_total_cadastrado or 0) for i in self.itens)

    @property
    def total_executado(self):
        return sum((i.vl_total or 0) for i in self.itens)

    @property
    def saldo(self):
        cedido = self.valor_cedido or 0
        return cedido - (self.total_executado or 0)


class SueqEmendaItem(db.Model):
    __tablename__ = 'emenda_itens'
    __table_args__ = SCHEMA
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    emenda_id = db.Column(UUID(as_uuid=True), db.ForeignKey('sueq.emendas.id'))
    emenda = db.Column(db.Text)
    item = db.Column(db.Text)
    qtde = db.Column(db.Numeric)
    vl_unitario = db.Column(db.Numeric)
    vl_total = db.Column(db.Numeric)
    cpl = db.Column(db.Text)
    status = db.Column(db.Text)
    nota_fiscal = db.Column(db.Text)
    empenho = db.Column(db.Text)
    patrimonio = db.Column(db.Text)
    unidade_entrega = db.Column(db.Text)
    data_entrega = db.Column(db.Text)
    ordem_pagamento = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    unidade_beneficiada = db.Column(db.Text)
    item_cadastrado = db.Column(db.Text)
    qtde_cadastrada = db.Column(db.Numeric)
    vl_unitario_cadastrado = db.Column(db.Numeric)
    vl_total_cadastrado = db.Column(db.Numeric)
    data_atualizacao = db.Column(db.Text)
    comprovante_pagamento = db.Column(db.Text)
    unidade_beneficiada_id = db.Column(db.BigInteger)
    unidade_entrega_id = db.Column(db.BigInteger)
    processo_id = db.Column(db.BigInteger, db.ForeignKey('sueq.processos.id'))

    emenda_ref = db.relationship('SueqEmenda', back_populates='itens')
    processo = db.relationship('SueqProcesso', foreign_keys=[processo_id])


class SueqChamado(db.Model):
    __tablename__ = 'chamados'
    __table_args__ = SCHEMA
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocolo = db.Column(db.Text)
    carimbo = db.Column(db.Text)
    data_solicitacao = db.Column(db.Text)
    unidade = db.Column(db.Text)
    equipamento = db.Column(db.Text)
    fabricante = db.Column(db.Text)
    serie = db.Column(db.Text)
    patrimonio = db.Column(db.Text)
    categoria = db.Column(db.Text)
    servico = db.Column(db.Text)
    problema = db.Column(db.Text)
    descricao = db.Column(db.Text)
    rechamado = db.Column(db.Text)
    observacao = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    data_rechamado = db.Column(db.Text)
    endereco = db.Column(db.Text)
    telefone = db.Column(db.Text)
    responsavel = db.Column(db.Text)
    grau_urgencia = db.Column(db.Text)
    email_retorno = db.Column(db.Text)
    status = db.Column(db.Text, default='sem_status')
    cpl_contrato = db.Column(db.Text)
    contrato_id = db.Column(db.Integer)
    os_numero = db.Column(db.Text)
    servico_realizado = db.Column(db.Text)
    situacao_os = db.Column(db.Text)
    ocorrencias = db.Column(db.Text)
    glosa = db.Column(db.Numeric(10, 2))
    nf_referencia = db.Column(db.Text)
    competencia = db.Column(db.Text)
    fiscalizado_por = db.Column(db.Text)
    fiscalizado_em = db.Column(db.Date)
    unidade_id = db.Column(db.BigInteger, db.ForeignKey('sueq.unidades.id'))

    unidade_ref = db.relationship('SueqUnidade', foreign_keys=[unidade_id])
    controle = db.relationship('SueqChamadoControle', back_populates='chamado', uselist=False)


class SueqChamadoControle(db.Model):
    __tablename__ = 'chamados_controle'
    __table_args__ = SCHEMA
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    protocolo = db.Column(db.Text)
    status = db.Column(db.Text, default='Aberto')
    data_atendimento = db.Column(db.Text)
    empresa = db.Column(db.Text)
    os = db.Column(db.Text)
    feito = db.Column(db.Text)
    obs = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    chamado_protocolo = db.Column(db.Text)
    motivo_invalido = db.Column(db.Text)
    cpl_contrato = db.Column(db.Text)
    contrato_id = db.Column(db.Integer)
    servico_realizado = db.Column(db.Text)
    situacao_os = db.Column(db.Text)
    ocorrencias = db.Column(db.Text)
    glosa = db.Column(db.Numeric(10, 2))
    nf_referencia = db.Column(db.Text)
    competencia = db.Column(db.Text)
    fiscalizado_por = db.Column(db.Text)
    fiscalizado_em = db.Column(db.Date)
    data_atendimento_os = db.Column(db.Date)
    chamado_id = db.Column(UUID(as_uuid=True), db.ForeignKey('sueq.chamados.id'))

    chamado = db.relationship('SueqChamado', back_populates='controle')
