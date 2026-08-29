# -*- coding: utf-8 -*-
"""Permissões por perfil e seção — Ver, Editar, Adicionar.
Controlado pelo administrador em Configurações > Gestão de Perfis."""
from app import db


# Seções do sistema (ordem para exibição)
SECOES = [
    ('Unidades',       'Unidades',        'hospital'),
    ('Salas',          'Salas',           'door-open'),
    ('Equipamentos',   'Equipamentos',    'pc-display'),
    ('Chamados',       'Chamados',        'wrench-adjustable'),
    ('Contratos',      'Contratos',       'file-earmark-text'),
    ('Usuários',       'Usuários',        'people'),
    ('Relatórios',     'Relatórios',      'bar-chart-line'),
    ('Configurações',  'Configurações',   'gear'),
    ('Transferências', 'Transferências',  'arrow-left-right'),
    ('Planejamentos',  'Planejamentos',   'kanban'),
    ('Auditoria',      'Auditoria',       'journal-text'),
]

# Mapeamento: acao (pode) -> (secao, tipo: ver|editar|adicionar)
ACAO_PARA_SECAO_TIPO = {
    # Unidades
    'ver_todas_unidades':  ('Unidades', 'ver'),
    'cadastrar_unidade':   ('Unidades', 'adicionar'),
    'editar_unidade':      ('Unidades', 'editar'),
    'excluir_unidade':     ('Unidades', 'editar'),
    # Salas
    'cadastrar_sala':      ('Salas', 'adicionar'),
    'editar_sala':         ('Salas', 'editar'),
    # Equipamentos
    'cadastrar_equipamento':   ('Equipamentos', 'adicionar'),
    'editar_equipamento':      ('Equipamentos', 'editar'),
    'dar_baixa_equipamento':   ('Equipamentos', 'editar'),
    'gerenciar_tipos_equipamento': ('Configurações', 'editar'),
    # Chamados
    'abrir_chamado':       ('Chamados', 'adicionar'),
    'editar_chamado':      ('Chamados', 'editar'),
    'cancelar_chamado':    ('Chamados', 'editar'),
    'fechar_chamado':      ('Chamados', 'editar'),
    'ver_chamados_todos':  ('Chamados', 'ver'),
    # Contratos
    'cadastrar_contrato':  ('Contratos', 'adicionar'),
    'editar_contrato':     ('Contratos', 'editar'),
    # Usuários
    'gerenciar_usuarios':  ('Usuários', 'editar'),
    'cadastrar_usuario':   ('Usuários', 'adicionar'),
    'ver_usuarios_unidade': ('Usuários', 'ver'),
    'vincular_profissionais': ('Usuários', 'editar'),
    # Relatórios
    'emitir_relatorios':   ('Relatórios', 'ver'),
    'ver_dashboard_geral': ('Relatórios', 'ver'),
    # Transferências
    'solicitar_transferencia': ('Transferências', 'adicionar'),
    'aceitar_transferencia':   ('Transferências', 'editar'),
    'ver_transferencias':      ('Transferências', 'ver'),
    # Planejamentos
    'criar_plano':         ('Planejamentos', 'adicionar'),
    'editar_plano_gut':    ('Planejamentos', 'editar'),
    'criar_acao':          ('Planejamentos', 'adicionar'),
    'alterar_status_acao': ('Planejamentos', 'editar'),
    # Auditoria
    'ver_auditoria':       ('Auditoria', 'ver'),
    # Gestão de perfis (especial — só admin via código)
    'gerenciar_perfis':    ('Configurações', 'editar'),
}


class PerfilPermissao(db.Model):
    """Permissões por perfil e seção (Ver, Editar, Adicionar)."""
    __tablename__ = 'perfil_permissoes'

    perfil   = db.Column(db.String(50), primary_key=True)
    secao    = db.Column(db.String(80), primary_key=True)
    ver      = db.Column(db.Boolean, nullable=False, default=False)
    editar   = db.Column(db.Boolean, nullable=False, default=False)
    adicionar = db.Column(db.Boolean, nullable=False, default=False)

    @classmethod
    def tem_permissao(cls, perfil: str, secao: str, tipo: str) -> bool:
        """Retorna True se o perfil tem a permissão (ver, editar ou adicionar) na seção."""
        row = cls.query.filter_by(perfil=perfil, secao=secao).first()
        if not row:
            return False
        if tipo == 'ver':
            return row.ver
        if tipo == 'editar':
            return row.editar
        if tipo == 'adicionar':
            return row.adicionar
        return False
