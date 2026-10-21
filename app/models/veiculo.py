# -*- coding: utf-8 -*-
"""Veículos das unidades (cadastro próprio, fora do patrimônio de equipamentos)."""
import re

from app import db
from app.utils import agora_local_callable

PREFIXO_ALUGADO = 'AL-'
PREFIXO_MAX_DIGITOS = 4

CATEGORIAS_VEICULO = ['Carro de passeio', 'Utilitário', 'Caminhonete', 'Van', 'Micro-ônibus / ônibus',
                      'Ambulância', 'Motocicleta', 'Caminhão']
COMBUSTIVEIS_VEICULO = ['Flex', 'Gasolina', 'Etanol', 'Diesel', 'GNV', 'Elétrico', 'Híbrido']

CLASSIFICACAO_VEICULOS = 'Veículos'
DESCRICAO_VEICULOS = (
    'Meio de transporte, motorizado ou não, destinado a apoiar as ações, '
    'os programas e políticas do Ministério da Saúde.'
)

# Itens de veículo da lista de itens ativos da RENEM (FNS, agosto de 2019).
ITENS_RENEM_VEICULO = [
    'Ambulância Tipo A - Simples Remoção Tipo Furgão',
    'Ambulância Tipo A - Simples Remoção Tipo Furgoneta',
    'Ambulância Tipo A - Simples Remoção Tipo pick-up 4x4',
    'Embarcação para Transporte com Motor Popa (até 12 pessoas)',
    'Micro-ônibus Rural de Transporte Sanitário',
    'Micro-ônibus Urbano de Transporte Sanitário',
    'Unidade Móvel de Saúde - SAMU (Suporte Básico e/ou Avançado de Vida)',
    'Unidade Móvel para controle de zoonoses Tipo 1',
    'Unidade Móvel para controle de zoonoses Tipo 2',
    'Unidade Móvel para controle de zoonoses Tipo 3',
    'Unidade Odontológica Móvel - UOM',
    'Veículo de Passeio - Transporte de Equipe (5 pessoas, 0 Km)',
    'Veículo de Transporte Adaptado',
    'Veículo de Transporte Sanitário (Com Acessibilidade - 1 Cadeirante)',
    'Veículo Pick-up Cabine Dupla 4x4 (Diesel)',
    'Veículo Tipo Motocicleta (Cross)',
    'Veículo Tipo Van',
]


def icone_tipo_veiculo(nome):
    texto = (nome or '').lower()
    if 'motocic' in texto:
        return 'fas fa-motorcycle'
    if 'embarcat' in texto:
        return 'fas fa-ship'
    if 'micro-ônibus' in texto or 'micro-onibus' in texto:
        return 'fas fa-bus'
    if any(p in texto for p in ('ambulância', 'ambulancia', 'samu', 'zoonoses', 'odontológica móvel', 'odontologica movel')):
        return 'fas fa-truck-medical'
    if 'pick-up' in texto or 'pickup' in texto:
        return 'fas fa-truck-pickup'
    if 'van' in texto:
        return 'fas fa-van-shuttle'
    if 'adaptado' in texto or 'sanitário' in texto or 'sanitario' in texto:
        return 'fas fa-wheelchair'
    return 'fas fa-car-side'


def normalizar_prefixo(texto):
    """'al-383' → ('383', True). Quem digita o AL- já diz que é alugado."""
    prefixo = (texto or '').strip().upper()
    if prefixo.startswith(PREFIXO_ALUGADO):
        return prefixo[len(PREFIXO_ALUGADO):].strip(), True
    return prefixo, False


def normalizar_placa(texto):
    return re.sub(r'[^A-Z0-9]', '', (texto or '').upper())


class TipoVeiculo(db.Model):
    """Item de veículo da RENEM. O carro da unidade (prefixo e placa) continua em Veiculo."""
    __tablename__ = 'tipos_veiculo'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(180), nullable=False)
    descricao = db.Column(db.Text)
    icone = db.Column(db.String(80), nullable=False, default='fas fa-car-side')
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_equipamento.id', ondelete='RESTRICT'))
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable, onupdate=agora_local_callable)

    categoria = db.relationship('CategoriaEquipamento', backref=db.backref('tipos_veiculo', lazy='dynamic'))

    def __repr__(self):
        return f'<TipoVeiculo {self.nome}>'


class ModeloVeiculo(db.Model):
    """Catálogo de modelos para sugerir no cadastro (o campo continua livre)."""
    __tablename__ = 'veiculo_modelos'

    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(60), nullable=False)
    nome = db.Column(db.String(80), nullable=False)
    categoria = db.Column(db.String(40))

    __table_args__ = (db.UniqueConstraint('marca', 'nome'),)


class Veiculo(db.Model):
    __tablename__ = 'veiculos'

    id = db.Column(db.Integer, primary_key=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='CASCADE'), nullable=False)
    # Veículo não tem patrimônio: é identificado pelo prefixo (383; alugado aparece como AL-383).
    prefixo = db.Column(db.String(20), nullable=False)
    alugado = db.Column(db.Boolean, nullable=False, default=False)
    locadora = db.Column(db.String(150))
    placa = db.Column(db.String(10), nullable=False)
    marca = db.Column(db.String(60))
    modelo = db.Column(db.String(80))
    categoria = db.Column(db.String(40))
    tipo_veiculo_id = db.Column(db.Integer, db.ForeignKey('tipos_veiculo.id', ondelete='SET NULL'))
    ano = db.Column(db.String(9))
    cor = db.Column(db.String(30))
    combustivel = db.Column(db.String(20))
    lotacao = db.Column(db.Integer)
    renavam = db.Column(db.String(20))
    chassi = db.Column(db.String(30))
    km_cadastro = db.Column(db.Integer)
    licenciamento_vencimento = db.Column(db.Date)
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable, onupdate=agora_local_callable)

    unidade = db.relationship('Unidade')
    criador = db.relationship('Usuario', foreign_keys=[criado_por])
    tipo_renem = db.relationship('TipoVeiculo', foreign_keys=[tipo_veiculo_id])

    @property
    def prefixo_exibicao(self):
        if not self.prefixo:
            return ''
        return f'{PREFIXO_ALUGADO}{self.prefixo}' if self.alugado else self.prefixo

    @property
    def marca_modelo(self):
        return ' '.join(p for p in [self.marca, self.modelo] if p)

    @property
    def placa_exibicao(self):
        p = self.placa or ''
        return f'{p[:3]}-{p[3:]}' if len(p) == 7 and p[3].isdigit() and p[4].isdigit() else p

    @property
    def rotulo(self):
        return ' · '.join(p for p in [self.prefixo_exibicao, self.placa_exibicao, self.marca_modelo] if p)

    def __repr__(self):
        return f'<Veiculo {self.prefixo_exibicao} {self.placa}>'
