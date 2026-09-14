from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.predio import Predio
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.models.identidade import cidade_padrao

predios_bp = Blueprint('predios', __name__, url_prefix='/configuracoes/predios')


def _exigir_admin():
    if not current_user.pode('cadastrar_predio'):
        abort(403)


# ──────────────────────────────────────────────
#  LISTAR
# ──────────────────────────────────────────────
@predios_bp.route('/')
@login_required
def listar():
    if not current_user.pode('ver_predios') and not current_user.pode('cadastrar_predio'):
        abort(403)
    predios = Predio.query.order_by(Predio.nome).all()
    return render_template('predios/listar.html', predios=predios)


# ──────────────────────────────────────────────
#  DETALHE
# ──────────────────────────────────────────────
@predios_bp.route('/<int:id>')
@login_required
def detalhe(id):
    if not current_user.pode('ver_predios') and not current_user.pode('cadastrar_predio'):
        abort(403)
    from app.models.chamado import Chamado
    predio = Predio.query.get_or_404(id)
    unidades = predio.unidades.filter_by(status='ativa').order_by(Unidade.nome).all()
    # Chamados prediais vinculados ao prédio
    chamados_prediais = Chamado.query.filter_by(
        predio_id=id, tipo_chamado='predial'
    ).order_by(Chamado.criado_em.desc()).limit(20).all()
    return render_template('predios/detalhe.html',
                           predio=predio,
                           unidades=unidades,
                           chamados_prediais=chamados_prediais)


# ──────────────────────────────────────────────
#  NOVO
# ──────────────────────────────────────────────
@predios_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    _exigir_admin()
    usuarios = Usuario.query.filter(
        Usuario.ativo == True,
        Usuario.perfil != 'administrador'
    ).order_by(Usuario.nome).all()

    if request.method == 'POST':
        predio = Predio(
            nome=request.form['nome'].strip(),
            endereco=request.form.get('endereco', '').strip() or None,
            numero=request.form.get('numero', '').strip() or None,
            complemento=request.form.get('complemento', '').strip() or None,
            bairro=request.form.get('bairro', '').strip() or None,
            cidade=request.form.get('cidade', '').strip() or cidade_padrao(),
            uf=request.form.get('uf', 'SP').strip(),
            cep=request.form.get('cep', '').strip() or None,
            telefone=request.form.get('telefone', '').strip() or None,
            link_maps=request.form.get('link_maps', '').strip() or None,
            latitude=request.form.get('latitude', type=float),
            longitude=request.form.get('longitude', type=float),
            responsavel_predial_id=request.form.get('responsavel_predial_id', type=int) or None,
            observacoes=request.form.get('observacoes', '').strip() or None,
        )
        db.session.add(predio)
        db.session.commit()
        from app.routes.relatorios import invalidate_mapa_saude_payload_cache
        invalidate_mapa_saude_payload_cache()
        flash(f'Prédio "{predio.nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('predios.detalhe', id=predio.id))

    return render_template('predios/form.html', predio=None, usuarios=usuarios)


# ──────────────────────────────────────────────
#  EDITAR
# ──────────────────────────────────────────────
@predios_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    _exigir_admin()
    predio = Predio.query.get_or_404(id)
    usuarios = Usuario.query.filter(
        Usuario.ativo == True,
        Usuario.perfil != 'administrador'
    ).order_by(Usuario.nome).all()

    if request.method == 'POST':
        predio.nome = request.form['nome'].strip()
        predio.endereco = request.form.get('endereco', '').strip() or None
        predio.numero = request.form.get('numero', '').strip() or None
        predio.complemento = request.form.get('complemento', '').strip() or None
        predio.bairro = request.form.get('bairro', '').strip() or None
        predio.cidade = request.form.get('cidade', '').strip() or cidade_padrao()
        predio.uf = request.form.get('uf', 'SP').strip()
        predio.cep = request.form.get('cep', '').strip() or None
        predio.telefone  = request.form.get('telefone', '').strip() or None
        predio.link_maps = request.form.get('link_maps', '').strip() or None
        predio.latitude = request.form.get('latitude', type=float)
        predio.longitude = request.form.get('longitude', type=float)
        predio.responsavel_predial_id = request.form.get('responsavel_predial_id', type=int) or None
        predio.observacoes = request.form.get('observacoes', '').strip() or None
        db.session.commit()
        from app.routes.relatorios import invalidate_mapa_saude_payload_cache
        invalidate_mapa_saude_payload_cache()
        flash('Prédio atualizado com sucesso!', 'success')
        return redirect(url_for('predios.detalhe', id=predio.id))

    return render_template('predios/form.html', predio=predio, usuarios=usuarios)


# ──────────────────────────────────────────────
#  DESATIVAR
# ──────────────────────────────────────────────
@predios_bp.route('/<int:id>/desativar', methods=['POST'])
@login_required
def desativar(id):
    _exigir_admin()
    predio = Predio.query.get_or_404(id)
    predio.ativo = False
    db.session.commit()
    flash(f'Prédio "{predio.nome}" desativado.', 'info')
    return redirect(url_for('predios.listar'))
