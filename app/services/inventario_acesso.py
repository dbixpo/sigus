# -*- coding: utf-8 -*-
"""Quem mexe no inventário.

UBS, na fala da SUEQ, é gestor de área (coordenador) e apoio administrativo.
Eles fazem o primeiro levantamento. Depois que a unidade encerra esse
inventário, só transferem e alteram estado e condição.

SUEQ preenche as informações adicionais e, com a TI, inclui, corrige e
exclui depois do levantamento inicial.
"""

PERFIS_UNIDADE = ('coordenador', 'administrativo')


def _nomes_setor(usuario):
    nomes = []
    for setor in usuario.setores_vinculados:
        nomes.append((setor.nome or '').lower())
        if setor.divisao and setor.divisao.nome:
            nomes.append(setor.divisao.nome.lower())
    return ' '.join(nomes)


def eh_sueq(usuario):
    if not getattr(usuario, 'is_authenticated', False):
        return False
    if usuario.perfil in ('administrador', 'gestor_secretaria'):
        return True
    if 'sueq' in _nomes_setor(usuario):
        return True
    return usuario.pode('editar_chamados_sueq')


def eh_ti(usuario):
    if not getattr(usuario, 'is_authenticated', False):
        return False
    if usuario.perfil == 'administrador':
        return True
    texto = _nomes_setor(usuario)
    return any(p in texto for p in ('informatica', 'informática', 'tecnologia da inform', ' ti', 'ti ')) or texto.strip() in ('ti', 't.i.', 't.i')


def gestor_patrimonio(usuario):
    """SUEQ, TI ou gestão central: inclusão, correção e exclusão."""
    if not getattr(usuario, 'is_authenticated', False):
        return False
    if usuario.perfil in ('administrador', 'gestor_secretaria'):
        return True
    return eh_sueq(usuario) or eh_ti(usuario)


def pode_informacoes_adicionais(usuario):
    """Nota, empenho, incorporação e demais dados patrimoniais: só a SUEQ."""
    return eh_sueq(usuario)


def pode_incluir(usuario, unidade):
    if gestor_patrimonio(usuario):
        return True
    if usuario.perfil in PERFIS_UNIDADE:
        return bool(unidade) and not unidade.inventario_inicial_concluido
    return usuario.pode('cadastrar_equipamento')


def pode_corrigir_cadastro(usuario, unidade):
    """Identificação, tipo, marca, modelo e sala."""
    if gestor_patrimonio(usuario):
        return True
    if usuario.perfil in PERFIS_UNIDADE:
        return bool(unidade) and not unidade.inventario_inicial_concluido
    return usuario.pode('editar_equipamento')


def pode_alterar_estado(usuario, unidade):
    if gestor_patrimonio(usuario):
        return True
    if usuario.perfil in PERFIS_UNIDADE:
        return True
    return usuario.pode('editar_equipamento')


def pode_anexar_documento(usuario, unidade):
    if gestor_patrimonio(usuario):
        return True
    if usuario.perfil in PERFIS_UNIDADE:
        return bool(unidade) and not unidade.inventario_inicial_concluido
    return usuario.pode('editar_equipamento')


def marca_nova_fica_pendente(usuario):
    """Unidade pode cadastrar marca/modelo; a SUEQ valida depois."""
    return usuario.perfil in PERFIS_UNIDADE and not gestor_patrimonio(usuario)
