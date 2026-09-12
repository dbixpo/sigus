# -*- coding: utf-8 -*-
"""Consulta cadastro de paciente no SISWEB (robô da TI), só para preencher o formulário.

Credenciais vêm do .env (SIS_USUARIO / SIS_SENHA). Não versionar senha.
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path


_PADRAO_DIGITO = re.compile(r'\D+')

_DEFAULT_SIS_PATH = Path(
    os.environ.get(
        'SIS_CONSULTA_PATH',
        r'C:\Users\hardr\Documents\GitHub\api-consulta-usuario-sis',
    )
)


def _so_digitos(valor: str) -> str:
    return _PADRAO_DIGITO.sub('', valor or '')


def _criterio(valor: str, tipo: str | None = None) -> dict:
    bruto = (valor or '').strip()
    if not bruto:
        raise ValueError('Informe o dado para buscar no SIS.')
    digitos = _so_digitos(bruto)
    tipo = (tipo or '').strip().lower()
    if tipo in {'cpf', 'cns', 'prontuario'}:
        if tipo == 'cpf':
            if len(digitos) != 11:
                raise ValueError('CPF precisa ter 11 números.')
            return {'cpf': digitos, 'prontuario': '', 'cns': ''}
        if tipo == 'cns':
            if len(digitos) != 15:
                raise ValueError('CNS precisa ter 15 números.')
            return {'cns': digitos, 'prontuario': '', 'cpf': ''}
        if not (digitos or bruto):
            raise ValueError('Informe o prontuário.')
        return {'prontuario': digitos or bruto, 'cpf': '', 'cns': ''}
    if len(digitos) == 11:
        return {'cpf': digitos, 'prontuario': '', 'cns': ''}
    if len(digitos) == 15:
        return {'cns': digitos, 'prontuario': '', 'cpf': ''}
    return {'prontuario': digitos or bruto, 'cpf': '', 'cns': ''}


def _data_iso(valor: str | None) -> str | None:
    texto = (valor or '').strip()
    if not texto:
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(texto[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return None


def configurado() -> bool:
    return bool(os.environ.get('SIS_USUARIO', '').strip() and os.environ.get('SIS_SENHA', '').strip())


def _carregar_pacote():
    raiz = Path(os.environ.get('SIS_CONSULTA_PATH') or _DEFAULT_SIS_PATH)
    if not raiz.is_dir():
        raise RuntimeError(
            'Pasta da consulta SIS não encontrada. Defina SIS_CONSULTA_PATH no .env '
            '(ex.: C:\\Users\\hardr\\Documents\\GitHub\\api-consulta-usuario-sis).'
        )
    caminho = str(raiz.resolve())
    if caminho not in sys.path:
        sys.path.insert(0, caminho)
    from sis.cliente import ClienteSIS
    from sis.paciente import buscar_paciente_id
    return ClienteSIS, buscar_paciente_id


def buscar_paciente(valor: str, tipo: str | None = None) -> dict:
    """Devolve identificação mínima para o formulário do NSP."""
    if not configurado():
        raise RuntimeError('Consulta ao SIS não configurada (SIS_USUARIO / SIS_SENHA no .env).')

    criterio = _criterio(valor, tipo)
    ClienteSIS, buscar_paciente_id = _carregar_pacote()
    usuario = os.environ.get('SIS_USUARIO', '').strip()
    senha = os.environ.get('SIS_SENHA', '').strip()
    ambiente = (os.environ.get('SIS_AMBIENTE') or 'producao').strip().lower()
    ssl_bruto = (os.environ.get('SIS_SSL_VERIFY') or '').strip().lower()
    ssl_verify = None
    if ssl_bruto in {'0', 'false', 'nao', 'não', 'n'}:
        ssl_verify = False
    elif ssl_bruto in {'1', 'true', 'sim', 's'}:
        ssl_verify = True

    cliente = ClienteSIS(usuario, senha, ambiente=ambiente, ssl_verify=ssl_verify)
    cliente.login()
    try:
        _pid, consulta, _primeiro = buscar_paciente_id(cliente, **criterio)
    finally:
        try:
            cliente.logout()
        except Exception:
            pass

    resumo = consulta.get('resumo_pesquisa') or {}
    nome = (resumo.get('nome') or '').strip()
    if not nome:
        raise RuntimeError('O SIS não devolveu o nome do usuário.')
    return {
        'ok': True,
        'nome': nome,
        'nome_mae': (resumo.get('nome_mae') or '').strip() or None,
        'data_nascimento': _data_iso(resumo.get('nascimento')),
        'prontuario': (resumo.get('prontuario') or '').strip() or None,
        'cpf': _so_digitos(resumo.get('cpf') or '') or None,
        'cns': _so_digitos(resumo.get('cns') or '') or None,
        'criterio': consulta.get('tipo'),
    }
