from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, current_app, g, session
from flask_login import login_required, current_user
from datetime import datetime, date
import os, uuid, mimetypes
from app import db
from app.chamado_acesso import (
    chamado_abertura_acesso, tpl_ctx_abertura, aplicar_solicitante_chamado,
    historico_usuario_id, historico_acao, notificar_abertura, redirect_pos_abertura,
)
from app.models.chamado import (
    Chamado, ChamadoHistorico, ChamadoFoto, ChamadoSolicitacaoItem, SetorManutencao,
    TIPOS_CHAMADO, TIPOS_CHAMADO_LABELS,
    PRIORIDADES, PRIORIDADES_LABELS, PRIORIDADES_BADGE,
    STATUS_CHAMADO, STATUS_CHAMADO_LABELS, STATUS_CHAMADO_BADGE,
    CATEGORIAS_BP, SERVICOS_BP, PROBLEMA_EM,
    MOTIVOS_SOLICITACAO, MOTIVOS_SOLICITACAO_LABELS,
    TIPOS_ANDAMENTO, prioridade_de_gut,
)
from app.models.unidade import Unidade, UsuarioUnidade
from app.models.usuario import Usuario
from app.models.predio import Predio
from app.models.sala import Sala
from app.models.equipamento import Equipamento, TipoEquipamento
from app.models.contrato import Contrato, ContratoTipoEquipamento

_TIPOS_FORM_EXCLUIDOS = {'solicitacao_equipamento', 'solicitacao_administrativa'}

chamados_bp = Blueprint('chamados', __name__, url_prefix='/chamados')

_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            'static', 'uploads', 'chamados')
_UPLOAD_DIR_AND = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                'static', 'uploads', 'andamentos')
_MAX_MB = 50
_ALLOWED_MIME_PREFIX = ('image/', 'video/')


def _salvar_foto(file_obj):
    """Salva um arquivo de foto/vídeo e retorna ChamadoFoto (sem chamado_id)."""
    original  = file_obj.filename or 'sem_nome'
    mime      = file_obj.mimetype or mimetypes.guess_type(original)[0] or 'application/octet-stream'
    ext       = os.path.splitext(original)[1].lower() or ''
    filename  = f"{uuid.uuid4().hex}{ext}"
    dest      = os.path.join(_UPLOAD_DIR, filename)
    os.makedirs(_UPLOAD_DIR, exist_ok=True)
    file_obj.save(dest)
    return ChamadoFoto(filename=filename, original=original, mime_type=mime)


def _salvar_anexo(file_obj):
    """Salva qualquer arquivo como anexo de andamento e retorna AnexoAndamento (sem andamento_id)."""
    original  = file_obj.filename or 'sem_nome'
    mime      = file_obj.mimetype or mimetypes.guess_type(original)[0] or 'application/octet-stream'
    ext       = os.path.splitext(original)[1].lower() or ''
    filename  = f"{uuid.uuid4().hex}{ext}"
    dest      = os.path.join(_UPLOAD_DIR_AND, filename)
    os.makedirs(_UPLOAD_DIR_AND, exist_ok=True)
    conteudo  = file_obj.read()
    tamanho   = len(conteudo)
    with open(dest, 'wb') as fh:
        fh.write(conteudo)
    return AnexoAndamento(filename=filename, original=original,
                          mime_type=mime, tamanho_bytes=tamanho)


def _unidade_contexto_externo():
    u = Unidade.query.filter_by(id=session.get('externo_unidade_id'), status='ativa').first()
    if not u:
        return [], None, False
    return [u], u, True


def _unidades_do_usuario():
    if getattr(g, 'chamado_externo', False):
        return [session.get('externo_unidade_id')]
    if current_user.is_authenticated and current_user.pode('ver_chamados_todos'):
        return None
    return [uu.unidade_id for uu in current_user.unidades.filter_by(ativo=True).all()]


def _unidade_id_form(form_id):
    if getattr(g, 'chamado_externo', False):
        return session.get('externo_unidade_id')
    return form_id


def _validar_gut_form(form):
    g = form.get('gravidade', type=int)
    u = form.get('urgencia', type=int)
    t = form.get('tendencia', type=int)
    if not all(v and 1 <= v <= 5 for v in (g, u, t)):
        return None, 'Preencha Gravidade, Urgência e Tendência (matriz GUT).'
    return (g, u, t), None


def _aplicar_gut_chamado(chamado, gravidade, urgencia, tendencia):
    chamado.sa_gravidade = gravidade
    chamado.sa_urgencia = urgencia
    chamado.sa_tendencia = tendencia
    chamado.prioridade = prioridade_de_gut(gravidade, urgencia, tendencia)


def _historico_obs_abertura(chamado, descricao=''):
    """Monta observação da abertura incluindo GUT do solicitante."""
    partes = []
    if descricao and str(descricao).strip():
        partes.append(str(descricao).strip()[:200])
    if chamado.gut_solicitante_preenchido:
        partes.append(f'Priorização do solicitante: {chamado.gut_solicitante_resumo}')
    return '\n\n'.join(partes) if partes else None


def _sincronizar_prioridade_chamado(chamado):
    chamado.prioridade = chamado.prioridade_efetiva_slug


def _unidades_responsaveis_tipo(tipo_chamado, incluir_unidade_id=None):
    """Unidades ativas configuradas para tratar o tipo de chamado."""
    unidades = list(Unidade.que_tratam_tipo(tipo_chamado))
    ids = {u.id for u in unidades}
    if incluir_unidade_id and incluir_unidade_id not in ids:
        extra = Unidade.query.filter_by(id=incluir_unidade_id, status='ativa').first()
        if extra:
            unidades.append(extra)
    unidades.sort(key=lambda u: u.nome.lower())
    return unidades


def _validar_unidade_responsavel_id(tipo_chamado, unidade_id):
    """Valida unidade responsável para o tipo de chamado. Retorna (id|None, mensagem_erro|None)."""
    if not unidade_id or str(unidade_id) == '0':
        return None, None
    try:
        uid = int(unidade_id)
    except (TypeError, ValueError):
        return None, 'Unidade responsável inválida.'
    u = Unidade.query.get(uid)
    if not u or u.status != 'ativa':
        return None, 'Unidade responsável inválida.'
    if not u.trata_tipo_chamado(tipo_chamado):
        lbl = TIPOS_CHAMADO_LABELS.get(tipo_chamado, tipo_chamado)
        return None, f'A unidade selecionada não trata chamados do tipo {lbl}.'
    return uid, None


def _unidade_contexto_chamado():
    """Unidade fixa da navbar (ou única vinculada) + lista para validação."""
    if getattr(g, 'chamado_externo', False):
        return _unidade_contexto_externo()

    ids_unidades = _unidades_do_usuario()
    if ids_unidades is not None:
        unidades = Unidade.query.filter(
            Unidade.id.in_(ids_unidades), Unidade.status == 'ativa'
        ).order_by(Unidade.nome).all()
    else:
        unidades = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()

    unidade_fixa = None
    if current_user.unidade_padrao_id and current_user.unidade_padrao:
        up = current_user.unidade_padrao
        if up.status == 'ativa':
            unidade_fixa = up
    if not unidade_fixa:
        ativas = current_user.unidades_ativas
        if len(ativas) == 1:
            unidade_fixa = ativas[0]
    if not unidade_fixa and ids_unidades is not None and len(unidades) == 1:
        unidade_fixa = unidades[0]

    bloqueada = unidade_fixa is not None
    return ([unidade_fixa] if bloqueada else unidades), unidade_fixa, bloqueada


def _unidade_contexto_sa():
    """SA: trava na unidade efetiva da navbar (mesma regra do dashboard)."""
    if getattr(g, 'chamado_externo', False):
        return _unidade_contexto_externo()

    ids_efetivos = current_user.ids_unidades_efetivos()
    unidade_fixa = None

    if ids_efetivos is not None and len(ids_efetivos) == 1:
        unidade_fixa = Unidade.query.filter_by(id=ids_efetivos[0], status='ativa').first()
    elif current_user.unidade_padrao_id and current_user.unidade_padrao:
        up = current_user.unidade_padrao
        if up.status == 'ativa':
            unidade_fixa = up

    if unidade_fixa:
        return [unidade_fixa], unidade_fixa, True

    ids_unidades = _unidades_do_usuario()
    if ids_unidades is not None:
        unidades = Unidade.query.filter(
            Unidade.id.in_(ids_unidades), Unidade.status == 'ativa'
        ).order_by(Unidade.nome).all()
    else:
        unidades = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    return unidades, None, False


@chamados_bp.route('/escolha-tipo')
@chamado_abertura_acesso
def escolha_tipo():
    return render_template('chamados/escolha_tipo.html', **tpl_ctx_abertura())


@chamados_bp.route('/novo/predial', methods=['GET', 'POST'])
@chamado_abertura_acesso
def novo_predial():
    ids_unidades = _unidades_do_usuario()
    if ids_unidades is not None:
        unidades = Unidade.query.filter(
            Unidade.id.in_(ids_unidades), Unidade.status == 'ativa'
        ).order_by(Unidade.nome).all()
    else:
        unidades = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()

    setores = SetorManutencao.query.order_by(SetorManutencao.nome).all()

    if request.method == 'POST':
        unidade_id  = _unidade_id_form(request.form.get('unidade_id', type=int))
        sala_id     = request.form.get('sala_id', type=int) or None
        descricao   = request.form.get('descricao', '').strip()
        local_livre = request.form.get('local_livre', '').strip()

        gut_vals, gut_erro = _validar_gut_form(request.form)
        if gut_erro:
            flash(gut_erro, 'danger')
            return render_template('chamados/form_predial.html',
                                   unidades=unidades, setores=setores,
                                   form_data=request.form, **tpl_ctx_abertura())

        # Determina prédio automaticamente
        predio_id = None
        unidade = Unidade.query.get(unidade_id)
        if unidade and unidade.predio_id:
            predio_id = unidade.predio_id

        # Monta título (usa "Sala/Setor" em vez do nome da sala, que pode ser alterado)
        sala = Sala.query.get(sala_id) if sala_id else None
        if sala:
            titulo = "Predial: Sala/Setor"
        elif local_livre:
            titulo = f"Predial: {local_livre}"
        else:
            titulo = "Chamado Predial"

        chamado = Chamado(
            numero=Chamado.gerar_numero('predial'),
            unidade_id=unidade_id,
            predio_id=predio_id,
            sala_id=sala_id,
            tipo_chamado='predial',
            titulo=titulo,
            descricao=descricao,
            prioridade='media',
            setor_id=request.form.get('setor_id', type=int) or None,
        )
        _aplicar_gut_chamado(chamado, *gut_vals)
        aplicar_solicitante_chamado(chamado)
        db.session.add(chamado)
        db.session.flush()

        # Fotos
        for f in request.files.getlist('fotos')[:10]:
            if f and f.filename:
                size_mb = len(f.read()) / (1024 * 1024)
                f.seek(0)
                if size_mb <= _MAX_MB:
                    foto = _salvar_foto(f)
                    foto.chamado_id = chamado.id
                    db.session.add(foto)

        db.session.add(ChamadoHistorico(
            chamado_id=chamado.id,
            usuario_id=historico_usuario_id(),
            acao=historico_acao('Chamado Predial aberto'),
            observacao=_historico_obs_abertura(chamado, descricao)
        ))
        db.session.flush()
        notificar_abertura(chamado)
        db.session.commit()
        return redirect_pos_abertura(chamado)

    return render_template('chamados/form_predial.html',
                           unidades=unidades, setores=setores,
                           form_data={}, **tpl_ctx_abertura())


@chamados_bp.route('/novo/bem-permanente', methods=['GET', 'POST'])
@chamado_abertura_acesso
def novo_bem_permanente():
    ids_unidades = _unidades_do_usuario()
    if ids_unidades is not None:
        unidades = Unidade.query.filter(
            Unidade.id.in_(ids_unidades), Unidade.status == 'ativa'
        ).order_by(Unidade.nome).all()
    else:
        unidades = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()

    setores = SetorManutencao.query.order_by(SetorManutencao.nome).all()

    # Pré-seleção via querystring vinda do detalhe do equipamento
    equip_id_pre = request.args.get('equipamento_id', type=int)

    if request.method == 'POST':
        unidade_id  = _unidade_id_form(request.form.get('unidade_id', type=int))
        equip_id    = request.form.get('equipamento_id', type=int) or None
        descricao   = request.form.get('descricao', '').strip()
        bp_rec_str  = request.form.get('bp_rechamado', 'nao')

        gut_vals, gut_erro = _validar_gut_form(request.form)
        if gut_erro:
            flash(gut_erro, 'danger')
            return render_template('chamados/form_bem_permanente.html',
                                   unidades=unidades, setores=setores,
                                   servicos=SERVICOS_BP, problema_em=PROBLEMA_EM,
                                   form_data=request.form,
                                   equip_id_pre=equip_id_pre, **tpl_ctx_abertura())

        equip = Equipamento.query.get(equip_id) if equip_id else None

        # Gera título a partir do equipamento cadastrado
        if equip:
            titulo = f"Manutenção: {equip.nome_display}"
            if equip.numero_patrimonio:
                titulo += f" [{equip.numero_patrimonio}]"
        else:
            titulo = "Chamado de Bem Permanente"

        # Verifica chamado em aberto JÁ para este equipamento específico
        if equip_id:
            chamado_aberto = Chamado.query.filter(
                Chamado.equipamento_id == equip_id,
                Chamado.status.in_(['aberto', 'em_andamento', 'aguardando_peca']),
            ).first()
            if chamado_aberto and not request.form.get('confirmar_duplicado'):
                flash(f'Atenção: o equipamento já possui o chamado '
                      f'<strong>{chamado_aberto.numero}</strong> em aberto '
                      f'({chamado_aberto.status_label}). Confirme para abrir mesmo assim.',
                      'warning')
                return render_template('chamados/form_bem_permanente.html',
                                       unidades=unidades, setores=setores,
                                       servicos=SERVICOS_BP, problema_em=PROBLEMA_EM,
                                       alerta_duplicado=True, form_data=request.form,
                                       equip_id_pre=equip_id)

                return render_template('chamados/form_bem_permanente.html',
                                       unidades=unidades, setores=setores,
                                       servicos=SERVICOS_BP, problema_em=PROBLEMA_EM,
                                       alerta_duplicado=True, form_data=request.form,
                                       equip_id_pre=equip_id, **tpl_ctx_abertura())

        chamado = Chamado(
            numero=Chamado.gerar_numero('equipamento'),
            unidade_id=unidade_id,
            equipamento_id=equip_id,
            tipo_chamado='equipamento',
            titulo=titulo,
            descricao=descricao,
            prioridade='media',
            setor_id=request.form.get('setor_id', type=int) or None,
            bp_servico    = request.form.get('bp_servico') or None,
            bp_problema_em= request.form.get('bp_problema_em') or None,
            bp_rechamado  = (bp_rec_str == 'sim'),
        )
        _aplicar_gut_chamado(chamado, *gut_vals)
        aplicar_solicitante_chamado(chamado)

        if bp_rec_str == 'sim':
            dr = request.form.get('bp_data_rechamado', '').strip()
            if dr:
                try:
                    chamado.bp_data_rechamado = date.fromisoformat(dr)
                except ValueError:
                    pass

        db.session.add(chamado)
        db.session.flush()

        # Fotos
        for f in request.files.getlist('fotos')[:10]:
            if f and f.filename:
                size_mb = len(f.read()) / (1024 * 1024)
                f.seek(0)
                if size_mb <= _MAX_MB:
                    foto = _salvar_foto(f)
                    foto.chamado_id = chamado.id
                    db.session.add(foto)

        db.session.add(ChamadoHistorico(
            chamado_id=chamado.id,
            usuario_id=historico_usuario_id(),
            acao=historico_acao('Chamado de Bem Permanente aberto'),
            observacao=_historico_obs_abertura(chamado, descricao)
        ))
        db.session.flush()
        notificar_abertura(chamado)
        db.session.commit()
        return redirect_pos_abertura(chamado)

    return render_template('chamados/form_bem_permanente.html',
                           unidades=unidades, setores=setores,
                           servicos=SERVICOS_BP, problema_em=PROBLEMA_EM,
                           alerta_duplicado=False, form_data={},
                           equip_id_pre=equip_id_pre, **tpl_ctx_abertura())


@chamados_bp.route('/novo/solicitacao-equipamento', methods=['GET', 'POST'])
@chamado_abertura_acesso
def novo_solicitacao_equipamento():
    ids_unidades = _unidades_do_usuario()
    if ids_unidades is not None:
        unidades = Unidade.query.filter(
            Unidade.id.in_(ids_unidades), Unidade.status == 'ativa'
        ).order_by(Unidade.nome).all()
    else:
        unidades = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()

    # Unidade pré-selecionada para gestor local (unidade do navbar ou única unidade)
    unidade_presetada = None
    if getattr(g, 'chamado_externo', False):
        _, unidade_presetada, _ = _unidade_contexto_externo()
    elif ids_unidades is not None and unidades:
        if current_user.unidade_padrao_id and current_user.unidade_padrao:
            up = current_user.unidade_padrao
            if up.id in [u.id for u in unidades] and up.status == 'ativa':
                unidade_presetada = up
        if not unidade_presetada and len(unidades) == 1:
            unidade_presetada = unidades[0]

    # Tipos de equipamento ativos (todos, para solicitação)
    tipos_equipamento = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()

    if request.method == 'POST':
        unidade_id = _unidade_id_form(request.form.get('unidade_id', type=int))
        tipo_equip_id = request.form.get('tipo_equipamento_id', type=int)
        tipo_livre = request.form.get('se_tipo_livre', '').strip()
        descricao = request.form.get('descricao', '').strip() or 'Solicitação de equipamento'

        gut_vals, gut_erro = _validar_gut_form(request.form)
        if gut_erro:
            flash(gut_erro, 'danger')
            return render_template('chamados/form_solicitacao_equipamento.html',
                                   unidades=unidades, tipos_equipamento=tipos_equipamento,
                                   unidade_presetada=unidade_presetada, motivos=MOTIVOS_SOLICITACAO,
                                   form_data=request.form, **tpl_ctx_abertura())

        if not unidade_id or unidade_id not in [u.id for u in unidades]:
            flash('Selecione uma unidade válida.', 'danger')
            return render_template('chamados/form_solicitacao_equipamento.html',
                                   unidades=unidades, tipos_equipamento=tipos_equipamento,
                                   unidade_presetada=unidade_presetada, motivos=MOTIVOS_SOLICITACAO,
                                   form_data=request.form)

        tipo_eq = TipoEquipamento.query.get(tipo_equip_id) if tipo_equip_id else None
        is_tipo_nao_listado = not tipo_eq and tipo_livre
        if not tipo_eq and not tipo_livre:
            flash('Selecione um tipo de equipamento ou informe o item em "Tipo não listado".', 'danger')
            return render_template('chamados/form_solicitacao_equipamento.html',
                                   unidades=unidades, tipos_equipamento=tipos_equipamento,
                                   unidade_presetada=unidade_presetada, motivos=MOTIVOS_SOLICITACAO,
                                   form_data=request.form)

        titulo = f"Solicitação: {tipo_livre}" if is_tipo_nao_listado else f"Solicitação: {tipo_eq.nome}"

        chamado = Chamado(
            numero=Chamado.gerar_numero('solicitacao_equipamento'),
            unidade_id=unidade_id,
            tipo_chamado='solicitacao_equipamento',
            se_tipo_equipamento_id=tipo_equip_id or None,
            se_tipo_livre=tipo_livre or None,
            titulo=titulo,
            descricao=descricao,
            prioridade='media',
        )
        _aplicar_gut_chamado(chamado, *gut_vals)
        aplicar_solicitante_chamado(chamado)

        db.session.add(chamado)
        db.session.flush()

        # Itens: itens_sala_id_N, itens_motivo_N, itens_equipamento_id_N, itens_observacao_N
        num_itens = request.form.get('num_itens', type=int) or 0
        itens_criados = 0
        for n in range(min(num_itens, 100)):
            sala_id = request.form.get(f'itens_sala_id_{n}', type=int)
            motivo = request.form.get(f'itens_motivo_{n}', 'ampliacao')
            equip_id = request.form.get(f'itens_equipamento_id_{n}', type=int)
            obs = (request.form.get(f'itens_observacao_{n}', '') or '').strip()

            if not sala_id:
                continue

            item = ChamadoSolicitacaoItem(
                chamado_id=chamado.id,
                sala_id=sala_id,
                motivo=motivo if motivo in ('ampliacao', 'substituicao') else 'ampliacao',
                equipamento_id=equip_id or None,
                observacao=obs or None,
            )
            db.session.add(item)
            itens_criados += 1

        if itens_criados == 0:
            db.session.rollback()
            flash('Adicione pelo menos um item com sala selecionada.', 'danger')
            return render_template('chamados/form_solicitacao_equipamento.html',
                                   unidades=unidades, tipos_equipamento=tipos_equipamento,
                                   unidade_presetada=unidade_presetada, motivos=MOTIVOS_SOLICITACAO,
                                   form_data=request.form)

        db.session.add(ChamadoHistorico(
            chamado_id=chamado.id,
            usuario_id=historico_usuario_id(),
            acao=historico_acao('Chamado de Solicitação de Equipamento aberto'),
            observacao=_historico_obs_abertura(chamado, descricao)
        ))
        db.session.flush()
        notificar_abertura(chamado)
        db.session.commit()
        return redirect_pos_abertura(chamado)

    return render_template('chamados/form_solicitacao_equipamento.html',
                           unidades=unidades,
                           tipos_equipamento=tipos_equipamento,
                           unidade_presetada=unidade_presetada,
                           motivos=MOTIVOS_SOLICITACAO,
                           **tpl_ctx_abertura())


@chamados_bp.route('/novo/solicitacao-administrativa', methods=['GET', 'POST'])
@chamado_abertura_acesso
def novo_solicitacao_administrativa():
    unidades, unidade_presetada, unidade_bloqueada = _unidade_contexto_sa()
    unidades_destino = Unidade.que_tratam_tipo('solicitacao_administrativa')

    ctx = tpl_ctx_abertura(
        unidades=unidades,
        unidade_presetada=unidade_presetada,
        unidade_bloqueada=unidade_bloqueada,
        unidades_destino=unidades_destino,
        form_data={},
    )

    if request.method == 'POST':
        unidade_id = unidade_presetada.id if unidade_bloqueada else _unidade_id_form(request.form.get('unidade_id', type=int))
        destino_id = request.form.get('unidade_responsavel_id', type=int)
        ids_destino = {u.id for u in unidades_destino}
        gravidade = request.form.get('gravidade', type=int)
        urgencia = request.form.get('urgencia', type=int)
        tendencia = request.form.get('tendencia', type=int)
        titulo = request.form.get('titulo', '').strip()
        descricao = request.form.get('descricao', '').strip()

        ctx['form_data'] = request.form

        if not unidade_id or unidade_id not in [u.id for u in unidades]:
            flash('Selecione uma unidade válida.', 'danger')
            return render_template('chamados/form_solicitacao_administrativa.html', **ctx)

        if not destino_id or destino_id not in ids_destino:
            flash('Selecione para qual unidade/setor direcionar a solicitação.', 'danger')
            return render_template('chamados/form_solicitacao_administrativa.html', **ctx)

        if not all(v and 1 <= v <= 5 for v in (gravidade, urgencia, tendencia)):
            flash('Preencha Gravidade, Urgência e Tendência (matriz GUT).', 'danger')
            return render_template('chamados/form_solicitacao_administrativa.html', **ctx)

        if not descricao:
            flash('Descreva a solicitação.', 'danger')
            return render_template('chamados/form_solicitacao_administrativa.html', **ctx)

        if not titulo:
            titulo = descricao[:120] + ('…' if len(descricao) > 120 else '')

        prioridade = prioridade_de_gut(gravidade, urgencia, tendencia)

        chamado = Chamado(
            numero=Chamado.gerar_numero('solicitacao_administrativa'),
            unidade_id=unidade_id,
            unidade_responsavel_id=destino_id,
            tipo_chamado='solicitacao_administrativa',
            titulo=titulo,
            descricao=descricao,
            prioridade=prioridade,
            sa_gravidade=gravidade,
            sa_urgencia=urgencia,
            sa_tendencia=tendencia,
        )
        aplicar_solicitante_chamado(chamado)
        db.session.add(chamado)
        db.session.flush()

        for f in request.files.getlist('fotos')[:10]:
            if f and f.filename:
                size_mb = len(f.read()) / (1024 * 1024)
                f.seek(0)
                if size_mb <= _MAX_MB:
                    foto = _salvar_foto(f)
                    foto.chamado_id = chamado.id
                    db.session.add(foto)

        db.session.add(ChamadoHistorico(
            chamado_id=chamado.id,
            usuario_id=historico_usuario_id(),
            acao=historico_acao('Chamado de Solicitação Administrativa aberto'),
            observacao=_historico_obs_abertura(chamado, descricao),
        ))
        db.session.flush()
        notificar_abertura(chamado)
        db.session.commit()
        return redirect_pos_abertura(chamado)

    return render_template('chamados/form_solicitacao_administrativa.html', **ctx)


# ── APIs JSON para o formulário de Bem Permanente ─────────────────────────────

@chamados_bp.route('/api/unidade-info/<int:unidade_id>')
@chamado_abertura_acesso
def api_unidade_info(unidade_id):
    """Retorna dados da unidade: endereço, telefone, ramal, maps."""
    if getattr(g, 'chamado_externo', False) and unidade_id != session.get('externo_unidade_id'):
        abort(403)
    u = Unidade.query.get_or_404(unidade_id)
    partes = [p for p in [u.endereco, u.numero, u.complemento, u.bairro, u.cidade] if p]
    return jsonify({
        'endereco':  ', '.join(partes),
        'telefone':  u.telefone or '',
        'ramal':     u.ramal or '',
        'email':     u.email or '',
        'link_maps': u.link_maps or '',
    })


def _api_unidade_permitida(unidade_id):
    if getattr(g, 'chamado_externo', False):
        if unidade_id != session.get('externo_unidade_id'):
            abort(403)
        return
    if current_user.is_authenticated:
        ids = _unidades_do_usuario()
        if ids is not None and unidade_id not in ids:
            abort(403)


@chamados_bp.route('/api/tipos-equipamento-da-unidade/<int:unidade_id>')
@chamado_abertura_acesso
def api_tipos_equipamento_da_unidade(unidade_id):
    """Lista os Tipos de Equipamento que existem na unidade (com pelo menos 1 equip ativo)."""
    _api_unidade_permitida(unidade_id)
    from app.models.equipamento import TipoEquipamento
    from app.models.sala import Sala

    tipos = (
        db.session.query(TipoEquipamento)
        .join(Equipamento, Equipamento.tipo_equipamento_id == TipoEquipamento.id)
        .join(Sala, Equipamento.sala_id == Sala.id)
        .filter(
            Sala.unidade_id == unidade_id,
            Equipamento.ativo == True,
            TipoEquipamento.ativo == True,
        )
        .distinct()
        .order_by(TipoEquipamento.nome)
        .all()
    )
    return jsonify([{'id': t.id, 'nome': t.nome, 'icone': t.icone or 'fas fa-box'} for t in tipos])


@chamados_bp.route('/api/equipamentos-da-unidade/<int:unidade_id>')
@chamado_abertura_acesso
def api_equipamentos_da_unidade(unidade_id):
    """Lista equipamentos ativos de uma unidade, opcionalmente filtrados por tipo."""
    _api_unidade_permitida(unidade_id)
    from app.models.sala import Sala

    tipo_id = request.args.get('tipo_id', type=int)

    q = (
        db.session.query(Equipamento)
        .join(Sala, Equipamento.sala_id == Sala.id)
        .filter(
            Sala.unidade_id == unidade_id,
            Equipamento.ativo == True,
        )
    )
    if tipo_id:
        q = q.filter(Equipamento.tipo_equipamento_id == tipo_id)

    equipamentos = q.order_by(Equipamento.numero_patrimonio).all()

    result = []
    for e in equipamentos:
        # verifica chamado em aberto para este equipamento
        chamado_aberto = Chamado.query.filter(
            Chamado.equipamento_id == e.id,
            Chamado.status.in_(['aberto', 'em_andamento', 'aguardando_peca']),
        ).first()

        result.append({
            'id':          e.id,
            'nome':        e.nome_display,
            'patrimonio':  e.numero_patrimonio or '',
            'serie':       e.numero_serie or '',
            'sala':        e.sala.nome if e.sala else '',
            'tem_chamado': chamado_aberto.numero if chamado_aberto else None,
        })
    return jsonify(result)


@chamados_bp.route('/api/equipamento-detalhe/<int:equip_id>')
@chamado_abertura_acesso
def api_equipamento_detalhe(equip_id):
    """Retorna detalhes completos de um equipamento para auto-fill."""
    e = Equipamento.query.get_or_404(equip_id)
    if e.sala:
        _api_unidade_permitida(e.sala.unidade_id)
    marca  = e.marca.nome  if e.marca  else ''
    modelo = e.modelo.nome if e.modelo else ''
    tipo   = e.tipo_equipamento.nome if e.tipo_equipamento else ''
    sala   = e.sala.nome if e.sala else ''

    chamados_equip = (
        Chamado.query
        .filter_by(equipamento_id=e.id)
        .order_by(Chamado.criado_em.desc())
        .limit(5)
        .all()
    )
    historico = [{
        'numero':    c.numero,
        'status':    c.status_label,
        'badge':     c.status_badge,
        'criado_em': c.criado_em.strftime('%d/%m/%Y'),
        'descricao': (c.descricao or '')[:120],
    } for c in chamados_equip]

    return jsonify({
        'id':          e.id,
        'nome':        e.nome_display,
        'tipo':        tipo,
        'marca':       marca,
        'modelo':      modelo,
        'patrimonio':  e.numero_patrimonio or '',
        'serie':       e.numero_serie or '',
        'sala':        sala,
        'condicao':    e.condicao_label,
        'status':      e.status_label,
        'historico':   historico,
    })


@chamados_bp.route('/')
@login_required
def listar():
    from app.models.tipo_unidade import TipoUnidade
    from app.models.status_chamado import StatusChamado

    def _gl(p):
        return [int(v) for v in request.args.getlist(p) if v.isdigit()]
    def _gsl(p):
        return [v for v in request.args.getlist(p) if v]

    filtro_unidades        = _gl('unidade')
    filtro_tipo_unidades   = _gl('tipo_unidade')
    filtro_tipo_list       = _gsl('tipo')
    filtro_prioridade_list = _gsl('prioridade')

    # Status: se não vier nenhum na querystring, usa os marcados como padrão
    # (exceto se o usuário clicou explicitamente em "Ver todos" via ?ver_todos=1)
    filtro_status_list = _gsl('status')
    ver_todos = request.args.get('ver_todos') == '1'
    status_db = StatusChamado.ativos()
    slugs_padrao = [s.slug for s in status_db if s.padrao_listagem]
    filtro_aplicado_automatico = False
    if not filtro_status_list and slugs_padrao and not ver_todos:
        filtro_status_list = slugs_padrao
        filtro_aplicado_automatico = True

    query = Chamado.query
    if current_user.pode('ver_chamados_todos'):
        pass
    else:
        ids_unidades = [uu.unidade_id for uu in current_user.unidades.filter_by(ativo=True).all()]
        tipos_unidade_ids = current_user.tipos_unidade_ids_divisoes
        tipos_chamado_div = current_user.tipos_chamado_divisoes
        conds = []
        if ids_unidades:
            conds.append(Chamado.unidade_id.in_(ids_unidades))
        if tipos_unidade_ids:
            conds.append(Chamado.unidade.has(Unidade.tipo_unidade_id.in_(tipos_unidade_ids)))
        if tipos_chamado_div:
            conds.append(Chamado.tipo_chamado.in_(tipos_chamado_div))
        if conds:
            query = query.filter(db.or_(*conds))
        else:
            query = query.filter(Chamado.id < 0)

    if filtro_unidades:
        query = query.filter(Chamado.unidade_id.in_(filtro_unidades))
    if filtro_tipo_unidades:
        query = query.join(Unidade, Chamado.unidade_id == Unidade.id).filter(
            Unidade.tipo_unidade_id.in_(filtro_tipo_unidades)
        )
    if filtro_status_list:
        query = query.filter(Chamado.status.in_(filtro_status_list))
    if filtro_tipo_list:
        query = query.filter(Chamado.tipo_chamado.in_(filtro_tipo_list))
    if filtro_prioridade_list:
        query = query.filter(Chamado.prioridade.in_(filtro_prioridade_list))

    chamados      = query.order_by(Chamado.criado_em.desc()).all()
    unidades      = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()

    # Monta dict {slug: label} para o template — inclui todos os status ativos
    status_opts_db = {s.slug: s.label for s in status_db}

    return render_template('chamados/listar.html',
                           chamados=chamados,
                           unidades=unidades,
                           tipos_unidade=tipos_unidade,
                           tipos=TIPOS_CHAMADO_LABELS,
                           prioridades=PRIORIDADES_LABELS,
                           status_opts=status_opts_db,
                           status_db=status_db,
                           filtro_unidades=filtro_unidades,
                           filtro_tipo_unidades=filtro_tipo_unidades,
                           filtro_status_list=filtro_status_list,
                           filtro_tipo_list=filtro_tipo_list,
                           filtro_prioridade_list=filtro_prioridade_list,
                           filtro_aplicado_automatico=filtro_aplicado_automatico,
                           slugs_padrao=slugs_padrao)


@chamados_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if not current_user.pode('abrir_chamado'):
        abort(403)

    ids_unidades = _unidades_do_usuario()
    if ids_unidades is not None:
        unidades = Unidade.query.filter(
            Unidade.id.in_(ids_unidades), Unidade.status == 'ativa'
        ).order_by(Unidade.nome).all()
    else:
        unidades = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()

    setores = SetorManutencao.query.order_by(SetorManutencao.nome).all()

    # Pré-seleção via querystring (?predio_id=X&tipo=predial ou ?equipamento_id=Y)
    predio_id_pre = request.args.get('predio_id', type=int)
    tipo_pre      = request.args.get('tipo', '')
    equip_id_pre  = request.args.get('equipamento_id', type=int)

    predio_pre = Predio.query.get(predio_id_pre) if predio_id_pre else None
    predios    = Predio.query.filter_by(ativo=True).order_by(Predio.nome).all()

    if request.method == 'POST':
        unidade_id  = request.form.get('unidade_id', type=int)
        titulo      = request.form.get('titulo', '').strip()
        descricao   = request.form.get('descricao', '').strip()
        tipo_chamado = request.form.get('tipo_chamado', 'equipamento')

        gut_vals, gut_erro = _validar_gut_form(request.form)
        if gut_erro:
            flash(gut_erro, 'danger')
            tipos_form = [t for t in TIPOS_CHAMADO if t not in _TIPOS_FORM_EXCLUIDOS]
            return render_template('chamados/form.html',
                                   chamado=None, unidades=unidades, setores=setores,
                                   predios=predios, predio_pre=predio_pre,
                                   tipos=tipos_form, prioridades=PRIORIDADES,
                                   form_data=request.form)

        # Para chamados prediais: detecta o prédio da unidade automaticamente
        predio_id = None
        if tipo_chamado == 'predial':
            unidade = Unidade.query.get(unidade_id)
            if unidade and unidade.predio_id:
                predio_id = unidade.predio_id
            # Permite sobrescrever via form se vier explícito
            predio_id = request.form.get('predio_id', type=int) or predio_id

        chamados_similares = Chamado.query.filter(
            Chamado.unidade_id == unidade_id,
            Chamado.status.in_(['aberto', 'em_andamento']),
            Chamado.tipo_chamado == tipo_chamado,
        ).count()

        if chamados_similares > 0 and not request.form.get('confirmar_duplicado'):
            flash(f'Atenção: já existem {chamados_similares} chamado(s) similar(es) aberto(s) nesta unidade para este tipo. Confirme se deseja abrir mesmo assim.', 'warning')
            tipos_form = [t for t in TIPOS_CHAMADO if t not in _TIPOS_FORM_EXCLUIDOS]
            return render_template('chamados/form.html',
                                   chamado=None, unidades=unidades, setores=setores,
                                   predios=predios, predio_pre=predio_pre,
                                   tipos=tipos_form, prioridades=PRIORIDADES,
                                   alerta_duplicado=True,
                                   form_data=request.form)

        chamado = Chamado(
            numero=Chamado.gerar_numero(tipo_chamado),
            unidade_id=unidade_id,
            predio_id=predio_id,
            sala_id=request.form.get('sala_id', type=int) or None,
            equipamento_id=request.form.get('equipamento_id', type=int) or None,
            tipo_chamado=tipo_chamado,
            titulo=titulo,
            descricao=descricao,
            prioridade='media',
            setor_id=request.form.get('setor_id', type=int) or None,
            aberto_por=current_user.id,
        )
        _aplicar_gut_chamado(chamado, *gut_vals)
        db.session.add(chamado)
        db.session.flush()

        db.session.add(ChamadoHistorico(
            chamado_id=chamado.id,
            usuario_id=current_user.id,
            acao='Chamado aberto',
            observacao=_historico_obs_abertura(chamado, descricao)
        ))
        db.session.commit()
        flash(f'Chamado {chamado.numero} aberto com sucesso!', 'success')
        return redirect(url_for('chamados.detalhe', id=chamado.id))

    # Exclui tipos com fluxo próprio (SE, SA)
    tipos_form = [t for t in TIPOS_CHAMADO if t not in _TIPOS_FORM_EXCLUIDOS]
    return render_template('chamados/form.html',
                           chamado=None, unidades=unidades, setores=setores,
                           predios=predios, predio_pre=predio_pre,
                           tipos=tipos_form, prioridades=PRIORIDADES,
                           tipo_pre=tipo_pre, equip_id_pre=equip_id_pre,
                           alerta_duplicado=False, form_data={})


@chamados_bp.route('/<int:id>')
@login_required
def detalhe(id):
    chamado = Chamado.query.get_or_404(id)
    _verificar_acesso_chamado(chamado)
    historico = chamado.historico.order_by(ChamadoHistorico.criado_em).all()
    setores = SetorManutencao.query.order_by(SetorManutencao.nome).all()
    unidades_responsaveis = _unidades_responsaveis_tipo(
        chamado.tipo_chamado, chamado.unidade_responsavel_id
    )

    # Outros chamados do mesmo equipamento ou da mesma sala
    outros_chamados = []
    if chamado.equipamento_id:
        outros_chamados = (
            Chamado.query
            .filter(
                Chamado.equipamento_id == chamado.equipamento_id,
                Chamado.id != chamado.id,
            )
            .order_by(Chamado.criado_em.desc())
            .limit(10)
            .all()
        )
    elif chamado.sala_id:
        outros_chamados = (
            Chamado.query
            .filter(
                Chamado.sala_id == chamado.sala_id,
                Chamado.id != chamado.id,
            )
            .order_by(Chamado.criado_em.desc())
            .limit(10)
            .all()
        )

    # Contratos disponíveis para vincular ao andamento
    # — equipamento: contratos que cobrem tipo/marca/modelo do equipamento
    # — predial: todos os contratos ativos
    if chamado.equipamento_id and chamado.equipamento and chamado.equipamento.tipo_equipamento_id:
        from sqlalchemy import or_
        eq = chamado.equipamento
        q = (
            Contrato.query
            .join(ContratoTipoEquipamento, Contrato.id == ContratoTipoEquipamento.contrato_id)
            .filter(
                ContratoTipoEquipamento.tipo_equipamento_id == eq.tipo_equipamento_id,
                or_(ContratoTipoEquipamento.marca_id.is_(None),
                    ContratoTipoEquipamento.marca_id == eq.marca_id),
                or_(ContratoTipoEquipamento.modelo_id.is_(None),
                    ContratoTipoEquipamento.modelo_id == eq.modelo_id),
                Contrato.status.in_(['vigente', 'a_vencer']),
            )
            .order_by(Contrato.data_fim)
            .distinct()
        )
        contratos_equip = q.all()
    else:
        contratos_equip = (
            Contrato.query
            .filter(Contrato.status.in_(['vigente', 'a_vencer']))
            .order_by(Contrato.data_fim)
            .all()
        )

    # Andamentos com pendência aberta (pedido_info ou alerta sem resposta)
    pendencias = [
        h for h in historico
        if h.requer_resposta and h.respondido_em is None
    ]

    # Status do banco para o modal de andamento / alterar status
    from app.models.status_chamado import StatusChamado
    status_db = StatusChamado.ativos()
    status_opts_db  = [s.slug for s in status_db]
    status_labels_db = {s.slug: s.label for s in status_db}

    return render_template('chamados/detalhe.html',
                           chamado=chamado, historico=historico,
                           setores=setores, unidades_responsaveis=unidades_responsaveis,
                           status_opts=status_opts_db,
                           status_labels=status_labels_db,
                           outros_chamados=outros_chamados,
                           contratos_equip=contratos_equip,
                           pendencias=pendencias,
                           tipos_andamento=TIPOS_ANDAMENTO,
                           pode_revisar_gut=current_user.pode_ver_gestao_chamados)


@chamados_bp.route('/<int:id>/revisar-prioridade', methods=['POST'])
@login_required
def revisar_prioridade(id):
    """Revisão opcional da prioridade GUT pelo setor executante."""
    if not current_user.pode_ver_gestao_chamados:
        abort(403)
    chamado = Chamado.query.get_or_404(id)
    _verificar_acesso_chamado(chamado)

    if chamado.status in ['concluido', 'cancelado']:
        flash('Não é possível revisar prioridade de um chamado encerrado.', 'warning')
        return redirect(url_for('chamados.detalhe', id=id))

    gut_vals, gut_erro = _validar_gut_form(request.form)
    if gut_erro:
        flash(gut_erro, 'danger')
        return redirect(url_for('chamados.detalhe', id=id))

    g, u, t = gut_vals
    prio_anterior = chamado.prioridade_label
    sol = (chamado.sa_gravidade, chamado.sa_urgencia, chamado.sa_tendencia)

    if sol == gut_vals:
        chamado.gut_exec_gravidade = None
        chamado.gut_exec_urgencia = None
        chamado.gut_exec_tendencia = None
        _sincronizar_prioridade_chamado(chamado)
        acao = 'Prioridade mantida conforme informada pelo solicitante'
        obs = chamado.gut_solicitante_resumo
    else:
        chamado.gut_exec_gravidade = g
        chamado.gut_exec_urgencia = u
        chamado.gut_exec_tendencia = t
        _sincronizar_prioridade_chamado(chamado)
        acao = f'Prioridade revisada pelo setor: {prio_anterior} → {chamado.prioridade_label}'
        obs = (
            f'Solicitante: {chamado.gut_solicitante_resumo or "—"}\n'
            f'Setor: {chamado.gut_executante_resumo}'
        )

    db.session.add(ChamadoHistorico(
        chamado_id=chamado.id,
        usuario_id=current_user.id,
        acao=acao,
        observacao=obs,
    ))
    db.session.commit()
    flash('Prioridade atualizada.', 'success')
    return redirect(url_for('chamados.detalhe', id=id))


@chamados_bp.route('/<int:id>/atualizar', methods=['POST'])
@login_required
def atualizar_status(id):
    chamado = Chamado.query.get_or_404(id)
    _verificar_acesso_chamado(chamado)

    novo_status = request.form.get('status')
    observacao = request.form.get('observacao', '').strip()
    unidade_resp = request.form.get('unidade_responsavel_id', '0')

    uid, erro_unidade = _validar_unidade_responsavel_id(chamado.tipo_chamado, unidade_resp)
    if erro_unidade:
        flash(erro_unidade, 'danger')
        return redirect(url_for('chamados.detalhe', id=id))

    if novo_status == 'cancelado' and not current_user.pode('cancelar_chamado'):
        abort(403)
    if novo_status == 'concluido' and not current_user.pode('fechar_chamado'):
        abort(403)

    from app.models.status_chamado import StatusChamado
    status_obj = StatusChamado.query.filter_by(slug=novo_status).first()
    encerra = status_obj.encerra_chamado if status_obj else novo_status in ['concluido', 'cancelado']

    status_anterior = chamado.status
    chamado.status = novo_status
    chamado.unidade_responsavel_id = uid
    if encerra:
        chamado.fechado_em = datetime.utcnow()
        chamado.observacao_conclusao = observacao

    db.session.add(ChamadoHistorico(
        chamado_id=chamado.id,
        usuario_id=current_user.id,
        acao=f'Status alterado: {status_anterior} → {novo_status}',
        observacao=observacao
    ))
    db.session.commit()
    flash('Chamado atualizado!', 'success')
    return redirect(url_for('chamados.detalhe', id=id))


@chamados_bp.route('/<int:id>/andamento', methods=['POST'])
@login_required
def adicionar_andamento(id):
    chamado = Chamado.query.get_or_404(id)
    _verificar_acesso_chamado(chamado)

    from app.models.status_chamado import StatusChamado as _SC
    status_atual_obj = _SC.query.filter_by(slug=chamado.status).first()
    if status_atual_obj and status_atual_obj.encerra_chamado:
        flash('Não é possível adicionar andamentos a um chamado encerrado.', 'warning')
        return redirect(url_for('chamados.detalhe', id=id))
    elif not status_atual_obj and chamado.status in ['concluido', 'cancelado']:
        flash('Não é possível adicionar andamentos a um chamado encerrado.', 'warning')
        return redirect(url_for('chamados.detalhe', id=id))

    acao            = request.form.get('acao', '').strip()
    observacao      = request.form.get('observacao', '').strip()
    novo_status     = request.form.get('novo_status', '').strip() or None
    setor_id        = request.form.get('setor_id', type=int) or None
    tipo_andamento  = request.form.get('tipo_andamento', 'andamento').strip()
    requer_resposta = request.form.get('requer_resposta') == '1'
    contrato_id     = request.form.get('contrato_id', type=int) or None

    if not acao:
        flash('Informe a descrição da ação.', 'warning')
        return redirect(url_for('chamados.detalhe', id=id))

    if novo_status == 'cancelado' and not current_user.pode('cancelar_chamado'):
        abort(403)
    if novo_status == 'concluido' and not current_user.pode('fechar_chamado'):
        abort(403)

    # Nota de encerramento força tipo e status concluído
    if tipo_andamento == 'nota_encerramento':
        novo_status = 'concluido'
        if not current_user.pode('fechar_chamado'):
            abort(403)

    if novo_status:
        status_anterior  = chamado.status
        chamado.status   = novo_status
        novo_status_obj  = _SC.query.filter_by(slug=novo_status).first()
        encerra          = novo_status_obj.encerra_chamado if novo_status_obj else novo_status in ['concluido', 'cancelado']
        acao_hist = f'{acao} | Status: {status_anterior} → {novo_status}'
        if encerra:
            chamado.fechado_em           = datetime.utcnow()
            chamado.observacao_conclusao = observacao
    else:
        encerra   = False
        acao_hist = acao

    if setor_id:
        chamado.setor_id = setor_id

    # Pedido de informação e alerta sempre ficam como "requer_resposta"
    if tipo_andamento in ('pedido_info', 'alerta'):
        requer_resposta = True

    historico = ChamadoHistorico(
        chamado_id=chamado.id,
        usuario_id=current_user.id,
        acao=acao_hist,
        observacao=observacao if not encerra else None,
        tipo_andamento=tipo_andamento,
        requer_resposta=requer_resposta,
        contrato_id=contrato_id,
    )
    db.session.add(historico)
    db.session.flush()   # garante historico.id antes de salvar anexos

    # Processar anexos (qualquer tipo de arquivo, até 10, 50 MB cada)
    for f in request.files.getlist('anexos')[:10]:
        if f and f.filename:
            anexo = _salvar_anexo(f)
            if anexo.tamanho_bytes and anexo.tamanho_bytes / (1024 * 1024) <= _MAX_MB:
                anexo.andamento_id = historico.id
                db.session.add(anexo)
            else:
                import os as _os
                try:
                    _os.remove(os.path.join(_UPLOAD_DIR_AND, anexo.filename))
                except OSError:
                    pass

    from app.notificar import notificar_andamento, notificar_status_alterado
    notificar_andamento(chamado, historico, current_user.id)
    if novo_status:
        notificar_status_alterado(chamado, None, current_user.id)
    db.session.commit()
    flash('Andamento registrado com sucesso!', 'success')
    return redirect(url_for('chamados.detalhe', id=id))


@chamados_bp.route('/<int:id>/andamento/<int:and_id>/responder', methods=['POST'])
@login_required
def responder_andamento(id, and_id):
    """Marca um andamento de 'pedido_info' ou 'alerta' como respondido."""
    chamado = Chamado.query.get_or_404(id)
    _verificar_acesso_chamado(chamado)
    historico = ChamadoHistorico.query.get_or_404(and_id)
    if historico.chamado_id != chamado.id:
        abort(404)
    historico.respondido_em = datetime.utcnow()
    db.session.commit()
    flash('Pendência marcada como resolvida.', 'success')
    return redirect(url_for('chamados.detalhe', id=id))


@chamados_bp.route('/<int:id>/imprimir')
@login_required
def imprimir(id):
    chamado  = Chamado.query.get_or_404(id)
    _verificar_acesso_chamado(chamado)
    historico = chamado.historico.order_by(ChamadoHistorico.criado_em).all()
    now = datetime.utcnow()
    # URL curta para o QR code (evita URLs longas do Google Maps no QR)
    qr_url = None
    if chamado.unidade and chamado.unidade.link_maps:
        qr_url = url_for('unidades.maps_redirect', id=chamado.unidade.id, _external=True)
    return render_template('chamados/imprimir.html',
                           chamado=chamado, historico=historico,
                           now=now, qr_url=qr_url)


def _filtro_fila_unidade(unidade):
    """Chamados demandados para a unidade, nos tipos que ela trata."""
    return db.and_(
        Chamado.unidade_responsavel_id == unidade.id,
        Chamado.tipo_chamado.in_(unidade.tipos_chamado_recebe or []),
    )


def _chamado_na_fila_unidade(chamado, unidade):
    if not unidade or not unidade.trata_chamados:
        return False
    return (
        chamado.unidade_responsavel_id == unidade.id
        and chamado.tipo_chamado in (unidade.tipos_chamado_recebe or [])
    )


@chamados_bp.route('/gestao')
@login_required
def gestao():
    """Painel de gestão — fila da unidade logada (chamados demandados para ela)."""
    if not current_user.pode_ver_gestao_chamados:
        abort(403)

    unidade_op = current_user.unidade_logada
    if not unidade_op or not unidade_op.trata_chamados:
        abort(403)

    filtro_gestao = _filtro_fila_unidade(unidade_op)

    setores_disponiveis = SetorManutencao.query.order_by(SetorManutencao.nome).all()
    unidades_ativas = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    from app.models.status_chamado import StatusChamado
    status_db = StatusChamado.ativos()
    status_opts_db = {s.slug: s.label for s in status_db}
    status_badge_db = {s.slug: s.badge_cor for s in status_db}
    _hex = {'danger':'#dc3545','warning':'#ffc107','info':'#17a2b8','success':'#198754','secondary':'#6c757d','primary':'#0d6efd','dark':'#212529'}
    status_cores_db = {s.slug: _hex.get(s.badge_cor, '#6c757d') for s in status_db}
    setor_filtro  = request.args.get('setor', type=int)
    status_filtro = request.args.getlist('status')
    tipo_filtro   = request.args.getlist('tipo')
    prio_filtro   = request.args.getlist('prioridade')
    unidade_abriu_filtro = request.args.get('unidade_abriu', type=int)
    ver_todos = request.args.get('ver_todos') == '1'
    slugs_padrao = [s.slug for s in status_db if s.padrao_listagem]
    filtro_aplicado_automatico = False
    if not status_filtro and slugs_padrao and not ver_todos:
        status_filtro = slugs_padrao
        filtro_aplicado_automatico = True

    tipos_unidade = unidade_op.tipos_chamado_recebe or []
    tipos_gestao = {k: v for k, v in TIPOS_CHAMADO_LABELS.items() if k in tipos_unidade}

    query = Chamado.query.filter(filtro_gestao)

    if setor_filtro:
        query = query.filter(Chamado.setor_id == setor_filtro)
    if unidade_abriu_filtro:
        query = query.filter(Chamado.unidade_id == unidade_abriu_filtro)
    if status_filtro:
        query = query.filter(Chamado.status.in_(status_filtro))
    if tipo_filtro:
        tipos_ok = [t for t in tipo_filtro if t in tipos_unidade]
        if tipos_ok:
            query = query.filter(Chamado.tipo_chamado.in_(tipos_ok))
    if prio_filtro:
        query = query.filter(Chamado.prioridade.in_(prio_filtro))

    _prio_order = db.case(
        {'alta': 1, 'urgente': 1, 'media': 2, 'baixa': 3},
        value=Chamado.prioridade,
        else_=4
    )
    chamados = query.order_by(_prio_order, Chamado.criado_em.asc()).all()

    base_q = Chamado.query.filter(filtro_gestao)
    slugs_status = [s.slug for s in status_db]
    totais = {s: base_q.filter(Chamado.status == s).count() for s in slugs_status}
    total_geral = base_q.count()

    return render_template('chamados/gestao.html',
                           chamados=chamados,
                           total_geral=total_geral,
                           setores=setores_disponiveis,
                           setor_filtro=setor_filtro,
                           status_filtro=status_filtro,
                           tipo_filtro=tipo_filtro,
                           prio_filtro=prio_filtro,
                           unidades_ativas=unidades_ativas,
                           unidade_abriu_filtro=unidade_abriu_filtro,
                           ver_todos=ver_todos,
                           filtro_aplicado_automatico=filtro_aplicado_automatico,
                           gestao_unidade=unidade_op,
                           totais=totais,
                           tipos=tipos_gestao,
                           prioridades=PRIORIDADES_LABELS,
                           status_opts=status_opts_db,
                           status_badge=status_badge_db,
                           status_cores=status_cores_db,
                           prio_badge=PRIORIDADES_BADGE)


@chamados_bp.route('/gestao/<int:id>/atualizar-rapido', methods=['POST'])
@login_required
def gestao_atualizar_rapido(id):
    """Atualização rápida de status/setor/responsável direto da fila de gestão."""
    if not current_user.pode_ver_gestao_chamados:
        abort(403)
    chamado = Chamado.query.get_or_404(id)
    unidade_op = current_user.unidade_logada
    if not _chamado_na_fila_unidade(chamado, unidade_op):
        abort(403)

    novo_status  = request.form.get('status')
    observacao   = request.form.get('observacao', '').strip()
    unidade_resp = request.form.get('unidade_responsavel_id', '0')

    uid, erro_unidade = _validar_unidade_responsavel_id(chamado.tipo_chamado, unidade_resp)
    if erro_unidade:
        flash(erro_unidade, 'danger')
        redir_url = request.referrer
        if redir_url and 'gestao' in redir_url:
            return redirect(redir_url)
        return redirect(url_for('chamados.gestao'))

    if novo_status == 'concluido' and not current_user.pode('fechar_chamado'):
        abort(403)
    if novo_status == 'cancelado' and not current_user.pode('cancelar_chamado'):
        abort(403)

    status_anterior = chamado.status
    chamado.status  = novo_status
    chamado.unidade_responsavel_id = uid

    if novo_status in ['concluido', 'cancelado']:
        chamado.fechado_em           = datetime.utcnow()
        chamado.observacao_conclusao = observacao

    acao = f'Status alterado via Gestão: {status_anterior} → {novo_status}'

    db.session.add(ChamadoHistorico(
        chamado_id=chamado.id,
        usuario_id=current_user.id,
        acao=acao,
        observacao=observacao or None,
    ))
    db.session.commit()
    flash(f'Chamado {chamado.numero} atualizado.', 'success')
    # Preserva filtros: referer ou parâmetros do form
    redir_url = request.referrer
    if redir_url and 'gestao' in redir_url:
        return redirect(redir_url)
    params = {k: v for k, v in request.args.items()}
    return redirect(url_for('chamados.gestao', **params))


@chamados_bp.route('/api/salas/<int:unidade_id>')
@chamado_abertura_acesso
def api_salas(unidade_id):
    _api_unidade_permitida(unidade_id)
    unidade = Unidade.query.get_or_404(unidade_id)
    salas   = Sala.query.filter_by(unidade_id=unidade_id, ativo=True).order_by(Sala.nome).all()

    def _chamados_abertos(sala_id):
        return Chamado.query.filter(
            Chamado.sala_id == sala_id,
            Chamado.status.in_(['aberto', 'em_andamento', 'aguardando_peca']),
            Chamado.tipo_chamado == 'predial',
        ).count()

    return jsonify({
        'predio_id': unidade.predio_id,
        'salas': [{
            'id':              s.id,
            'nome':            s.nome,
            'tipo':            s.tipo_label if s.tipo_label != '—' else '',
            'chamados_abertos': _chamados_abertos(s.id),
        } for s in salas],
    })


@chamados_bp.route('/api/equipamentos/<int:sala_id>')
@login_required
def api_equipamentos(sala_id):
    from flask import jsonify
    equips = Equipamento.query.filter_by(sala_id=sala_id, ativo=True).all()
    return jsonify([{'id': e.id, 'nome': e.nome_display} for e in equips])


def _verificar_acesso_chamado(chamado):
    if current_user.pode('ver_chamados_todos'):
        return
    ids = [uu.unidade_id for uu in current_user.unidades.filter_by(ativo=True).all()]
    if chamado.unidade_id not in ids and chamado.aberto_por != current_user.id:
        abort(403)
