from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.transferencia import TransferenciaEquipamento, DocumentoTransferencia, ItemDocumentoTransferencia, ItemLojinha
from app.models.equipamento import Equipamento
from app.models.unidade import Unidade, UsuarioUnidade
from app.models.sala import Sala

transferencias_bp = Blueprint('transferencias', __name__, url_prefix='/transferencias')


def _unidades_do_usuario():
    """Retorna lista de unidade_ids efetivos (considera unidade padrão).
    None = vê todas (gestor central em 'Todas'); lista = unidades para ações."""
    return current_user.ids_unidades_efetivos()


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

    # Filtro de unidade (admin/gestor central podem escolher)
    unidade_filtro = None
    if current_user.pode('ver_todas_unidades') and unidade_id:
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
                           status_concluida=status_concluida, ids_unidades_user=ids_unidades_user)


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
            if it['equipamento_id']:
                eq = Equipamento.query.get(it['equipamento_id'])
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
    if ids_unidades is None:
        unidades_origem = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    else:
        unidades_origem = Unidade.query.filter(
            Unidade.id.in_(ids_unidades),
            Unidade.status == 'ativa'
        ).order_by(Unidade.nome).all()

    unidades_destino = Unidade.query.filter(
        Unidade.status == 'ativa'
    ).order_by(Unidade.nome).all()

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
        if ids_unidades is not None and unidade_origem_id not in ids_unidades:
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
            if equip_id:
                eq = Equipamento.query.get(equip_id)
                if eq:
                    _registrar_evento(
                        eq,
                        f'{doc.tipo_label} solicitado para {doc.unidade_destino.nome}',
                        f'Documento #{doc.id}. {observacao}'
                    )

        db.session.commit()
        flash(f'Termo de {doc.tipo_label.lower()} criado! Aguardando aceite da unidade destino.', 'success')
        return redirect(url_for('transferencias.listar', aba='enviadas'))

    return render_template('transferencias/novo.html',
                           unidades_origem=unidades_origem,
                           unidades_destino=unidades_destino)


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

    ids_unidades = _unidades_do_usuario()
    if ids_unidades is None:
        flash('Selecione uma unidade na barra superior para aceitar em nome dela.', 'warning')
        return redirect(url_for('transferencias.listar', aba='pendentes'))
    if doc.unidade_destino_id not in ids_unidades:
        abort(403)
    if current_user.perfil not in ['administrador', 'gestor_secretaria', 'coordenador', 'administrativo']:
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
            doc.status = 'aceita'
            doc.aceito_por = current_user.id
            doc.observacao_aceite = obs
            doc.resolvido_em = datetime.utcnow()

            for item in doc.itens.all():
                if item.equipamento_id:
                    eq = item.equipamento
                    eq.sala_id = sala_id
                    _registrar_evento(
                        eq,
                        f'{doc.tipo_label} aceito — alocado em {doc.sala_destino.nome} ({doc.unidade_destino.nome})',
                        f'Aceito por {current_user.nome}. {obs}'
                    )
            db.session.commit()
            flash('Documento aceito! Equipamentos realocados com sucesso.', 'success')

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
                           doc=doc, salas_destino=salas_destino)


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
    ids_unidades = _unidades_do_usuario()
    if ids_unidades is not None and transf.unidade_destino_id not in ids_unidades:
        abort(403)
    if current_user.perfil not in ['administrador', 'gestor_secretaria', 'coordenador', 'administrativo']:
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
            transf.sala_destino_id = sala_id
            transf.equipamento.sala_id = sala_id
            transf.status = 'aceita'
            transf.aceito_por = current_user.id
            transf.observacao_aceite = obs
            transf.resolvido_em = datetime.utcnow()
            _registrar_evento(transf.equipamento, f'Transferência aceita — {transf.sala_destino.nome}', obs)
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
    if ids_unidades is not None and unidade_id not in ids_unidades and not current_user.pode('ver_todas_unidades'):
        abort(403)
    equips = (
        db.session.query(Equipamento)
        .join(Sala, Equipamento.sala_id == Sala.id)
        .filter(Sala.unidade_id == unidade_id, Equipamento.ativo == True)
        .order_by(Equipamento.numero_patrimonio)
        .all()
    )
    return jsonify([{
        'id': e.id,
        'nome': e.nome_display,
        'patrimonio': e.numero_patrimonio or '',
        'serie': e.numero_serie or '',
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
def _registrar_evento(equipamento, acao, obs=''):
    """Registra um evento de transferência no histórico do equipamento."""
    from app.models.transferencia import HistoricoEquipamento
    db.session.add(HistoricoEquipamento(
        equipamento_id=equipamento.id,
        usuario_id=current_user.id,
        acao=acao,
        observacao=obs or None,
    ))
