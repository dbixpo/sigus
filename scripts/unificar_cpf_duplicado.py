#!/usr/bin/env python3
"""Une cadastros com o mesmo CPF e tira a cópia que não tem matrícula.

Fica o cadastro que já tem matrícula. Se a cópia sem matrícula estiver
ligada a uma unidade, o vínculo passa para quem fica — e, se essa pessoa
tem uma matrícula só, o vínculo da unidade aponta para ela.

Não apaga quando os dois cadastros têm matrícula (pessoas diferentes com
CPF repetido por engano) nem quando a cópia tem chamado, ficha ou outro
histórico. Nesse caso só lista, para alguém decidir na mão.

Uso (na raiz do projeto, com o .env do banco):
  python scripts/unificar_cpf_duplicado.py
  python scripts/unificar_cpf_duplicado.py --aplicar
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sqlalchemy import text

from app import create_app, db
from app.models.matricula import MatriculaProfissional
from app.models.unidade import UsuarioUnidade
from app.models.usuario import Usuario
from app.utils import cpf_valido, digitos_cpf


def _mascarar(digitos):
    if len(digitos) != 11:
        return digitos or '(vazio)'
    return f'{digitos[:3]}.***.***-{digitos[-2:]}'


def _refs_fk():
    return db.session.execute(text("""
        SELECT c.relname AS tabela, a.attname AS coluna, co.confdeltype AS acao
        FROM pg_constraint co
        JOIN pg_class c ON c.oid = co.conrelid
        JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY (co.conkey)
        JOIN pg_class f ON f.oid = co.confrelid
        WHERE co.contype = 'f' AND f.relname = 'usuarios'
        ORDER BY 1, 2
    """)).fetchall()


def _contagens(usuario_id, refs):
    achados = []
    for tabela, coluna, acao in refs:
        n = db.session.execute(
            text(f'SELECT count(*) FROM {tabela} WHERE {coluna} = :id'),
            {'id': usuario_id},
        ).scalar()
        if n:
            achados.append((tabela, coluna, acao, n))
    return achados


def _mover_vinculos_unidade(origem, destino):
    """Passa o vínculo de unidade da cópia para quem fica. Devolve o que fez."""
    feitos = []
    mats = MatriculaProfissional.query.filter_by(usuario_id=destino.id, ativo=True).all()
    mat_unica = mats[0] if len(mats) == 1 else None
    for vinculo in UsuarioUnidade.query.filter_by(usuario_id=origem.id).all():
        ja = UsuarioUnidade.query.filter_by(
            usuario_id=destino.id, unidade_id=vinculo.unidade_id,
        ).first()
        if ja:
            if not ja.matricula_id and vinculo.matricula_id:
                ja.matricula_id = vinculo.matricula_id
                feitos.append(f'unidade {vinculo.unidade_id}: matrícula copiada para o vínculo que já existia')
            elif not ja.matricula_id and mat_unica:
                ja.matricula_id = mat_unica.id
                feitos.append(f'unidade {vinculo.unidade_id}: matrícula {mat_unica.numero} no vínculo que já existia')
            db.session.delete(vinculo)
            feitos.append(f'unidade {vinculo.unidade_id}: vínculo repetido da cópia removido')
            continue
        vinculo.usuario_id = destino.id
        if not vinculo.matricula_id and mat_unica:
            vinculo.matricula_id = mat_unica.id
            feitos.append(
                f'unidade {vinculo.unidade_id}: vínculo passou para id {destino.id} '
                f'com a matrícula {mat_unica.numero}'
            )
        else:
            feitos.append(f'unidade {vinculo.unidade_id}: vínculo passou para id {destino.id}')
    return feitos


def _completar_matricula_nos_vinculos(usuario):
    """Se a pessoa tem uma matrícula ativa e o vínculo da unidade está sem ela, preenche."""
    mats = MatriculaProfissional.query.filter_by(usuario_id=usuario.id, ativo=True).all()
    if len(mats) != 1:
        return []
    mat = mats[0]
    feitos = []
    for vinculo in UsuarioUnidade.query.filter_by(usuario_id=usuario.id, ativo=True).all():
        if vinculo.matricula_id:
            continue
        vinculo.matricula_id = mat.id
        feitos.append(f'unidade {vinculo.unidade_id}: matrícula {mat.numero} gravada no vínculo')
    return feitos


def unificar(aplicar):
    refs = _refs_fk()
    usuarios = Usuario.query.filter(Usuario.cpf.isnot(None)).all()
    grupos = defaultdict(list)
    invalidos = []
    for usuario in usuarios:
        digitos = digitos_cpf(usuario.cpf)
        if not digitos:
            continue
        if not cpf_valido(digitos):
            invalidos.append(usuario)
            continue
        grupos[digitos].append(usuario)

    removidos = []
    conflitos = []
    ajustes = []

    for digitos, lista in sorted(grupos.items(), key=lambda kv: kv[0]):
        if len(lista) < 2:
            continue
        com = [u for u in lista if u.matriculas.first()]
        sem = [u for u in lista if u not in com]
        if not sem or not com:
            conflitos.append((
                digitos,
                [(u.id, u.nome) for u in lista],
                'os cadastros repetidos todos têm matrícula, ou nenhum tem',
            ))
            continue
        if len(com) > 1:
            conflitos.append((
                digitos,
                [(u.id, u.nome) for u in com],
                'mais de um cadastro com matrícula; as cópias sem matrícula é que saem',
            ))
        destino = min(com, key=lambda u: u.id)
        for origem in sem:
            ponto = db.session.begin_nested()
            passos = _mover_vinculos_unidade(origem, destino)
            db.session.flush()
            restantes = _contagens(origem.id, refs)
            # a = NO ACTION, r = RESTRICT. Cascade e SET NULL acompanham a exclusão.
            bloqueios = [(t, c, n) for t, c, acao, n in restantes if acao in ('a', 'r')]
            if bloqueios:
                ponto.rollback()
                conflitos.append((
                    digitos,
                    [(origem.id, origem.nome)],
                    'cópia sem matrícula tem histórico e não foi apagada: '
                    + ', '.join(f'{t}.{c}={n}' for t, c, n in bloqueios),
                ))
                continue
            ficha = {
                'origem_id': origem.id,
                'origem_nome': origem.nome,
                'origem_email': origem.email,
                'destino_id': destino.id,
                'destino_nome': destino.nome,
                'cpf': digitos,
            }
            db.session.delete(origem)
            ponto.commit()
            ajustes.extend(passos)
            ajustes.extend(_completar_matricula_nos_vinculos(destino))
            removidos.append(ficha)

    if aplicar:
        db.session.commit()
    else:
        db.session.rollback()

    return removidos, conflitos, invalidos, ajustes


def main():
    parser = argparse.ArgumentParser(description='Une usuários com o mesmo CPF.')
    parser.add_argument('--aplicar', action='store_true', help='Grava a limpeza. Sem isto, só mostra.')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        removidos, conflitos, invalidos, ajustes = unificar(args.aplicar)
        modo = 'APLICADO' if args.aplicar else 'SIMULAÇÃO (nada gravado)'
        print(modo)
        print(f'Cópias sem matrícula removidas: {len(removidos)}')
        for item in removidos:
            print(
                f'  tirou id={item["origem_id"]} {item["origem_nome"]} <{item["origem_email"]}> '
                f'— ficou id={item["destino_id"]} {item["destino_nome"]} CPF {_mascarar(item["cpf"])}'
            )
        if ajustes:
            print('Vínculos de unidade ajustados:')
            for linha in ajustes:
                print(f'  {linha}')
        if conflitos:
            print(f'Não mexi ({len(conflitos)}):')
            for digitos, lista, motivo in conflitos:
                nomes = '; '.join(f'id={uid} {nome}' for uid, nome in lista)
                print(f'  CPF {_mascarar(digitos)} — {motivo} — {nomes}')
        if invalidos:
            print(f'CPF inválido já gravado ({len(invalidos)}), deixei como está:')
            for u in invalidos:
                print(f'  id={u.id} {u.nome} dígitos={len(digitos_cpf(u.cpf))}')


if __name__ == '__main__':
    main()
