# -*- coding: utf-8 -*-
"""Permissões por perfil e seção — Ver, Editar, Adicionar.
Controlado pelo administrador em Configurações > Gestão de Perfis."""
from app import db


# Seções do sistema (ordem para exibição)
# Estrutura: (chave, label, ícone, seção_pai ou None)
SECOES = [
    # PATRIMÔNIO (seção pai)
    ('PATRIMÔNIO',     'PATRIMÔNIO',      'box-seam', None),
    ('PAT_Predios',    'Prédios',         'buildings', 'PATRIMÔNIO'),
    ('Unidades',       'Unidades',        'hospital', 'PATRIMÔNIO'),
    ('Salas',          'Salas',           'door-open', 'PATRIMÔNIO'),
    ('Equipamentos',   'Equipamentos',    'pc-display', 'PATRIMÔNIO'),
    # OPERAÇÕES (seção pai)
    ('OPERAÇÕES',      'OPERAÇÕES',       'briefcase', None),
    ('OP_Chamados',    'Chamados',        'wrench-adjustable', 'OPERAÇÕES'),
    ('OP_GestaoChamados', 'Gestão de Chamados', 'kanban', 'OPERAÇÕES'),
    ('OP_Transferencias', 'Transferências', 'arrow-left-right', 'OPERAÇÕES'),
    ('OP_Contratos',   'Contratos',       'file-earmark-text', 'OPERAÇÕES'),
    ('OP_Emendas',     'Emendas',         'bank', 'OPERAÇÕES'),
    ('OP_Licitacoes',  'Licitações',      'hammer', 'OPERAÇÕES'),
    ('OP_ChamadosSueq','Chamados SUEQ',   'tools', 'OPERAÇÕES'),
    ('OP_ControleEmpenho', 'Controle de Empenho', 'currency-dollar', 'OPERAÇÕES'),
    ('OP_Empresas',    'Empresas',        'building', 'OPERAÇÕES'),
    # GESTÃO (seção pai)
    ('GESTÃO',         'GESTÃO',          'clipboard-check', None),
    ('Planejamentos',  'Planejamentos',   'kanban', 'GESTÃO'),
    ('Agenda',         'Agenda',          'calendar-event', 'GESTÃO'),
    ('Relatórios',     'Relatórios',      'bar-chart-line', 'GESTÃO'),
    # OUTROS (seção pai)
    ('OUTROS',         'OUTROS',          'three-dots-vertical', None),
    ('OUT_LinksUteis', 'Links Úteis',    'link-45deg', 'OUTROS'),
    ('OUT_CadastroPublico', 'Cadastro Público', 'person-plus', 'OUTROS'),
    # RECURSOS HUMANOS (seção pai)
    ('RECURSOS_HUMANOS', 'RECURSOS HUMANOS', 'people-fill', None),
    ('RH_FaltasAbonadas', 'Faltas Abonadas', 'calendar-check', 'RECURSOS_HUMANOS'),
    # CONFIGURAÇÕES (seção pai)
    ('CONFIGURAÇÕES',  'CONFIGURAÇÕES',  'gear', None),
    ('CONF_Sistema',   'Configurações do Sistema', 'gear-fill', 'CONFIGURAÇÕES'),
    ('Usuários',       'Usuários',        'people', 'CONFIGURAÇÕES'),
    ('Auditoria',      'Auditoria',       'journal-text', 'CONFIGURAÇÕES'),
]

# Mapeamento: acao (pode) -> (secao, tipo: ver|editar|adicionar)
ACAO_PARA_SECAO_TIPO = {
    # PATRIMÔNIO - Prédios
    'ver_predios':         ('PAT_Predios', 'ver'),
    'cadastrar_predio':    ('PAT_Predios', 'adicionar'),
    'editar_predio':       ('PAT_Predios', 'editar'),
    # PATRIMÔNIO - Unidades
    'ver_todas_unidades':  ('Unidades', 'ver'),
    'cadastrar_unidade':   ('Unidades', 'adicionar'),
    'editar_unidade':      ('Unidades', 'editar'),
    'excluir_unidade':     ('Unidades', 'editar'),
    # PATRIMÔNIO - Salas
    'cadastrar_sala':      ('Salas', 'adicionar'),
    'editar_sala':         ('Salas', 'editar'),
    'ver_salas':           ('Salas', 'ver'),
    # PATRIMÔNIO - Equipamentos
    'cadastrar_equipamento':   ('Equipamentos', 'adicionar'),
    'editar_equipamento':      ('Equipamentos', 'editar'),
    'dar_baixa_equipamento':   ('Equipamentos', 'editar'),
    'ver_equipamentos':        ('Equipamentos', 'ver'),
    # OPERAÇÕES - Chamados
    'abrir_chamado':       ('OP_Chamados', 'adicionar'),
    'editar_chamado':      ('OP_Chamados', 'editar'),
    'cancelar_chamado':    ('OP_Chamados', 'editar'),
    'fechar_chamado':      ('OP_Chamados', 'editar'),
    'ver_chamados_todos':  ('OP_Chamados', 'ver'),
    # OPERAÇÕES - Gestão de Chamados
    'gerir_chamados_setor': ('OP_GestaoChamados', 'ver'),
    'gerir_chamados_editar': ('OP_GestaoChamados', 'editar'),
    # OPERAÇÕES - Transferências
    'solicitar_transferencia': ('OP_Transferencias', 'adicionar'),
    'aceitar_transferencia':   ('OP_Transferencias', 'editar'),
    'ver_transferencias':      ('OP_Transferencias', 'ver'),
    # OPERAÇÕES - Contratos
    'cadastrar_contrato':  ('OP_Contratos', 'adicionar'),
    'editar_contrato':     ('OP_Contratos', 'editar'),
    'ver_contratos':       ('OP_Contratos', 'ver'),
    # OPERAÇÕES - Emendas / Licitações / Chamados SUEQ
    'ver_emendas':         ('OP_Emendas', 'ver'),
    'editar_emendas':      ('OP_Emendas', 'editar'),
    'adicionar_emendas':   ('OP_Emendas', 'adicionar'),
    'ver_licitacoes':      ('OP_Licitacoes', 'ver'),
    'editar_licitacoes':   ('OP_Licitacoes', 'editar'),
    'adicionar_licitacoes': ('OP_Licitacoes', 'adicionar'),
    'ver_chamados_sueq':   ('OP_ChamadosSueq', 'ver'),
    'editar_chamados_sueq': ('OP_ChamadosSueq', 'editar'),
    'adicionar_chamados_sueq': ('OP_ChamadosSueq', 'adicionar'),
    # OPERAÇÕES - Controle de Empenho
    'ver_controle_empenho': ('OP_ControleEmpenho', 'ver'),
    'editar_controle_empenho': ('OP_ControleEmpenho', 'editar'),
    'adicionar_controle_empenho': ('OP_ControleEmpenho', 'adicionar'),
    # OPERAÇÕES - Empresas
    'ver_empresas':        ('OP_Empresas', 'ver'),
    'editar_empresas':     ('OP_Empresas', 'editar'),
    'adicionar_empresas':  ('OP_Empresas', 'adicionar'),
    # GESTÃO - Planejamentos
    'criar_plano':         ('Planejamentos', 'adicionar'),
    'editar_plano_gut':    ('Planejamentos', 'editar'),
    'criar_acao':          ('Planejamentos', 'adicionar'),
    'alterar_status_acao': ('Planejamentos', 'editar'),
    'ver_planejamentos':  ('Planejamentos', 'ver'),
    # GESTÃO - Agenda
    'ver_agenda':         ('Agenda', 'ver'),
    'editar_agenda':      ('Agenda', 'editar'),
    'adicionar_agenda':   ('Agenda', 'adicionar'),
    # GESTÃO - Relatórios
    'emitir_relatorios':   ('Relatórios', 'ver'),
    'ver_dashboard_geral': ('Relatórios', 'ver'),
    # OUTROS - Links Úteis
    'ver_links_uteis':     ('OUT_LinksUteis', 'ver'),
    'editar_links_uteis':  ('OUT_LinksUteis', 'editar'),
    'adicionar_links_uteis': ('OUT_LinksUteis', 'adicionar'),
    # RECURSOS HUMANOS - Faltas Abonadas
    'ver_faltas_abonadas': ('RH_FaltasAbonadas', 'ver'),
    'editar_faltas_abonadas': ('RH_FaltasAbonadas', 'editar'),
    'adicionar_faltas_abonadas': ('RH_FaltasAbonadas', 'adicionar'),
    # CONFIGURAÇÕES - Sistema
    'gerenciar_tipos_equipamento': ('CONF_Sistema', 'editar'),
    'gerenciar_perfis':    ('CONF_Sistema', 'editar'),
    'ver_configuracoes':   ('CONF_Sistema', 'ver'),
    # CONFIGURAÇÕES - Usuários
    'gerenciar_usuarios':  ('Usuários', 'editar'),
    'cadastrar_usuario':   ('Usuários', 'adicionar'),
    'ver_usuarios_unidade': ('Usuários', 'ver'),
    'vincular_profissionais': ('Usuários', 'editar'),
    # CONFIGURAÇÕES - Auditoria
    'ver_auditoria':       ('Auditoria', 'ver'),
    # Planejamentos
    'criar_plano':         ('Planejamentos', 'adicionar'),
    'editar_plano_gut':    ('Planejamentos', 'editar'),
    'criar_acao':          ('Planejamentos', 'adicionar'),
    'alterar_status_acao': ('Planejamentos', 'editar'),
    # Auditoria
    'ver_auditoria':       ('Auditoria', 'ver'),
    # Gestão de perfis (especial — só admin via código)
    'gerenciar_perfis':    ('Configurações', 'editar'),
    # OUTROS - Cadastro Público
    'ver_cadastro_publico': ('OUT_CadastroPublico', 'ver'),
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
