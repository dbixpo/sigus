import unicodedata

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.sala import Sala
from app.models.tipo_sala import TipoSala
from app.models.unidade import Unidade

salas_bp = Blueprint('salas', __name__, url_prefix='/salas')


@salas_bp.route('/cadastro-externo', methods=['GET', 'POST'])
def cadastro_externo():
    """Cadastro externo de salas por unidade (sem login)."""
    unidades = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    tipos = TipoSala.query.filter_by(ativo=True).order_by(TipoSala.nome).all()

    if request.method == 'POST':
        unidade_id = request.form.get('unidade_id', type=int)
        sala_id = request.form.get('sala_id', type=int)
        nome = (request.form.get('nome') or '').strip()
        tipo_sala_id = request.form.get('tipo_sala_id', type=int) or None
        tipo_obj = TipoSala.query.get(tipo_sala_id) if tipo_sala_id else None
        responsavel = (request.form.get('responsavel') or '').strip()
        capacidade_maxima = request.form.get('capacidade_maxima', type=int)
        ramal = (request.form.get('ramal') or '').strip()
        observacoes = (request.form.get('observacoes') or '').strip()

        unidade = Unidade.query.get(unidade_id) if unidade_id else None
        if not unidade or unidade.status != 'ativa':
            flash('Selecione uma unidade válida para continuar.', 'danger')
            return redirect(url_for('salas.cadastro_externo'))

        if not nome:
            flash('Informe o nome da sala.', 'danger')
            return redirect(url_for('salas.cadastro_externo', unidade_id=unidade_id))

        if not tipo_obj or not getattr(tipo_obj, 'ativo', True):
            flash('Selecione um tipo de sala válido.', 'danger')
            return redirect(url_for('salas.cadastro_externo', unidade_id=unidade_id))

        if capacidade_maxima is None or capacidade_maxima < 0:
            flash('Informe a capacidade máxima de pessoas (0 ou mais).', 'danger')
            return redirect(url_for('salas.cadastro_externo', unidade_id=unidade_id))

        if sala_id:
            sala = Sala.query.get_or_404(sala_id)
            if sala.unidade_id != unidade_id:
                flash('A sala selecionada não pertence à unidade informada.', 'danger')
                return redirect(url_for('salas.cadastro_externo', unidade_id=unidade_id))
            sala.nome = nome
            sala.tipo = tipo_obj.nome if tipo_obj else (request.form.get('tipo') or sala.tipo)
            sala.tipo_sala_id = tipo_sala_id
            sala.responsavel = responsavel
            sala.capacidade_maxima = capacidade_maxima
            sala.ramal = ramal
            sala.observacoes = observacoes
            db.session.commit()
            flash(f'Sala "{sala.nome}" atualizada com sucesso!', 'success')
        else:
            sala = Sala(
                unidade_id=unidade_id,
                nome=nome,
                tipo=tipo_obj.nome if tipo_obj else request.form.get('tipo', ''),
                tipo_sala_id=tipo_sala_id,
                responsavel=responsavel,
                capacidade_maxima=capacidade_maxima,
                ramal=ramal,
                observacoes=observacoes,
            )
            db.session.add(sala)
            db.session.commit()
            flash(f'Sala "{sala.nome}" cadastrada com sucesso!', 'success')

        return redirect(url_for('salas.cadastro_externo', unidade_id=unidade_id))

    unidade_id = request.args.get('unidade_id', type=int)
    edit_id = request.args.get('edit_id', type=int)
    unidade = Unidade.query.get(unidade_id) if unidade_id else None
    salas = []
    sala_edicao = None

    if unidade and unidade.status == 'ativa':
        salas = (
            Sala.query
            .filter_by(unidade_id=unidade.id, ativo=True)
            .order_by(Sala.nome.asc())
            .all()
        )
        if edit_id:
            sala_edicao = Sala.query.filter_by(id=edit_id, unidade_id=unidade.id, ativo=True).first()
            if not sala_edicao:
                flash('Sala para edição não encontrada nesta unidade.', 'warning')

    return render_template(
        'salas/cadastro_externo.html',
        unidades=unidades,
        tipos=tipos,
        unidade=unidade,
        unidade_id=unidade_id,
        salas=salas,
        sala_edicao=sala_edicao,
    )


@salas_bp.route('/api/unidades', methods=['GET'])
def api_unidades():
    """Busca de unidades ativas para o live search (sem login)."""
    q = (request.args.get('q') or '').strip()
    limit = request.args.get('limit', default=30, type=int)
    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50

    query = Unidade.query.filter_by(status='ativa')
    if q:
        query = query.filter(Unidade.nome.ilike(f'%{q}%'))

    unidades = query.order_by(Unidade.nome.asc()).limit(limit).all()
    # Ordenação final consistente (case/acentos) para o dropdown
    def _sort_key(nome: str) -> str:
        base = unicodedata.normalize("NFKD", (nome or ""))
        sem_acentos = "".join(ch for ch in base if not unicodedata.combining(ch))
        return sem_acentos.casefold()

    unidades = sorted(unidades, key=lambda u: _sort_key(u.nome))
    return {
        "items": [{"id": u.id, "nome": u.nome} for u in unidades],
        "q": q,
        "limit": limit,
    }


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
        if not tipo_obj or not getattr(tipo_obj, 'ativo', True):
            flash('Selecione um tipo de sala válido.', 'danger')
            return redirect(url_for('salas.nova', unidade_id=unidade_id))
        capacidade_maxima = request.form.get('capacidade_maxima', type=int)
        if capacidade_maxima is None or capacidade_maxima < 0:
            flash('Informe a capacidade máxima de pessoas (0 ou mais).', 'danger')
            return redirect(url_for('salas.nova', unidade_id=unidade_id))
        sala = Sala(
            unidade_id=unidade_id,
            nome=request.form['nome'].strip(),
            tipo=tipo_obj.nome if tipo_obj else request.form.get('tipo', ''),
            tipo_sala_id=tipo_sala_id,
            responsavel=request.form.get('responsavel', '').strip(),
            capacidade_maxima=capacidade_maxima,
            ramal=request.form.get('ramal', '').strip(),
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
        if not tipo_obj or not getattr(tipo_obj, 'ativo', True):
            flash('Selecione um tipo de sala válido.', 'danger')
            return redirect(url_for('salas.editar', id=id))
        capacidade_maxima = request.form.get('capacidade_maxima', type=int)
        if capacidade_maxima is None or capacidade_maxima < 0:
            flash('Informe a capacidade máxima de pessoas (0 ou mais).', 'danger')
            return redirect(url_for('salas.editar', id=id))
        sala.nome = request.form['nome'].strip()
        sala.tipo = tipo_obj.nome if tipo_obj else request.form.get('tipo', sala.tipo)
        sala.tipo_sala_id = tipo_sala_id
        sala.responsavel = request.form.get('responsavel', '').strip()
        sala.capacidade_maxima = capacidade_maxima
        sala.ramal = request.form.get('ramal', '').strip()
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
