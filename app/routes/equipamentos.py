import mimetypes
import os
import uuid

from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.equipamento import (
    Equipamento, TipoEquipamento, CampoTipoEquipamento,
    Marca, Modelo, EquipamentoCampoValor, EquipamentoUsuario, EquipamentoDocumento,
    FORMAS_INCORPORACAO,
)
from datetime import date, datetime
from app.services.inventario_acesso import (
    marca_nova_fica_pendente, pode_alterar_estado, pode_anexar_documento,
    pode_corrigir_cadastro, pode_incluir, pode_informacoes_adicionais, gestor_patrimonio,
)
from app.models.sala import Sala
from app.models.unidade import Unidade, UsuarioUnidade
from app.models.tipo_unidade import TipoUnidade
from app.models.usuario import Usuario

equipamentos_bp = Blueprint('equipamentos', __name__, url_prefix='/equipamentos')

PREFIXO_PATRIMONIO = 'PMS-'

def _normalizar_icone_fontawesome(valor):
    """Normaliza o ícone do Font Awesome, adicionando prefixo 'fas' se necessário."""
    if not valor:
        return ''
    valor = valor.strip()
    if not valor:
        return ''
    
    import re
    # Se já tem prefixo (fas, far, fab, fal, fad), retorna como está
    if re.match(r'^(fas|far|fab|fal|fad)\s+fa-', valor):
        return valor
    
    # Se começa com fa- mas não tem prefixo, adiciona fas
    if valor.startswith('fa-'):
        return 'fas ' + valor
    
    # Se não começa com fa- e não tem prefixo, adiciona fas fa-
    if not re.match(r'^(fas|far|fab|fal|fad)\s+', valor):
        nome_icone = re.sub(r'^fa-', '', valor)
        return 'fas fa-' + nome_icone
    
    return valor

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


def _parse_ano_aquisicao(valor) -> date | None:
    """
    Aceita 'YYYY' (novo) e 'YYYY-MM-DD' (legado) e retorna YYYY-01-01.
    """
    if valor is None:
        return None
    v = str(valor).strip()
    if not v:
        return None

    # Legado: se vier no formato de data, pega só o ano (YYYY-...)
    if '-' in v:
        v = v.split('-', 1)[0].strip()

    if not v.isdigit() or len(v) != 4:
        return None

    ano = int(v)
    if ano < 1900 or ano > 2100:
        return None

    return date(ano, 1, 1)


def _parse_data(valor):
    if valor is None:
        return None
    v = str(valor).strip()
    if not v:
        return None
    if len(v) == 4 and v.isdigit():
        return date(int(v), 1, 1)
    try:
        return datetime.strptime(v[:10], '%Y-%m-%d').date()
    except ValueError:
        return None


def _parse_ano(valor):
    v = str(valor or '').strip()
    if len(v) == 4 and v.isdigit():
        ano = int(v)
        if 1900 <= ano <= 2100:
            return ano
    return None


def _rotulo_estado(status, condicao):
    from app.models.status_equipamento import CONDICAO_LABELS, mapa_status
    item = mapa_status().get(status)
    nome = item.nome if item else status
    return f'{nome} / {CONDICAO_LABELS.get(condicao, "—")}'


def _status_condicao_do_form():
    from app.models.status_equipamento import (
        StatusEquipamento, normalizar_condicao, opcoes_status,
    )
    codigo = request.form.get('status') or 'ativo'
    status = StatusEquipamento.query.filter_by(codigo=codigo).first()
    if not status or status.codigo not in {s.codigo for s in opcoes_status(codigo)}:
        status = StatusEquipamento.query.filter_by(codigo='ativo').first()
    if not status or not status.pede_condicao:
        return (status.codigo if status else 'ativo'), None
    return status.codigo, normalizar_condicao(request.form.get('condicao')) or 'boa'


def _resolver_marca_modelo(tipo):
    """Marca e modelo do tipo. Texto livre da unidade fica pendente de validação."""
    marca_id = request.form.get('marca_id', type=int) or None
    modelo_id = request.form.get('modelo_id', type=int) or None
    nova_marca = (request.form.get('nova_marca') or '').strip()
    novo_modelo = (request.form.get('novo_modelo') or '').strip()
    pendente = marca_nova_fica_pendente(current_user)

    if nova_marca:
        marca = Marca.query.filter(db.func.lower(Marca.nome) == nova_marca.lower()).first()
        if not marca:
            marca = Marca(nome=nova_marca, pendente=pendente)
            db.session.add(marca)
            db.session.flush()
        elif not pendente and marca.pendente:
            marca.pendente = False
        if not marca.suporta_tipo(tipo.id):
            marca.tipos.append(tipo)
        marca_id = marca.id

    if novo_modelo and marca_id:
        modelo = Modelo.query.filter(
            Modelo.marca_id == marca_id,
            Modelo.tipo_equipamento_id == tipo.id,
            db.func.lower(Modelo.nome) == novo_modelo.lower(),
        ).first()
        if not modelo:
            modelo = Modelo(
                marca_id=marca_id, tipo_equipamento_id=tipo.id,
                nome=novo_modelo, pendente=pendente,
            )
            db.session.add(modelo)
            db.session.flush()
        elif not pendente and modelo.pendente:
            modelo.pendente = False
        modelo_id = modelo.id

    if marca_id:
        marca = db.session.get(Marca, marca_id)
        if not marca or not marca.suporta_tipo(tipo.id):
            return None, None
        if modelo_id:
            modelo = db.session.get(Modelo, modelo_id)
            if not modelo or modelo.marca_id != marca_id:
                modelo_id = None
            elif modelo.tipo_equipamento_id and modelo.tipo_equipamento_id != tipo.id:
                modelo_id = None
    return marca_id, modelo_id


def _aplicar_identificacao(equipamento, tipo):
    equipamento.numero_patrimonio = _normalizar_patrimonio(request.form.get('numero_patrimonio', ''))
    equipamento.numero_serie = request.form.get('numero_serie', '').strip() or None
    equipamento.ano_fabricacao = _parse_ano(request.form.get('ano_fabricacao'))
    equipamento.observacoes = request.form.get('observacoes', '').strip()
    marca_id, modelo_id = _resolver_marca_modelo(tipo)
    equipamento.marca_id = marca_id
    equipamento.modelo_id = modelo_id
    for campo in tipo.campos.all():
        valor = request.form.get(f'campo_{campo.id}', '').strip()
        cv = equipamento.campos_valores.filter_by(campo_id=campo.id).first()
        if cv:
            cv.valor = valor
        elif valor:
            db.session.add(EquipamentoCampoValor(
                equipamento_id=equipamento.id, campo_id=campo.id, valor=valor))


def _aplicar_info_sueq(equipamento):
    proprio = request.form.get('proprio')
    equipamento.proprio = {'sim': True, 'nao': False}.get(proprio)
    forma = request.form.get('forma_incorporacao') or None
    equipamento.forma_incorporacao = forma if forma in dict(FORMAS_INCORPORACAO) else None
    equipamento.data_aquisicao = _parse_data(request.form.get('data_aquisicao'))
    equipamento.valor_estimado = request.form.get('valor_estimado') or None
    equipamento.numero_nota_fiscal = request.form.get('numero_nota_fiscal', '').strip() or None
    equipamento.numero_empenho = request.form.get('numero_empenho', '').strip() or None
    equipamento.fonte_recurso = request.form.get('fonte_recurso', '').strip() or None
    equipamento.numero_processo = request.form.get('numero_processo', '').strip() or None
    equipamento.numero_contrato_af = request.form.get('numero_contrato_af', '').strip() or None
    equipamento.fornecedor = request.form.get('fornecedor', '').strip() or None
    equipamento.data_entrega_unidade = _parse_data(request.form.get('data_entrega_unidade'))
    equipamento.garantia = request.form.get('garantia', '').strip() or None
    equipamento.vida_util_estimada = request.form.get('vida_util_estimada', '').strip() or None
    equipamento.data_desativacao = _parse_data(request.form.get('data_desativacao'))


def _ctx_form(unidade, equipamento=None):
    from app.models.status_equipamento import CONDICAO_LABELS as CONDICOES, opcoes_status
    corrigir = pode_corrigir_cadastro(current_user, unidade)
    atual = equipamento.status if equipamento else None
    status = opcoes_status(atual)
    return {
        'pode_editar_cadastro': corrigir,
        'pode_info_adicional': pode_informacoes_adicionais(current_user),
        'somente_estado': not corrigir,
        'marca_pendente': marca_nova_fica_pendente(current_user),
        'status_itens': status,
        'condicoes': CONDICOES,
        'formas_incorporacao': FORMAS_INCORPORACAO,
    }


def _nome_marca(marca):
    return f'{marca.nome} (pendente de validação)' if marca.pendente else marca.nome


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

    from app.models.status_equipamento import opcoes_status
    equipamentos  = query.order_by(Equipamento.id.desc()).all()
    tipos         = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()
    unidades      = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()

    return render_template('equipamentos/listar.html',
                           equipamentos=equipamentos,
                           tipos=tipos,
                           tipos_unidade=tipos_unidade,
                           unidades=unidades,
                           status_opts={s.codigo: s.nome for s in opcoes_status()},
                           condicao_opts={'boa': 'Boa', 'regular': 'Regular', 'ruim': 'Ruim'},
                           filtro_tipos=filtro_tipos,
                           filtro_tipo_unidades=filtro_tipo_unidades,
                           filtro_unidades=filtro_unidades,
                           filtro_status_list=filtro_status_list,
                           filtro_condicao_list=filtro_condicao_list)


@equipamentos_bp.route('/novo/<int:sala_id>', methods=['GET', 'POST'])
@login_required
def novo(sala_id):
    sala = Sala.query.get_or_404(sala_id)
    if not pode_incluir(current_user, sala.unidade):
        abort(403)
    tipos = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()

    if request.method == 'POST':
        tipo_id = request.form.get('tipo_equipamento_id', type=int)
        tipo = TipoEquipamento.query.get_or_404(tipo_id)
        status, condicao = _status_condicao_do_form()
        equipamento = Equipamento(
            sala_id=sala_id,
            tipo_equipamento_id=tipo_id,
            status=status,
            condicao=condicao,
            criado_por=current_user.id,
        )
        db.session.add(equipamento)
        db.session.flush()
        _aplicar_identificacao(equipamento, tipo)
        if pode_informacoes_adicionais(current_user):
            _aplicar_info_sueq(equipamento)
        db.session.commit()
        flash('Equipamento cadastrado com sucesso!', 'success')
        return redirect(url_for('equipamentos.detalhe', id=equipamento.id))

    return render_template('equipamentos/form.html',
                           equipamento=None, sala=sala, tipos=tipos,
                           **_ctx_form(sala.unidade))


@equipamentos_bp.route('/novo-na-unidade/<int:unidade_id>', methods=['GET', 'POST'])
@login_required
def novo_na_unidade(unidade_id):
    """Cadastrar equipamento a partir da página da unidade — o usuário escolhe a sala."""
    unidade = Unidade.query.get_or_404(unidade_id)
    if not pode_incluir(current_user, unidade):
        abort(403)
    salas   = Sala.query.filter_by(unidade_id=unidade_id, ativo=True).order_by(Sala.nome).all()
    tipos   = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()

    # Usuários disponíveis para vincular durante o cadastro (mesma lógica do detalhe do equipamento)
    ids_unidade = {uu.usuario_id for uu in unidade.usuarios.filter_by(ativo=True).all() if uu.usuario_id}
    usuarios_disponiveis = Usuario.query.filter(
        Usuario.id.in_(ids_unidade) if ids_unidade else db.false(),
        Usuario.ativo == True,
        Usuario.perfil != 'administrador',
    ).order_by(Usuario.nome).all()

    if request.method == 'POST':
        sala_id = request.form.get('sala_id', type=int)
        if not sala_id:
            flash('Selecione uma sala para o equipamento.', 'danger')
            return render_template('equipamentos/form.html',
                                   equipamento=None, sala=None, unidade=unidade,
                                   salas=salas, tipos=tipos,
                                   campos_valores={},
                                   usuarios_disponiveis=usuarios_disponiveis,
                                   **_ctx_form(unidade))
        sala    = Sala.query.get_or_404(sala_id)
        if sala.unidade_id != unidade.id:
            abort(403)
        tipo_id = request.form.get('tipo_equipamento_id', type=int)
        tipo    = TipoEquipamento.query.get_or_404(tipo_id)
        status, condicao = _status_condicao_do_form()
        equipamento = Equipamento(
            sala_id=sala_id,
            tipo_equipamento_id=tipo_id,
            status=status,
            condicao=condicao,
            criado_por=current_user.id,
        )
        db.session.add(equipamento)
        db.session.flush()
        _aplicar_identificacao(equipamento, tipo)
        if pode_informacoes_adicionais(current_user):
            _aplicar_info_sueq(equipamento)
        db.session.commit()
        flash('Equipamento cadastrado com sucesso!', 'success')
        # Direciona para a tela do equipamento recém-criado e abre a aba de usuários
        # para permitir vincular o profissional já no passo seguinte.
        if current_user.pode('editar_equipamento'):
            usuario_id = request.form.get('usuario_id', type=int)
            observacao = request.form.get('observacao', '').strip() or None
            if usuario_id:
                vinculo_unidade = UsuarioUnidade.query.filter_by(
                    usuario_id=usuario_id,
                    unidade_id=unidade_id,
                    ativo=True
                ).first()
                if not vinculo_unidade:
                    flash('Usuário selecionado não pertence à unidade informada (vínculo não criado).', 'warning')
                else:
                    existente = EquipamentoUsuario.query.filter_by(
                        equipamento_id=equipamento.id,
                        usuario_id=usuario_id
                    ).first()
                    if not existente:
                        db.session.add(EquipamentoUsuario(
                            equipamento_id=equipamento.id,
                            usuario_id=usuario_id,
                            observacao=observacao,
                        ))
                        db.session.commit()
        return redirect(url_for('equipamentos.detalhe', id=equipamento.id) + '#tab-usuarios')

    return render_template('equipamentos/form.html',
                           equipamento=None, sala=None, unidade=unidade,
                           salas=salas, tipos=tipos,
                           campos_valores={},
                           usuarios_disponiveis=usuarios_disponiveis,
                           **_ctx_form(unidade))


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
                           usuarios_disponiveis=usuarios_disponiveis,
                           documentos=equipamento.documentos.all(),
                           formas_incorporacao=FORMAS_INCORPORACAO,
                           pode_anexar=pode_anexar_documento(current_user, unidade))


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
    from app.models.transferencia import HistoricoEquipamento

    equipamento = Equipamento.query.get_or_404(id)
    unidade = equipamento.sala.unidade
    if not pode_corrigir_cadastro(current_user, unidade) and not pode_alterar_estado(current_user, unidade):
        abort(403)
    salas = Sala.query.filter_by(unidade_id=unidade.id, ativo=True).order_by(Sala.nome).all()
    pode_alterar_tipo = pode_corrigir_cadastro(current_user, unidade)
    tipos = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    if equipamento.tipo_equipamento and equipamento.tipo_equipamento not in tipos:
        tipos = [equipamento.tipo_equipamento] + tipos
    campos_valores = {cv.campo_id: cv.valor for cv in equipamento.campos_valores.all()}
    ctx = _ctx_form(unidade, equipamento)

    def _render_editar():
        return render_template('equipamentos/form.html',
                               equipamento=equipamento, sala=equipamento.sala,
                               unidade=unidade, salas=salas,
                               pode_alterar_tipo=pode_alterar_tipo,
                               tipos=tipos,
                               campos_valores=campos_valores,
                               **ctx)

    if request.method == 'POST':
        if not ctx['pode_editar_cadastro']:
            status, condicao = _status_condicao_do_form()
            if status != equipamento.status or condicao != equipamento.condicao:
                db.session.add(HistoricoEquipamento(
                    equipamento_id=equipamento.id,
                    usuario_id=current_user.id,
                    acao='Estado e condição atualizados',
                    observacao=_rotulo_estado(status, condicao),
                ))
            equipamento.status = status
            equipamento.condicao = condicao
            db.session.commit()
            flash('Estado e condição atualizados.', 'success')
            return redirect(url_for('equipamentos.detalhe', id=equipamento.id))

        novo_sala_id = request.form.get('sala_id', type=int)
        if novo_sala_id and novo_sala_id != equipamento.sala_id:
            nova_sala = Sala.query.filter_by(
                id=novo_sala_id, unidade_id=unidade.id, ativo=True
            ).first()
            if not nova_sala:
                flash('Sala inválida para esta unidade.', 'danger')
                return _render_editar()
            sala_antiga = equipamento.sala.nome
            equipamento.sala_id = novo_sala_id
            db.session.add(HistoricoEquipamento(
                equipamento_id=equipamento.id,
                usuario_id=current_user.id,
                acao=f'Realocado de {sala_antiga} para {nova_sala.nome}',
            ))

        tipo_atual = equipamento.tipo_equipamento
        if pode_alterar_tipo:
            novo_tipo_id = request.form.get('tipo_equipamento_id', type=int)
            if novo_tipo_id and novo_tipo_id != equipamento.tipo_equipamento_id:
                novo_tipo = TipoEquipamento.query.get(novo_tipo_id)
                if not novo_tipo:
                    flash('Tipo de equipamento inválido.', 'danger')
                    return _render_editar()
                tipo_antigo = equipamento.tipo_equipamento.nome
                EquipamentoCampoValor.query.filter_by(equipamento_id=equipamento.id).delete()
                equipamento.tipo_equipamento_id = novo_tipo_id
                tipo_atual = novo_tipo
                db.session.add(HistoricoEquipamento(
                    equipamento_id=equipamento.id,
                    usuario_id=current_user.id,
                    acao=f'Tipo alterado de {tipo_antigo} para {novo_tipo.nome}',
                ))

        status, condicao = _status_condicao_do_form()
        if status != equipamento.status or condicao != equipamento.condicao:
            db.session.add(HistoricoEquipamento(
                equipamento_id=equipamento.id,
                usuario_id=current_user.id,
                acao='Estado e condição atualizados',
                observacao=_rotulo_estado(status, condicao),
            ))
        equipamento.status = status
        equipamento.condicao = condicao
        db.session.flush()
        _aplicar_identificacao(equipamento, tipo_atual)
        if pode_informacoes_adicionais(current_user):
            _aplicar_info_sueq(equipamento)
        db.session.commit()
        flash('Equipamento atualizado com sucesso!', 'success')
        return redirect(url_for('equipamentos.detalhe', id=equipamento.id))

    return _render_editar()


@equipamentos_bp.route('/<int:id>/baixa', methods=['POST'])
@login_required
def dar_baixa(id):
    from app.models.transferencia import HistoricoEquipamento
    equipamento = Equipamento.query.get_or_404(id)
    unidade = equipamento.sala.unidade
    if not pode_alterar_estado(current_user, unidade):
        abort(403)
    equipamento.status = 'inservivel'
    equipamento.condicao = None
    db.session.add(HistoricoEquipamento(
        equipamento_id=id,
        usuario_id=current_user.id,
        acao='Marcado como inservível/sem recuperação',
        observacao=request.form.get('motivo', '').strip() or None,
    ))
    db.session.commit()
    flash('Equipamento marcado como inservível/sem recuperação.', 'warning')
    return redirect(url_for('equipamentos.detalhe', id=id))


@equipamentos_bp.route('/api/marcas-por-tipo/<int:tipo_id>')
@login_required
def api_marcas_por_tipo(tipo_id):
    """Retorna as marcas vinculadas ao tipo de equipamento selecionado."""
    tipo = TipoEquipamento.query.get_or_404(tipo_id)
    marcas = tipo.marcas.order_by(Marca.nome).all()
    return jsonify([{'id': m.id, 'nome': _nome_marca(m)} for m in marcas])


@equipamentos_bp.route('/api/modelos/<int:marca_id>')
@login_required
def api_modelos(marca_id):
    tipo_id = request.args.get('tipo_id', type=int)
    q = Modelo.query.filter_by(marca_id=marca_id)
    if tipo_id:
        q = q.filter_by(tipo_equipamento_id=tipo_id)
    modelos = q.order_by(Modelo.nome).all()
    return jsonify([{
        'id': m.id,
        'nome': f'{m.nome} (pendente de validação)' if m.pendente else m.nome,
    } for m in modelos])


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


_UPLOAD_EXT = {'.pdf', '.png', '.jpg', '.jpeg', '.webp', '.doc', '.docx', '.xls', '.xlsx'}
_UPLOAD_MAX = 15 * 1024 * 1024


def _pasta_documentos():
    pasta = os.path.join(current_app.root_path, 'static', 'uploads', 'equipamentos')
    os.makedirs(pasta, exist_ok=True)
    return pasta


@equipamentos_bp.route('/<int:id>/documentos', methods=['POST'])
@login_required
def enviar_documento(id):
    equipamento = Equipamento.query.get_or_404(id)
    unidade = equipamento.sala.unidade
    if not pode_anexar_documento(current_user, unidade):
        abort(403)
    arquivo = request.files.get('arquivo')
    if not arquivo or not arquivo.filename:
        flash('Selecione um arquivo.', 'warning')
        return redirect(url_for('equipamentos.detalhe', id=id) + '#tab-documentos')
    original = arquivo.filename
    ext = os.path.splitext(original)[1].lower()
    if ext not in _UPLOAD_EXT:
        flash('Envie PDF, imagem ou planilha/documento do Office.', 'warning')
        return redirect(url_for('equipamentos.detalhe', id=id) + '#tab-documentos')
    arquivo.stream.seek(0, os.SEEK_END)
    tamanho = arquivo.stream.tell()
    arquivo.stream.seek(0)
    if tamanho > _UPLOAD_MAX:
        flash('O arquivo passa de 15 MB.', 'warning')
        return redirect(url_for('equipamentos.detalhe', id=id) + '#tab-documentos')
    filename = f'{uuid.uuid4().hex}{ext}'
    arquivo.save(os.path.join(_pasta_documentos(), filename))
    mime = arquivo.mimetype or mimetypes.guess_type(original)[0] or 'application/octet-stream'
    db.session.add(EquipamentoDocumento(
        equipamento_id=id, filename=filename, original=original,
        mime_type=mime, tamanho_bytes=tamanho, criado_por=current_user.id,
    ))
    from app.models.transferencia import HistoricoEquipamento
    db.session.add(HistoricoEquipamento(
        equipamento_id=id, usuario_id=current_user.id,
        acao='Documento incluído no prontuário', observacao=original,
    ))
    db.session.commit()
    flash('Documento incluído no prontuário.', 'success')
    return redirect(url_for('equipamentos.detalhe', id=id) + '#tab-documentos')


@equipamentos_bp.route('/<int:id>/documentos/<int:doc_id>/excluir', methods=['POST'])
@login_required
def excluir_documento(id, doc_id):
    equipamento = Equipamento.query.get_or_404(id)
    if not pode_anexar_documento(current_user, equipamento.sala.unidade):
        abort(403)
    doc = EquipamentoDocumento.query.filter_by(id=doc_id, equipamento_id=id).first_or_404()
    caminho = os.path.join(_pasta_documentos(), doc.filename)
    if os.path.isfile(caminho):
        os.remove(caminho)
    db.session.delete(doc)
    db.session.commit()
    flash('Documento removido.', 'info')
    return redirect(url_for('equipamentos.detalhe', id=id) + '#tab-documentos')


@equipamentos_bp.route('/marcas-pendentes', methods=['GET', 'POST'])
@login_required
def marcas_pendentes():
    if not pode_informacoes_adicionais(current_user):
        abort(403)
    if request.method == 'POST':
        acao = request.form.get('acao')
        tipo = request.form.get('tipo')
        item_id = request.form.get('item_id', type=int)
        if tipo == 'marca' and item_id:
            marca = Marca.query.get_or_404(item_id)
            if acao == 'validar':
                marca.pendente = False
                for modelo in marca.modelos.filter_by(pendente=True):
                    modelo.pendente = False
                flash(f'Marca {marca.nome} validada.', 'success')
            elif acao == 'recusar' and marca.equipamentos.count() == 0:
                db.session.delete(marca)
                flash('Marca recusada e removida.', 'info')
            elif acao == 'recusar':
                flash('Essa marca já está em algum equipamento. Valide ou troque o equipamento antes de recusar.', 'warning')
        elif tipo == 'modelo' and item_id:
            modelo = Modelo.query.get_or_404(item_id)
            if acao == 'validar':
                modelo.pendente = False
                if modelo.marca and modelo.marca.pendente:
                    modelo.marca.pendente = False
                flash(f'Modelo {modelo.nome} validado.', 'success')
            elif acao == 'recusar' and modelo.equipamentos.count() == 0:
                db.session.delete(modelo)
                flash('Modelo recusado e removido.', 'info')
            elif acao == 'recusar':
                flash('Esse modelo já está em algum equipamento.', 'warning')
        db.session.commit()
        return redirect(url_for('equipamentos.marcas_pendentes'))
    marcas = Marca.query.filter_by(pendente=True).order_by(Marca.nome).all()
    modelos = Modelo.query.filter_by(pendente=True).order_by(Modelo.nome).all()
    return render_template('equipamentos/marcas_pendentes.html', marcas=marcas, modelos=modelos)


@equipamentos_bp.route('/unidade/<int:unidade_id>/inventario-inicial', methods=['POST'])
@login_required
def alternar_inventario_inicial(unidade_id):
    if not gestor_patrimonio(current_user):
        abort(403)
    unidade = Unidade.query.get_or_404(unidade_id)
    unidade.inventario_inicial_concluido = not unidade.inventario_inicial_concluido
    db.session.commit()
    if unidade.inventario_inicial_concluido:
        flash('Inventário inicial encerrado. A unidade passa a transferir e alterar só o estado e a condição.', 'success')
    else:
        flash('Inventário inicial reaberto para a unidade cadastrar e corrigir.', 'success')
    return redirect(url_for('unidades.detalhe', id=unidade.id) + '#tab-equipamentos')


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
            icone=_normalizar_icone_fontawesome(request.form.get('icone', 'fas fa-box')),
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
        tipo.icone = _normalizar_icone_fontawesome(request.form.get('icone', 'fas fa-box'))
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
