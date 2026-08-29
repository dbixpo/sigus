"""
Script para inicializar o banco de dados SAMU.
Cria as tabelas e um usuário administrador padrão.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.usuario import Usuario
from app.models.unidade_samu import UnidadeSamu
from app.models.tipo_unidade_samu import TipoUnidadeSamu
from app.models.base_descentralizada import BaseDescentralizada
from app.models.cid10 import CID10
from app.models.cido import CidO
from app.models.ocorrencia import Ocorrencia

app = create_app('development')

with app.app_context():
    db.create_all()
    print('Tabelas criadas.')

    # Usuário admin padrão (só cria se não existir)
    admin = Usuario.query.filter_by(usuario='administrador.sd').first()
    if not admin:
        admin = Usuario(
            usuario='administrador.sd',
            nome='Administrador Saúde Digital',
            perfil='administrador',
            ativo=True,
        )
        admin.set_senha('@Qweszxc7895123')
        db.session.add(admin)
        db.session.commit()
        print('Usuário admin criado: administrador.sd / @Qweszxc7895123')
    else:
        print('Usuário admin já existe.')

    # Unidade SAMU padrão (para testes)
    if UnidadeSamu.query.count() == 0:
        u = UnidadeSamu(tipo_registro='central', nome='Central SAMU 192', ativo=True)
        db.session.add(u)
        db.session.commit()
        print('Unidade SAMU padrão criada: Central SAMU 192')

    # Importar CID-10 e CID-O dos XML (se existirem em assets/references/CID10XML/)
    try:
        from app.cid10_import import importar_todos
        r = importar_todos(app)
        if r['erros']:
            for e in r['erros']:
                print(f'Aviso CID: {e}')
        elif r['cid10']['novos'] or r['cid10']['atualizados'] or r['cido']['novos'] or r['cido']['atualizados']:
            c10, co = r['cid10'], r['cido']
            print(f'CID-10: {c10["novos"]} novos, {c10["atualizados"]} atualizados | CID-O: {co["novos"]} novos, {co["atualizados"]} atualizados')
    except Exception as e:
        print(f'Aviso: importação CID não executada: {e}')

    print('Inicialização concluída.')
