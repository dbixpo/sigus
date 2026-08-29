from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.contrato import Contrato, ContratoTipoEquipamento, ContratoAcao, ACAO_TIPOS, MODALIDADE_OPCOES
from app.models.equipamento import Equipamento, TipoEquipamento, Marca, Modelo
from app.models.empresa import EmpresaContratada

contratos_bp = Blueprint('contratos', __name__, url_prefix='/contratos')


def _sort_contratos(query, sort_col, order):
    """Aplica ordenação na query de contratos."""
    asc = order != 'desc'
    col_map = {
        'identificador': db.func.coalesce(Contrato.numero_sei, Contrato.cpl),
        'empresa': db.func.coalesce(EmpresaContratada.razao_social, Contrato.empresa),
        'tipo': Contrato.tipo_contrato,
        'objeto': Contrato.objeto,
        'inicio': Contrato.data_inicio,
        'vencimento': Contrato.data_fim,
        'dias': Contrato.data_fim,
        'status': Contrato.status,
        'atualizado': Contrato.atualizado_em,
    }
    col = col_map.get(sort_col)
    if not col:
        return query.order_by(Contrato.data_fim.asc())
    if sort_col == 'dias':
        return query.order_by(col.desc() if asc else col.asc())
    return query.order_by(col.asc() if asc else col.desc())


@contratos_bp.route('/')
@login_required
def listar():
    if not current_user.pode('cadastrar_contrato') and not current_user.pode('editar_contrato'):
        abort(403)
    status = request.args.get('status', '')
    mandado_judicial = request.args.get('mandado_judicial', '')
    sort_col = request.args.get('sort', 'vencimento')
    order = request.args.get('order', 'asc')
    query = Contrato.query.outerjoin(EmpresaContratada, Contrato.empresa_id == EmpresaContratada.id)
    if status:
        query = query.filter(Contrato.status == status)
    if mandado_judicial == '1':
        query = query.filter(Contrato.mandado_judicial == True)
    elif mandado_judicial == '0':
        query = query.filter(Contrato.mandado_judicial == False)
    query = _sort_contratos(query, sort_col, order)
    contratos = query.all()
    for c in contratos:
        c.atualizar_status()
    db.session.commit()
    return render_template('contratos/listar.html',
                           contratos=contratos, filtro_status=status, filtro_mandado_judicial=mandado_judicial,
                           sort_col=sort_col, sort_order=order)


def _obter_empresa_form():
    """Retorna (empresa_id, empresa_str) a partir do form. Usa razão social (administrativo)."""
    emp_id = request.form.get('empresa_id', '').strip()
    if emp_id == 'outro':
        return None, request.form.get('empresa', '').strip()
    if emp_id and emp_id.isdigit():
        emp = EmpresaContratada.query.get(int(emp_id))
        if emp:
            return emp.id, emp.razao_social
    return None, request.form.get('empresa', '').strip()


@contratos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if not current_user.pode('cadastrar_contrato'):
        abort(403)
    empresas = EmpresaContratada.query.filter_by(ativo=True).order_by(EmpresaContratada.razao_social).all()
    if request.method == 'POST':
        from datetime import date
        from datetime import datetime as dt
        emp_id, emp_str = _obter_empresa_form()
        if not emp_id and not emp_str:
            flash('Selecione uma empresa cadastrada ou informe o nome manualmente.', 'danger')
            return render_template('contratos/form.html', contrato=None, empresas=empresas, modalidades=MODALIDADE_OPCOES)
        numero_sei = request.form.get('numero_sei', '').strip() or None
        cpl = request.form.get('cpl', '').strip() or None
        if not numero_sei and not cpl:
            flash('Informe a CPL (contratos antigos) ou o Nº do Processo SEI (contratos novos).', 'danger')
            return render_template('contratos/form.html', contrato=None, empresas=empresas, modalidades=MODALIDADE_OPCOES)
        data_inicio = dt.strptime(request.form['data_inicio'], '%Y-%m-%d').date()
        data_fim = dt.strptime(request.form['data_fim'], '%Y-%m-%d').date()
        data_assinatura = None
        if request.form.get('data_assinatura'):
            data_assinatura = dt.strptime(request.form['data_assinatura'], '%Y-%m-%d').date()
        def _decimal(v):
            if not v:
                return None
            try:
                return float(str(v).replace(',', '.'))
            except (ValueError, TypeError):
                return None
        contrato = Contrato(
            numero_sei=numero_sei,
            link_sei=request.form.get('link_sei', '').strip() or None,
            cpl=cpl,
            empresa=emp_str or None,
            empresa_id=emp_id,
            modalidade=request.form.get('modalidade', '').strip() or None,
            tipo_contrato=request.form.get('tipo_contrato', '').strip(),
            objeto=request.form.get('objeto', '').strip(),
            data_inicio=data_inicio,
            data_fim=data_fim,
            data_assinatura=data_assinatura,
            valor_total=_decimal(request.form.get('valor_total')),
            observacoes=request.form.get('observacoes', '').strip(),
            criado_por=current_user.id,
            secao=request.form.get('secao', '').strip() or None,
            numero_contrato=request.form.get('numero_contrato', '').strip() or None,
            vigencia=request.form.get('vigencia', '').strip() or None,
            fonte=request.form.get('fonte', '').strip() or None,
            valor_inicial=_decimal(request.form.get('valor_inicial')),
            valor_atual=_decimal(request.form.get('valor_atual')),
            valor_mensal_atual=_decimal(request.form.get('valor_mensal_atual')),
            aditivo_data_pct=request.form.get('aditivo_data_pct', '').strip() or None,
            reajuste_data_base_pct=request.form.get('reajuste_data_base_pct', '').strip() or None,
            fiscalizacao=request.form.get('fiscalizacao', '').strip() or None,
            supressao_data_pct=request.form.get('supressao_data_pct', '').strip() or None,
            contato_nome_telefone=request.form.get('contato_nome_telefone', '').strip() or None,
            empenhos=request.form.get('empenhos', '').strip() or None,
            mandado_judicial=request.form.get('mandado_judicial') == '1',
        )
        contrato.atualizar_status()
        db.session.add(contrato)
        db.session.commit()
        flash(f'Contrato {contrato.identificador} cadastrado!', 'success')
        return redirect(url_for('contratos.detalhe', id=contrato.id))
    return render_template('contratos/form.html', contrato=None, empresas=empresas, modalidades=MODALIDADE_OPCOES)


@contratos_bp.route('/<int:id>')
@login_required
def detalhe(id):
    from app.models.contrato import ContratoAcao
    from app.models.contrato_financeiro import ContratoFinanceiro
    from datetime import date
    contrato = Contrato.query.get_or_404(id)
    itens = contrato.tipos_equipamento.all()
    acoes = contrato.acoes.order_by(ContratoAcao.data_acao.desc(), ContratoAcao.criado_em.desc()).all()
    empenhos = ContratoFinanceiro.query.filter_by(contrato_id=id).order_by(db.desc(ContratoFinanceiro.criado_em)).all()
    # Histórico unificado: ações + empenhos, ordenado por data (mais recente primeiro)
    historico = []
    for a in acoes:
        historico.append({'tipo': 'acao', 'data': a.data_acao, 'item': a})
    for e in empenhos:
        dt = e.criado_em.date() if e.criado_em else (e.data_necessaria or date(1900, 1, 1))
        historico.append({'tipo': 'empenho', 'data': dt, 'item': e})
    historico.sort(key=lambda x: x['data'], reverse=True)
    tipos_equipamento_disponiveis = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    return render_template('contratos/detalhe.html',
                           contrato=contrato, itens=itens, acoes=acoes, empenhos=empenhos,
                           historico=historico,
                           tipos_equipamento_disponiveis=tipos_equipamento_disponiveis, acao_tipos=ACAO_TIPOS)


@contratos_bp.route('/<int:id>/imprimir')
@login_required
def imprimir(id):
    if not current_user.pode('cadastrar_contrato') and not current_user.pode('editar_contrato'):
        abort(403)
    from app.models.contrato import ContratoAcao
    from app.models.chamado import Chamado, ChamadoHistorico
    contrato = Contrato.query.get_or_404(id)
    itens = contrato.tipos_equipamento.all()
    acoes = contrato.acoes.order_by(ContratoAcao.data_acao.asc(), ContratoAcao.criado_em.asc()).all()
    chamados = (Chamado.query
                .join(ChamadoHistorico, Chamado.id == ChamadoHistorico.chamado_id)
                .filter(ChamadoHistorico.contrato_id == id)
                .order_by(Chamado.criado_em.desc())
                .distinct()
                .all())
    from datetime import datetime
    return render_template('contratos/imprimir.html',
                           contrato=contrato, itens=itens, acoes=acoes, chamados=chamados,
                           now=datetime.utcnow())


@contratos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.pode('editar_contrato'):
        abort(403)
    contrato = Contrato.query.get_or_404(id)
    empresas = EmpresaContratada.query.filter_by(ativo=True).order_by(EmpresaContratada.razao_social).all()
    if request.method == 'POST':
        from datetime import datetime as dt, date
        emp_id, emp_str = _obter_empresa_form()
        if not emp_id and not emp_str:
            flash('Selecione uma empresa cadastrada ou informe o nome manualmente.', 'danger')
            return render_template('contratos/form.html', contrato=contrato, empresas=empresas, modalidades=MODALIDADE_OPCOES)
        numero_sei = request.form.get('numero_sei', '').strip() or None
        cpl = request.form.get('cpl', '').strip() or None
        if not numero_sei and not cpl:
            flash('Informe a CPL (contratos antigos) ou o Nº do Processo SEI (contratos novos).', 'danger')
            return render_template('contratos/form.html', contrato=contrato, empresas=empresas, modalidades=MODALIDADE_OPCOES)
        def _decimal(v):
            if not v:
                return None
            try:
                return float(str(v).replace(',', '.'))
            except (ValueError, TypeError):
                return None
        data_assinatura = None
        if request.form.get('data_assinatura'):
            data_assinatura = dt.strptime(request.form['data_assinatura'], '%Y-%m-%d').date()
        contrato.numero_sei = numero_sei
        contrato.link_sei = request.form.get('link_sei', '').strip() or None
        contrato.cpl = cpl
        contrato.empresa = emp_str or None
        contrato.empresa_id = emp_id
        contrato.modalidade = request.form.get('modalidade', '').strip() or None
        contrato.tipo_contrato = request.form.get('tipo_contrato', '').strip()
        contrato.objeto = request.form.get('objeto', '').strip()
        contrato.data_inicio = dt.strptime(request.form['data_inicio'], '%Y-%m-%d').date()
        contrato.data_fim = dt.strptime(request.form['data_fim'], '%Y-%m-%d').date()
        contrato.data_assinatura = data_assinatura
        contrato.valor_total = _decimal(request.form.get('valor_total'))
        contrato.observacoes = request.form.get('observacoes', '').strip()
        contrato.secao = request.form.get('secao', '').strip() or None
        contrato.numero_contrato = request.form.get('numero_contrato', '').strip() or None
        contrato.vigencia = request.form.get('vigencia', '').strip() or None
        contrato.fonte = request.form.get('fonte', '').strip() or None
        contrato.valor_inicial = _decimal(request.form.get('valor_inicial'))
        contrato.valor_atual = _decimal(request.form.get('valor_atual'))
        contrato.valor_mensal_atual = _decimal(request.form.get('valor_mensal_atual'))
        contrato.aditivo_data_pct = request.form.get('aditivo_data_pct', '').strip() or None
        contrato.reajuste_data_base_pct = request.form.get('reajuste_data_base_pct', '').strip() or None
        contrato.fiscalizacao = request.form.get('fiscalizacao', '').strip() or None
        contrato.supressao_data_pct = request.form.get('supressao_data_pct', '').strip() or None
        contrato.contato_nome_telefone = request.form.get('contato_nome_telefone', '').strip() or None
        contrato.empenhos = request.form.get('empenhos', '').strip() or None
        contrato.mandado_judicial = request.form.get('mandado_judicial') == '1'
        contrato.atualizar_status()
        db.session.commit()
        flash('Contrato atualizado!', 'success')
        return redirect(url_for('contratos.detalhe', id=contrato.id))
    return render_template('contratos/form.html', contrato=contrato, empresas=empresas, modalidades=MODALIDADE_OPCOES)


@contratos_bp.route('/api/marcas-por-tipo/<int:tipo_id>')
@login_required
def api_marcas_por_tipo(tipo_id):
    """Marcas vinculadas ao tipo (para select cascata)."""
    tipo = TipoEquipamento.query.get_or_404(tipo_id)
    marcas = tipo.marcas.order_by(Marca.nome).all()
    return jsonify([{'id': m.id, 'nome': m.nome} for m in marcas])


@contratos_bp.route('/api/modelos')
@login_required
def api_modelos():
    """Modelos por marca e tipo (para select cascata)."""
    marca_id = request.args.get('marca_id', type=int)
    tipo_id = request.args.get('tipo_id', type=int)
    if not marca_id:
        return jsonify([])
    q = Modelo.query.filter_by(marca_id=marca_id)
    if tipo_id:
        q = q.filter_by(tipo_equipamento_id=tipo_id)
    modelos = q.order_by(Modelo.nome).all()
    return jsonify([{'id': m.id, 'nome': m.nome} for m in modelos])


@contratos_bp.route('/<int:id>/vincular-item', methods=['POST'])
@login_required
def vincular_item(id):
    if not current_user.pode('editar_contrato'):
        abort(403)
    contrato = Contrato.query.get_or_404(id)
    tipo_equipamento_id = request.form.get('tipo_equipamento_id', type=int)
    marca_id = request.form.get('marca_id', type=int) or None
    modelo_id = request.form.get('modelo_id', type=int) or None
    descricao = request.form.get('descricao_cobertura', '').strip()

    # Se marca não informada, modelo deve ser vazio
    if not marca_id:
        modelo_id = None

    q = ContratoTipoEquipamento.query.filter_by(
        contrato_id=id, tipo_equipamento_id=tipo_equipamento_id)
    if marca_id is None:
        q = q.filter(ContratoTipoEquipamento.marca_id.is_(None))
    else:
        q = q.filter(ContratoTipoEquipamento.marca_id == marca_id)
    if modelo_id is None:
        q = q.filter(ContratoTipoEquipamento.modelo_id.is_(None))
    else:
        q = q.filter(ContratoTipoEquipamento.modelo_id == modelo_id)
    existente = q.first()

    if not existente:
        db.session.add(ContratoTipoEquipamento(
            contrato_id=id,
            tipo_equipamento_id=tipo_equipamento_id,
            marca_id=marca_id,
            modelo_id=modelo_id,
            descricao_cobertura=descricao or None
        ))
        db.session.commit()
        flash('Item vinculado ao contrato!', 'success')
    else:
        flash('Esta combinação (tipo/marca/modelo) já está vinculada a este contrato.', 'warning')
    return redirect(url_for('contratos.detalhe', id=id))


@contratos_bp.route('/<int:id>/acao', methods=['POST'])
@login_required
def adicionar_acao(id):
    if not current_user.pode('editar_contrato'):
        abort(403)
    from datetime import datetime as dt, date
    import os
    import uuid
    import mimetypes
    contrato = Contrato.query.get_or_404(id)
    tipo = request.form.get('tipo', '').strip()
    if tipo not in [t[0] for t in ACAO_TIPOS]:
        flash('Tipo de ação inválido.', 'danger')
        return redirect(url_for('contratos.detalhe', id=id))
    data_acao = dt.strptime(request.form.get('data_acao', ''), '%Y-%m-%d').date()
    obs = request.form.get('observacao', '').strip() or None
    periodo_meses = request.form.get('periodo_meses', type=int) or None
    nova_data_fim = None
    if request.form.get('nova_data_fim'):
        nova_data_fim = dt.strptime(request.form['nova_data_fim'], '%Y-%m-%d').date()
    elif periodo_meses and contrato.data_fim:
        d = contrato.data_fim
        new_month = d.month + periodo_meses
        year = d.year + (new_month - 1) // 12
        month = ((new_month - 1) % 12) + 1
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        day = min(d.day, last_day)
        nova_data_fim = date(year, month, day)
    def _float(val):
        if not val:
            return None
        try:
            return float(str(val).replace(',', '.'))
        except (ValueError, TypeError):
            return None
    valor_adicional = _float(request.form.get('valor_adicional'))
    porcentagem_adicional = _float(request.form.get('porcentagem_adicional'))
    porcentagem_multa = _float(request.form.get('porcentagem_multa'))
    anexo_filename = None
    f = request.files.get('anexo')
    if f and f.filename:
        mime = f.mimetype or mimetypes.guess_type(f.filename)[0] or ''
        ext = (os.path.splitext(f.filename)[1] or '').lower()
        if ext in ('.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif') or (mime and mime.startswith('image/')):
            ext = (os.path.splitext(f.filename)[1] or '.pdf').lower()
            anexo_filename = f'{uuid.uuid4().hex}{ext}'
            upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'contrato_acoes')
            os.makedirs(upload_dir, exist_ok=True)
            f.save(os.path.join(upload_dir, anexo_filename))
    acao = ContratoAcao(
        contrato_id=id,
        tipo=tipo,
        data_acao=data_acao,
        observacao=obs,
        periodo_meses=periodo_meses,
        nova_data_fim=nova_data_fim,
        valor_adicional=valor_adicional,
        porcentagem_adicional=porcentagem_adicional,
        porcentagem_multa=porcentagem_multa,
        anexo_filename=anexo_filename,
        criado_por=current_user.id,
    )
    db.session.add(acao)
    if tipo == 'termo_encerramento':
        contrato.status = 'encerrado'
    elif tipo in ('prorrogacao', 'prorrogacao_excepcional', 'renovacao') and nova_data_fim:
        contrato.data_fim = nova_data_fim
        contrato.atualizar_status()
    else:
        contrato.atualizar_status()
    db.session.commit()
    flash(f'Ação {acao.tipo_label} registrada!', 'success')
    return redirect(url_for('contratos.detalhe', id=id))


@contratos_bp.route('/item/<int:item_id>/remover', methods=['POST'])
@login_required
def remover_item(item_id):
    if not current_user.pode('editar_contrato'):
        abort(403)
    item = ContratoTipoEquipamento.query.get_or_404(item_id)
    contrato_id = item.contrato_id
    db.session.delete(item)
    db.session.commit()
    flash('Item removido do contrato.', 'info')
    return redirect(url_for('contratos.detalhe', id=contrato_id))
