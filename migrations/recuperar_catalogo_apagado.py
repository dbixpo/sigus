# -*- coding: utf-8 -*-
"""Recoloca no catálogo o que as planilhas ainda têm e o banco perdeu.

Não cria equipamento físico. Não renomeia tipo que já existe. Não mexe em
informática que já está cadastrada. Campos personalizados que só existiam
na tela não estão nas planilhas e não voltam.

    python migrations/recuperar_catalogo_apagado.py
    python migrations/recuperar_catalogo_apagado.py --aplicar
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.equipamento import TipoEquipamento, vincular_categoria
from app.models.tipo_sala import KitPadraoSala, TipoSala
from importar_itens_flavia import (
    ICONES, NAO_CADASTRAR, PLANILHA, aplicar as aplicar_flavia, ler as ler_flavia, norm,
)
from importar_padrao_salas import PLANILHA_PADRAO, ler_planilha

# Informática que já estava no SIGUS: não cria de novo se o nome já existe.
# Se o tipo sumiu, a planilha pode recolocá-lo.


def main():
    aplicar = '--aplicar' in sys.argv
    if not os.path.isfile(PLANILHA):
        raise SystemExit(f'Planilha não encontrada: {PLANILHA}')
    if not os.path.isfile(PLANILHA_PADRAO):
        raise SystemExit(f'Planilha não encontrada: {PLANILHA_PADRAO}')

    flavia = ler_flavia(PLANILHA)
    _, itens, kit, _, _ = ler_planilha(PLANILHA_PADRAO)

    app = create_app()
    with app.app_context():
        por_norm = {norm(t.nome): t for t in TipoEquipamento.query.all()}
        codigos = {t.codigo: t for t in TipoEquipamento.query.all() if t.codigo}
        faltam_flavia = [nome for nome in flavia if norm(nome) not in por_norm and norm(nome) not in NAO_CADASTRAR]
        faltam_padrao = [
            (codigo, info['nome']) for codigo, info in itens.items()
            if norm(info['nome']) not in por_norm and codigo not in codigos
        ]
        salas = {s.codigo: s for s in TipoSala.query.all() if s.codigo}
        kit_faltando = 0
        for amb, item in kit:
            if amb not in salas:
                continue
            tipo = codigos.get(item) or por_norm.get(norm(itens[item]['nome']))
            if not tipo:
                kit_faltando += 1
                continue
            existe = KitPadraoSala.query.filter_by(
                tipo_sala_id=salas[amb].id, tipo_equipamento_id=tipo.id,
            ).first()
            if not existe:
                kit_faltando += 1
        print(f'planilha Flavia: {len(flavia)} nomes')
        print(f'planilha padrao: {len(itens)} itens')
        print(f'tipos no banco: {len(por_norm)}')
        print(f'tipos a criar pela Flavia: {len(faltam_flavia)}')
        print(f'tipos a criar so pelo padrao: {len(faltam_padrao)}')
        print(f'linhas de kit que faltam (onde a sala padrao ja existe): {kit_faltando}')
        if not aplicar:
            print('Simulacao. Nada foi gravado.')
            return

        pulados, criados, reusados, marcas, modelos = aplicar_flavia(flavia)
        db.session.flush()
        por_norm = {norm(t.nome): t for t in TipoEquipamento.query.all()}
        codigos = {t.codigo: t for t in TipoEquipamento.query.all() if t.codigo}
        criados_padrao = 0
        for codigo, info in itens.items():
            if codigo in codigos:
                continue
            tipo = por_norm.get(norm(info['nome']))
            if tipo:
                if not tipo.codigo:
                    tipo.codigo = codigo
                    codigos[codigo] = tipo
                continue
            if norm(info['nome']) in NAO_CADASTRAR:
                continue
            tipo = TipoEquipamento(
                nome=info['nome'][:150],
                codigo=codigo,
                tem_patrimonio=True,
                ativo=True,
                icone=ICONES.get(info['classificacao'], 'fas fa-box'),
                valor_referencia=info['valor'],
                natureza_kit=info['natureza'],
            )
            db.session.add(tipo)
            db.session.flush()
            if info['classificacao']:
                vincular_categoria(tipo, info['classificacao'])
            por_norm[norm(tipo.nome)] = tipo
            codigos[codigo] = tipo
            criados_padrao += 1

        salas = {s.codigo: s for s in TipoSala.query.all() if s.codigo}
        kits = 0
        for (amb, item), qtd in kit.items():
            sala = salas.get(amb)
            tipo = codigos.get(item)
            if not sala or not tipo:
                continue
            linha = KitPadraoSala.query.filter_by(
                tipo_sala_id=sala.id, tipo_equipamento_id=tipo.id,
            ).first()
            if linha:
                continue
            db.session.add(KitPadraoSala(
                tipo_sala_id=sala.id,
                tipo_equipamento_id=tipo.id,
                quantidade=qtd,
            ))
            kits += 1
        db.session.commit()
        print(f'tipos criados pela Flavia: {criados}')
        print(f'tipos que ja existiam e receberam marca/modelo: {reusados}')
        print(f'marcas novas: {marcas}')
        print(f'modelos novos: {modelos}')
        print(f'tipos criados pelo padrao: {criados_padrao}')
        print(f'kits inseridos: {kits}')
        print(f'ignorados por ja serem de informatica: {len(pulados)}')


if __name__ == '__main__':
    main()
