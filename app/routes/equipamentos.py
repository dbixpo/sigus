from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.equipamento import (
    Equipamento, TipoEquipamento, CampoTipoEquipamento,
    Marca, Modelo, EquipamentoCampoValor, EquipamentoUsuario,
    STATUS_EQUIPAMENTO, STATUS_LABELS,
    CONDICAO_EQUIPAMENTO, CONDICAO_LABELS
)
from app.models.sala import Sala
from app.models.unidade import Unidade, UsuarioUnidade
from app.models.tipo_unidade import TipoUnidade
from app.models.usuario import Usuario

equipamentos_bp = Blueprint('equipamentos', __name__, url_prefix='/equipamentos')

PREFIXO_PATRIMONIO = 'PMS-'

def _normalizar_patrimonio(valor: str) -> str | None:
    """Garante que o nº de patrimônio sempre comece com PMS-."""
    v = (valor or '').strip()
    if not v:
        return None
    # Remove prefixo duplicado/variante de capitalização, depois re-aplica
    while v.upper().startswith(PREFIXO_PATRIMONIO):
        v = v[len(PREFIXO_PATRIMONIO):]
    v = v.strip()
    return (PREFIXO_PATRIMONIO + v) if v else None


@equipamentos_bp.route('/')
@login_required
def listar():
    def _gl(p):
        return [int(v) for v in request.args.getlist(p) if v.isdigit()]
    def _gsl(p):
        return [v for v in request.args.getlist(p) if v]

    filtro_unidades       = _gl('unidade')
    filtro_tipo_unidades  = _gl('tipo_unidade')
    filtro_tipos          = _gl('tipo')
    filtro_status_list    = _gsl('status')
    filtro_condicao_list  = _gsl('condicao')

    query = Equipamento.query.filter_by(ativo=True)

    sala_join_done = False
    if not current_user.pode('ver_todas_unidades'):
        ids_unidades = [uu.unidade_id for uu in current_user.unidades.filter_by(ativo=True).all()]
        query = query.join(Sala, Equipamento.sala_id == Sala.id).filter(Sala.unidade_id.in_(ids_unidades))
        sala_join_done = True

    if filtro_unidades or filtro_tipo_unidades:
        if not sala_join_done:
            query = query.join(Sala, Equipamento.sala_id == Sala.id)
            sala_join_done = True
        if filtro_unidades:
            query = query.filter(Sala.unidade_id.in_(filtro_unidades))
        if filtro_tipo_unidades:
            query = query.join(Unidade, Sala.unidade_id == Unidade.id).filter(
                Unidade.tipo_unidade_id.in_(filtro_tipo_unidades)
            )

    if filtro_tipos:
        query = query.filter(Equipamento.tipo_equipamento_id.in_(filtro_tipos))
    if filtro_status_list:
        query = query.filter(Equipamento.status.in_(filtro_status_list))
    if filtro_condicao_list:
        query = query.filter(Equipamento.condicao.in_(filtro_condicao_list))

    equipamentos  = query.order_by(Equipamento.id.desc()).all()
    tipos         = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()
    unidades      = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()

    return render_template('equipamentos/listar.html',
                           equipamentos=equipamentos,
                           tipos=tipos,
                           tipos_unidade=tipos_unidade,
                           unidades=unidades,
                           status_opts=STATUS_LABELS,
                           condicao_opts=CONDICAO_LABELS,
                           filtro_tipos=filtro_tipos,
                           filtro_tipo_unidades=filtro_tipo_unidades,
                           filtro_unidades=filtro_unidades,
                           filtro_status_list=filtro_status_list,
                           filtro_condicao_list=filtro_condicao_list)


@equipamentos_bp.route('/novo/<int:sala_id>', methods=['GET', 'POST'])
@login_required
def novo(sala_id):
    if not current_user.pode('cadastrar_equipamento'):
        abort(403)
    sala = Sala.query.get_or_404(sala_id)
    tipos = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    marcas = Marca.query.order_by(Marca.nome).all()

    if request.method == 'POST':
        tipo_id = request.form.get('tipo_equipamento_id', type=int)
        tipo = TipoEquipamento.query.get_or_404(tipo_id)

        marca_id = request.form.get('marca_id', type=int) or None
        modelo_id = request.form.get('modelo_id', type=int) or None

        nova_marca = request.form.get('nova_marca', '').strip()
        if nova_marca:
            m = Marca.query.filter_by(nome=nova_marca).first()
            if not m:
                m = Marca(nome=nova_marca)
                db.session.add(m)
                db.session.flush()
            marca_id = m.id

        novo_modelo = request.form.get('novo_modelo', '').strip()
        if novo_modelo and marca_id:
            md = Modelo.query.filter_by(marca_id=marca_id, nome=novo_modelo).first()
            if not md:
                md = Modelo(marca_id=marca_id, nome=novo_modelo)
                db.session.add(md)
                db.session.flush()
            modelo_id = md.id

        equipamento = Equipamento(
            sala_id=sala_id,
            tipo_equipamento_id=tipo_id,
            numero_patrimonio=_normalizar_patrimonio(request.form.get('numero_patrimonio', '')),
            numero_serie=request.form.get('numero_serie', '').strip() or None,
            marca_id=marca_id,
            modelo_id=modelo_id,
            data_aquisicao=request.form.get('data_aquisicao') or None,
            valor_estimado=request.form.get('valor_estimado') or None,
            tempo_uso_anos=request.form.get('tempo_uso_anos') or None,
            status=request.form.get('status', 'ativo'),
            condicao=request.form.get('condicao', 'boa'),
            observacoes=request.form.get('observacoes', '').strip(),
            criado_por=current_user.id,
        )
        db.session.add(equipamento)
        db.session.flush()

        for campo in tipo.campos.all():
            valor = request.form.get(f'campo_{campo.id}', '').strip()
            if valor:
                db.session.add(EquipamentoCampoValor(
                    equipamento_id=equipamento.id,
                    campo_id=campo.id,
                    valor=valor
                ))

        db.session.commit()
        flash(f'Equipamento cadastrado com sucesso!', 'success')
        return redirect(url_for('salas.detalhe', id=sala_id))

    return render_template('equipamentos/form.html',
                           equipamento=None, sala=sala, tipos=tipos, marcas=marcas,
                           status_opts=STATUS_EQUIPAMENTO, condicao_opts=CONDICAO_EQUIPAMENTO)


@equipamentos_bp.route('/novo-na-unidade/<int:unidade_id>', methods=['GET', 'POST'])
@login_required
def novo_na_unidade(unidade_id):
    """Cadastrar equipamento a partir da página da unidade — o usuário escolhe a sala."""
    if not current_user.pode('cadastrar_equipamento'):
        abort(403)
    unidade = Unidade.query.get_or_404(unidade_id)
    salas   = Sala.query.filter_by(unidade_id=unidade_id, ativo=True).order_by(Sala.nome).all()
    tipos   = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    marcas  = Marca.query.order_by(Marca.nome).all()

    if request.method == 'POST':
        sala_id = request.form.get('sala_id', type=int)
        if not sala_id:
            flash('Selecione uma sala para o equipamento.', 'danger')
            return render_template('equipamentos/form.html',
                                   equipamento=None, sala=None, unidade=unidade,
                                   salas=salas, tipos=tipos, marcas=marcas,
                                   status_opts=STATUS_EQUIPAMENTO,
                                   condicao_opts=CONDICAO_EQUIPAMENTO,
                                   campos_valores={})
        sala    = Sala.query.get_or_404(sala_id)
        tipo_id = request.form.get('tipo_equipamento_id', type=int)
        tipo    = TipoEquipamento.query.get_or_404(tipo_id)

        marca_id  = request.form.get('marca_id', type=int) or None
        modelo_id = request.form.get('modelo_id', type=int) or None

        nova_marca = request.form.get('nova_marca', '').strip()
        if nova_marca:
            m = Marca.query.filter_by(nome=nova_marca).first()
            if not m:
                m = Marca(nome=nova_marca)
                db.session.add(m)
                db.session.flush()
            marca_id = m.id

        novo_modelo = request.form.get('novo_modelo', '').strip()
        if novo_modelo and marca_id:
            md = Modelo.query.filter_by(marca_id=marca_id, nome=novo_modelo).first()
            if not md:
                md = Modelo(marca_id=marca_id, nome=novo_modelo)
                db.session.add(md)
                db.session.flush()
            modelo_id = md.id

        equipamento = Equipamento(
            sala_id=sala_id,
            tipo_equipamento_id=tipo_id,
            numero_patrimonio=_normalizar_patrimonio(request.form.get('numero_patrimonio', '')),
            numero_serie=request.form.get('numero_serie', '').strip() or None,
            marca_id=marca_id,
            modelo_id=modelo_id,
            data_aquisicao=request.form.get('data_aquisicao') or None,
            valor_estimado=request.form.get('valor_estimado') or None,
            tempo_uso_anos=request.form.get('tempo_uso_anos') or None,
            status=request.form.get('status', 'ativo'),
            condicao=request.form.get('condicao', 'boa'),
            observacoes=request.form.get('observacoes', '').strip(),
            criado_por=current_user.id,
        )
        db.session.add(equipamento)
        db.session.flush()

        for campo in tipo.campos.all():
            valor = request.form.get(f'campo_{campo.id}', '').strip()
            if valor:
                db.session.add(EquipamentoCampoValor(
                    equipamento_id=equipamento.id,
                    campo_id=campo.id,
                    valor=valor
                ))

        db.session.commit()
        flash('Equipamento cadastrado com sucesso!', 'success')
        return redirect(url_for('unidades.detalhe', id=unidade_id) + '#tab-equipamentos')

    return render_template('equipamentos/form.html',
                           equipamento=None, sala=None, unidade=unidade,
                           salas=salas, tipos=tipos, marcas=marcas,
                           status_opts=STATUS_EQUIPAMENTO,
                           condicao_opts=CONDICAO_EQUIPAMENTO,
                           campos_valores={})


@equipamentos_bp.route('/<int:id>')
@login_required
def detalhe(id):
    from app.models.transferencia import HistoricoEquipamento, TransferenciaEquipamento, DocumentoTransferencia, ItemDocumentoTransferencia
    equipamento = Equipamento.query.get_or_404(id)
    campos_valores = {cv.campo_id: cv.valor for cv in equipamento.campos_valores.all()}
    chamados_hist = equipamento.chamados.order_by(db.text('criado_em desc')).limit(15).all()
    contrato_ativo = equipamento.contrato_vigente
    historico_equip = HistoricoEquipamento.query.filter_by(
        equipamento_id=id
    ).order_by(HistoricoEquipamento.criado_em.desc()).limit(20).all()
    # Transferências legado (1:1) + documentos (termo com múltiplos itens)
    transferencias_legado = TransferenciaEquipamento.query.filter_by(
        equipamento_id=id
    ).order_by(TransferenciaEquipamento.criado_em.desc()).all()
    itens_doc = ItemDocumentoTransferencia.query.filter_by(equipamento_id=id).all()
    documentos_ids = {i.documento_id for i in itens_doc}
    documentos_transf = DocumentoTransferencia.query.filter(
        DocumentoTransferencia.id.in_(documentos_ids)
    ).order_by(DocumentoTransferencia.criado_em.desc()).all() if documentos_ids else []
    # Unifica: cada item tem unidade_origem, unidade_destino, status_label, status_badge, criado_em, link
    transferencias_hist = list(transferencias_legado)
    for doc in documentos_transf:
        transferencias_hist.append(doc)
    transferencias_hist.sort(key=lambda x: x.criado_em or x.resolvido_em, reverse=True)
    usuarios_vinculados = equipamento.usuarios_vinculados.all()

    # Usuários disponíveis para vincular: ativos na mesma unidade, ainda não vinculados
    ids_ja_vinculados = {ev.usuario_id for ev in usuarios_vinculados}
    unidade = equipamento.sala.unidade if equipamento.sala else None
    if unidade:
        ids_unidade = {uu.usuario_id for uu in unidade.usuarios.filter_by(ativo=True).all()}
    else:
        ids_unidade = set()
    usuarios_disponiveis = Usuario.query.filter(
        Usuario.id.in_(ids_unidade - ids_ja_vinculados),
        Usuario.ativo == True,
        Usuario.perfil != 'administrador'
    ).order_by(Usuario.nome).all()

    return render_template('equipamentos/detalhe.html',
                           equipamento=equipamento,
                           campos_valores=campos_valores,
                           chamados_hist=chamados_hist,
                           contrato_ativo=contrato_ativo,
                           historico_equip=historico_equip,
                           transferencias_hist=transferencias_hist,
                           usuarios_vinculados=usuarios_vinculados,
                           usuarios_disponiveis=usuarios_disponiveis)


@equipamentos_bp.route('/<int:id>/vincular-usuario', methods=['POST'])
@login_required
def vincular_usuario(id):
    if not current_user.pode('editar_equipamento'):
        abort(403)
    equipamento = Equipamento.query.get_or_404(id)
    usuario_id  = request.form.get('usuario_id', type=int)
    observacao  = request.form.get('observacao', '').strip() or None
    if not usuario_id:
        flash('Selecione um usuário.', 'warning')
        return redirect(url_for('equipamentos.detalhe', id=id))
    existente = EquipamentoUsuario.query.filter_by(
        equipamento_id=id, usuario_id=usuario_id
    ).first()
    if existente:
        flash('Esse usuário já está vinculado a este equipamento.', 'warning')
        return redirect(url_for('equipamentos.detalhe', id=id))
    db.session.add(EquipamentoUsuario(
        equipamento_id=id,
        usuario_id=usuario_id,
        observacao=observacao,
    ))
    db.session.commit()
    usuario = Usuario.query.get(usuario_id)
    flash(f'{usuario.nome} vinculado ao equipamento.', 'success')
    return redirect(url_for('equipamentos.detalhe', id=id) + '#tab-usuarios')


@equipamentos_bp.route('/<int:id>/desvincular-usuario/<int:usuario_id>', methods=['POST'])
@login_required
def desvincular_usuario(id, usuario_id):
    if not current_user.pode('editar_equipamento'):
        abort(403)
    vinculo = EquipamentoUsuario.query.filter_by(
        equipamento_id=id, usuario_id=usuario_id
    ).first_or_404()
    nome = vinculo.usuario.nome
    db.session.delete(vinculo)
    db.session.commit()
    flash(f'{nome} desvinculado do equipamento.', 'info')
    return redirect(url_for('equipamentos.detalhe', id=id) + '#tab-usuarios')


@equipamentos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.pode('editar_equipamento'):
        abort(403)
    equipamento = Equipamento.query.get_or_404(id)
    tipos = TipoEquipamento.query.order_by(TipoEquipamento.nome).all()
    marcas = Marca.query.order_by(Marca.nome).all()
    modelos = Modelo.query.filter_by(marca_id=equipamento.marca_id).order_by(Modelo.nome).all() if equipamento.marca_id else []
    campos_valores = {cv.campo_id: cv.valor for cv in equipamento.campos_valores.all()}

    if request.method == 'POST':
        equipamento.numero_patrimonio = _normalizar_patrimonio(request.form.get('numero_patrimonio', ''))
        equipamento.numero_serie = request.form.get('numero_serie', '').strip() or None
        equipamento.marca_id = request.form.get('marca_id', type=int) or None
        equipamento.modelo_id = request.form.get('modelo_id', type=int) or None
        equipamento.data_aquisicao = request.form.get('data_aquisicao') or None
        equipamento.valor_estimado = request.form.get('valor_estimado') or None
        equipamento.tempo_uso_anos = request.form.get('tempo_uso_anos') or None
        equipamento.status = request.form.get('status', 'ativo')
        equipamento.condicao = request.form.get('condicao', 'boa')
        equipamento.observacoes = request.form.get('observacoes', '').strip()

        for campo in equipamento.tipo_equipamento.campos.all():
            valor = request.form.get(f'campo_{campo.id}', '').strip()
            cv = equipamento.campos_valores.filter_by(campo_id=campo.id).first()
            if cv:
                cv.valor = valor
            elif valor:
                db.session.add(EquipamentoCampoValor(
                    equipamento_id=equipamento.id, campo_id=campo.id, valor=valor))

        db.session.commit()
        flash('Equipamento atualizado com sucesso!', 'success')
        return redirect(url_for('equipamentos.detalhe', id=equipamento.id))

    return render_template('equipamentos/form.html',
                           equipamento=equipamento, sala=equipamento.sala,
                           tipos=tipos, marcas=marcas, modelos=modelos,
                           campos_valores=campos_valores,
                           status_opts=STATUS_EQUIPAMENTO, condicao_opts=CONDICAO_EQUIPAMENTO)


@equipamentos_bp.route('/<int:id>/baixa', methods=['POST'])
@login_required
def dar_baixa(id):
    if not current_user.pode('dar_baixa_equipamento'):
        abort(403)
    from app.models.transferencia import HistoricoEquipamento
    equipamento = Equipamento.query.get_or_404(id)
    sala_id = equipamento.sala_id
    equipamento.status = 'baixado'
    equipamento.ativo = False
    db.session.add(HistoricoEquipamento(
        equipamento_id=id,
        usuario_id=current_user.id,
        acao='Baixa registrada',
        observacao=request.form.get('motivo', '').strip() or None,
    ))
    db.session.commit()
    flash('Equipamento baixado com sucesso.', 'warning')
    return redirect(url_for('salas.detalhe', id=sala_id))


@equipamentos_bp.route('/api/marcas-por-tipo/<int:tipo_id>')
@login_required
def api_marcas_por_tipo(tipo_id):
    """Retorna as marcas vinculadas ao tipo de equipamento selecionado."""
    tipo = TipoEquipamento.query.get_or_404(tipo_id)
    marcas = tipo.marcas.order_by(Marca.nome).all()
    return jsonify([{'id': m.id, 'nome': m.nome} for m in marcas])


@equipamentos_bp.route('/api/modelos/<int:marca_id>')
@login_required
def api_modelos(marca_id):
    tipo_id = request.args.get('tipo_id', type=int)
    q = Modelo.query.filter_by(marca_id=marca_id)
    if tipo_id:
        q = q.filter_by(tipo_equipamento_id=tipo_id)
    modelos = q.order_by(Modelo.nome).all()
    return jsonify([{'id': m.id, 'nome': m.nome} for m in modelos])


@equipamentos_bp.route('/api/campos/<int:tipo_id>')
@login_required
def api_campos(tipo_id):
    tipo = TipoEquipamento.query.get_or_404(tipo_id)
    campos = tipo.campos.order_by(CampoTipoEquipamento.ordem).all()
    return jsonify([{
        'id': c.id,
        'nome_campo': c.nome_campo,
        'tipo_dado': c.tipo_dado,
        'obrigatorio': c.obrigatorio,
        'opcoes_selecao': c.opcoes_selecao
    } for c in campos])


# ── Tipos de Equipamento (admin) ──────────────────────────────────────────────

@equipamentos_bp.route('/tipos')
@login_required
def listar_tipos():
    if not current_user.pode('gerenciar_tipos_equipamento'):
        abort(403)
    tipos = TipoEquipamento.query.order_by(TipoEquipamento.nome).all()
    return render_template('equipamentos/tipos/listar.html', tipos=tipos)


@equipamentos_bp.route('/tipos/novo', methods=['GET', 'POST'])
@login_required
def novo_tipo():
    if not current_user.pode('gerenciar_tipos_equipamento'):
        abort(403)
    if request.method == 'POST':
        tipo = TipoEquipamento(
            nome=request.form['nome'].strip(),
            descricao=request.form.get('descricao', '').strip(),
            tem_patrimonio=request.form.get('tem_patrimonio') == 'on',
            icone=request.form.get('icone', 'bi-box').strip(),
        )
        db.session.add(tipo)
        db.session.commit()
        flash(f'Tipo "{tipo.nome}" cadastrado!', 'success')
        return redirect(url_for('equipamentos.editar_tipo', id=tipo.id))
    return render_template('equipamentos/tipos/form.html', tipo=None)


@equipamentos_bp.route('/tipos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tipo(id):
    if not current_user.pode('gerenciar_tipos_equipamento'):
        abort(403)
    tipo = TipoEquipamento.query.get_or_404(id)
    if request.method == 'POST':
        tipo.nome = request.form['nome'].strip()
        tipo.descricao = request.form.get('descricao', '').strip()
        tipo.tem_patrimonio = request.form.get('tem_patrimonio') == 'on'
        tipo.icone = request.form.get('icone', 'bi-box').strip()
        db.session.commit()
        flash('Tipo atualizado!', 'success')
        return redirect(url_for('equipamentos.listar_tipos'))
    campos = tipo.campos.order_by(CampoTipoEquipamento.ordem).all()
    return render_template('equipamentos/tipos/form.html', tipo=tipo, campos=campos)


@equipamentos_bp.route('/tipos/<int:tipo_id>/campo/novo', methods=['POST'])
@login_required
def novo_campo_tipo(tipo_id):
    if not current_user.pode('gerenciar_tipos_equipamento'):
        abort(403)
    import json
    tipo = TipoEquipamento.query.get_or_404(tipo_id)
    opcoes_raw = request.form.get('opcoes_selecao', '').strip()
    opcoes = None
    if opcoes_raw:
        try:
            opcoes = json.loads(opcoes_raw)
        except Exception:
            opcoes = [o.strip() for o in opcoes_raw.split(',') if o.strip()]

    campo = CampoTipoEquipamento(
        tipo_equipamento_id=tipo_id,
        nome_campo=request.form['nome_campo'].strip(),
        tipo_dado=request.form.get('tipo_dado', 'texto'),
        obrigatorio=request.form.get('obrigatorio') == 'on',
        opcoes_selecao=opcoes,
        ordem=request.form.get('ordem', 0, type=int),
    )
    db.session.add(campo)
    db.session.commit()
    flash('Campo adicionado!', 'success')
    return redirect(url_for('equipamentos.editar_tipo', id=tipo_id))


@equipamentos_bp.route('/tipos/campo/<int:campo_id>/excluir', methods=['POST'])
@login_required
def excluir_campo_tipo(campo_id):
    if not current_user.pode('gerenciar_tipos_equipamento'):
        abort(403)
    campo = CampoTipoEquipamento.query.get_or_404(campo_id)
    tipo_id = campo.tipo_equipamento_id
    db.session.delete(campo)
    db.session.commit()
    flash('Campo removido.', 'info')
    return redirect(url_for('equipamentos.editar_tipo', id=tipo_id))
