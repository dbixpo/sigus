#!/usr/bin/env python3
"""
Ajuste de senha e/ou perfil direto no banco (use na raiz do projeto; .env com DATABASE_URL).

Exemplos (PowerShell):
  python scripts/reset_usuario_sigus.py --email administrador.sigus@sorocaba.sp.gov.br --nova-senha "NovaSenhaForte123"
  python scripts/reset_usuario_sigus.py --email nicolly.lemos@sorocaba.sp.gov.br --perfil profissional

ATENÇÃO: não versionar senhas em comando ou histórico.
Não use migrations/recriar_admin.py em produção sem backup — ele remove TODOS os usuários com perfil administrador.
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app import create_app, db  # noqa: E402
from app.models.usuario import Usuario, PERFIS  # noqa: E402


def main():
    p = argparse.ArgumentParser(description='Redefine senha e/ou perfil de um usuário SIGUS.')
    p.add_argument('--email', required=True, help='E-mail do usuário (login)')
    p.add_argument('--nova-senha', default='', help='Nova senha em texto plano')
    p.add_argument('--perfil', default=None, choices=list(PERFIS.keys()), help='Novo perfil')
    args = p.parse_args()

    if not args.nova_senha and args.perfil is None:
        p.error('Informe --nova-senha e/ou --perfil.')

    app = create_app()
    with app.app_context():
        email = args.email.strip().lower()
        u = Usuario.query.filter_by(email=email).first()
        if not u:
            print(f'ERRO: nenhum usuário com e-mail {email!r}.')
            sys.exit(1)

        if args.nova_senha:
            u.set_senha(args.nova_senha)
            print('Senha atualizada.')
        if args.perfil is not None:
            u.perfil = args.perfil
            print(f'Perfil atualizado para {args.perfil!r} ({PERFIS[args.perfil]}).')

        db.session.commit()
        print(f'OK: id={u.id} nome={u.nome!r} email={u.email!r} perfil={u.perfil}')


if __name__ == '__main__':
    main()
