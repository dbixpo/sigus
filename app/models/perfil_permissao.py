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
    ('Veiculos',       'Veículos',        'car-front', 'PATRIMÔNIO'),
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
    ('Agenda',         'Agenda',          'calendar-event', 'GESTÃO'),
    ('Planejamentos',  'Planejamentos',   'kanban', 'GESTÃO'),
    ('SegurancaPaciente', 'Segurança do Paciente', 'heart-pulse', 'GESTÃO'),
    ('Relatórios',     'Relatórios',      'bar-chart-line', 'GESTÃO'),
    ('Mural',          'Mural e comunicados', 'images', 'GESTÃO'),
    # OUTROS (seção pai)
    ('OUTROS',         'OUTROS',          'three-dots-vertical', None),
    ('OUT_LinksUteis', 'Links Úteis',    'link-45deg', 'OUTROS'),
    ('OUT_Metabase',   'Metabase',       'chart-pie', 'OUTROS'),
    ('OUT_CadastroPublico', 'Cadastro Público', 'person-plus', 'OUTROS'),
    # RECURSOS HUMANOS (seção pai)
    ('RECURSOS_HUMANOS', 'RECURSOS HUMANOS', 'people-fill', None),
    ('RH_FaltasAbonadas', 'Faltas Abonadas', 'calendar-check', 'RECURSOS_HUMANOS'),
    ('RH_Apontamentos', 'Apontamentos da unidade', 'calendar-week', 'RECURSOS_HUMANOS'),
    # CONFIGURAÇÕES (seção pai)
    ('CONFIGURAÇÕES',  'CONFIGURAÇÕES',  'gear', None),
    ('CONF_Sistema',   'Configurações do Sistema', 'gear-fill', 'CONFIGURAÇÕES'),
    ('CONF_Identidade', 'Identidade e assets', 'landmark', 'CONFIGURAÇÕES'),
    ('CONF_Feriados',  'Feriados',        'calendar-day', 'CONFIGURAÇÕES'),
    ('CONF_Campanhas', 'Campanhas da saúde', 'ribbon', 'CONFIGURAÇÕES'),
    ('CONF_TiposAcao', 'Tipos de ação do mural', 'images', 'CONFIGURAÇÕES'),
    ('CONF_TiposUnidade', 'Tipos de unidade', 'layer-group', 'CONFIGURAÇÕES'),
    ('CONF_PadraoSalas', 'Padrão de salas', 'clipboard-check', 'CONFIGURAÇÕES'),
    ('CONF_TiposSala', 'Tipos de sala',   'door-open', 'CONFIGURAÇÕES'),
    ('CONF_Classificacao', 'Classificação RENEM', 'layer-group', 'CONFIGURAÇÕES'),
    ('CONF_CatalogoEquip', 'Catálogo de equipamentos', 'pc-display', 'CONFIGURAÇÕES'),
    ('CONF_StatusEquip', 'Status de equipamento', 'toggle-on', 'CONFIGURAÇÕES'),
    ('CONF_TiposVeiculo', 'Catálogo de veículos', 'car-front', 'CONFIGURAÇÕES'),
    ('CONF_Marcas',    'Marcas e modelos', 'tag', 'CONFIGURAÇÕES'),
    ('CONF_Divisoes',  'Divisões e setores', 'sitemap', 'CONFIGURAÇÕES'),
    ('CONF_StatusChamado', 'Status de chamados', 'clipboard-list', 'CONFIGURAÇÕES'),
    ('CONF_Cbos',      'CBOs',            'briefcase', 'CONFIGURAÇÕES'),
    ('CONF_NspCatalogo', 'Catálogos da Segurança do Paciente', 'heart-pulse', 'CONFIGURAÇÕES'),
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
    # PATRIMÔNIO - Veículos
    'ver_veiculos':            ('Veiculos', 'ver'),
    'cadastrar_veiculo':       ('Veiculos', 'adicionar'),
    'editar_veiculo':          ('Veiculos', 'editar'),
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
    # GESTÃO - Segurança do Paciente
    'ver_nsp':            ('SegurancaPaciente', 'ver'),
    'editar_nsp':         ('SegurancaPaciente', 'editar'),
    'adicionar_nsp':      ('SegurancaPaciente', 'adicionar'),
    # GESTÃO - Relatórios
    'emitir_relatorios':   ('Relatórios', 'ver'),
    'ver_dashboard_geral': ('Relatórios', 'ver'),
    # GESTÃO - Mural e comunicados
    'ver_mural':           ('Mural', 'ver'),
    'publicar_mural':      ('Mural', 'adicionar'),
    'compartilhar_mural':  ('Mural', 'editar'),
    # OUTROS - Links Úteis
    'ver_links_uteis':     ('OUT_LinksUteis', 'ver'),
    'editar_links_uteis':  ('OUT_LinksUteis', 'editar'),
    'adicionar_links_uteis': ('OUT_LinksUteis', 'adicionar'),
    'ver_metabase':        ('OUT_Metabase', 'ver'),
    'editar_metabase':     ('OUT_Metabase', 'editar'),
    'adicionar_metabase':  ('OUT_Metabase', 'adicionar'),
    # RECURSOS HUMANOS - Faltas Abonadas
    'ver_faltas_abonadas': ('RH_FaltasAbonadas', 'ver'),
    'editar_faltas_abonadas': ('RH_FaltasAbonadas', 'editar'),
    'adicionar_faltas_abonadas': ('RH_FaltasAbonadas', 'adicionar'),
    'ver_apontamentos_unidade': ('RH_Apontamentos', 'ver'),
    'editar_apontamentos_unidade': ('RH_Apontamentos', 'editar'),
    'importar_frequencia': ('RH_Apontamentos', 'adicionar'),
    # CONFIGURAÇÕES - Sistema
    'gerenciar_tipos_equipamento': ('CONF_CatalogoEquip', 'editar'),
    'gerenciar_perfis':    ('CONF_Sistema', 'editar'),
    'ver_configuracoes':   ('CONF_Sistema', 'ver'),
    'ver_identidade':      ('CONF_Identidade', 'ver'),
    'editar_identidade':   ('CONF_Identidade', 'editar'),
    'ver_feriados':        ('CONF_Feriados', 'ver'),
    'editar_feriados':     ('CONF_Feriados', 'editar'),
    'adicionar_feriados':  ('CONF_Feriados', 'adicionar'),
    'ver_campanhas':       ('CONF_Campanhas', 'ver'),
    'editar_campanhas':    ('CONF_Campanhas', 'editar'),
    'adicionar_campanhas': ('CONF_Campanhas', 'adicionar'),
    'ver_tipos_acao':      ('CONF_TiposAcao', 'ver'),
    'editar_tipos_acao':   ('CONF_TiposAcao', 'editar'),
    'adicionar_tipos_acao': ('CONF_TiposAcao', 'adicionar'),
    'ver_tipos_unidade':   ('CONF_TiposUnidade', 'ver'),
    'editar_tipos_unidade': ('CONF_TiposUnidade', 'editar'),
    'adicionar_tipos_unidade': ('CONF_TiposUnidade', 'adicionar'),
    'ver_padrao_salas':    ('CONF_PadraoSalas', 'ver'),
    'editar_padrao_salas': ('CONF_PadraoSalas', 'editar'),
    'adicionar_padrao_salas': ('CONF_PadraoSalas', 'adicionar'),
    'ver_tipos_sala':      ('CONF_TiposSala', 'ver'),
    'editar_tipos_sala':   ('CONF_TiposSala', 'editar'),
    'adicionar_tipos_sala': ('CONF_TiposSala', 'adicionar'),
    'ver_classificacao':   ('CONF_Classificacao', 'ver'),
    'editar_classificacao': ('CONF_Classificacao', 'editar'),
    'adicionar_classificacao': ('CONF_Classificacao', 'adicionar'),
    'ver_catalogo_equip':  ('CONF_CatalogoEquip', 'ver'),
    'editar_catalogo_equip': ('CONF_CatalogoEquip', 'editar'),
    'adicionar_catalogo_equip': ('CONF_CatalogoEquip', 'adicionar'),
    'ver_status_equip':    ('CONF_StatusEquip', 'ver'),
    'editar_status_equip': ('CONF_StatusEquip', 'editar'),
    'adicionar_status_equip': ('CONF_StatusEquip', 'adicionar'),
    'ver_tipos_veiculo':   ('CONF_TiposVeiculo', 'ver'),
    'editar_tipos_veiculo': ('CONF_TiposVeiculo', 'editar'),
    'adicionar_tipos_veiculo': ('CONF_TiposVeiculo', 'adicionar'),
    'ver_marcas':          ('CONF_Marcas', 'ver'),
    'editar_marcas':       ('CONF_Marcas', 'editar'),
    'adicionar_marcas':    ('CONF_Marcas', 'adicionar'),
    'ver_divisoes':        ('CONF_Divisoes', 'ver'),
    'editar_divisoes':     ('CONF_Divisoes', 'editar'),
    'adicionar_divisoes':  ('CONF_Divisoes', 'adicionar'),
    'ver_status_chamado':  ('CONF_StatusChamado', 'ver'),
    'editar_status_chamado': ('CONF_StatusChamado', 'editar'),
    'adicionar_status_chamado': ('CONF_StatusChamado', 'adicionar'),
    'ver_cbos':            ('CONF_Cbos', 'ver'),
    'editar_cbos':         ('CONF_Cbos', 'editar'),
    'adicionar_cbos':      ('CONF_Cbos', 'adicionar'),
    'ver_nsp_catalogo':    ('CONF_NspCatalogo', 'ver'),
    'editar_nsp_catalogo': ('CONF_NspCatalogo', 'editar'),
    'adicionar_nsp_catalogo': ('CONF_NspCatalogo', 'adicionar'),
    # CONFIGURAÇÕES - Usuários
    'gerenciar_usuarios':  ('Usuários', 'editar'),
    'cadastrar_usuario':   ('Usuários', 'adicionar'),
    'ver_usuarios_unidade': ('Usuários', 'ver'),
    'vincular_profissionais': ('Usuários', 'editar'),
    # CONFIGURAÇÕES - Auditoria
    'ver_auditoria':       ('Auditoria', 'ver'),
    # OUTROS - Cadastro Público
    'ver_cadastro_publico': ('OUT_CadastroPublico', 'ver'),
    'editar_cadastro_publico': ('OUT_CadastroPublico', 'editar'),
    'adicionar_cadastro_publico': ('OUT_CadastroPublico', 'adicionar'),
}

# Texto curto na tela de gestão de perfis.
SECAO_DICAS = {
    'Mural': 'Ver mostra o mural. Adicionar publica na própria unidade. Editar permite comunicar para várias unidades.',
    'RH_Apontamentos': 'A tela Apontamentos da unidade só abre para Gestor de Área, Gestor Central e Administrador. Cada um vê só a planilha que ele mesmo subiu. Meus apontamentos continua pessoal.',
    'SegurancaPaciente': 'Ver abre o menu. Quem conduz os casos continua sendo a lista de membros do Núcleo e das comissões.',
    'Relatórios': 'Todos os relatórios do menu, inclusive inventário, mural e base de servidores do RH.',
    'CONF_Sistema': 'Abre o grupo Configurações. Cada catálogo abaixo tem o próprio interruptor.',
    'CONF_Identidade': 'Município, logos e domínio de e-mail. O Administrador sempre pode; os demais só se esta linha estiver marcada.',
    'OUT_CadastroPublico': 'Link e QR code do formulário público de vínculo profissional.',
    'OUT_Metabase': 'Ver abre o menu Metabase. Editar e Adicionar configuram a conexão e os painéis.',
    'Veiculos': 'A aba de veículos da unidade. O catálogo de tipos fica em Configurações.',
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
