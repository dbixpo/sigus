# -*- coding: utf-8 -*-
"""Audita e repara termos aceitos com equipamentos fora da unidade destino.

Uso:
    python migrations/reparar_realocacao_transferencias.py --dry-run
    python migrations/reparar_realocacao_transferencias.py
    python migrations/reparar_realocacao_transferencias.py --patrimonio 177971
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.transferencia import DocumentoTransferencia, ItemDocumentoTransferencia
from app.routes.transferencias import (
    auditar_realocacoes_pendentes,
    reparar_realocacoes_pendentes,
    _variantes_patrimonio,
)


def _filtrar_por_patrimonio(pendencias, patrimonio):
    variantes = set(_variantes_patrimonio(patrimonio))
    return [p for p in pendencias if p.get('item') in variantes or patrimonio in str(p.get('item', ''))]


def main(dry_run=False, patrimonio=None):
    app = create_app()
    with app.app_context():
        pendencias = auditar_realocacoes_pendentes()
        if patrimonio:
            pendencias = _filtrar_por_patrimonio(pendencias, patrimonio)

        if not pendencias:
            print('Nenhuma pendência de realocação encontrada.')
            return

        print(f'Pendências encontradas: {len(pendencias)}')
        for p in pendencias:
            ref = f"Doc #{p['doc_id']}" if 'doc_id' in p else f"Transf #{p['transf_id']}"
            print(f'  - {ref} | {p["item"]} | {p["motivo"]}')

        if dry_run:
            print('\nDry-run: nenhuma alteração gravada. Rode sem --dry-run para corrigir.')
            return

        resultado = reparar_realocacoes_pendentes()
        db.session.commit()
        print(
            f'\nReparo concluído: {resultado["movidos"]} movido(s), '
            f'{resultado["criados"]} cadastrado(s).'
        )
        if resultado['nao_resolvidos']:
            print('Não resolvidos (sem patrimônio/série ou tipo desconhecido):')
            for nr in resultado['nao_resolvidos']:
                print(f'  - Doc #{nr["doc_id"]}: {nr["item"]}')

        restantes = auditar_realocacoes_pendentes()
        if patrimonio:
            restantes = _filtrar_por_patrimonio(restantes, patrimonio)
        if restantes:
            print(f'\nAtenção: ainda restam {len(restantes)} pendência(s) após o reparo.')
        else:
            print('\nAuditoria pós-reparo: nenhuma pendência com patrimônio/série.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Audita e repara realocação de transferências aceitas.')
    parser.add_argument('--dry-run', action='store_true', help='Somente lista pendências')
    parser.add_argument('--patrimonio', help='Filtrar por patrimônio (ex: 177971)')
    args = parser.parse_args()
    main(dry_run=args.dry_run, patrimonio=args.patrimonio)
