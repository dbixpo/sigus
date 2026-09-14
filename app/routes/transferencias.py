from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.transferencia import TransferenciaEquipamento, DocumentoTransferencia, ItemDocumentoTransferencia, ItemLojinha
from app.models.equipamento import Equipamento, TipoEquipamento
from app.models.unidade import Unidade, UsuarioUnidade
from app.models.sala import Sala

transferencias_bp = Blueprint('transferencias', __name__, url_prefix='/transferencias')

PREFIXO_PATRIMONIO = 'PMS-'


def _normalizar_patrimonio(valor):
    v = (valor or '').strip()
    if not v:
        return None
    while v.upper().startswith(PREFIXO_PATRIMONIO):
        v = v[len(PREFIXO_PATRIMONIO):].strip()
    return (PREFIXO_PATRIMONIO + v) if v else None


def _variantes_patrimonio(valor):
    """Gera variantes de busca (com/sem prefixo PMS-)."""
    pat = (valor or '').strip()
    if not pat:
        return []
    variantes = {pat, pat.upper()}
    if pat.upper().startswith(PREFIXO_PATRIMONIO):
        sufixo = pat[len(PREFIXO_PATRIMONIO):].strip()
        if sufixo:
            variantes.add(sufixo)
            variantes.add(PREFIXO_PATRIMONIO + sufixo)
    else:
        variantes.add(PREFIXO_PATRIMONIO + pat)
    return list(variantes)


def _equipamento_do_item(item, unidade_origem_id=None):
    """Resolve o equipamento do inventário vinculado a um item de documento."""
    if item.equipamento_id and item.equipamento:
        return item.equipamento

    pat = (item.numero_patrimonio or '').strip()
    ser = (item.numero_serie or '').strip()
    if not pat and not ser:
        return None

    def _buscar(unidade_id=None):
        q = Equipamento.query
        if pat:
            variantes = _variantes_patrimonio(pat)
            q = q.filter(Equipamento.numero_patrimonio.in_(variantes))
        elif ser:
            q = q.filter(Equipamento.numero_serie == ser)
        if unidade_id:
            q = (
                q.join(Sala, Equipamento.sala_id == Sala.id)
                .filter(Sala.unidade_id == unidade_id)
            )
        return q.first()

    if unidade_origem_id:
        eq = _buscar(unidade_origem_id)
        if eq:
            return eq
    return _buscar(None)


def _vincular_equipamento_item(item, unidade_origem_id):
    """Preenche equipamento_id no item quando só há patrimônio/série informados."""
    if item.equipamento_id:
        return item.equipamento
    eq = _equipamento_do_item(item, unidade_origem_id)
    if eq:
        item.equipamento_id = eq.id
    return eq


def _inferir_tipo_equipamento_id(descricao):
    d = (descricao or '').lower()
    if 'all-in-one' in d or 'all in one' in d:
        tipo = TipoEquipamento.query.filter(TipoEquipamento.nome.ilike('%All-In-One%')).first()
    elif any(p in d for p in ('micro', 'computador', 'desktop', 'notebook', ' pc')):
        tipo = TipoEquipamento.query.filter(TipoEquipamento.nome.ilike('%Computador (Gabinete)%')).first()
    else:
        tipo = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).first()
    return tipo.id if tipo else None


def _criar_equipamento_do_item(item, sala, doc, usuario_id=None):
    """Cadastra no inventário da unidade destino quando o termo traz patrimônio/série manual."""
    pat = _normalizar_patrimonio(item.numero_patrimonio)
    ser = (item.numero_serie or '').strip() or None
    if not pat and not ser:
        return None

    if pat:
        existente = Equipamento.query.filter(
            Equipamento.numero_patrimonio.in_(_variantes_patrimonio(item.numero_patrimonio))
        ).first()
        if existente:
            item.equipamento_id = existente.id
            return existente

    tipo_id = _inferir_tipo_equipamento_id(item.descricao_exibicao())
    if not tipo_id:
        return None

    eq = Equipamento(
        sala_id=sala.id,
        tipo_equipamento_id=tipo_id,
        numero_patrimonio=pat,
        numero_serie=ser,
        status='ativo',
        condicao='regular' if item.classificacao == 'B' else 'boa',
        observacoes=(
            f'Cadastrado automaticamente na {doc.tipo_label.lower()} '
            f'(termo #{doc.id}) para {doc.unidade_destino.nome}.'
        ),
        criado_por=usuario_id or (getattr(current_user, 'id', None) if current_user else None) or doc.aceito_por,
        ativo=True,
    )
    db.session.add(eq)
    db.session.flush()
    item.equipamento_id = eq.id
    return eq


def _realocar_itens_documento(doc, sala_id, obs='', criar_se_ausente=False, usuario_id=None):
    """Move equipamentos do documento para a sala de destino. Retorna (movidos, criados, nao_encontrados)."""
    sala = Sala.query.filter_by(
        id=sala_id, unidade_id=doc.unidade_destino_id, ativo=True
    ).first()
    if not sala:
        return 0, 0, ['sala de destino inválida']

    movidos = 0
    criados = 0
    nao_encontrados = []
    uid = usuario_id or (getattr(current_user, 'id', None) if current_user else None) or doc.aceito_por
    if current_user and getattr(current_user, 'is_authenticated', False):
        nome_usuario = current_user.nome
    elif doc.aceitador:
        nome_usuario = doc.aceitador.nome
    else:
        nome_usuario = 'Sistema'

    for item in doc.itens.all():
        eq = _vincular_equipamento_item(item, doc.unidade_origem_id)
        criado_agora = False
        if not eq and criar_se_ausente:
            eq = _criar_equipamento_do_item(item, sala, doc, usuario_id=uid)
            criado_agora = eq is not None
        if not eq:
            if item.numero_patrimonio or item.numero_serie:
                nao_encontrados.append(item.numero_patrimonio_ou_serie() or item.descricao_exibicao())
            continue

        ja_na_sala = eq.sala_id == sala.id
        if not ja_na_sala:
            eq.sala_id = sala.id
        eq.ativo = True

        if criado_agora:
            criados += 1
            _registrar_evento(
                eq,
                f'{doc.tipo_label} aceito — cadastrado em {sala.nome} ({doc.unidade_destino.nome})',
                f'{"Aceito" if doc.status == "pendente" else "Reprocessado"} por {nome_usuario}. {obs}'.strip(),
                usuario_id=uid,
            )
        elif not ja_na_sala:
            movidos += 1
            _registrar_evento(
                eq,
                f'{doc.tipo_label} aceito — alocado em {sala.nome} ({doc.unidade_destino.nome})',
                f'{"Aceito" if doc.status == "pendente" else "Reprocessado"} por {nome_usuario}. {obs}'.strip(),
                usuario_id=uid,
            )
    return movidos, criados, nao_encontrados


def _auditar_documento_aceito(doc):
    """Lista itens de um termo aceito que não estão na sala/unidade de destino."""
    if doc.status != 'aceita' or not doc.sala_destino_id:
        return []
    sala_dest = Sala.query.get(doc.sala_destino_id)
    if not sala_dest:
        return [{'doc_id': doc.id, 'item': '—', 'motivo': 'sala de destino inválida'}]

    pendencias = []
    for item in doc.itens.all():
        ident = item.numero_patrimonio_ou_serie() or item.descricao_exibicao() or f'item #{item.id}'
        eq = item.equipamento if item.equipamento_id else _equipamento_do_item(item, doc.unidade_origem_id)
        if not eq:
            if item.numero_patrimonio or item.numero_serie:
                pendencias.append({
                    'doc_id': doc.id,
                    'item': ident,
                    'motivo': 'equipamento não encontrado no inventário',
                })
            continue
        if eq.sala_id != sala_dest.id:
            local = eq.sala.unidade.nome if eq.sala and eq.sala.unidade else '?'
            pendencias.append({
                'doc_id': doc.id,
                'item': ident,
                'motivo': f'ainda em {local} (sala {eq.sala.nome if eq.sala else eq.sala_id})',
            })
    return pendencias


def _auditar_transferencia_legada(transf):
    """Lista transferências legadas aceitas com equipamento fora da sala destino."""
    if transf.status != 'aceita' or not transf.sala_destino_id or not transf.equipamento:
        return []
    eq = transf.equipamento
    ident = eq.numero_patrimonio or eq.numero_serie or str(eq.id)
    if eq.sala_id != transf.sala_destino_id:
        local = eq.sala.unidade.nome if eq.sala and eq.sala.unidade else '?'
        return [{
            'transf_id': transf.id,
            'item': ident,
            'motivo': f'ainda em {local}',
        }]
    return []


def auditar_realocacoes_pendentes():
    """Auditoria global — termos aceitos com inventário inconsistente."""
    docs = DocumentoTransferencia.query.filter_by(status='aceita').filter(
        DocumentoTransferencia.sala_destino_id.isnot(None)
    ).all()
    legado = TransferenciaEquipamento.query.filter_by(status='aceita').filter(
        TransferenciaEquipamento.sala_destino_id.isnot(None)
    ).all()
    pendencias = []
    for doc in docs:
        pendencias.extend(_auditar_documento_aceito(doc))
    for transf in legado:
        pendencias.extend(_auditar_transferencia_legada(transf))
    return pendencias


def reparar_realocacoes_pendentes(usuario_id=None):
    """Corrige termos aceitos com equipamentos fora da unidade destino."""
    total_movidos = total_criados = 0
    nao_resolvidos = []

    docs = DocumentoTransferencia.query.filter_by(status='aceita').filter(
        DocumentoTransferencia.sala_destino_id.isnot(None)
    ).all()
    for doc in docs:
        if not _auditar_documento_aceito(doc):
            continue
        movidos, criados, parciais = _realocar_itens_documento(
            doc, doc.sala_destino_id, criar_se_ausente=True, usuario_id=usuario_id or doc.aceito_por
        )
        total_movidos += movidos
        total_criados += criados
        if parciais:
            nao_resolvidos.extend({'doc_id': doc.id, 'item': i} for i in parciais)

    for transf in TransferenciaEquipamento.query.filter_by(status='aceita').filter(
        TransferenciaEquipamento.sala_destino_id.isnot(None)
    ).all():
        for p in _auditar_transferencia_legada(transf):
            eq = transf.equipamento
            sala = Sala.query.get(transf.sala_destino_id)
            if eq and sala and eq.sala_id != sala.id:
                eq.sala_id = sala.id
                eq.ativo = True
                _registrar_evento(
                    eq, f'Transferência reprocessada — {sala.nome}',
                    'Correção automática de realocação.', usuario_id=usuario_id or transf.aceito_por
                )
                total_movidos += 1

    return {
        'movidos': total_movidos,
        'criados': total_criados,
        'nao_resolvidos': nao_resolvidos,
    }


def _unidades_do_usuario():
    """Retorna lista de unidade_ids efetivos (considera unidade padrão).
    None = vê todas (gestor central em 'Todas'); lista = unidades para ações."""
    return current_user.ids_unidades_efetivos()


def _pode_escolher_qualquer_unidade():
    """Administrador e gestor central realocam inventário entre qualquer par da rede."""
    return current_user.perfil in ('administrador', 'gestor_secretaria')


def _pode_resolver_aceite(unidade_destino_id):
    """Quem pode aceitar/recusar o termo na unidade destino."""
    if current_user.perfil not in ('administrador', 'gestor_secretaria', 'coordenador', 'administrativo'):
        return False
    if not current_user.pode('aceitar_transferencia'):
        return False
    if _pode_escolher_qualquer_unidade():
        return True
    ids = _unidades_do_usuario()
    return bool(ids) and unidade_destino_id in ids


def _unidades_ativas():
    return Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()


# ──────────────────────────────────────────────
#  LISTAR — pendentes recebidas + histórico
# ──────────────────────────────────────────────
@transferencias_bp.route('/')
@login_required
def listar():
    if not current_user.pode('ver_transferencias'):
        abort(403)
    ids_unidades = _unidades_do_usuario()
    unidade_id = request.args.get('unidade_id', type=int)
    lojinha_classificacao = request.args.get('lojinha_classificacao', '')  # '', 'A', 'B'
    status_concluida = request.args.get('status_concluida', '')  # '', 'aceita', 'recusada', 'cancelada'
    aba = request.args.get('aba', 'pendentes')
    if aba not in ('pendentes', 'enviadas', 'concluidas', 'lojinha'):
        aba = 'pendentes'

    # Filtro de unidade (admin/gestor central veem a rede; o dropdown ainda recorta)
    pode_qualquer = _pode_escolher_qualquer_unidade()
    unidade_filtro = None
    if pode_qualquer:
        if unidade_id:
            unidade_filtro = Unidade.query.get(unidade_id)
            ids_filtro = [unidade_id] if unidade_filtro else None
        else:
            ids_filtro = None
    elif current_user.pode('ver_todas_unidades') and unidade_id:
        unidade_filtro = Unidade.query.get(unidade_id)
        if unidade_filtro:
            ids_filtro = [unidade_id]
        else:
            ids_filtro = ids_unidades
    else:
        ids_filtro = ids_unidades

    def _filtra_unidades(q, col_origem=None, col_destino=None):
        if ids_filtro is None:
            return q
        if col_origem and col_destino:
            return q.filter(db.or_(
                col_origem.in_(ids_filtro),
                col_destino.in_(ids_filtro),
            ))
        if col_destino:
            return q.filter(col_destino.in_(ids_filtro))
        if col_origem:
            return q.filter(col_origem.in_(ids_filtro))
        return q

    # Documentos de transferência/empréstimo (novo modelo)
    # Pendentes para aceitar (chegaram para minhas unidades)
    q_pendentes = DocumentoTransferencia.query.filter_by(status='pendente')
    q_pendentes = _filtra_unidades(q_pendentes, col_destino=DocumentoTransferencia.unidade_destino_id)
    pendentes = q_pendentes.order_by(DocumentoTransferencia.criado_em.desc()).all()

    # Enviadas (minhas unidades enviaram, aguardando)
    q_enviadas = DocumentoTransferencia.query.filter_by(status='pendente')
    q_enviadas = _filtra_unidades(q_enviadas, col_origem=DocumentoTransferencia.unidade_origem_id)
    enviadas = q_enviadas.order_by(DocumentoTransferencia.criado_em.desc()).all()

    # Histórico (concluídas: aceita, recusada, cancelada)
    q_hist = DocumentoTransferencia.query.filter(
        DocumentoTransferencia.status.in_(['aceita', 'recusada', 'cancelada'])
    )
    if status_concluida in ('aceita', 'recusada', 'cancelada'):
        q_hist = q_hist.filter(DocumentoTransferencia.status == status_concluida)
    q_hist = _filtra_unidades(
        q_hist,
        col_origem=DocumentoTransferencia.unidade_origem_id,
        col_destino=DocumentoTransferencia.unidade_destino_id,
    )
    historico = q_hist.order_by(
        db.func.coalesce(DocumentoTransferencia.resolvido_em, DocumentoTransferencia.criado_em).desc(),
        DocumentoTransferencia.criado_em.desc()
    ).limit(100).all()

    unidades = []
    if current_user.pode('ver_todas_unidades'):
        unidades = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()

    # Lojinha Interna — itens à disposição, agrupados por unidade
    q_lojinha = ItemLojinha.query.filter_by(ativo=True)
    if unidade_id and (unidade_filtro or aba == 'lojinha'):
        q_lojinha = q_lojinha.filter(ItemLojinha.unidade_id == unidade_id)
    if lojinha_classificacao in ('A', 'B'):
        q_lojinha = q_lojinha.filter(ItemLojinha.classificacao == lojinha_classificacao)
    lojinha_itens = q_lojinha.order_by(ItemLojinha.unidade_id, ItemLojinha.criado_em.desc()).all()
    # Agrupa por unidade para facilitar criação de documento de transferência
    from itertools import groupby
    lojinha_por_unidade = [(u, list(g)) for u, g in groupby(lojinha_itens, key=lambda i: i.unidade)]

    # Na aba lojinha, todos veem filtro de unidade (não só admin)
    unidades_lojinha = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all() if aba == 'lojinha' else unidades

    ids_unidades_user = ids_unidades  # para template (quem pode remover da lojinha)

    return render_template('transferencias/listar.html',
                           pendentes=pendentes, enviadas=enviadas, historico=historico,
                           lojinha_itens=lojinha_itens, lojinha_por_unidade=lojinha_por_unidade,
                           aba=aba, unidade_id=unidade_id, unidade_filtro=unidade_filtro, unidades=unidades,
                           unidades_lojinha=unidades_lojinha, lojinha_classificacao=lojinha_classificacao,
                           status_concluida=status_concluida, ids_unidades_user=ids_unidades_user,
                           pode_qualquer_unidade=pode_qualquer)


# ──────────────────────────────────────────────
#  LOJINHA INTERNA — adicionar itens à disposição
# ──────────────────────────────────────────────
@transferencias_bp.route('/lojinha/adicionar', methods=['GET', 'POST'])
@login_required
def lojinha_adicionar():
    if not current_user.pode('ver_transferencias'):
        abort(403)
    ids_unidades = _unidades_do_usuario()
    if ids_unidades is None:
        unidades_origem = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    else:
        unidades_origem = Unidade.query.filter(
            Unidade.id.in_(ids_unidades),
            Unidade.status == 'ativa'
        ).order_by(Unidade.nome).all()

    if request.method == 'POST':
        unidade_id = request.form.get('unidade_id', type=int)
        items_raw = request.form.get('items_json')
        if not unidade_id:
            flash('Selecione a unidade.', 'danger')
            return redirect(url_for('transferencias.lojinha_adicionar'))
        if ids_unidades is not None and unidade_id not in ids_unidades:
            abort(403)
        if items_raw:
            import json
            try:
                items_data = json.loads(items_raw)
            except json.JSONDecodeError:
                items_data = []
        else:
            items_data = []
        if not items_data:
            flash('Adicione pelo menos um item.', 'danger')
            return redirect(url_for('transferencias.lojinha_adicionar'))

        for it in items_data:
            equip_id = it.get('equipamento_id') or None
            qtd = int(it.get('quantidade', 1) or 1)
            desc = (it.get('descricao') or '').strip()
            classif = (it.get('classificacao') or 'A').upper()
            if classif not in ('A', 'B'):
                classif = 'A'
            pat = (it.get('numero_patrimonio') or '').strip() or None
            ser = (it.get('numero_serie') or '').strip() or None
            item = ItemLojinha(
                unidade_id=unidade_id,
                equipamento_id=equip_id if equip_id else None,
                quantidade=qtd,
                descricao=desc or None,
                classificacao=classif,
                numero_patrimonio=pat,
                numero_serie=ser,
                criado_por=current_user.id,
                ativo=True,
            )
            db.session.add(item)
        db.session.commit()
        flash('Itens adicionados à Lojinha! Outras unidades podem ver o que está à disposição.', 'success')
        return redirect(url_for('transferencias.listar', aba='lojinha'))

    return render_template('transferencias/lojinha_adicionar.html', unidades_origem=unidades_origem)


@transferencias_bp.route('/lojinha/<int:id>/remover', methods=['POST'])
@login_required
def lojinha_remover(id):
    item = ItemLojinha.query.get_or_404(id)
    if not item.ativo:
        flash('Este item já foi removido.', 'warning')
        return redirect(url_for('transferencias.listar', aba='lojinha'))
    ids_unidades = _unidades_do_usuario()
    if ids_unidades is not None and item.unidade_id not in ids_unidades:
        abort(403)
    item.ativo = False
    db.session.commit()
    flash('Item removido da Lojinha.', 'info')
    return redirect(url_for('transferencias.listar', aba='lojinha'))


@transferencias_bp.route('/lojinha/finalizar', methods=['POST'])
@login_required
def lojinha_finalizar():
    """Cria documento(s) de transferência a partir dos itens do carrinho da Lojinha."""
    if not current_user.pode('ver_transferencias'):
        abort(403)
    import json
    ids_unidades = _unidades_do_usuario()
    if not ids_unidades:
        flash('Selecione uma unidade na barra superior para finalizar a compra.', 'warning')
        return redirect(url_for('transferencias.listar', aba='lojinha'))
    unidade_destino_id = ids_unidades[0]

    cart_raw = request.form.get('cart_json', '[]')
    try:
        cart = json.loads(cart_raw)
    except json.JSONDecodeError:
        flash('Dados do carrinho inválidos.', 'danger')
        return redirect(url_for('transferencias.listar', aba='lojinha'))
    if not cart:
        flash('Carrinho vazio.', 'warning')
        return redirect(url_for('transferencias.listar', aba='lojinha'))

    validos = []
    for c in cart:
        item_loj = ItemLojinha.query.get(c.get('item_id'))
        if not item_loj or not item_loj.ativo:
            continue
        if item_loj.unidade_id == unidade_destino_id:
            continue
        qtd = min(max(1, int(c.get('quantidade', 1))), item_loj.quantidade)
        validos.append({
            'item_lojinha': item_loj,
            'quantidade': qtd,
            'descricao': c.get('descricao') or item_loj.descricao_exibicao(),
            'classificacao': (c.get('classificacao') or item_loj.classificacao).upper()[:1] or 'A',
            'unidade_id': item_loj.unidade_id,
            'equipamento_id': item_loj.equipamento_id,
            'numero_patrimonio': item_loj.numero_patrimonio,
            'numero_serie': item_loj.numero_serie,
        })

    if not validos:
        flash('Nenhum item válido no carrinho.', 'warning')
        return redirect(url_for('transferencias.listar', aba='lojinha'))

    from collections import defaultdict
    por_origem = defaultdict(list)
    qtd_tirada_por_item = defaultdict(int)  # item_loj.id -> quantidade total retirada
    for v in validos:
        por_origem[v['unidade_id']].append(v)
        qtd_tirada_por_item[v['item_lojinha'].id] += v['quantidade']

    criados = 0
    for unidade_origem_id, itens in por_origem.items():
        doc = DocumentoTransferencia(
            tipo='doacao',
            unidade_origem_id=unidade_origem_id,
            unidade_destino_id=unidade_destino_id,
            criado_por=current_user.id,
            status='pendente',
            observacao='Solicitação a partir da Lojinha Interna.',
        )
        db.session.add(doc)
        db.session.flush()
        for it in itens:
            item_doc = ItemDocumentoTransferencia(
                documento_id=doc.id,
                equipamento_id=it['equipamento_id'],
                quantidade=it['quantidade'],
                descricao=it['descricao'] or None,
                classificacao=it['classificacao'],
                numero_patrimonio=it['numero_patrimonio'] or None,
                numero_serie=it['numero_serie'] or None,
            )
            db.session.add(item_doc)
            eq = _vincular_equipamento_item(item_doc, unidade_origem_id)
            if eq:
                _registrar_evento(
                    eq, f'Doação solicitada para {doc.unidade_destino.nome}',
                    f'Documento #{doc.id} — Lojinha Interna.'
                )
        criados += 1

    # Consumir saldo na Lojinha
    for item_loj_id, qtd_tirada in qtd_tirada_por_item.items():
        item_loj = ItemLojinha.query.get(item_loj_id)
        if item_loj:
            item_loj.quantidade -= qtd_tirada
            if item_loj.quantidade <= 0:
                item_loj.ativo = False

    db.session.commit()
    flash('Documento(s) de transferência criado(s)! Aceite na aba Pendentes para confirmar o recebimento.', 'success')
    return redirect(url_for('transferencias.listar', aba='pendentes'))


# ──────────────────────────────────────────────
#  SOLICITAR TRANSFERÊNCIA
# ──────────────────────────────────────────────
@transferencias_bp.route('/solicitar/<int:equipamento_id>', methods=['GET', 'POST'])
@login_required
def solicitar(equipamento_id):
    if not current_user.pode('editar_equipamento'):
        abort(403)

    equipamento = Equipamento.query.get_or_404(equipamento_id)

    # Verifica acesso à unidade de origem
    ids_unidades = _unidades_do_usuario()
    sala_atual = equipamento.sala
    if ids_unidades is not None and sala_atual.unidade_id not in ids_unidades:
        abort(403)

    # Não permite solicitar se já há uma transferência pendente para este equipamento
    pendente = TransferenciaEquipamento.query.filter_by(
        equipamento_id=equipamento_id, status='pendente'
    ).first()
    if pendente:
        flash('Este equipamento já possui uma transferência pendente. Aguarde a resolução antes de solicitar outra.', 'warning')
        return redirect(url_for('equipamentos.detalhe', id=equipamento_id))

    if current_user.pode('ver_todas_unidades'):
        unidades_destino = Unidade.query.filter(
            Unidade.status == 'ativa',
            Unidade.id != sala_atual.unidade_id
        ).order_by(Unidade.nome).all()
    else:
        unidades_destino = Unidade.query.filter(
            Unidade.status == 'ativa',
            Unidade.id != sala_atual.unidade_id
        ).order_by(Unidade.nome).all()

    if request.method == 'POST':
        unidade_destino_id = request.form.get('unidade_destino_id', type=int)
        observacao = request.form.get('observacao', '').strip()

        if not unidade_destino_id:
            flash('Selecione a unidade de destino.', 'danger')
        else:
            transf = TransferenciaEquipamento(
                equipamento_id=equipamento_id,
                sala_origem_id=equipamento.sala_id,
                unidade_origem_id=sala_atual.unidade_id,
                unidade_destino_id=unidade_destino_id,
                solicitado_por=current_user.id,
                observacao=observacao,
                status='pendente',
            )
            db.session.add(transf)

            # Registra no histórico de chamados como evento de equipamento
            db.session.flush()
            _registrar_evento(
                equipamento,
                f'Transferência solicitada para {transf.unidade_destino.nome}',
                f'Solicitado por {current_user.nome}. {observacao}'
            )

            db.session.commit()
            flash(f'Transferência solicitada com sucesso! O coordenador da unidade destino precisa aceitar.', 'success')
            return redirect(url_for('equipamentos.detalhe', id=equipamento_id))

    return render_template('transferencias/solicitar.html',
                           equipamento=equipamento,
                           unidades_destino=unidades_destino)


# ──────────────────────────────────────────────
#  CRIAR DOCUMENTO (Termo de Transferência/Empréstimo)
# ──────────────────────────────────────────────
@transferencias_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def documento_novo():
    if not current_user.pode('ver_transferencias'):
        abort(403)
    ids_unidades = _unidades_do_usuario()
    pode_qualquer = _pode_escolher_qualquer_unidade()
    if pode_qualquer or ids_unidades is None:
        unidades_origem = _unidades_ativas()
    else:
        unidades_origem = Unidade.query.filter(
            Unidade.id.in_(ids_unidades),
            Unidade.status == 'ativa'
        ).order_by(Unidade.nome).all()

    unidades_destino = _unidades_ativas()

    if request.method == 'POST':
        tipo = request.form.get('tipo')  # emprestimo | transferencia
        unidade_origem_id = request.form.get('unidade_origem_id', type=int)
        unidade_destino_id = request.form.get('unidade_destino_id', type=int)
        observacao = request.form.get('observacao', '').strip()

        if tipo not in ('emprestimo', 'transferencia'):
            flash('Informe se é Empréstimo ou Transferência.', 'danger')
            return redirect(url_for('transferencias.documento_novo'))
        if not unidade_origem_id or not unidade_destino_id:
            flash('Informe unidade de origem e destino.', 'danger')
            return redirect(url_for('transferencias.documento_novo'))
        if unidade_origem_id == unidade_destino_id:
            flash('Origem e destino não podem ser iguais.', 'danger')
            return redirect(url_for('transferencias.documento_novo'))
        if not pode_qualquer and ids_unidades is not None and unidade_origem_id not in ids_unidades:
            abort(403)

        # Itens: items_json ou form items
        items_raw = request.form.get('items_json')
        if items_raw:
            import json
            try:
                items_data = json.loads(items_raw)
            except json.JSONDecodeError:
                items_data = []
        else:
            items_data = []

        if not items_data:
            flash('Adicione pelo menos um item ao documento.', 'danger')
            return redirect(url_for('transferencias.documento_novo'))

        doc = DocumentoTransferencia(
            tipo=tipo,
            unidade_origem_id=unidade_origem_id,
            unidade_destino_id=unidade_destino_id,
            criado_por=current_user.id,
            status='pendente',
            observacao=observacao or None,
        )
        db.session.add(doc)
        db.session.flush()

        for it in items_data:
            equip_id = it.get('equipamento_id') or None
            qtd = int(it.get('quantidade', 1) or 1)
            desc = (it.get('descricao') or '').strip()
            classif = (it.get('classificacao') or 'A').upper()
            if classif not in ('A', 'B'):
                classif = 'A'
            pat = (it.get('numero_patrimonio') or '').strip() or None
            ser = (it.get('numero_serie') or '').strip() or None

            item = ItemDocumentoTransferencia(
                documento_id=doc.id,
                equipamento_id=equip_id if equip_id else None,
                quantidade=qtd,
                descricao=desc or None,
                classificacao=classif,
                numero_patrimonio=pat,
                numero_serie=ser,
            )
            db.session.add(item)
            eq = _vincular_equipamento_item(item, unidade_origem_id)
            if eq:
                _registrar_evento(
                    eq,
                    f'{doc.tipo_label} solicitado para {doc.unidade_destino.nome}',
                    f'Documento #{doc.id}. {observacao}'
                )

        db.session.commit()
        if pode_qualquer:
            flash(
                f'Termo de {doc.tipo_label.lower()} criado. Confirme o aceite e a sala na unidade destino.',
                'success'
            )
            return redirect(url_for('transferencias.documento_aceitar', id=doc.id))
        flash(f'Termo de {doc.tipo_label.lower()} criado! Aguardando aceite da unidade destino.', 'success')
        return redirect(url_for('transferencias.listar', aba='enviadas'))

    return render_template('transferencias/novo.html',
                           unidades_origem=unidades_origem,
                           unidades_destino=unidades_destino,
                           pode_qualquer_unidade=pode_qualquer)


# ──────────────────────────────────────────────
#  ACEITAR / RECUSAR DOCUMENTO
# ──────────────────────────────────────────────
@transferencias_bp.route('/documento/<int:id>/aceitar', methods=['GET', 'POST'])
@login_required
def documento_aceitar(id):
    doc = DocumentoTransferencia.query.get_or_404(id)
    if doc.status != 'pendente':
        flash('Este documento já foi resolvido.', 'warning')
        return redirect(url_for('transferencias.listar'))

    if not _pode_resolver_aceite(doc.unidade_destino_id):
        if (
            current_user.perfil in ('administrador', 'gestor_secretaria', 'coordenador', 'administrativo')
            and not _pode_escolher_qualquer_unidade()
            and _unidades_do_usuario() is None
        ):
            flash('Selecione uma unidade na barra superior para aceitar em nome dela.', 'warning')
            return redirect(url_for('transferencias.listar', aba='pendentes'))
        abort(403)

    salas_destino = Sala.query.filter_by(
        unidade_id=doc.unidade_destino_id, ativo=True
    ).order_by(Sala.nome).all()

    if request.method == 'POST':
        acao = request.form.get('acao')
        obs = request.form.get('observacao_aceite', '').strip()
        sala_id = request.form.get('sala_destino_id', type=int)

        if acao == 'aceitar':
            if not sala_id:
                flash('Selecione a sala de destino.', 'danger')
                return render_template('transferencias/documento_aceitar.html',
                                       doc=doc, salas_destino=salas_destino)

            doc.sala_destino_id = sala_id
            movidos, criados, nao_encontrados = _realocar_itens_documento(
                doc, sala_id, obs, criar_se_ausente=True
            )
            if nao_encontrados:
                db.session.rollback()
                flash(
                    'Não foi possível concluir o aceite. Os itens abaixo possuem patrimônio/série '
                    'mas não puderam ser localizados ou cadastrados no inventário: '
                    f'{", ".join(nao_encontrados)}.',
                    'danger'
                )
                return render_template('transferencias/documento_aceitar.html',
                                       doc=doc, salas_destino=salas_destino)

            doc.status = 'aceita'
            doc.aceito_por = current_user.id
            doc.observacao_aceite = obs
            doc.resolvido_em = datetime.utcnow()
            db.session.commit()

            partes = []
            if movidos:
                partes.append(f'{movidos} realocado(s)')
            if criados:
                partes.append(f'{criados} cadastrado(s) no inventário')
            flash(
                f'Documento aceito! {" e ".join(partes) or "Itens registrados"}.' if partes
                else 'Documento aceito!',
                'success'
            )

        elif acao == 'recusar':
            doc.status = 'recusada'
            doc.aceito_por = current_user.id
            doc.observacao_aceite = obs
            doc.resolvido_em = datetime.utcnow()
            for item in doc.itens.all():
                if item.equipamento_id:
                    _registrar_evento(
                        item.equipamento,
                        f'{doc.tipo_label} recusado pela unidade {doc.unidade_destino.nome}',
                        f'Recusado por {current_user.nome}. {obs}'
                    )
            db.session.commit()
            flash('Documento recusado.', 'info')

        return redirect(url_for('transferencias.listar'))

    return render_template('transferencias/documento_aceitar.html',
                           doc=doc, salas_destino=salas_destino,
                           pode_qualquer_unidade=_pode_escolher_qualquer_unidade())


# ──────────────────────────────────────────────
#  CANCELAR DOCUMENTO (quem enviou pode cancelar)
# ──────────────────────────────────────────────
@transferencias_bp.route('/documento/<int:id>/cancelar', methods=['POST'])
@login_required
def documento_cancelar(id):
    doc = DocumentoTransferencia.query.get_or_404(id)
    if doc.status != 'pendente':
        flash('Não é possível cancelar um documento já resolvido.', 'warning')
        return redirect(url_for('transferencias.listar'))

    # Pode cancelar: criador do documento ou gestor/admin
    pode = (doc.criado_por == current_user.id) or current_user.pode('ver_todas_unidades')
    if not pode:
        abort(403)

    doc.status = 'cancelada'
    doc.aceito_por = current_user.id
    doc.resolvido_em = datetime.utcnow()
    doc.observacao_aceite = 'Cancelado pelo solicitante.'
    for item in doc.itens.all():
        if item.equipamento_id:
            _registrar_evento(
                item.equipamento,
                f'{doc.tipo_label} cancelado',
                f'Cancelado por {current_user.nome}.'
            )
    db.session.commit()
    flash('Documento cancelado.', 'info')
    return redirect(url_for('transferencias.listar'))


# ──────────────────────────────────────────────
#  ACEITAR / RECUSAR (legado — TransferenciaEquipamento 1:1, via solicitar)
# ──────────────────────────────────────────────
@transferencias_bp.route('/<int:id>/aceitar', methods=['GET', 'POST'])
@login_required
def aceitar(id):
    transf = TransferenciaEquipamento.query.get_or_404(id)
    if transf.status != 'pendente':
        flash('Esta transferência já foi resolvida.', 'warning')
        return redirect(url_for('transferencias.listar'))
    if not _pode_resolver_aceite(transf.unidade_destino_id):
        abort(403)
    salas_destino = Sala.query.filter_by(unidade_id=transf.unidade_destino_id, ativo=True).order_by(Sala.nome).all()
    if request.method == 'POST':
        acao = request.form.get('acao')
        obs = request.form.get('observacao_aceite', '').strip()
        sala_id = request.form.get('sala_destino_id', type=int)
        if acao == 'aceitar':
            if not sala_id:
                flash('Selecione a sala de destino.', 'danger')
                return render_template('transferencias/aceitar.html', transf=transf, salas_destino=salas_destino)
            sala = Sala.query.filter_by(
                id=sala_id, unidade_id=transf.unidade_destino_id, ativo=True
            ).first()
            if not sala:
                flash('Sala de destino inválida.', 'danger')
                return render_template('transferencias/aceitar.html', transf=transf, salas_destino=salas_destino)
            transf.sala_destino_id = sala.id
            transf.equipamento.sala_id = sala.id
            transf.status = 'aceita'
            transf.aceito_por = current_user.id
            transf.observacao_aceite = obs
            transf.resolvido_em = datetime.utcnow()
            _registrar_evento(transf.equipamento, f'Transferência aceita — {sala.nome}', obs)
            db.session.commit()
            flash('Transferência aceita!', 'success')
        elif acao == 'recusar':
            transf.status = 'recusada'
            transf.aceito_por = current_user.id
            transf.observacao_aceite = obs
            transf.resolvido_em = datetime.utcnow()
            _registrar_evento(transf.equipamento, f'Transferência recusada', obs)
            db.session.commit()
            flash('Transferência recusada.', 'info')
        return redirect(url_for('transferencias.listar'))
    return render_template('transferencias/aceitar.html', transf=transf, salas_destino=salas_destino)


# ──────────────────────────────────────────────
#  VERIFICAR DOCUMENTO (público — para QR de validação)
# ──────────────────────────────────────────────
@transferencias_bp.route('/documento/<int:id>/verificar')
def documento_verificar(id):
    """Página pública para validação via QR code — simula assinatura digital."""
    doc = DocumentoTransferencia.query.get_or_404(id)
    return render_template('transferencias/verificar.html', doc=doc)


# ──────────────────────────────────────────────
#  IMPRIMIR DOCUMENTO
# ──────────────────────────────────────────────
@transferencias_bp.route('/documento/<int:id>/imprimir')
@login_required
def documento_imprimir(id):
    doc = DocumentoTransferencia.query.get_or_404(id)
    ids_unidades = _unidades_do_usuario()
    if ids_unidades is not None:
        if doc.unidade_origem_id not in ids_unidades and doc.unidade_destino_id not in ids_unidades:
            abort(403)
    qr_url_origem = url_for('unidades.maps_redirect', id=doc.unidade_origem_id, _external=True) if doc.unidade_origem.link_maps else None
    qr_url_destino = url_for('unidades.maps_redirect', id=doc.unidade_destino_id, _external=True) if doc.unidade_destino.link_maps else None
    qr_url_verificar = url_for('transferencias.documento_verificar', id=doc.id, _external=True)
    return render_template('transferencias/imprimir.html', doc=doc, now=datetime.utcnow(),
                           qr_url_origem=qr_url_origem, qr_url_destino=qr_url_destino,
                           qr_url_verificar=qr_url_verificar)


# ──────────────────────────────────────────────
#  API — equipamentos por unidade (para formulário novo documento)
# ──────────────────────────────────────────────
@transferencias_bp.route('/api/equipamentos-unidade/<int:unidade_id>')
@login_required
def api_equipamentos_unidade(unidade_id):
    if not current_user.pode('ver_transferencias'):
        abort(403)
    ids_unidades = _unidades_do_usuario()
    if (
        not _pode_escolher_qualquer_unidade()
        and ids_unidades is not None
        and unidade_id not in ids_unidades
        and not current_user.pode('ver_todas_unidades')
    ):
        abort(403)
    equips = (
        db.session.query(Equipamento)
        .join(Sala, Equipamento.sala_id == Sala.id)
        .filter(Sala.unidade_id == unidade_id, Equipamento.ativo == True)
        .order_by(Sala.nome, Equipamento.numero_patrimonio)
        .all()
    )
    return jsonify([{
        'id': e.id,
        'nome': e.nome_display,
        'patrimonio': e.numero_patrimonio or '',
        'serie': e.numero_serie or '',
        'sala': e.sala.nome if e.sala else '',
        'status': e.status_label,
    } for e in equips])


# ──────────────────────────────────────────────
#  API — salas por unidade (para o formulário de aceite)
# ──────────────────────────────────────────────
@transferencias_bp.route('/api/salas/<int:unidade_id>')
@login_required
def api_salas(unidade_id):
    salas = Sala.query.filter_by(unidade_id=unidade_id, ativo=True).order_by(Sala.nome).all()
    return jsonify([{'id': s.id, 'nome': s.nome} for s in salas])


# ──────────────────────────────────────────────
#  HELPER — evento no histórico do equipamento
# ──────────────────────────────────────────────
def _registrar_evento(equipamento, acao, obs='', usuario_id=None):
    """Registra um evento de transferência no histórico do equipamento."""
    from app.models.transferencia import HistoricoEquipamento
    uid = usuario_id
    if uid is None and current_user and getattr(current_user, 'is_authenticated', False):
        uid = current_user.id
    db.session.add(HistoricoEquipamento(
        equipamento_id=equipamento.id,
        usuario_id=uid,
        acao=acao,
        observacao=obs or None,
    ))
