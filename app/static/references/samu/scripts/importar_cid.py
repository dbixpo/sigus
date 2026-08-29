"""
Script para importar CID-10 e CID-O dos arquivos XML oficiais do DATASUS.
Execute: python scripts/importar_cid.py
Ou: flask cid-import (se o comando estiver registrado)

Os XMLs devem estar em assets/references/CID10XML/
- CID10.xml
- CID-O.xml
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.cid10_import import importar_todos

def main():
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    with app.app_context():
        r = importar_todos(app)
        if r['erros']:
            for e in r['erros']:
                print(f"ERRO: {e}", file=sys.stderr)
        c10 = r['cid10']
        co = r['cido']
        print(f"CID-10: {c10['novos']} novos, {c10['atualizados']} atualizados")
        print(f"CID-O:  {co['novos']} novos, {co['atualizados']} atualizados")
        print("Importação concluída.")

if __name__ == '__main__':
    main()
