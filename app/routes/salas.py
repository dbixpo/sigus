from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.sala import Sala
from app.models.tipo_sala import TipoSala
from app.models.unidade import Unidade

salas_bp = Blueprint('salas', __name__, url_prefix='/salas')


@salas_bp.route('/nova/<int:unidade_id>', methods=['GET', 'POST'])
@login_required
def nova(unidade_id):
    if not current_user.pode('cadastrar_sala'):
        abort(403)
    unidade = Unidade.query.get_or_404(unidade_id)
    tipos = TipoSala.query.filter_by(ativo=True).order_by(TipoSala.nome).all()
    if request.method == 'POST':
        tipo_sala_id = request.form.get('tipo_sala_id', type=int) or None
        tipo_obj = TipoSala.query.get(tipo_sala_id) if tipo_sala_id else None
        sala = Sala(
            unidade_id=unidade_id,
            nome=request.form['nome'].strip(),
            tipo=tipo_obj.nome if tipo_obj else request.form.get('tipo', ''),
            tipo_sala_id=tipo_sala_id,
            responsavel=request.form.get('responsavel', '').strip(),
            ramal=request.form.get('ramal', '').strip() or None,
            observacoes=request.form.get('observacoes', '').strip(),
        )
        db.session.add(sala)
        db.session.commit()
        flash(f'Sala "{sala.nome}" cadastrada com sucesso!', 'success')
        return redirect(url_for('unidades.detalhe', id=unidade_id))
    return render_template('salas/form.html', sala=None, unidade=unidade, tipos=tipos)


@salas_bp.route('/<int:id>')
@login_required
def detalhe(id):
    from app.models.chamado import Chamado
    sala = Sala.query.get_or_404(id)
    equipamentos = sala.equipamentos.filter_by(ativo=True).order_by('id').all()
    # Chamados vinculados diretamente à sala OU a equipamentos dela
    ids_equip = [e.id for e in equipamentos]
    chamados_sala = Chamado.query.filter(
        db.or_(
            Chamado.sala_id == id,
            Chamado.equipamento_id.in_(ids_equip) if ids_equip else db.false()
        )
    ).order_by(Chamado.criado_em.desc()).limit(20).all()
    return render_template('salas/detalhe.html', sala=sala, equipamentos=equipamentos,
                           chamados_sala=chamados_sala)


@salas_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.pode('editar_sala'):
        abort(403)
    sala = Sala.query.get_or_404(id)
    tipos = TipoSala.query.filter_by(ativo=True).order_by(TipoSala.nome).all()
    if request.method == 'POST':
        tipo_sala_id = request.form.get('tipo_sala_id', type=int) or None
        tipo_obj = TipoSala.query.get(tipo_sala_id) if tipo_sala_id else None
        sala.nome = request.form['nome'].strip()
        sala.tipo = tipo_obj.nome if tipo_obj else request.form.get('tipo', sala.tipo)
        sala.tipo_sala_id = tipo_sala_id
        sala.responsavel = request.form.get('responsavel', '').strip()
        sala.ramal = request.form.get('ramal', '').strip() or None
        sala.observacoes = request.form.get('observacoes', '').strip()
        db.session.commit()
        flash('Sala atualizada com sucesso!', 'success')
        return redirect(url_for('salas.detalhe', id=sala.id))
    return render_template('salas/form.html', sala=sala, unidade=sala.unidade, tipos=tipos)


@salas_bp.route('/<int:id>/desativar', methods=['POST'])
@login_required
def desativar(id):
    if not current_user.pode('editar_sala'):
        abort(403)
    sala = Sala.query.get_or_404(id)
    unidade_id = sala.unidade_id
    sala.ativo = False
    db.session.commit()
    flash(f'Sala "{sala.nome}" desativada.', 'info')
    return redirect(url_for('unidades.detalhe', id=unidade_id))
