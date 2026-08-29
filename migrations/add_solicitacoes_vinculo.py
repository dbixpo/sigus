# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.solicitacao_vinculo import SolicitacaoVinculo  # noqa: importa para criar tabela

app = create_app()
with app.app_context():
    db.create_all()
    print("OK: tabela solicitacoes_vinculo criada (se não existia).")
