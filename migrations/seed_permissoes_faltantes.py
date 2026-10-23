# -*- coding: utf-8 -*-
"""Cria em perfil_permissoes só as seções que ainda não têm linha.

Não altera interruptor que o administrador já gravou. Pode rodar de novo.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.perfil_permissao import PerfilPermissao

CATALOGOS = (
    'CONF_Feriados', 'CONF_TiposAcao', 'CONF_TiposUnidade', 'CONF_PadraoSalas',
    'CONF_TiposSala', 'CONF_Classificacao', 'CONF_CatalogoEquip', 'CONF_StatusEquip',
    'CONF_TiposVeiculo', 'CONF_Marcas', 'CONF_Divisoes', 'CONF_StatusChamado',
    'CONF_Cbos', 'CONF_NspCatalogo',
)
QUEM_JA_MEXIA_NO_CATALOGO = ('gestor_secretaria', 'coordenador', 'administrativo')
TODOS = QUEM_JA_MEXIA_NO_CATALOGO + ('profissional',)


def garantir(perfil, secao, ver, editar, adicionar):
    existe = PerfilPermissao.query.filter_by(perfil=perfil, secao=secao).first()
    if existe:
        return 0
    db.session.add(PerfilPermissao(
        perfil=perfil, secao=secao, ver=ver, editar=editar, adicionar=adicionar,
    ))
    return 1


app = create_app()
with app.app_context():
    novas = 0
    for perfil in QUEM_JA_MEXIA_NO_CATALOGO:
        for secao in CATALOGOS:
            novas += garantir(perfil, secao, True, True, True)
        novas += garantir(perfil, 'CONF_Sistema', True, False, False)
        novas += garantir(perfil, 'CONF_Identidade', False, False, False)
        novas += garantir(perfil, 'Mural', True, perfil == 'gestor_secretaria', True)
        novas += garantir(perfil, 'RH_Apontamentos', True, True, True)
    for secao in CATALOGOS:
        novas += garantir('profissional', secao, False, False, False)
    novas += garantir('profissional', 'CONF_Sistema', False, False, False)
    novas += garantir('profissional', 'CONF_Identidade', False, False, False)
    # Ver o mural todo mundo já via. Publicar e comunicar várias unidades, não.
    novas += garantir('profissional', 'Mural', True, False, False)
    # A planilha da unidade continua limitada ao papel na unidade.
    novas += garantir('profissional', 'RH_Apontamentos', True, True, True)
    db.session.commit()
    print(f'OK: {novas} linhas novas. Linhas existentes ficaram como estavam.')
os._exit(0)
