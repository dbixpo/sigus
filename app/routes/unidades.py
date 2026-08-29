from datetime import date
from urllib.parse import quote
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, make_response
from flask_login import login_required, current_user
from app import db
from app.models.unidade import Unidade, UsuarioUnidade
from app.models.tipo_unidade import TipoUnidade
from app.models.predio import Predio
from app.models.usuario import Usuario, CBOS, VINCULOS, TIPOS_VINCULO
from app.models.ficha_cnes import FichaCnesVinculo
from app.utils import _montar_corpo_email_ficha, _montar_corpo_email_rede

_CNES_DEST = 'cnes@sorocaba.sp.gov.br,suportesis.sorocaba@sorocaba.sp.gov.br'
_REDE_DEST = 'suportesis.sorocaba@sorocaba.sp.gov.br'


def _links_email_ficha(ficha):
    """Retorna dict com links mailto para CNES e Rede a partir de uma ficha."""
    u = ficha.unidade
    prof = ficha.usuario
    tipo_verb = 'Vinculação' if ficha.tipo == 'cadastro' else 'Desvinculação'

    assunto_cnes = quote(f'{tipo_verb} CNES — {prof.nome} — {u.nome}')
    corpo_cnes   = quote(_montar_corpo_email_ficha(ficha))

    assunto_rede = quote(f'Acesso à Rede — {tipo_verb} — {prof.nome} — {u.nome}')
    corpo_rede   = quote(_montar_corpo_email_rede(ficha))

    return {
        'cnes': f'mailto:{_CNES_DEST}?subject={assunto_cnes}&body={corpo_cnes}',
        'rede': f'mailto:{_REDE_DEST}?subject={assunto_rede}&body={corpo_rede}',
    }

unidades_bp = Blueprint('unidades', __name__, url_prefix='/unidades')


@unidades_bp.route('/')
@login_required
def listar():
    if current_user.pode('ver_todas_unidades'):
        unidades = Unidade.query.order_by(Unidade.nome).all()
    else:
        ids = [uu.unidade_id for uu in current_user.unidades.filter_by(ativo=True).all()]
        unidades = Unidade.query.filter(Unidade.id.in_(ids)).order_by(Unidade.nome).all()
        # Usuário com exatamente 1 unidade → abre direto, sem precisar escolher
        if len(unidades) == 1:
            return redirect(url_for('unidades.detalhe', id=unidades[0].id))
    return render_template('unidades/listar.html', unidades=unidades)


@unidades_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    if not current_user.pode('cadastrar_unidade'):
        abort(403)
    tipos = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()
    predios = Predio.query.filter_by(ativo=True).order_by(Predio.nome).all()
    predios_data = {p.id: {
        'nome':        p.nome,
        'telefone':    p.telefone or '',
        'endereco':    p.endereco or '',
        'numero':      p.numero or '',
        'complemento': p.complemento or '',
        'bairro':      p.bairro or '',
        'cidade':      p.cidade or '',
        'uf':          p.uf or '',
        'cep':         p.cep or '',
        'link_maps':   p.link_maps or '',
    } for p in predios}
    gerentes_disponiveis = Usuario.query.filter(
        Usuario.perfil.in_(['coordenador', 'administrador']),
        Usuario.ativo == True
    ).order_by(Usuario.nome).all()
    predio_id_pre = request.args.get('predio_id', type=int)
    if request.method == 'POST':
        tipo_id = request.form.get('tipo_unidade_id', type=int)
        tipo_obj = TipoUnidade.query.get(tipo_id) if tipo_id else None
        u = Unidade(
            nome=request.form['nome'].strip(),
            tipo=tipo_obj.sigla if tipo_obj else '',
            tipo_unidade_id=tipo_id,
            predio_id=request.form.get('predio_id', type=int) or None,
            endereco=request.form.get('endereco', '').strip(),
            numero=request.form.get('numero', '').strip(),
            complemento=request.form.get('complemento', '').strip() or None,
            bairro=request.form.get('bairro', '').strip(),
            cidade=request.form.get('cidade', 'Sorocaba').strip(),
            uf=request.form.get('uf', 'SP').upper(),
            cep=request.form.get('cep', '').strip(),
            telefone=request.form.get('telefone', '').strip(),
            ramal=request.form.get('ramal', '').strip() or None,
            email=request.form.get('email', '').strip(),
            link_maps=request.form.get('link_maps', '').strip() or None,
            numero_cnes=request.form.get('numero_cnes', '').strip() or None,
            observacoes=request.form.get('observacoes', '').strip(),
        )
        db.session.add(u)
        db.session.flush()
        for gid in request.form.getlist('gerentes[]'):
            gid = int(gid)
            db.session.add(UsuarioUnidade(usuario_id=gid, unidade_id=u.id, papel='gerente'))
        db.session.commit()
        flash(f'Unidade "{u.nome}" cadastrada com sucesso!', 'success')
        return redirect(url_for('unidades.detalhe', id=u.id))
    return render_template('unidades/form.html', unidade=None, tipos=tipos,
                           predios=predios, predios_data=predios_data,
                           predio_id_pre=predio_id_pre,
                           gerentes_disponiveis=gerentes_disponiveis,
                           gerentes_atuais=[])


@unidades_bp.route('/<int:id>')
@login_required
def detalhe(id):
    unidade = Unidade.query.get_or_404(id)
    _verificar_acesso(unidade)
    salas = unidade.salas.filter_by(ativo=True).order_by('nome').all()

    # Todos os vínculos (ativos e inativos) para a tabela de profissionais
    todos_vinculos = unidade.usuarios.order_by(
        db.text('ativo DESC, usuario_unidade.id ASC')
    ).all()
    vinculos_ativos = [v for v in todos_vinculos if v.ativo]
    ids_vinculados  = [v.usuario_id for v in vinculos_ativos]

    # Última ficha de cadastro por profissional (para CBO/CH/Vínculo na tabela)
    ultima_ficha_por_usuario = {}
    fichas = (FichaCnesVinculo.query
              .filter_by(unidade_id=id)
              .order_by(FichaCnesVinculo.gerado_em.desc())
              .all())
    for f in fichas:
        if f.usuario_id not in ultima_ficha_por_usuario or f.tipo == 'cadastro':
            ultima_ficha_por_usuario[f.usuario_id] = f

    # Links de e-mail por vínculo (a partir da última ficha)
    links_email_vinculo = {}
    for uid, f in ultima_ficha_por_usuario.items():
        links_email_vinculo[uid] = _links_email_ficha(f)

    chamados_recentes = unidade.chamados.filter(
        db.text("status NOT IN ('cancelado', 'concluido')")
    ).order_by(db.text('criado_em desc')).limit(10).all()

    usuarios_disponiveis = Usuario.query.filter(
        Usuario.ativo == True,
        Usuario.perfil != 'administrador',
        ~Usuario.id.in_(ids_vinculados)
    ).order_by(Usuario.nome).all()

    # Equipamentos agrupados por sala
    from app.models.equipamento import Equipamento
    equipamentos_por_sala = {}
    for sala in salas:
        equips = sala.equipamentos.filter_by(ativo=True).order_by('id').all()
        equipamentos_por_sala[sala.id] = equips
    total_equipamentos_unidade = sum(len(v) for v in equipamentos_por_sala.values())

    # Solicitações de vínculo pendentes e histórico
    from app.models.solicitacao_vinculo import SolicitacaoVinculo
    solicitacoes_pendentes = (SolicitacaoVinculo.query
                              .filter_by(unidade_id=id, status='pendente')
                              .order_by(SolicitacaoVinculo.criado_em.asc())
                              .all())
    solicitacoes_historico = (SolicitacaoVinculo.query
                              .filter(SolicitacaoVinculo.unidade_id == id,
                                      SolicitacaoVinculo.status != 'pendente')
                              .order_by(SolicitacaoVinculo.aprovado_em.desc())
                              .limit(20).all())

    return render_template('unidades/detalhe.html',
                           unidade=unidade, salas=salas,
                           todos_vinculos=todos_vinculos,
                           vinculos=vinculos_ativos,
                           chamados_recentes=chamados_recentes,
                           usuarios_disponiveis=usuarios_disponiveis,
                           fichas=fichas,
                           ultima_ficha_por_usuario=ultima_ficha_por_usuario,
                           links_email_vinculo=links_email_vinculo,
                           cbos=CBOS,
                           vinculos_cnes=VINCULOS,
                           tipos_vinculo=TIPOS_VINCULO,
                           equipamentos_por_sala=equipamentos_por_sala,
                           total_equipamentos_unidade=total_equipamentos_unidade,
                           solicitacoes_pendentes=solicitacoes_pendentes,
                           solicitacoes_historico=solicitacoes_historico)


@unidades_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.pode('editar_unidade'):
        abort(403)
    unidade = Unidade.query.get_or_404(id)
    tipos = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()
    predios = Predio.query.filter_by(ativo=True).order_by(Predio.nome).all()
    predios_data = {p.id: {
        'nome':        p.nome,
        'telefone':    p.telefone or '',
        'endereco':    p.endereco or '',
        'numero':      p.numero or '',
        'complemento': p.complemento or '',
        'bairro':      p.bairro or '',
        'cidade':      p.cidade or '',
        'uf':          p.uf or '',
        'cep':         p.cep or '',
        'link_maps':   p.link_maps or '',
    } for p in predios}
    gerentes_disponiveis = Usuario.query.filter(
        Usuario.perfil.in_(['coordenador', 'administrador']),
        Usuario.ativo == True
    ).order_by(Usuario.nome).all()
    gerentes_atuais = [v.usuario_id for v in unidade.usuarios.filter_by(ativo=True).all()
                       if v.usuario and v.usuario.perfil in ('coordenador', 'administrador')]
    if request.method == 'POST':
        tipo_id = request.form.get('tipo_unidade_id', type=int)
        tipo_obj = TipoUnidade.query.get(tipo_id) if tipo_id else None
        unidade.nome = request.form['nome'].strip()
        unidade.tipo = tipo_obj.sigla if tipo_obj else unidade.tipo
        unidade.tipo_unidade_id = tipo_id
        unidade.predio_id = request.form.get('predio_id', type=int) or None
        unidade.endereco = request.form.get('endereco', '').strip()
        unidade.numero = request.form.get('numero', '').strip()
        unidade.complemento = request.form.get('complemento', '').strip() or None
        unidade.bairro = request.form.get('bairro', '').strip()
        unidade.cidade = request.form.get('cidade', 'Sorocaba').strip()
        unidade.uf = request.form.get('uf', 'SP').upper()
        unidade.cep = request.form.get('cep', '').strip()
        unidade.telefone = request.form.get('telefone', '').strip()
        unidade.ramal    = request.form.get('ramal', '').strip() or None
        unidade.email = request.form.get('email', '').strip()
        unidade.link_maps   = request.form.get('link_maps', '').strip() or None
        unidade.numero_cnes = request.form.get('numero_cnes', '').strip() or None
        unidade.status = request.form.get('status', 'ativa')
        unidade.observacoes = request.form.get('observacoes', '').strip()

        db.session.commit()
        flash('Unidade atualizada com sucesso!', 'success')
        return redirect(url_for('unidades.detalhe', id=unidade.id))
    return render_template('unidades/form.html', unidade=unidade, tipos=tipos,
                           predios=predios, predios_data=predios_data,
                           predio_id_pre=None,
                           gerentes_disponiveis=gerentes_disponiveis,
                           gerentes_atuais=gerentes_atuais)


@unidades_bp.route('/<int:id>/vincular', methods=['POST'])
@login_required
def vincular_usuario(id):
    if not current_user.pode('vincular_profissionais'):
        abort(403)
    unidade = Unidade.query.get_or_404(id)
    usuario_id = request.form.get('usuario_id', type=int)
    usuario = Usuario.query.get_or_404(usuario_id)

    if current_user.perfil == 'administrativo' and usuario.perfil == 'coordenador':
        flash('Administrativos não podem vincular gerentes.', 'danger')
        return redirect(url_for('unidades.detalhe', id=id))

    # Criar ou reativar vínculo
    matricula_id = request.form.get('matricula_id', type=int) or None
    existente = UsuarioUnidade.query.filter_by(usuario_id=usuario_id, unidade_id=id).first()
    if existente:
        existente.ativo = True
        if matricula_id:
            existente.matricula_id = matricula_id
    else:
        db.session.add(UsuarioUnidade(usuario_id=usuario_id, unidade_id=id,
                                      matricula_id=matricula_id))

    # Gravar ficha CNES de cadastro com os dados do modal
    dt_str = request.form.get('dt_entrada_unidade', '')
    ch_str = request.form.get('carga_horaria', '')
    ficha = FichaCnesVinculo(
        usuario_id=usuario_id,
        unidade_id=id,
        tipo='cadastro',
        vinculo=request.form.get('vinculo') or None,
        tipo_vinculo=request.form.get('tipo_vinculo') or None,
        carga_horaria=int(ch_str) if ch_str.isdigit() else None,
        cbo=request.form.get('cbo') or None,
        especialidade_residencia=request.form.get('especialidade_residencia', '').strip() or None,
        dt_entrada_unidade=date.fromisoformat(dt_str) if dt_str else None,
        cns_profissional=request.form.get('cns_profissional', '').strip() or None,
        observacoes=request.form.get('observacoes', '').strip() or None,
        gerado_por=current_user.id,
    )
    db.session.add(ficha)
    db.session.flush()

    # Notifica o novo membro sobre chamados em aberto da unidade (para ele ficar a par)
    if usuario.perfil in ('coordenador', 'administrativo', 'administrador', 'gestor_secretaria'):
        from app.models.chamado import Chamado as _Chamado
        from app.models.notificacao import Notificacao as _Notif
        chamados_abertos = (_Chamado.query
                            .filter_by(unidade_id=id)
                            .filter(~_Chamado.status.in_(['cancelado', 'concluido']))
                            .order_by(_Chamado.criado_em.desc())
                            .limit(20).all())
        for c in chamados_abertos:
            db.session.add(_Notif(
                usuario_id=usuario_id,
                tipo='chamado_aberto',
                titulo=f'Chamado em aberto: {c.numero}',
                texto=c.titulo,
                chamado_id=c.id,
            ))

    db.session.commit()

    flash(f'{usuario.nome} vinculado(a). Ficha CNES de cadastro gerada.', 'success')
    return redirect(url_for('unidades.detalhe', id=id))


@unidades_bp.route('/<int:id>/desvincular/<int:usuario_id>', methods=['POST'])
@login_required
def desvincular_usuario(id, usuario_id):
    if not current_user.pode('vincular_profissionais'):
        abort(403)
    vinculo = UsuarioUnidade.query.filter_by(unidade_id=id, usuario_id=usuario_id).first_or_404()
    usuario = Usuario.query.get(usuario_id)
    unidade = Unidade.query.get_or_404(id)

    if current_user.perfil == 'administrativo' and usuario and usuario.perfil == 'coordenador':
        flash('Administrativos não podem desvincular gerentes.', 'danger')
        return redirect(url_for('unidades.detalhe', id=id))

    vinculo.ativo = False

    # Gravar ficha CNES de descadastro
    ficha = FichaCnesVinculo(
        usuario_id=usuario_id,
        unidade_id=id,
        tipo='descadastro',
        observacoes=request.form.get('motivo', '').strip() or None,
        gerado_por=current_user.id,
    )
    db.session.add(ficha)
    db.session.commit()

    flash(f'Vínculo removido. Ficha CNES de descadastro gerada.', 'info')
    return redirect(url_for('unidades.detalhe', id=id))


@unidades_bp.route('/<int:id>/editar-cbo/<int:usuario_id>', methods=['POST'])
@login_required
def editar_cbo_vinculo(id, usuario_id):
    """Altera o CBO de um profissional APENAS no vínculo com a unidade,
    gerando automaticamente uma ficha CNES de alteração."""
    if not current_user.pode('vincular_profissionais'):
        abort(403)
    unidade = Unidade.query.get_or_404(id)
    usuario = Usuario.query.get_or_404(usuario_id)
    _verificar_acesso(unidade)

    novo_cbo = request.form.get('cbo', '').strip() or None
    if not novo_cbo:
        flash('Selecione um CBO válido.', 'warning')
        return redirect(url_for('unidades.detalhe', id=id))

    ch_str = request.form.get('carga_horaria', '')
    vinculo = request.form.get('vinculo') or None
    tipo_vinculo = request.form.get('tipo_vinculo') or None

    ficha = FichaCnesVinculo(
        usuario_id=usuario_id,
        unidade_id=id,
        tipo='alteracao',
        cbo=novo_cbo,
        carga_horaria=int(ch_str) if ch_str.isdigit() else None,
        vinculo=vinculo,
        tipo_vinculo=tipo_vinculo,
        cns_profissional=request.form.get('cns_profissional', '').strip() or None,
        observacoes=request.form.get('observacoes', '').strip() or None,
        gerado_por=current_user.id,
    )
    db.session.add(ficha)
    db.session.commit()

    flash(f'CBO de {usuario.nome} atualizado no vínculo. Ficha de Alteração CNES gerada.', 'success')
    return redirect(url_for('unidades.ficha_cnes_vinculo', ficha_id=ficha.id))


@unidades_bp.route('/<int:id>/toggle-matricula/<int:matricula_id>', methods=['POST'])
@login_required
def toggle_matricula(id, matricula_id):
    """Ativa ou desativa uma matrícula de um profissional vinculado a esta unidade."""
    if not current_user.pode('vincular_profissionais'):
        abort(403)
    from app.models.matricula import MatriculaProfissional
    _verificar_acesso(Unidade.query.get_or_404(id))
    mat = MatriculaProfissional.query.get_or_404(matricula_id)
    mat.ativo = not mat.ativo
    db.session.commit()
    estado = 'ativada' if mat.ativo else 'desativada'
    flash(f'Matrícula {mat.numero} {estado}.', 'success')
    return redirect(url_for('unidades.detalhe', id=id))


@unidades_bp.route('/<int:id>/maps')
@login_required
def maps_redirect(id):
    """Redireciona para o link_maps da unidade — URL curta para QR code."""
    unidade = Unidade.query.get_or_404(id)
    if unidade.link_maps:
        return redirect(unidade.link_maps)
    abort(404)


@unidades_bp.route('/ficha-cnes/<int:ficha_id>')
@login_required
def ficha_cnes_vinculo(ficha_id):
    """Exibe a ficha CNES de uma vinculação específica para impressão/e-mail."""
    ficha   = FichaCnesVinculo.query.get_or_404(ficha_id)
    usuario = ficha.usuario
    unidade = ficha.unidade
    _verificar_acesso(unidade)

    # Matrícula vinculada ao profissional nessa unidade (para reg_conselho e orgao_emissor)
    vinculo_unidade = UsuarioUnidade.query.filter_by(
        usuario_id=usuario.id, unidade_id=unidade.id
    ).first()
    matricula = vinculo_unidade.matricula if vinculo_unidade else None
    # Fallback: primeira matrícula ativa do profissional
    if not matricula:
        from app.models.matricula import MatriculaProfissional
        matricula = MatriculaProfissional.query.filter_by(
            usuario_id=usuario.id, ativo=True
        ).first()

    # Assinatura digital — busca na solicitação aprovada mais recente desse profissional/unidade
    from app.models.solicitacao_vinculo import SolicitacaoVinculo as _SolVinculo
    _sol_assinada = _SolVinculo.query.filter_by(
        usuario_criado=usuario.id,
        unidade_id=unidade.id,
        status='aprovado',
    ).order_by(_SolVinculo.aprovado_em.desc()).first()
    assinatura_base64 = _sol_assinada.assinatura_base64 if _sol_assinada else None

    tipo_verb = {'cadastro': 'Vinculação', 'alteracao': 'Alteração', 'descadastro': 'Desvinculação'}.get(ficha.tipo, 'Ficha')
    assunto_cnes = f'{tipo_verb} CNES — {usuario.nome} — {unidade.nome}'
    corpo_cnes   = _montar_corpo_email_ficha(ficha)
    dest_cnes    = 'cnes@sorocaba.sp.gov.br,suportesis.sorocaba@sorocaba.sp.gov.br'

    assunto_rede = f'Acesso à Rede — {tipo_verb} — {usuario.nome} — {unidade.nome}'
    corpo_rede   = _montar_corpo_email_rede(ficha)
    dest_rede    = 'suportesis.sorocaba@sorocaba.sp.gov.br'

    resp = make_response(render_template('unidades/ficha_cnes_vinculo.html',
                           ficha=ficha,
                           usuario=usuario,
                           unidade=unidade,
                           matricula=matricula,
                           assinatura_base64=assinatura_base64,
                           assunto_cnes=assunto_cnes,
                           corpo_cnes=corpo_cnes,
                           dest_cnes=dest_cnes,
                           assunto_rede=assunto_rede,
                           corpo_rede=corpo_rede,
                           dest_rede=dest_rede))
    resp.headers['X-Frame-Options'] = 'SAMEORIGIN'  # Permite exibir no modal de impressão (iframe)
    return resp


@unidades_bp.route('/<int:id>/gerar-ficha/<int:usuario_id>', methods=['POST'])
@login_required
def gerar_ficha(id, usuario_id):
    """Gera uma ficha CNES (cadastro, alteracao ou descadastro) sem alterar o vínculo."""
    if not current_user.pode('vincular_profissionais'):
        abort(403)
    unidade = Unidade.query.get_or_404(id)
    usuario = Usuario.query.get_or_404(usuario_id)
    _verificar_acesso(unidade)

    tipo = request.form.get('tipo_ficha', 'cadastro')
    if tipo not in ('cadastro', 'alteracao', 'descadastro'):
        tipo = 'cadastro'

    dt_str = request.form.get('dt_entrada_unidade', '')
    ch_str = request.form.get('carga_horaria', '')

    ficha = FichaCnesVinculo(
        usuario_id=usuario_id,
        unidade_id=id,
        tipo=tipo,
        vinculo=request.form.get('vinculo') or None,
        tipo_vinculo=request.form.get('tipo_vinculo') or None,
        carga_horaria=int(ch_str) if ch_str.isdigit() else None,
        cbo=request.form.get('cbo') or None,
        especialidade_residencia=request.form.get('especialidade_residencia', '').strip() or None,
        dt_entrada_unidade=date.fromisoformat(dt_str) if dt_str else None,
        cns_profissional=request.form.get('cns_profissional', '').strip() or None,
        cnpj_empresa=request.form.get('cnpj_empresa', '').strip() or None,
        nome_empresa=request.form.get('nome_empresa', '').strip() or None,
        observacoes=request.form.get('observacoes', '').strip() or None,
        gerado_por=current_user.id,
    )
    db.session.add(ficha)
    db.session.commit()

    labels = {'cadastro': 'Cadastro', 'alteracao': 'Alteração', 'descadastro': 'Descadastro'}
    flash(f'Ficha CNES de {labels[tipo]} gerada para {usuario.nome}.', 'success')

    # Redireciona para a própria ficha gerada
    return redirect(url_for('unidades.ficha_cnes_vinculo', ficha_id=ficha.id))


@unidades_bp.route('/sem-vinculo')
@login_required
def sem_vinculo():
    """Página exibida quando o usuário não tem vínculo com nenhuma unidade ativa."""
    return render_template('unidades/sem_vinculo.html')


def _verificar_acesso(unidade):
    if current_user.pode('ver_todas_unidades'):
        return
    ids = [uu.unidade_id for uu in current_user.unidades.filter_by(ativo=True).all()]
    if unidade.id not in ids:
        abort(403)
