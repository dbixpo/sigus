"""Recria o usuário administrador.

APAGA todos os usuários com perfil administrador e cria um novo.

Não use em produção. Para trocar senha de um admin existente:
    python scripts/reset_usuario_sigus.py --email ... --nova-senha ...

Obrigatório no ambiente:
    SIGUS_ADMIN_EMAIL
    SIGUS_ADMIN_SENHA
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.usuario import Usuario

email = (os.environ.get('SIGUS_ADMIN_EMAIL') or '').strip().lower()
senha = os.environ.get('SIGUS_ADMIN_SENHA') or ''
if not email or not senha:
    sys.exit(
        'Defina SIGUS_ADMIN_EMAIL e SIGUS_ADMIN_SENHA. '
        'Este script remove TODOS os administradores. Prefira scripts/reset_usuario_sigus.py.'
    )

app = create_app()
with app.app_context():
    antigos = Usuario.query.filter_by(perfil='administrador').all()
    for u in antigos:
        print(f'  Removendo: {u.email}')
        db.session.delete(u)
    db.session.commit()

    novo = Usuario(
        nome='Administrador SIGUS',
        email=email,
        perfil='administrador',
        ativo=True,
    )
    novo.set_senha(senha)
    db.session.add(novo)
    db.session.commit()
    print(f'  Criado: {novo.email} (id={novo.id})')
    print('OK.')
