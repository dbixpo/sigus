# -*- coding: utf-8 -*-
"""Padrão de salas: compara o kit de cada tipo de sala com o inventário real."""
import re
import unicodedata
from collections import OrderedDict, defaultdict
from decimal import Decimal

from sqlalchemy.orm import joinedload

from app import db
from app.models.equipamento import Equipamento, TipoEquipamento
from app.models.sala import Sala
from app.models.tipo_sala import KitPadraoSala, TipoSala
from app.models.unidade import Unidade

GRUPO_FORA_DO_PADRAO = 'Outros tipos (fora do padrão)'
CLASSIFICACAO_SEM = 'Outros'


def agrupar_tipos_sala(tipos):
    """[(grupo, [tipos])] na ordem do catálogo; tipos sem código vão para o fim."""
    grupos = OrderedDict()
    padrao = sorted((t for t in tipos if t.codigo), key=lambda t: (t.ordem or 999, t.codigo))
    for t in padrao:
        grupos.setdefault(t.grupo or 'Ambientes padrão', []).append(t)
    outros = sorted((t for t in tipos if not t.codigo), key=lambda t: t.nome.lower())
    if outros:
        grupos[GRUPO_FORA_DO_PADRAO] = outros
    return list(grupos.items())


def agrupar_tipos_equipamento(tipos):
    """[(classificação, [tipos])] em ordem alfabética; sem classificação no fim."""
    grupos = defaultdict(list)
    for t in tipos:
        grupos[t.classificacao or CLASSIFICACAO_SEM].append(t)
    ordem = sorted((g for g in grupos if g != CLASSIFICACAO_SEM), key=str.lower)
    if CLASSIFICACAO_SEM in grupos:
        ordem.append(CLASSIFICACAO_SEM)
    return [(g, sorted(grupos[g], key=lambda t: t.nome.lower())) for g in ordem]


def _normalizar(texto):
    texto = unicodedata.normalize('NFD', texto or '')
    return ' '.join(''.join(c for c in texto if not unicodedata.combining(c)).lower().split())


# Primeira regra que casar com "nome da sala + tipo atual" vence; a ordem vai do mais específico ao mais genérico.
# Código None encerra a busca sem sugestão (ex.: banheiro sem sexo definido, corredor).
_REGRAS_AMBIENTE = [
    (r'^corredor', None),
    (r'vestiario.*fem|fem.*vestiario', 'AMB-46'),
    (r'vestiario.*masc|masc.*vestiario', 'AMB-47'),
    (r'(banheiro|sanitario|\bwc\b).*(pcd|acessivel).*fem|(pcd|acessivel).*fem', 'AMB-04'),
    (r'(banheiro|sanitario|\bwc\b).*(pcd|acessivel).*masc|(pcd|acessivel).*masc', 'AMB-05'),
    (r'(banheiro|sanitario|\bwc\b).*fem', 'AMB-06'),
    (r'(banheiro|sanitario|\bwc\b).*masc', 'AMB-07'),
    (r'banheiro|sanitario|\bwc\b|vestiario', None),
    (r'escov', 'AMB-23'),
    (r'odonto|dentist|saude bucal', 'AMB-22'),
    (r'gineco|preventivo|colpo', 'AMB-13'),
    (r'pediat|puericult', 'AMB-12'),
    (r'vacina|imuniza', 'AMB-30'),
    (r'curativo', 'AMB-24'),
    (r'coleta', 'AMB-27'),
    (r'pos[ -]?consulta', 'AMB-21'),
    (r'telessa|telemed|teleconsult|teleatend', 'AMB-17'),
    (r'lilas|protegid', 'AMB-18'),
    (r'emulti|multiprof|psicolog|nutri|fisio|fono|assist\w* social|podolog', 'AMB-16'),
    (r'acolhimento|triagem|escuta|pre[ -]?consulta', 'AMB-15'),
    (r'emergencia|estabiliz|urgencia', 'AMB-29'),
    (r'aplicacao', 'AMB-25'),
    (r'medicac|inalac|nebuliz|reidrat|observac', 'AMB-26'),
    (r'esteriliz|\bcme\b', 'AMB-33'),
    (r'farmacia|dispensa', 'AMB-38'),
    (r'almox', 'AMB-49'),
    (r'\bcopa\b|cozinha|refeit', 'AMB-45'),
    (r'reuniao|auditorio', 'AMB-41'),
    (r'\bacs\b|agentes? comunit', 'AMB-42'),
    (r'faturamento|\bguias\b', 'AMB-43'),
    (r'coordena|gerencia|gestao|administra|diretoria', 'AMB-40'),
    (r'recepc', 'AMB-01'),
    (r'espera', 'AMB-02'),
    (r'arquivo|prontuario', 'AMB-03'),
    (r'amament', 'AMB-09'),
    (r'brinquedo', 'AMB-10'),
    (r'fraldario', 'AMB-08'),
    (r'conforto|descompress|convivencia|descanso', 'AMB-48'),
    (r'\brack\b|servidor|\bti\b|\bcpd\b', 'AMB-56'),
    (r'\bdml\b|material de limpeza', 'AMB-51'),
    (r'residuo|\blixo\b', 'AMB-52'),
    (r'pratica|coletiva', 'AMB-31'),
    (r'consultorio|clinico', 'AMB-11'),
]


def sugerir_ambiente(sala):
    """Código AMB sugerido pelo nome da sala e pelo tipo atual (None se nada casar)."""
    texto = _normalizar(f'{sala.nome} {sala.tipo_label}')
    for padrao, codigo in _REGRAS_AMBIENTE:
        if re.search(padrao, texto):
            return codigo
    return None


def candidatos_catalogo(tipo, catalogo):
    """Itens do catálogo cujo nome começa pela primeira palavra do tipo (ex.: Balança → as 3 balanças)."""
    palavras = [p for p in _normalizar(tipo.nome).split() if len(p) >= 4]
    if not palavras:
        return []
    return [c for c in catalogo if _normalizar(c.nome).startswith(palavras[0])]


def resumo_padrao():
    """Números da visão geral em Configurações → Padrão de salas."""
    ambientes = TipoSala.query.filter(TipoSala.codigo.isnot(None)).count()
    com_kit = db.session.query(db.func.count(db.distinct(KitPadraoSala.tipo_sala_id))).scalar() or 0
    itens = TipoEquipamento.query.filter(TipoEquipamento.codigo.isnot(None)).count()
    itens_sem_valor = TipoEquipamento.query.filter(TipoEquipamento.codigo.isnot(None),
                                                   TipoEquipamento.valor_referencia.is_(None)).count()

    def salas(so_padrao):
        q = (db.session.query(TipoSala.codigo.isnot(None), db.func.count(Sala.id))
             .select_from(Sala).join(Unidade, Unidade.id == Sala.unidade_id)
             .outerjoin(TipoSala, TipoSala.id == Sala.tipo_sala_id)
             .filter(Sala.ativo.is_(True), Unidade.status == 'ativa'))
        if so_padrao:
            q = q.filter(Unidade.codigo_imovel.isnot(None))
        contagem = dict(q.group_by(TipoSala.codigo.isnot(None)).all())
        return {'no_padrao': contagem.get(True, 0), 'fora': contagem.get(False, 0) + contagem.get(None, 0)}

    no_catalogo = db.or_(TipoEquipamento.codigo.isnot(None), TipoEquipamento.conta_como_id.isnot(None))
    equip = dict(db.session.query(no_catalogo, db.func.count(Equipamento.id))
                 .select_from(Equipamento).join(TipoEquipamento, TipoEquipamento.id == Equipamento.tipo_equipamento_id)
                 .filter(Equipamento.ativo.is_(True), Equipamento.status != 'baixado')
                 .group_by(no_catalogo).all())
    return {
        'ambientes': ambientes, 'ambientes_com_kit': com_kit, 'ambientes_sem_kit': ambientes - com_kit,
        'itens': itens, 'itens_sem_valor': itens_sem_valor,
        'salas_ubs': salas(True), 'salas_todas': salas(False),
        'equip_no_catalogo': equip.get(True, 0), 'equip_fora': equip.get(False, 0),
    }


def _kits_por_tipo_sala(tipo_sala_ids=None):
    q = KitPadraoSala.query.options(joinedload(KitPadraoSala.tipo_equipamento))
    if tipo_sala_ids:
        q = q.filter(KitPadraoSala.tipo_sala_id.in_(tipo_sala_ids))
    kits = defaultdict(list)
    for k in q.all():
        kits[k.tipo_sala_id].append(k)
    for lista in kits.values():
        lista.sort(key=lambda k: (k.tipo_equipamento.codigo or '', k.tipo_equipamento.nome))
    return kits


def _contagem_equipamentos(sala_ids):
    """{sala_id: {tipo_equipamento_id: qtd}} já aplicando o 'conta como'."""
    contagem = defaultdict(lambda: defaultdict(int))
    if not sala_ids:
        return contagem
    equivalente = dict(db.session.query(TipoEquipamento.id, TipoEquipamento.conta_como_id)
                       .filter(TipoEquipamento.conta_como_id.isnot(None)).all())
    linhas = (db.session.query(Equipamento.sala_id, Equipamento.tipo_equipamento_id, db.func.count(Equipamento.id))
              .filter(Equipamento.sala_id.in_(sala_ids), Equipamento.ativo.is_(True),
                      Equipamento.status != 'baixado')
              .group_by(Equipamento.sala_id, Equipamento.tipo_equipamento_id).all())
    for sala_id, tipo_id, n in linhas:
        contagem[sala_id][equivalente.get(tipo_id, tipo_id)] += n
    return contagem


def _avaliar_sala(sala, kit, contagem_sala):
    linhas = []
    esperado = atendido = falta = sobra = 0
    custo = Decimal('0')
    for k in kit:
        te = k.tipo_equipamento
        enc = contagem_sala.get(te.id, 0)
        f = max(0, k.quantidade - enc)
        s = max(0, enc - k.quantidade)
        c = (te.valor_referencia or Decimal('0')) * f
        linhas.append({
            'tipo_equipamento': te, 'esperado': k.quantidade, 'encontrado': enc,
            'falta': f, 'sobra': s, 'valor': te.valor_referencia, 'custo': c, 'observacao': k.observacao,
        })
        esperado += k.quantidade
        atendido += min(enc, k.quantidade)
        falta += f
        sobra += s
        custo += c
    return {
        'sala': sala, 'linhas': linhas, 'esperado': esperado, 'atendido': atendido,
        'falta': falta, 'sobra': sobra, 'custo': custo,
        'pct': round(100 * atendido / esperado) if esperado else None,
    }


def aderencia_sala(sala):
    """Avaliação de uma sala (None se o tipo não tem kit)."""
    if not sala.tipo_sala_id:
        return None
    kit = _kits_por_tipo_sala([sala.tipo_sala_id]).get(sala.tipo_sala_id)
    if not kit:
        return None
    return _avaliar_sala(sala, kit, _contagem_equipamentos([sala.id])[sala.id])


def calcular_aderencia(unidade_ids=None, tipo_unidade_ids=None, tipo_sala_ids=None, so_unidades_do_padrao=False):
    """Avalia todas as salas ativas do filtro.

    unidade_ids=None significa todas as unidades (lista vazia = nenhuma).
    so_unidades_do_padrao restringe às unidades com código de imóvel (as da planilha do padrão).
    """
    q = (Sala.query.join(Unidade, Sala.unidade_id == Unidade.id)
         .options(joinedload(Sala.unidade), joinedload(Sala.tipo_sala))
         .filter(Sala.ativo.is_(True), Unidade.status == 'ativa'))
    if so_unidades_do_padrao:
        q = q.filter(Unidade.codigo_imovel.isnot(None))
    if unidade_ids is not None:
        q = q.filter(Sala.unidade_id.in_(unidade_ids or [0]))
    if tipo_unidade_ids:
        q = q.filter(Unidade.tipo_unidade_id.in_(tipo_unidade_ids))
    if tipo_sala_ids:
        q = q.filter(Sala.tipo_sala_id.in_(tipo_sala_ids))
    salas = q.all()

    kits = _kits_por_tipo_sala()
    contagem = _contagem_equipamentos([s.id for s in salas if s.tipo_sala_id in kits])

    avaliadas, sem_padrao, sem_kit = [], [], []
    por_unidade = OrderedDict()
    por_item = {}

    for s in sorted(salas, key=lambda s: (s.unidade.nome.lower(), s.nome.lower())):
        u = por_unidade.setdefault(s.unidade_id, {
            'unidade': s.unidade, 'salas': 0, 'avaliadas': 0, 'sem_padrao': 0, 'sem_kit': 0,
            'esperado': 0, 'atendido': 0, 'falta': 0, 'sobra': 0, 'custo': Decimal('0'),
        })
        u['salas'] += 1
        tipo = s.tipo_sala
        if not tipo or not tipo.codigo:
            sem_padrao.append(s)
            u['sem_padrao'] += 1
            continue
        kit = kits.get(tipo.id)
        if not kit:
            sem_kit.append(s)
            u['sem_kit'] += 1
            continue
        av = _avaliar_sala(s, kit, contagem[s.id])
        avaliadas.append(av)
        u['avaliadas'] += 1
        for campo in ('esperado', 'atendido', 'falta', 'sobra', 'custo'):
            u[campo] += av[campo]
        for ln in av['linhas']:
            if not ln['falta']:
                continue
            te = ln['tipo_equipamento']
            it = por_item.setdefault(te.id, {
                'tipo_equipamento': te, 'falta': 0, 'custo': Decimal('0'),
                'salas': 0, 'unidades': set(),
            })
            it['falta'] += ln['falta']
            it['custo'] += ln['custo']
            it['salas'] += 1
            it['unidades'].add(s.unidade_id)

    for u in por_unidade.values():
        u['pct'] = round(100 * u['atendido'] / u['esperado']) if u['esperado'] else None
    unidades = sorted((u for u in por_unidade.values() if u['avaliadas'] or u['sem_padrao']),
                      key=lambda u: u['unidade'].nome.lower())
    itens = sorted(por_item.values(), key=lambda i: (-i['custo'], i['tipo_equipamento'].nome))
    for it in itens:
        it['unidades'] = len(it['unidades'])

    esperado = sum(a['esperado'] for a in avaliadas)
    atendido = sum(a['atendido'] for a in avaliadas)
    return {
        'avaliadas': avaliadas,
        'sem_padrao': sem_padrao,
        'sem_kit': sem_kit,
        'unidades': unidades,
        'itens': itens,
        'totais': {
            'salas': len(salas),
            'avaliadas': len(avaliadas),
            'sem_padrao': len(sem_padrao),
            'sem_kit': len(sem_kit),
            'esperado': esperado,
            'atendido': atendido,
            'falta': sum(a['falta'] for a in avaliadas),
            'sobra': sum(a['sobra'] for a in avaliadas),
            'custo': sum((a['custo'] for a in avaliadas), Decimal('0')),
            'pct': round(100 * atendido / esperado) if esperado else None,
        },
    }
