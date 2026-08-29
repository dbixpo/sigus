# -*- coding: utf-8 -*-
"""
Migração: cria tabela perfil_permissoes e popula com os valores padrão
a partir da matriz de permissões hardcoded no Usuario.pode().
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.perfil_permissao import PerfilPermissao

# Matriz padrão: (perfil, secao, ver, editar, adicionar)
DEFAULTS = [
    # administrador — tudo
    ('administrador', 'Unidades', True, True, True),
    ('administrador', 'Salas', True, True, True),
    ('administrador', 'Equipamentos', True, True, True),
    ('administrador', 'Chamados', True, True, True),
    ('administrador', 'Contratos', True, True, True),
    ('administrador', 'Usuários', True, True, True),
    ('administrador', 'Relatórios', True, False, False),
    ('administrador', 'Configurações', True, True, True),
    ('administrador', 'Transferências', True, True, True),
    ('administrador', 'Planejamentos', True, True, True),
    ('administrador', 'Auditoria', True, False, False),
    # gestor_secretaria
    ('gestor_secretaria', 'Unidades', True, False, False),
    ('gestor_secretaria', 'Salas', False, False, False),
    ('gestor_secretaria', 'Equipamentos', False, False, False),
    ('gestor_secretaria', 'Chamados', True, True, False),
    ('gestor_secretaria', 'Contratos', True, True, True),
    ('gestor_secretaria', 'Usuários', True, False, True),
    ('gestor_secretaria', 'Relatórios', True, False, False),
    ('gestor_secretaria', 'Configurações', False, False, False),
    ('gestor_secretaria', 'Transferências', True, True, True),
    ('gestor_secretaria', 'Planejamentos', True, True, True),
    ('gestor_secretaria', 'Auditoria', False, False, False),
    # coordenador
    ('coordenador', 'Unidades', True, False, False),
    ('coordenador', 'Salas', True, True, True),
    ('coordenador', 'Equipamentos', True, True, True),
    ('coordenador', 'Chamados', True, True, True),
    ('coordenador', 'Contratos', False, False, False),
    ('coordenador', 'Usuários', True, False, True),
    ('coordenador', 'Relatórios', True, False, False),
    ('coordenador', 'Configurações', False, False, False),
    ('coordenador', 'Transferências', True, True, True),
    ('coordenador', 'Planejamentos', True, True, True),
    ('coordenador', 'Auditoria', False, False, False),
    # administrativo
    ('administrativo', 'Unidades', True, False, False),
    ('administrativo', 'Salas', True, False, False),
    ('administrativo', 'Equipamentos', True, True, True),
    ('administrativo', 'Chamados', True, True, True),
    ('administrativo', 'Contratos', False, False, False),
    ('administrativo', 'Usuários', True, False, True),
    ('administrativo', 'Relatórios', False, False, False),
    ('administrativo', 'Configurações', False, False, False),
    ('administrativo', 'Transferências', True, True, True),
    ('administrativo', 'Planejamentos', True, True, True),
    ('administrativo', 'Auditoria', False, False, False),
    # profissional
    ('profissional', 'Unidades', True, False, False),
    ('profissional', 'Salas', True, False, False),
    ('profissional', 'Equipamentos', True, False, False),
    ('profissional', 'Chamados', True, False, True),
    ('profissional', 'Contratos', False, False, False),
    ('profissional', 'Usuários', False, False, False),
    ('profissional', 'Relatórios', False, False, False),
    ('profissional', 'Configurações', False, False, False),
    ('profissional', 'Transferências', False, False, False),
    ('profissional', 'Planejamentos', True, True, True),
    ('profissional', 'Auditoria', False, False, False),
]

app = create_app()
with app.app_context():
    PerfilPermissao.__table__.create(db.engine, checkfirst=True)

    if PerfilPermissao.query.count() == 0:
        for perfil, secao, ver, editar, adicionar in DEFAULTS:
            db.session.add(PerfilPermissao(
                perfil=perfil,
                secao=secao,
                ver=ver,
                editar=editar,
                adicionar=adicionar,
            ))
        db.session.commit()
        print("OK: perfil_permissoes criada e populada com valores padrão.")
    else:
        print("OK: perfil_permissoes já existia. Nenhuma alteração.")
