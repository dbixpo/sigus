# -*- coding: utf-8 -*-
"""Primeira instalação em banco vazio (outro município ou homologação nova).

Cria as tabelas a partir dos models e aplica os seeds essenciais.
Não use em produção que já tem dados. Não restaura dump da Prefeitura de Sorocaba.

Na raiz do repositório, com o .env apontando para o banco VAZIO:

    .\\venv\\Scripts\\python.exe migrations\\bootstrap_nova_instalacao.py

Depois: primeiro administrador (só banco vazio) e identidade da casa.

    $env:SIGUS_ADMIN_EMAIL='admin@seu-municipio.gov.br'
    $env:SIGUS_ADMIN_SENHA='...'
    .\\venv\\Scripts\\python.exe migrations\\recriar_admin.py
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
import app.models  # noqa: F401 — registra tabelas no metadata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEEDS = [
    'criar_tabela_cbos.py',
    'add_identidade_sistema.py',
    'add_perfil_permissoes.py',
    'add_noticias_mural.py',
    'add_ciencia_auditoria.py',
    'add_ciencia_cpf.py',
    'add_ciencia_filtros.py',
    'add_mural_social.py',
    'add_lojinha_destino.py',
    'add_nsp.py',
    'add_nsp_sis.py',
    'add_agenda.py',
    'add_agenda_reunioes.py',
    'add_feriados.py',
    'add_status_chamado.py',
]

UPLOADS = [
    os.path.join('app', 'static', 'uploads', 'comunicados'),
    os.path.join('app', 'static', 'uploads', 'acoes'),
    os.path.join('app', 'static', 'uploads', 'nsp'),
    os.path.join('app', 'static', 'uploads', 'chamados'),
    os.path.join('app', 'static', 'uploads', 'identidade'),
    os.path.join('app', 'static', 'uploads', 'perfis'),
]


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        print('OK: tabelas criadas (create_all).')

    for rel in UPLOADS:
        os.makedirs(os.path.join(RAIZ, rel), exist_ok=True)
    os.makedirs(os.path.join(RAIZ, 'logs'), exist_ok=True)

    py = sys.executable
    for nome in SEEDS:
        caminho = os.path.join(RAIZ, 'migrations', nome)
        print(f'— {nome}')
        r = subprocess.run([py, caminho], cwd=RAIZ)
        if r.returncode != 0:
            sys.exit(f'Falhou: {nome}')

    print('OK: bootstrap concluído. Crie o administrador e ajuste a identidade.')


if __name__ == '__main__':
    main()
