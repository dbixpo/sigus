from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.tipo_unidade import TipoUnidade
from app.models.tipo_sala import TipoSala
from app.models.equipamento import TipoEquipamento, CampoTipoEquipamento, Marca, Modelo
from app.models.usuario import Usuario, PERFIS, HIERARQUIA
from app.models.link_util import LinkUtil
from app.models.tipo_link import TipoLink
from app.models.status_chamado import StatusChamado, BADGE_CORES
from app.models.auditoria import Auditoria, ACAO_OPCOES, MODULO_OPCOES
from app.models.chamado import Divisao, SetorManutencao, TIPOS_CHAMADO_LABELS
from app.models.perfil_permissao import PerfilPermissao, SECOES
from app.models.cbo import CBO
from app.models.unidade import Unidade
from app.models.predio import Predio

configuracoes_bp = Blueprint('configuracoes', __name__, url_prefix='/configuracoes')


def _exigir_admin():
    """Acesso à página inicial de configurações (tipos, marcas, unidades, prédios, etc.)."""
    if (not current_user.pode('ver_configuracoes') and not current_user.pode('gerenciar_tipos_equipamento') 
        and not current_user.pode('gerenciar_perfis') and not current_user.pode('ver_todas_unidades') 
        and not current_user.pode('cadastrar_unidade') and not current_user.pode('ver_predios') 
        and not current_user.pode('cadastrar_predio')):
        abort(403)


def _exigir_auditoria():
    """Apenas perfil administrador pode acessar auditoria."""
    if not current_user.pode('ver_auditoria'):
        abort(403)


def _normalizar_icone_fontawesome(valor):
    """Normaliza o ícone do Font Awesome, adicionando prefixo 'fas' se necessário."""
    if not valor:
        return ''
    valor = valor.strip()
    if not valor:
        return ''
    
    # Compatibilidade com ícones antigos em Bootstrap Icons (bi / bi-*)
    if valor.startswith('bi '):
        partes = valor.split()
        if len(partes) > 1 and partes[1].startswith('bi-'):
            return 'fas fa-' + partes[1][3:]
    if valor.startswith('bi-'):
        return 'fas fa-' + valor[3:]

    # Se já tem prefixo (fas, far, fab, fal, fad), retorna como está
    import re
    if re.match(r'^(fas|far|fab|fal|fad)\s+fa-', valor):
        return valor
    
    # Se começa com fa- mas não tem prefixo, adiciona fas
    if valor.startswith('fa-'):
        return 'fas ' + valor
    
    # Se não começa com fa- e não tem prefixo, adiciona fas fa-
    if not re.match(r'^(fas|far|fab|fal|fad)\s+', valor):
        # Remove fa- se já existir no início
        nome_icone = re.sub(r'^fa-', '', valor)
        return 'fas fa-' + nome_icone
    
    return valor


def _exigir_gerenciar_perfis():
    """Apenas administrador pode gerenciar perfis."""
    if not current_user.pode('gerenciar_perfis'):
        abort(403)


# ══════════════════════════════════════════════════════════
#  ÍNDICE DE CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════

@configuracoes_bp.route('/')
@login_required
def index():
    _exigir_admin()
    total_unidades       = Unidade.query.filter_by(status='ativa').count()
    total_predios        = Predio.query.filter_by(ativo=True).count()
    total_tipos_unidade  = TipoUnidade.query.count()
    total_tipos_sala     = TipoSala.query.count()
    total_tipos_equip    = TipoEquipamento.query.count()
    total_perfis         = len(PERFIS)
    total_marcas         = Marca.query.count()
    total_modelos        = Modelo.query.count()
    total_links          = LinkUtil.query.count()
    total_tipos_link     = TipoLink.query.count()
    total_status_chamado = StatusChamado.query.filter_by(ativo=True).count()
    total_divisoes = Divisao.query.filter_by(ativo=True).count()
    total_setores = SetorManutencao.query.count()
    total_cbos = CBO.query.count()
    return render_template('configuracoes/index.html',
                           total_unidades=total_unidades,
                           total_predios=total_predios,
                           total_tipos_unidade=total_tipos_unidade,
                           total_tipos_sala=total_tipos_sala,
                           total_tipos_equip=total_tipos_equip,
                           total_perfis=total_perfis,
                           total_marcas=total_marcas,
                           total_modelos=total_modelos,
                           total_links=total_links,
                           total_tipos_link=total_tipos_link,
                           total_status_chamado=total_status_chamado,
                           total_divisoes=total_divisoes,
                           total_setores=total_setores,
                           total_cbos=total_cbos)


# ══════════════════════════════════════════════════════════
#  TIPOS DE UNIDADE
# ══════════════════════════════════════════════════════════

@configuracoes_bp.route('/tipos-unidade')
@login_required
def tipos_unidade():
    _exigir_admin()
    tipos = TipoUnidade.query.order_by(TipoUnidade.nome).all()
    return render_template('configuracoes/tipos_unidade/listar.html', tipos=tipos)


@configuracoes_bp.route('/tipos-unidade/novo', methods=['GET', 'POST'])
@login_required
def novo_tipo_unidade():
    _exigir_admin()
    if request.method == 'POST':
        sigla = request.form['sigla'].strip().upper()
        nome = request.form['nome'].strip()

        if TipoUnidade.query.filter_by(sigla=sigla).first():
            flash(f'Já existe um tipo com a sigla "{sigla}".', 'danger')
            return render_template('configuracoes/tipos_unidade/form.html', tipo=None)

        tipo = TipoUnidade(
            sigla=sigla,
            nome=nome,
            descricao=request.form.get('descricao', '').strip(),
            ativo=request.form.get('ativo') == 'on',
        )
        db.session.add(tipo)
        db.session.commit()
        flash(f'Tipo "{tipo.sigla} — {tipo.nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('configuracoes.tipos_unidade'))
    return render_template('configuracoes/tipos_unidade/form.html', tipo=None)


@configuracoes_bp.route('/tipos-unidade/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tipo_unidade(id):
    _exigir_admin()
    tipo = TipoUnidade.query.get_or_404(id)
    if request.method == 'POST':
        nova_sigla = request.form['sigla'].strip().upper()
        conflito = TipoUnidade.query.filter(
            TipoUnidade.sigla == nova_sigla,
            TipoUnidade.id != id
        ).first()
        if conflito:
            flash(f'Já existe outro tipo com a sigla "{nova_sigla}".', 'danger')
            return render_template('configuracoes/tipos_unidade/form.html', tipo=tipo)

        tipo.sigla = nova_sigla
        tipo.nome = request.form['nome'].strip()
        tipo.descricao = request.form.get('descricao', '').strip()
        tipo.ativo = request.form.get('ativo') == 'on'
        db.session.commit()
        flash('Tipo de unidade atualizado!', 'success')
        return redirect(url_for('configuracoes.tipos_unidade'))
    return render_template('configuracoes/tipos_unidade/form.html', tipo=tipo)


@configuracoes_bp.route('/tipos-unidade/<int:id>/alternar-status', methods=['POST'])
@login_required
def alternar_status_tipo_unidade(id):
    _exigir_admin()
    tipo = TipoUnidade.query.get_or_404(id)
    tipo.ativo = not tipo.ativo
    db.session.commit()
    estado = 'ativado' if tipo.ativo else 'desativado'
    flash(f'Tipo "{tipo.sigla}" {estado}.', 'info')
    return redirect(url_for('configuracoes.tipos_unidade'))


# ══════════════════════════════════════════════════════════
#  DIVISÕES E SETORES
# ══════════════════════════════════════════════════════════

def _parse_tipos_unidade_ids():
    """Converte form getlist('tipos_unidade_ids') em lista de ints."""
    ids = request.form.getlist('tipos_unidade_ids')
    return [int(x) for x in ids if str(x).isdigit()]


@configuracoes_bp.route('/divisoes')
@login_required
def divisoes():
    _exigir_admin()
    divisoes_list = Divisao.query.order_by(Divisao.nome).all()
    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()
    tipos_map = {t.id: t for t in tipos_unidade}
    return render_template('configuracoes/divisoes/listar.html',
                           divisoes=divisoes_list, tipos_unidade=tipos_unidade, tipos_map=tipos_map)


@configuracoes_bp.route('/divisoes/novo', methods=['GET', 'POST'])
@login_required
def nova_divisao():
    _exigir_admin()
    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        if not nome:
            flash('Nome é obrigatório.', 'danger')
            return render_template('configuracoes/divisoes/form.html', divisao=None,
                                   tipos_unidade=tipos_unidade, tipos_chamado_labels=TIPOS_CHAMADO_LABELS)
        tipos_chamado = request.form.getlist('tipos_chamado')
        tipos_unidade_ids = _parse_tipos_unidade_ids()
        div = Divisao(
            nome=nome,
            descricao=request.form.get('descricao', '').strip() or None,
            tipos_chamado=tipos_chamado,
            tipos_unidade_ids=tipos_unidade_ids,
            ativo=request.form.get('ativo') == 'on',
        )
        db.session.add(div)
        db.session.commit()
        flash(f'Divisão "{div.nome}" cadastrada com sucesso!', 'success')
        return redirect(url_for('configuracoes.divisoes'))
    return render_template('configuracoes/divisoes/form.html', divisao=None,
                           tipos_unidade=tipos_unidade, tipos_chamado_labels=TIPOS_CHAMADO_LABELS)


@configuracoes_bp.route('/divisoes/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_divisao(id):
    _exigir_admin()
    divisao = Divisao.query.get_or_404(id)
    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()
    if request.method == 'POST':
        divisao.nome = request.form.get('nome', '').strip()
        divisao.descricao = request.form.get('descricao', '').strip() or None
        divisao.tipos_chamado = request.form.getlist('tipos_chamado')
        divisao.tipos_unidade_ids = _parse_tipos_unidade_ids()
        divisao.ativo = request.form.get('ativo') == 'on'
        db.session.commit()
        flash('Divisão atualizada!', 'success')
        return redirect(url_for('configuracoes.divisoes'))
    return render_template('configuracoes/divisoes/form.html', divisao=divisao,
                           tipos_unidade=tipos_unidade, tipos_chamado_labels=TIPOS_CHAMADO_LABELS)


@configuracoes_bp.route('/setores')
@login_required
def setores():
    _exigir_admin()
    setores_list = SetorManutencao.query.order_by(SetorManutencao.nome).all()
    return render_template('configuracoes/setores/listar.html', setores=setores_list)


@configuracoes_bp.route('/setores/novo', methods=['GET', 'POST'])
@login_required
def novo_setor():
    _exigir_admin()
    divisoes_list = Divisao.query.filter_by(ativo=True).order_by(Divisao.nome).all()
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        if not nome:
            flash('Nome é obrigatório.', 'danger')
            return render_template('configuracoes/setores/form.html', setor=None,
                                   divisoes=divisoes_list, tipos_chamado_labels=TIPOS_CHAMADO_LABELS)
        divisao_id = request.form.get('divisao_id', type=int) or None
        tipos_chamado = request.form.getlist('tipos_chamado')
        s = SetorManutencao(
            nome=nome,
            divisao_id=divisao_id,
            descricao=request.form.get('descricao', '').strip() or None,
            tipos_chamado=tipos_chamado if tipos_chamado else [],
        )
        db.session.add(s)
        db.session.commit()
        flash(f'Setor "{s.nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('configuracoes.setores'))
    return render_template('configuracoes/setores/form.html', setor=None,
                           divisoes=divisoes_list, tipos_chamado_labels=TIPOS_CHAMADO_LABELS)


@configuracoes_bp.route('/setores/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_setor(id):
    _exigir_admin()
    setor = SetorManutencao.query.get_or_404(id)
    divisoes_list = Divisao.query.filter_by(ativo=True).order_by(Divisao.nome).all()
    if request.method == 'POST':
        setor.nome = request.form.get('nome', '').strip()
        setor.divisao_id = request.form.get('divisao_id', type=int) or None
        setor.descricao = request.form.get('descricao', '').strip() or None
        setor.tipos_chamado = request.form.getlist('tipos_chamado') or []
        db.session.commit()
        flash('Setor atualizado!', 'success')
        return redirect(url_for('configuracoes.setores'))
    return render_template('configuracoes/setores/form.html', setor=setor,
                           divisoes=divisoes_list, tipos_chamado_labels=TIPOS_CHAMADO_LABELS)


# ══════════════════════════════════════════════════════════
#  TIPOS DE SALA
# ══════════════════════════════════════════════════════════

@configuracoes_bp.route('/tipos-sala')
@login_required
def tipos_sala():
    _exigir_admin()
    tipos = TipoSala.query.order_by(TipoSala.nome).all()
    for t in tipos:
        t.icone = _normalizar_icone_fontawesome(t.icone) or 'fas fa-door-open'
    return render_template('configuracoes/tipos_sala/listar.html', tipos=tipos)


@configuracoes_bp.route('/tipos-sala/novo', methods=['GET', 'POST'])
@login_required
def novo_tipo_sala():
    _exigir_admin()
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        if TipoSala.query.filter_by(nome=nome).first():
            flash(f'Já existe um tipo de sala chamado "{nome}".', 'danger')
            return render_template('configuracoes/tipos_sala/form.html', tipo=None)
        tipo = TipoSala(
            nome=nome,
            descricao=request.form.get('descricao', '').strip() or None,
            icone=_normalizar_icone_fontawesome(request.form.get('icone', 'fas fa-door-open')),
            ativo=request.form.get('ativo') == 'on',
        )
        db.session.add(tipo)
        db.session.commit()
        flash(f'Tipo de sala "{tipo.nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('configuracoes.tipos_sala'))
    return render_template('configuracoes/tipos_sala/form.html', tipo=None)


@configuracoes_bp.route('/tipos-sala/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tipo_sala(id):
    _exigir_admin()
    tipo = TipoSala.query.get_or_404(id)
    if request.method == 'POST':
        novo_nome = request.form['nome'].strip()
        conflito = TipoSala.query.filter(TipoSala.nome == novo_nome, TipoSala.id != id).first()
        if conflito:
            flash(f'Já existe outro tipo de sala chamado "{novo_nome}".', 'danger')
            return render_template('configuracoes/tipos_sala/form.html', tipo=tipo)
        tipo.nome = novo_nome
        tipo.descricao = request.form.get('descricao', '').strip() or None
        tipo.icone = _normalizar_icone_fontawesome(request.form.get('icone', 'fas fa-door-open'))
        tipo.ativo = request.form.get('ativo') == 'on'
        db.session.commit()
        flash('Tipo de sala atualizado!', 'success')
        return redirect(url_for('configuracoes.tipos_sala'))
    tipo.icone = _normalizar_icone_fontawesome(tipo.icone) or 'fas fa-door-open'
    return render_template('configuracoes/tipos_sala/form.html', tipo=tipo)


@configuracoes_bp.route('/tipos-sala/<int:id>/alternar-status', methods=['POST'])
@login_required
def alternar_status_tipo_sala(id):
    _exigir_admin()
    tipo = TipoSala.query.get_or_404(id)
    if tipo.ativo and tipo.salas.filter_by(ativo=True).count() > 0:
        flash(f'Não é possível desativar "{tipo.nome}" pois existem salas cadastradas com este tipo.', 'danger')
        return redirect(url_for('configuracoes.tipos_sala'))
    tipo.ativo = not tipo.ativo
    db.session.commit()
    estado = 'ativado' if tipo.ativo else 'desativado'
    flash(f'Tipo "{tipo.nome}" {estado}.', 'info')
    return redirect(url_for('configuracoes.tipos_sala'))


# ══════════════════════════════════════════════════════════
#  TIPOS DE EQUIPAMENTO
# ══════════════════════════════════════════════════════════

@configuracoes_bp.route('/tipos-equipamento')
@login_required
def tipos_equipamento():
    _exigir_admin()
    tipos = TipoEquipamento.query.order_by(TipoEquipamento.nome).all()
    return render_template('configuracoes/tipos_equipamento/listar.html', tipos=tipos)


@configuracoes_bp.route('/tipos-equipamento/novo', methods=['GET', 'POST'])
@login_required
def novo_tipo_equipamento():
    _exigir_admin()
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        if TipoEquipamento.query.filter_by(nome=nome).first():
            flash(f'Já existe um tipo chamado "{nome}".', 'danger')
            return render_template('configuracoes/tipos_equipamento/form.html', tipo=None, campos=[])

        tipo = TipoEquipamento(
            nome=nome,
            descricao=request.form.get('descricao', '').strip(),
            tem_patrimonio=request.form.get('tem_patrimonio') == 'on',
            icone=_normalizar_icone_fontawesome(request.form.get('icone', 'fas fa-box')),
        )
        db.session.add(tipo)
        db.session.commit()
        flash(f'Tipo "{tipo.nome}" cadastrado! Agora adicione os campos específicos.', 'success')
        return redirect(url_for('configuracoes.editar_tipo_equipamento', id=tipo.id))
    return render_template('configuracoes/tipos_equipamento/form.html', tipo=None, campos=[])


@configuracoes_bp.route('/tipos-equipamento/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tipo_equipamento(id):
    _exigir_admin()
    tipo = TipoEquipamento.query.get_or_404(id)
    if request.method == 'POST':
        novo_nome = request.form['nome'].strip()
        conflito = TipoEquipamento.query.filter(
            TipoEquipamento.nome == novo_nome,
            TipoEquipamento.id != id
        ).first()
        if conflito:
            flash(f'Já existe outro tipo chamado "{novo_nome}".', 'danger')
            campos = tipo.campos.order_by(CampoTipoEquipamento.ordem).all()
            return render_template('configuracoes/tipos_equipamento/form.html', tipo=tipo, campos=campos)

        tipo.nome = novo_nome
        tipo.descricao = request.form.get('descricao', '').strip()
        tipo.tem_patrimonio = request.form.get('tem_patrimonio') == 'on'
        tipo.icone = _normalizar_icone_fontawesome(request.form.get('icone', 'fas fa-box'))
        db.session.commit()
        flash('Tipo de equipamento atualizado!', 'success')
        return redirect(url_for('configuracoes.tipos_equipamento'))
    campos = tipo.campos.order_by(CampoTipoEquipamento.ordem).all()
    return render_template('configuracoes/tipos_equipamento/form.html', tipo=tipo, campos=campos)


@configuracoes_bp.route('/tipos-equipamento/<int:tipo_id>/campo/novo', methods=['POST'])
@login_required
def novo_campo_equipamento(tipo_id):
    _exigir_admin()
    import json
    tipo = TipoEquipamento.query.get_or_404(tipo_id)
    opcoes_raw = request.form.get('opcoes_selecao', '').strip()
    opcoes = None
    if opcoes_raw:
        try:
            opcoes = json.loads(opcoes_raw)
        except Exception:
            opcoes = [o.strip() for o in opcoes_raw.split(',') if o.strip()]

    ultimo = tipo.campos.order_by(CampoTipoEquipamento.ordem.desc()).first()
    proxima_ordem = (ultimo.ordem + 1) if ultimo else 1

    eh_destaque = request.form.get('campo_destaque') == 'on'
    # Garante que só um campo seja destaque por tipo
    if eh_destaque:
        db.session.query(CampoTipoEquipamento).filter_by(
            tipo_equipamento_id=tipo_id, campo_destaque=True
        ).update({'campo_destaque': False})

    campo = CampoTipoEquipamento(
        tipo_equipamento_id=tipo_id,
        nome_campo=request.form['nome_campo'].strip(),
        tipo_dado=request.form.get('tipo_dado', 'texto'),
        obrigatorio=request.form.get('obrigatorio') == 'on',
        campo_destaque=eh_destaque,
        opcoes_selecao=opcoes,
        ordem=request.form.get('ordem', proxima_ordem, type=int),
    )
    db.session.add(campo)
    db.session.commit()
    flash(f'Campo "{campo.nome_campo}" adicionado!', 'success')
    return redirect(url_for('configuracoes.editar_tipo_equipamento', id=tipo_id))


@configuracoes_bp.route('/tipos-equipamento/campo/<int:campo_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_campo_equipamento(campo_id):
    _exigir_admin()
    import json
    campo = CampoTipoEquipamento.query.get_or_404(campo_id)
    if request.method == 'POST':
        opcoes_raw = request.form.get('opcoes_selecao', '').strip()
        opcoes = None
        if opcoes_raw:
            try:
                opcoes = json.loads(opcoes_raw)
            except Exception:
                opcoes = [o.strip() for o in opcoes_raw.split(',') if o.strip()]

        campo.nome_campo = request.form['nome_campo'].strip()
        campo.tipo_dado = request.form.get('tipo_dado', 'texto')
        campo.obrigatorio = request.form.get('obrigatorio') == 'on'
        campo.opcoes_selecao = opcoes
        campo.ordem = request.form.get('ordem', campo.ordem, type=int)
        eh_destaque = request.form.get('campo_destaque') == 'on'
        # Garante que só um campo seja destaque por tipo
        if eh_destaque and not campo.campo_destaque:
            db.session.query(CampoTipoEquipamento).filter_by(
                tipo_equipamento_id=campo.tipo_equipamento_id, campo_destaque=True
            ).update({'campo_destaque': False})
        campo.campo_destaque = eh_destaque
        db.session.commit()
        flash('Campo atualizado!', 'success')
        return redirect(url_for('configuracoes.editar_tipo_equipamento', id=campo.tipo_equipamento_id))
    return render_template('configuracoes/tipos_equipamento/form_campo.html', campo=campo)


@configuracoes_bp.route('/tipos-equipamento/campo/<int:campo_id>/excluir', methods=['POST'])
@login_required
def excluir_campo_equipamento(campo_id):
    _exigir_admin()
    campo = CampoTipoEquipamento.query.get_or_404(campo_id)
    tipo_id = campo.tipo_equipamento_id
    db.session.delete(campo)
    db.session.commit()
    flash('Campo removido.', 'info')
    return redirect(url_for('configuracoes.editar_tipo_equipamento', id=tipo_id))


@configuracoes_bp.route('/tipos-equipamento/<int:id>/alternar-status', methods=['POST'])
@login_required
def alternar_status_tipo_equipamento(id):
    _exigir_admin()
    tipo = TipoEquipamento.query.get_or_404(id)
    # Verifica se tem equipamentos ativos antes de desativar
    if tipo.ativo and tipo.equipamentos.filter_by(ativo=True).count() > 0:
        flash(f'Não é possível desativar "{tipo.nome}" pois existem equipamentos cadastrados deste tipo.', 'danger')
        return redirect(url_for('configuracoes.tipos_equipamento'))
    tipo.ativo = not tipo.ativo
    db.session.commit()
    estado = 'ativado' if tipo.ativo else 'desativado'
    flash(f'Tipo "{tipo.nome}" {estado}.', 'info')
    return redirect(url_for('configuracoes.tipos_equipamento'))


# ══════════════════════════════════════════════════════════
#  MARCAS E MODELOS
# ══════════════════════════════════════════════════════════

@configuracoes_bp.route('/marcas')
@login_required
def marcas():
    _exigir_admin()
    tipos = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    marcas = Marca.query.order_by(Marca.nome).all()
    return render_template('configuracoes/marcas/listar.html', tipos=tipos, marcas=marcas)


@configuracoes_bp.route('/marcas/nova', methods=['GET', 'POST'])
@login_required
def nova_marca():
    _exigir_admin()
    tipos = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        if Marca.query.filter_by(nome=nome).first():
            flash(f'Já existe uma marca chamada "{nome}".', 'danger')
            return render_template('configuracoes/marcas/form.html', marca=None, tipos=tipos)
        marca = Marca(nome=nome)
        db.session.add(marca)
        db.session.flush()
        ids_tipos = request.form.getlist('tipos[]', type=int)
        for tid in ids_tipos:
            t = TipoEquipamento.query.get(tid)
            if t:
                marca.tipos.append(t)
        db.session.commit()
        flash(f'Marca "{nome}" cadastrada!', 'success')
        return redirect(url_for('configuracoes.detalhe_marca', id=marca.id))
    pre_tipo_id = request.args.get('tipo_id', type=int)
    return render_template('configuracoes/marcas/form.html', marca=None, tipos=tipos, pre_tipo_id=pre_tipo_id)


@configuracoes_bp.route('/marcas/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_marca(id):
    _exigir_admin()
    marca = Marca.query.get_or_404(id)
    tipos = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    if request.method == 'POST':
        novo_nome = request.form['nome'].strip()
        if Marca.query.filter(Marca.nome == novo_nome, Marca.id != id).first():
            flash(f'Já existe outra marca chamada "{novo_nome}".', 'danger')
            return render_template('configuracoes/marcas/form.html', marca=marca, tipos=tipos, pre_tipo_id=None)
        marca.nome = novo_nome
        # Atualiza tipos associados
        ids_tipos = request.form.getlist('tipos[]', type=int)
        marca.tipos = []
        db.session.flush()
        for tid in ids_tipos:
            t = TipoEquipamento.query.get(tid)
            if t:
                marca.tipos.append(t)
        db.session.commit()
        flash('Marca atualizada!', 'success')
        return redirect(url_for('configuracoes.marcas'))
    return render_template('configuracoes/marcas/form.html', marca=marca, tipos=tipos, pre_tipo_id=None)


@configuracoes_bp.route('/marcas/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_marca(id):
    _exigir_admin()
    marca = Marca.query.get_or_404(id)
    if marca.equipamentos.count() > 0:
        flash(f'Não é possível excluir "{marca.nome}" pois há equipamentos vinculados.', 'danger')
        return redirect(url_for('configuracoes.marcas'))
    # Exclui modelos órfãos antes
    for m in marca.modelos.all():
        db.session.delete(m)
    db.session.delete(marca)
    db.session.commit()
    flash(f'Marca "{marca.nome}" excluída.', 'info')
    return redirect(url_for('configuracoes.marcas'))


@configuracoes_bp.route('/modelos/novo', methods=['GET', 'POST'])
@login_required
def novo_modelo(marca_id=None):
    _exigir_admin()
    tipos = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    # marca_id pode vir via querystring (link direto da detalhe_marca) ou via POST
    if request.method == 'POST':
        tipo_id  = request.form.get('tipo_equipamento_id', type=int)
        marca_id = request.form.get('marca_id', type=int)
        nome     = request.form.get('nome', '').strip()
        if not tipo_id or not marca_id or not nome:
            flash('Preencha tipo, marca e nome do modelo.', 'danger')
            return render_template('configuracoes/marcas/form_modelo.html',
                                   modelo=None, tipos=tipos,
                                   pre_tipo_id=tipo_id, pre_marca_id=marca_id)
        duplicado = Modelo.query.filter_by(
            tipo_equipamento_id=tipo_id, marca_id=marca_id, nome=nome
        ).first()
        if duplicado:
            flash(f'Já existe o modelo "{nome}" para este tipo e marca.', 'danger')
            return render_template('configuracoes/marcas/form_modelo.html',
                                   modelo=None, tipos=tipos,
                                   pre_tipo_id=tipo_id, pre_marca_id=marca_id)
        db.session.add(Modelo(tipo_equipamento_id=tipo_id, marca_id=marca_id, nome=nome))
        db.session.commit()
        flash(f'Modelo "{nome}" cadastrado!', 'success')
        return redirect(url_for('configuracoes.marcas'))
    pre_tipo_id  = request.args.get('tipo_id',  type=int)
    pre_marca_id = request.args.get('marca_id', type=int)
    return render_template('configuracoes/marcas/form_modelo.html',
                           modelo=None, tipos=tipos,
                           pre_tipo_id=pre_tipo_id, pre_marca_id=pre_marca_id)


# Rota legada (vinda de link com marca_id no path) — redireciona
@configuracoes_bp.route('/marcas/<int:marca_id>/modelos/novo')
@login_required
def novo_modelo_compat(marca_id):
    return redirect(url_for('configuracoes.novo_modelo', marca_id=marca_id))


@configuracoes_bp.route('/modelos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_modelo(id):
    _exigir_admin()
    modelo = Modelo.query.get_or_404(id)
    tipos  = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    if request.method == 'POST':
        tipo_id   = request.form.get('tipo_equipamento_id', type=int)
        marca_id  = request.form.get('marca_id', type=int)
        novo_nome = request.form.get('nome', '').strip()
        if not tipo_id or not marca_id or not novo_nome:
            flash('Preencha tipo, marca e nome.', 'danger')
            return render_template('configuracoes/marcas/form_modelo.html',
                                   modelo=modelo, tipos=tipos,
                                   pre_tipo_id=tipo_id, pre_marca_id=marca_id)
        duplicado = Modelo.query.filter(
            Modelo.tipo_equipamento_id == tipo_id,
            Modelo.marca_id == marca_id,
            Modelo.nome == novo_nome,
            Modelo.id != id
        ).first()
        if duplicado:
            flash(f'Já existe o modelo "{novo_nome}" para este tipo e marca.', 'danger')
            return render_template('configuracoes/marcas/form_modelo.html',
                                   modelo=modelo, tipos=tipos,
                                   pre_tipo_id=tipo_id, pre_marca_id=marca_id)
        modelo.tipo_equipamento_id = tipo_id
        modelo.marca_id  = marca_id
        modelo.nome      = novo_nome
        db.session.commit()
        flash('Modelo atualizado!', 'success')
        return redirect(url_for('configuracoes.marcas'))
    return render_template('configuracoes/marcas/form_modelo.html',
                           modelo=modelo, tipos=tipos,
                           pre_tipo_id=modelo.tipo_equipamento_id,
                           pre_marca_id=modelo.marca_id)


@configuracoes_bp.route('/modelos/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_modelo(id):
    _exigir_admin()
    modelo = Modelo.query.get_or_404(id)
    if modelo.equipamentos.count() > 0:
        flash(f'Não é possível excluir "{modelo.nome}" pois há equipamentos vinculados.', 'danger')
        return redirect(url_for('configuracoes.marcas'))
    db.session.delete(modelo)
    db.session.commit()
    flash(f'Modelo "{modelo.nome}" excluído.', 'info')
    return redirect(url_for('configuracoes.marcas'))


@configuracoes_bp.route('/marcas/<int:id>')
@login_required
def detalhe_marca(id):
    _exigir_admin()
    marca   = Marca.query.get_or_404(id)
    tipos   = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    modelos = marca.modelos.order_by(Modelo.nome).all()
    return render_template('configuracoes/marcas/detalhe.html', marca=marca, modelos=modelos, tipos=tipos)


# ══════════════════════════════════════════════════════════
#  MARCAS — página separada (Configurações → Marcas)
# ══════════════════════════════════════════════════════════

@configuracoes_bp.route('/lista-marcas')
@login_required
def listar_marcas():
    _exigir_admin()
    lista = Marca.query.order_by(Marca.nome).all()
    return render_template('configuracoes/marcas2/listar.html', marcas=lista)


@configuracoes_bp.route('/lista-marcas/nova', methods=['GET', 'POST'])
@login_required
def nova_marca2():
    _exigir_admin()
    tipos = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    pre_tipo_id = request.args.get('tipo_id', type=int)
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        if not nome:
            flash('Informe o nome da marca.', 'danger')
            return render_template('configuracoes/marcas2/form.html',
                                   marca=None, tipos=tipos, pre_tipo_id=pre_tipo_id)
        if Marca.query.filter_by(nome=nome).first():
            flash(f'Já existe uma marca chamada "{nome}".', 'danger')
            return render_template('configuracoes/marcas2/form.html',
                                   marca=None, tipos=tipos, pre_tipo_id=pre_tipo_id)
        marca = Marca(nome=nome)
        db.session.add(marca)
        db.session.flush()
        for tid in request.form.getlist('tipos[]', type=int):
            t = TipoEquipamento.query.get(tid)
            if t:
                marca.tipos.append(t)
        db.session.commit()
        flash(f'Marca "{nome}" cadastrada!', 'success')
        return redirect(url_for('configuracoes.listar_marcas'))
    return render_template('configuracoes/marcas2/form.html',
                           marca=None, tipos=tipos, pre_tipo_id=pre_tipo_id)


@configuracoes_bp.route('/lista-marcas/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_marca2(id):
    _exigir_admin()
    marca = Marca.query.get_or_404(id)
    tipos = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    if request.method == 'POST':
        novo_nome = request.form.get('nome', '').strip()
        if not novo_nome:
            flash('Informe o nome da marca.', 'danger')
            return render_template('configuracoes/marcas2/form.html',
                                   marca=marca, tipos=tipos, pre_tipo_id=None)
        if Marca.query.filter(Marca.nome == novo_nome, Marca.id != id).first():
            flash(f'Já existe outra marca chamada "{novo_nome}".', 'danger')
            return render_template('configuracoes/marcas2/form.html',
                                   marca=marca, tipos=tipos, pre_tipo_id=None)
        marca.nome = novo_nome
        marca.tipos = []
        db.session.flush()
        for tid in request.form.getlist('tipos[]', type=int):
            t = TipoEquipamento.query.get(tid)
            if t:
                marca.tipos.append(t)
        db.session.commit()
        flash('Marca atualizada!', 'success')
        return redirect(url_for('configuracoes.listar_marcas'))
    return render_template('configuracoes/marcas2/form.html',
                           marca=marca, tipos=tipos, pre_tipo_id=None)


@configuracoes_bp.route('/lista-marcas/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_marca2(id):
    _exigir_admin()
    marca = Marca.query.get_or_404(id)
    if marca.equipamentos.count() > 0 or marca.modelos.count() > 0:
        flash(f'Não é possível excluir "{marca.nome}" pois há modelos ou equipamentos vinculados.', 'danger')
        return redirect(url_for('configuracoes.listar_marcas'))
    db.session.delete(marca)
    db.session.commit()
    flash(f'Marca "{marca.nome}" excluída.', 'info')
    return redirect(url_for('configuracoes.listar_marcas'))


# ══════════════════════════════════════════════════════════
#  MODELOS — página separada (Configurações → Modelos)
# ══════════════════════════════════════════════════════════

@configuracoes_bp.route('/lista-modelos')
@login_required
def listar_modelos():
    _exigir_admin()
    filtro_tipo  = request.args.get('tipo_id',  type=int)
    filtro_marca = request.args.get('marca_id', type=int)

    q = Modelo.query
    if filtro_tipo:
        q = q.filter_by(tipo_equipamento_id=filtro_tipo)
    if filtro_marca:
        q = q.filter_by(marca_id=filtro_marca)
    modelos = q.order_by(Modelo.nome).all()

    tipos = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    # Marcas para o filtro: se tipo selecionado, filtra; senão todas
    if filtro_tipo:
        tipo_obj = TipoEquipamento.query.get(filtro_tipo)
        marcas_filtro = tipo_obj.marcas.order_by(Marca.nome).all() if tipo_obj else []
    else:
        marcas_filtro = Marca.query.order_by(Marca.nome).all()

    return render_template('configuracoes/modelos/listar.html',
                           modelos=modelos, tipos=tipos,
                           marcas_filtro=marcas_filtro,
                           filtro_tipo=filtro_tipo,
                           filtro_marca=filtro_marca)


@configuracoes_bp.route('/lista-modelos/novo', methods=['GET', 'POST'])
@login_required
def novo_modelo2():
    _exigir_admin()
    tipos       = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    marcas_todas = Marca.query.order_by(Marca.nome).all()
    pre_tipo_id  = request.args.get('tipo_id',  type=int)
    pre_marca_id = request.args.get('marca_id', type=int)

    if request.method == 'POST':
        tipo_id  = request.form.get('tipo_equipamento_id', type=int)
        marca_id = request.form.get('marca_id', type=int)
        
        # Suporta múltiplos modelos (nomes[]) ou modelo único (nome)
        nomes_lista = request.form.getlist('nomes[]')
        nome_unico = request.form.get('nome', '').strip()
        
        # Prepara lista de nomes para processar
        nomes = []
        if nomes_lista:
            nomes = [n.strip() for n in nomes_lista if n.strip()]
        elif nome_unico:
            nomes = [nome_unico]
        
        if not tipo_id or not marca_id or not nomes:
            flash('Preencha tipo de equipamento, marca e pelo menos um nome de modelo.', 'danger')
            return render_template('configuracoes/modelos/form.html',
                                   modelo=None, tipos=tipos, marcas_todas=marcas_todas,
                                   pre_tipo_id=tipo_id, pre_marca_id=marca_id)
        
        # Processa cada modelo
        modelos_criados = []
        modelos_duplicados = []
        modelos_invalidos = []
        
        for nome in nomes:
            nome = nome.strip()
            if not nome:
                continue
            
            # Verifica se já existe
            if Modelo.query.filter_by(tipo_equipamento_id=tipo_id, marca_id=marca_id, nome=nome).first():
                modelos_duplicados.append(nome)
                continue
            
            try:
                modelo = Modelo(tipo_equipamento_id=tipo_id, marca_id=marca_id, nome=nome)
                db.session.add(modelo)
                modelos_criados.append(nome)
            except Exception as e:
                modelos_invalidos.append(nome)
        
        if modelos_criados:
            db.session.commit()
            if len(modelos_criados) == 1:
                flash(f'Modelo "{modelos_criados[0]}" cadastrado!', 'success')
            else:
                flash(f'{len(modelos_criados)} modelo(s) cadastrado(s): {", ".join(modelos_criados[:5])}{"..." if len(modelos_criados) > 5 else ""}', 'success')
        
        if modelos_duplicados:
            if len(modelos_duplicados) == 1:
                flash(f'Modelo "{modelos_duplicados[0]}" já existe e foi ignorado.', 'warning')
            else:
                flash(f'{len(modelos_duplicados)} modelo(s) já existiam e foram ignorados: {", ".join(modelos_duplicados[:3])}{"..." if len(modelos_duplicados) > 3 else ""}', 'warning')
        
        if modelos_invalidos:
            flash(f'Erro ao cadastrar {len(modelos_invalidos)} modelo(s).', 'danger')
        
        if modelos_criados:
            return redirect(url_for('configuracoes.listar_modelos'))
        else:
            # Se nenhum foi criado, volta ao formulário
            return render_template('configuracoes/modelos/form.html',
                                   modelo=None, tipos=tipos, marcas_todas=marcas_todas,
                                   pre_tipo_id=tipo_id, pre_marca_id=marca_id)

    return render_template('configuracoes/modelos/form.html',
                           modelo=None, tipos=tipos, marcas_todas=marcas_todas,
                           pre_tipo_id=pre_tipo_id, pre_marca_id=pre_marca_id)


@configuracoes_bp.route('/lista-modelos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_modelo2(id):
    _exigir_admin()
    modelo      = Modelo.query.get_or_404(id)
    tipos       = TipoEquipamento.query.filter_by(ativo=True).order_by(TipoEquipamento.nome).all()
    marcas_todas = Marca.query.order_by(Marca.nome).all()

    if request.method == 'POST':
        tipo_id   = request.form.get('tipo_equipamento_id', type=int)
        marca_id  = request.form.get('marca_id', type=int)
        novo_nome = request.form.get('nome', '').strip()
        if not tipo_id or not marca_id or not novo_nome:
            flash('Preencha tipo de equipamento, marca e nome.', 'danger')
            return render_template('configuracoes/modelos/form.html',
                                   modelo=modelo, tipos=tipos, marcas_todas=marcas_todas,
                                   pre_tipo_id=tipo_id, pre_marca_id=marca_id)
        if Modelo.query.filter(
            Modelo.tipo_equipamento_id == tipo_id,
            Modelo.marca_id == marca_id,
            Modelo.nome == novo_nome,
            Modelo.id != id
        ).first():
            flash(f'Já existe o modelo "{novo_nome}" para este tipo e marca.', 'danger')
            return render_template('configuracoes/modelos/form.html',
                                   modelo=modelo, tipos=tipos, marcas_todas=marcas_todas,
                                   pre_tipo_id=tipo_id, pre_marca_id=marca_id)
        modelo.tipo_equipamento_id = tipo_id
        modelo.marca_id  = marca_id
        modelo.nome      = novo_nome
        db.session.commit()
        flash('Modelo atualizado!', 'success')
        return redirect(url_for('configuracoes.listar_modelos'))

    return render_template('configuracoes/modelos/form.html',
                           modelo=modelo, tipos=tipos, marcas_todas=marcas_todas,
                           pre_tipo_id=modelo.tipo_equipamento_id,
                           pre_marca_id=modelo.marca_id)


@configuracoes_bp.route('/lista-modelos/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_modelo2(id):
    _exigir_admin()
    modelo = Modelo.query.get_or_404(id)
    if modelo.equipamentos.count() > 0:
        flash(f'Não é possível excluir "{modelo.nome}" pois há equipamentos vinculados.', 'danger')
        return redirect(url_for('configuracoes.listar_modelos'))
    db.session.delete(modelo)
    db.session.commit()
    flash(f'Modelo "{modelo.nome}" excluído.', 'info')
    return redirect(url_for('configuracoes.listar_modelos'))


# ══════════════════════════════════════════════════════════
#  API JSON – selects encadeados Tipo → Marca → Modelo
# ══════════════════════════════════════════════════════════

@configuracoes_bp.route('/api/marcas-por-tipo/<int:tipo_id>')
@login_required
def api_marcas_por_tipo(tipo_id):
    """Retorna as marcas associadas a um tipo de equipamento."""
    tipo = TipoEquipamento.query.get_or_404(tipo_id)
    marcas = tipo.marcas.order_by(Marca.nome).all()
    return jsonify([{'id': m.id, 'nome': m.nome} for m in marcas])


@configuracoes_bp.route('/api/modelos-por-marca/<int:marca_id>')
@login_required
def api_modelos_por_marca(marca_id):
    """Retorna os modelos de uma marca, opcionalmente filtrados por tipo."""
    tipo_id = request.args.get('tipo_id', type=int)
    q = Modelo.query.filter_by(marca_id=marca_id)
    if tipo_id:
        q = q.filter_by(tipo_equipamento_id=tipo_id)
    modelos = q.order_by(Modelo.nome).all()
    return jsonify([{'id': m.id, 'nome': m.nome} for m in modelos])


# ══════════════════════════════════════════════════════════
#  PERFIS DE ACESSO
# ══════════════════════════════════════════════════════════

# Mapeamento legível de cada permissão
PERMISSOES_LABELS = {
    # Unidades
    'ver_todas_unidades':           ('Visualizar todas as unidades',          'Unidades'),
    'cadastrar_unidade':            ('Cadastrar nova unidade',                 'Unidades'),
    'editar_unidade':               ('Editar dados de unidade',                'Unidades'),
    'excluir_unidade':              ('Excluir/desativar unidade',              'Unidades'),
    # Salas
    'cadastrar_sala':               ('Cadastrar salas',                        'Salas'),
    'editar_sala':                  ('Editar salas',                           'Salas'),
    # Equipamentos
    'cadastrar_equipamento':        ('Cadastrar equipamentos',                 'Equipamentos'),
    'editar_equipamento':           ('Editar equipamentos',                    'Equipamentos'),
    'dar_baixa_equipamento':        ('Dar baixa em equipamentos',              'Equipamentos'),
    'gerenciar_tipos_equipamento':  ('Gerenciar tipos de equipamento',         'Equipamentos'),
    # Chamados
    'abrir_chamado':                ('Abrir chamados',                         'Chamados'),
    'editar_chamado':               ('Editar chamados',                        'Chamados'),
    'cancelar_chamado':             ('Cancelar chamados',                      'Chamados'),
    'fechar_chamado':               ('Fechar/concluir chamados',               'Chamados'),
    'ver_chamados_todos':           ('Ver chamados de todas as unidades',      'Chamados'),
    # Contratos
    'cadastrar_contrato':           ('Cadastrar contratos',                    'Contratos'),
    'editar_contrato':              ('Editar contratos',                       'Contratos'),
    # Pessoas e acesso
    'gerenciar_usuarios':           ('Gerenciar usuários do sistema',          'Usuários'),
    'vincular_profissionais':       ('Vincular profissionais a unidades',      'Usuários'),
    # Relatórios e visão
    'emitir_relatorios':            ('Emitir relatórios e inventários',        'Relatórios'),
    'ver_dashboard_geral':          ('Ver dashboard geral da rede',            'Relatórios'),
}

# Ordem em que os grupos aparecem na tela
GRUPOS_ORDEM = ['Unidades', 'Salas', 'Equipamentos', 'Chamados', 'Contratos', 'Usuários', 'Relatórios']


@configuracoes_bp.route('/perfis')
@login_required
def perfis():
    """Lista todos os perfis — Gestão de Perfis. Apenas administrador."""
    _exigir_gerenciar_perfis()
    return render_template('configuracoes/perfis_listar.html', perfis=PERFIS, hierarquia=HIERARQUIA)


@configuracoes_bp.route('/perfis/<codigo>/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil(codigo):
    """Edita permissões de um perfil — Ver, Editar, Adicionar por seção."""
    _exigir_gerenciar_perfis()
    if codigo not in PERFIS:
        abort(404)
    if codigo == 'administrador':
        flash('O perfil Administrador possui acesso total e não pode ser alterado.', 'info')
        return redirect(url_for('configuracoes.perfis'))

    if request.method == 'POST':
        for secao_key, _label, _icon, _pai in SECOES:
            row = PerfilPermissao.query.filter_by(perfil=codigo, secao=secao_key).first()
            if not row:
                row = PerfilPermissao(perfil=codigo, secao=secao_key)
                db.session.add(row)
            row.ver = request.form.get(f'{secao_key}_ver') == '1'
            row.editar = request.form.get(f'{secao_key}_editar') == '1'
            row.adicionar = request.form.get(f'{secao_key}_adicionar') == '1'
        db.session.commit()
        flash(f'Permissões do perfil "{PERFIS[codigo]}" atualizadas com sucesso!', 'success')
        return redirect(url_for('configuracoes.perfis'))

    # Carregar permissões atuais
    permissoes = PerfilPermissao.query.filter_by(perfil=codigo).all()
    perm_map = {p.secao: p for p in permissoes}
    return render_template('configuracoes/perfis_editar.html',
                          perfil_codigo=codigo,
                          perfil_label=PERFIS[codigo],
                          secoes=SECOES,
                          perm_map=perm_map,
                      )

# ══════════════════════════════════════════════════════════
#  CBOs (Códigos Brasileiros de Ocupação)
# ══════════════════════════════════════════════════════════

@configuracoes_bp.route('/cbos')
@login_required
def cbos():
    _exigir_admin()
    cbos_list = CBO.query.order_by(CBO.codigo).all()
    return render_template('configuracoes/cbos/listar.html', cbos=cbos_list)


@configuracoes_bp.route('/cbos/novo', methods=['GET', 'POST'])
@login_required
def novo_cbo():
    _exigir_admin()
    if request.method == 'POST':
        codigo = request.form['codigo'].strip()
        descricao = request.form['descricao'].strip()

        if not codigo or not descricao:
            flash('Código e descrição são obrigatórios.', 'danger')
            return render_template('configuracoes/cbos/form.html', cbo=None)

        if CBO.query.filter_by(codigo=codigo).first():
            flash(f'Já existe um CBO com o código "{codigo}".', 'danger')
            return render_template('configuracoes/cbos/form.html', cbo=None)

        cbo = CBO(
            codigo=codigo,
            descricao=descricao,
            ativo=request.form.get('ativo') == 'on',
        )
        db.session.add(cbo)
        db.session.commit()
        flash(f'CBO "{cbo.codigo} — {cbo.descricao}" cadastrado com sucesso!', 'success')
        return redirect(url_for('configuracoes.cbos'))
    return render_template('configuracoes/cbos/form.html', cbo=None)


@configuracoes_bp.route('/cbos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_cbo(id):
    _exigir_admin()
    cbo = CBO.query.get_or_404(id)
    if request.method == 'POST':
        novo_codigo = request.form['codigo'].strip()
        descricao = request.form['descricao'].strip()

        if not novo_codigo or not descricao:
            flash('Código e descrição são obrigatórios.', 'danger')
            return render_template('configuracoes/cbos/form.html', cbo=cbo)

        conflito = CBO.query.filter(
            CBO.codigo == novo_codigo,
            CBO.id != id
        ).first()
        if conflito:
            flash(f'Já existe outro CBO com o código "{novo_codigo}".', 'danger')
            return render_template('configuracoes/cbos/form.html', cbo=cbo)

        cbo.codigo = novo_codigo
        cbo.descricao = descricao
        cbo.ativo = request.form.get('ativo') == 'on'
        db.session.commit()
        flash('CBO atualizado!', 'success')
        return redirect(url_for('configuracoes.cbos'))
    return render_template('configuracoes/cbos/form.html', cbo=cbo)


@configuracoes_bp.route('/cbos/<int:id>/alternar-status', methods=['POST'])
@login_required
def alternar_status_cbo(id):
    _exigir_admin()
    cbo = CBO.query.get_or_404(id)
    cbo.ativo = not cbo.ativo
    db.session.commit()
    estado = 'ativado' if cbo.ativo else 'desativado'
    flash(f'CBO "{cbo.codigo}" {estado}.', 'info')
    return redirect(url_for('configuracoes.cbos'))


# ══════════════════════════════════════════════════════════
#  STATUS DE CHAMADOS
# ══════════════════════════════════════════════════════════

@configuracoes_bp.route('/status-chamados')
@login_required
def status_chamados():
    _exigir_admin()
    status = StatusChamado.query.order_by(StatusChamado.ordem).all()
    return render_template('configuracoes/status_chamados/listar.html',
                           status=status, badge_cores=BADGE_CORES)


@configuracoes_bp.route('/status-chamados/novo', methods=['GET', 'POST'])
@login_required
def novo_status_chamado():
    _exigir_admin()
    if request.method == 'POST':
        slug  = request.form.get('slug', '').strip().lower().replace(' ', '_')
        label = request.form.get('label', '').strip()
        badge_cor       = request.form.get('badge_cor', 'secondary')
        padrao_listagem = request.form.get('padrao_listagem') == '1'
        encerra_chamado = request.form.get('encerra_chamado') == '1'
        ordem = request.form.get('ordem', type=int) or 99

        if not slug or not label:
            flash('Slug e nome são obrigatórios.', 'danger')
        elif StatusChamado.query.filter_by(slug=slug).first():
            flash('Já existe um status com esse slug.', 'danger')
        else:
            db.session.add(StatusChamado(
                slug=slug, label=label, badge_cor=badge_cor,
                ativo=True, padrao_listagem=padrao_listagem,
                encerra_chamado=encerra_chamado, ordem=ordem,
            ))
            db.session.commit()
            flash(f'Status "{label}" criado com sucesso!', 'success')
            return redirect(url_for('configuracoes.status_chamados'))

    max_ordem = db.session.query(db.func.max(StatusChamado.ordem)).scalar() or 0
    return render_template('configuracoes/status_chamados/form.html',
                           status=None, badge_cores=BADGE_CORES,
                           proximo_ordem=max_ordem + 1)


@configuracoes_bp.route('/status-chamados/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_status_chamado(id):
    _exigir_admin()
    s = StatusChamado.query.get_or_404(id)
    if request.method == 'POST':
        s.label           = request.form.get('label', '').strip()
        s.badge_cor       = request.form.get('badge_cor', 'secondary')
        s.ativo           = request.form.get('ativo') == '1'
        s.padrao_listagem = request.form.get('padrao_listagem') == '1'
        s.encerra_chamado = request.form.get('encerra_chamado') == '1'
        s.ordem           = request.form.get('ordem', type=int) or s.ordem
        if not s.label:
            flash('O nome é obrigatório.', 'danger')
        else:
            db.session.commit()
            flash(f'Status "{s.label}" atualizado!', 'success')
            return redirect(url_for('configuracoes.status_chamados'))
    return render_template('configuracoes/status_chamados/form.html',
                           status=s, badge_cores=BADGE_CORES,
                           proximo_ordem=s.ordem)


@configuracoes_bp.route('/status-chamados/<int:id>/toggle-ativo', methods=['POST'])
@login_required
def toggle_status_chamado(id):
    _exigir_admin()
    s = StatusChamado.query.get_or_404(id)
    s.ativo = not s.ativo
    db.session.commit()
    flash(f'Status "{s.label}" {"ativado" if s.ativo else "desativado"}.', 'success')
    return redirect(url_for('configuracoes.status_chamados'))


@configuracoes_bp.route('/status-chamados/<int:id>/toggle-padrao', methods=['POST'])
@login_required
def toggle_padrao_status_chamado(id):
    _exigir_admin()
    s = StatusChamado.query.get_or_404(id)
    s.padrao_listagem = not s.padrao_listagem
    db.session.commit()
    flash(f'Status "{s.label}" {"marcado como" if s.padrao_listagem else "removido do"} padrão de listagem.', 'success')
    return redirect(url_for('configuracoes.status_chamados'))


# ══════════════════════════════════════════════════════════
#  AUDITORIA (apenas administrador)
# ══════════════════════════════════════════════════════════

@configuracoes_bp.route('/auditoria')
@login_required
def auditoria():
    _exigir_auditoria()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 200)
    filtro_acao = request.args.get('acao', '').strip()
    filtro_modulo = request.args.get('modulo', '').strip()
    filtro_usuario_id = request.args.get('usuario_id', type=int)
    filtro_endpoint = request.args.get('endpoint', '').strip()
    filtro_data_inicio = request.args.get('data_inicio', '').strip()
    filtro_data_fim = request.args.get('data_fim', '').strip()

    query = Auditoria.query
    if filtro_acao:
        query = query.filter(Auditoria.acao == filtro_acao)
    if filtro_modulo:
        query = query.filter(Auditoria.modulo == filtro_modulo)
    if filtro_usuario_id is not None:
        query = query.filter(Auditoria.usuario_id == filtro_usuario_id)
    if filtro_endpoint:
        query = query.filter(Auditoria.endpoint.ilike(f'%{filtro_endpoint}%'))
    if filtro_data_inicio:
        try:
            from datetime import datetime
            dt = datetime.strptime(filtro_data_inicio, '%Y-%m-%d')
            query = query.filter(Auditoria.created_at >= dt)
        except ValueError:
            pass
    if filtro_data_fim:
        try:
            from datetime import datetime, timedelta
            dt = datetime.strptime(filtro_data_fim, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Auditoria.created_at < dt)
        except ValueError:
            pass

    query = query.order_by(Auditoria.created_at.desc())
    paginacao = query.paginate(page=page, per_page=per_page, error_out=False)
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    return render_template('configuracoes/auditoria/listar.html',
                           registros=paginacao.items,
                           paginacao=paginacao,
                           acao_opcoes=ACAO_OPCOES,
                           modulo_opcoes=MODULO_OPCOES,
                           usuarios=usuarios,
                           filtros={
                               'acao': filtro_acao,
                               'modulo': filtro_modulo,
                               'usuario_id': filtro_usuario_id,
                               'endpoint': filtro_endpoint,
                               'data_inicio': filtro_data_inicio,
                               'data_fim': filtro_data_fim,
                           })

