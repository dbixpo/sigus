"""Recria o usuário administrador com novo e-mail e senha."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.usuario import Usuario

app = create_app()
with app.app_context():
    # Remove todos os admins existentes
    antigos = Usuario.query.filter_by(perfil='administrador').all()
    for u in antigos:
        print(f'  Removendo: {u.email}')
        db.session.delete(u)
    db.session.commit()

    # Cria novo admin
    novo = Usuario(
        nome='Administrador SIGUS',
        email='administrador.sigus@sorocaba.sp.gov.br',
        perfil='administrador',
        ativo=True,
    )
    novo.set_senha('@Qweszxc7895123')
    db.session.add(novo)
    db.session.commit()
    print(f'  Criado: {novo.email} (id={novo.id})')
    print('OK.')
