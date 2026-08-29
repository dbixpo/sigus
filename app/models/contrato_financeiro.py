# -*- coding: utf-8 -*-
"""Empenhos, fontes e notas (planilha FINANCEIRO - DAG)."""
from datetime import datetime
from app import db

TIPO_OPCOES = [
    'Indicar Despesa', 'Reserva', 'Reserva Complementar',
]

MOTIVO_OPCOES = [
    'Aditivo', 'Aditivo MJ', 'Complemento', 'Complemento Prorrogação',
    'Indenização', 'Indenizatório', 'Investimento', 'Mandado Judicial',
    'Material de Consumo', 'Multa INSS', 'Novo', 'Novo Continuidade',
    'Novo MJ', 'Novo/Emergencial', 'Pendência', 'Pendência 23',
    'Pendência Ano Anterior', 'Piso de Enfermagem', 'Piso de Enfermagem Out/2024',
    'Piso Enfermagem DEZ', 'Piso Enfermagem NOV', 'Prorrogação', 'Reajuste',
    'Renovação', 'Renovação e Aditivo', 'Renovação/Aditivo', 'Repasse',
    'Reserva', 'Serviço', 'Vigente',
]


class ContratoFinanceiro(db.Model):
    __tablename__ = 'contrato_financeiro'

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id', ondelete='SET NULL'))
    tipo = db.Column(db.String(50))
    processo = db.Column(db.String(100))
    motivo = db.Column(db.String(80))
    prestador = db.Column(db.String(200))
    objeto = db.Column(db.Text)
    referencia = db.Column(db.String(150))
    valor_total = db.Column(db.Numeric(14, 2))
    especializada = db.Column(db.String(100))
    vigilancia = db.Column(db.String(100))
    atencao_basica = db.Column(db.String(100))
    outros = db.Column(db.String(100))
    tabela_sus = db.Column(db.String(100))
    complemento = db.Column(db.String(150))
    emenda_municipal = db.Column(db.String(100))
    emenda_estadual = db.Column(db.String(100))
    emenda_federal = db.Column(db.String(100))
    observacao = db.Column(db.Text)
    data_necessaria = db.Column(db.Date)
    data_envio_divisao = db.Column(db.Date)
    data_envio_fms = db.Column(db.Date)
    data_devolucao_setor = db.Column(db.Date)
    reservas = db.Column(db.String(200))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    contrato = db.relationship('Contrato', backref='empenhos_financeiros', foreign_keys=[contrato_id])

    @property
    def processo_display(self):
        """CPL ou Nº do Processo SEI — do contrato vinculado ou campo processo."""
        if self.contrato:
            return self.contrato.identificador
        return self.processo or '—'

    @property
    def prestador_display(self):
        """Prestador — do contrato vinculado ou campo prestador."""
        if self.contrato:
            return self.contrato.empresa_display
        return self.prestador or '—'
