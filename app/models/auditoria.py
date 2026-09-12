# -*- coding: utf-8 -*-
"""Registro de auditoria de requisições HTTP."""
from datetime import datetime
from app import db


ACAO_OPCOES = [
    'view', 'search', 'create', 'update', 'delete',
    'export', 'print', 'login',
]

MODULO_OPCOES = [
    'contratos', 'contrato_financeiro', 'chamados', 'configuracoes', 'relatorios',
    'usuarios', 'unidades', 'salas', 'equipamentos', 'auth',
    'transferencias', 'planejamentos', 'empresas', 'links',
    'rh', 'solicitacoes', 'notificacoes', 'predios', 'dashboard',
    'nsp',
]


class Auditoria(db.Model):
    __tablename__ = 'auditoria'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    acao = db.Column(db.String(50))
    modulo = db.Column(db.String(80))
    endpoint = db.Column(db.String(200))
    url = db.Column(db.String(500))
    method = db.Column(db.String(10))
    parametros = db.Column(db.JSON)
    entity_type = db.Column(db.String(80))
    entity_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    response_status = db.Column(db.Integer)
    detalhes = db.Column(db.Text)

    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
