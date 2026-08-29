"""Gestão - Quadro de Avisos etc. Apenas perfil Administrador."""
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from flask_login import login_required, current_user

from app import db
from app.models.aviso import Aviso

gestao_bp = Blueprint('gestao', __name__, url_prefix='/gestao')

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif'}


def _exigir_admin():
    if not current_user.pode('configuracoes'):
        flash('Acesso negado. Apenas o perfil Administrador pode acessar Gestão.', 'warning')
        return redirect(url_for('dashboard.index'))


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _upload_folder():
    base = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.instance_path, 'uploads')
    avisos_dir = os.path.join(base, 'avisos')
    os.makedirs(avisos_dir, exist_ok=True)
    return avisos_dir


@gestao_bp.before_request
@login_required
def before_request():
    _exigir_admin()


@gestao_bp.route('/quadro-avisos')
def quadro_avisos():
    """Lista avisos para gestão."""
    itens = Aviso.query.order_by(Aviso.ordem, Aviso.atualizado_em.desc()).all()
    return render_template('gestao/quadro_avisos_listar.html', itens=itens)


@gestao_bp.route('/quadro-avisos/novo', methods=['GET', 'POST'], defaults={'id': None})
@gestao_bp.route('/quadro-avisos/<int:id>/editar', methods=['GET', 'POST'])
def quadro_aviso_form(id):
    """Formulário de criar/editar aviso."""
    item = Aviso.query.get(id) if id else None
    if request.method == 'POST':
        if not item:
            item = Aviso()
            item.criado_por_id = current_user.id
            db.session.add(item)
        item.titulo = request.form.get('titulo', '').strip()
        item.mensagem = request.form.get('mensagem', '').strip() or None
        item.ativo = request.form.get('ativo') == 'on'

        f = request.files.get('anexo')
        if f and f.filename:
            if _allowed_file(f.filename):
                ext = f.filename.rsplit('.', 1)[1].lower()
                fn = secure_filename(f'{uuid.uuid4().hex}.{ext}')
                folder = _upload_folder()
                f.save(os.path.join(folder, fn))
                if item.anexo:
                    try:
                        os.remove(os.path.join(folder, item.anexo))
                    except OSError:
                        pass
                item.anexo = fn
            else:
                flash(f'Tipo de arquivo não permitido. Use: {", ".join(ALLOWED_EXTENSIONS)}', 'warning')

        if request.form.get('remover_anexo') == '1' and item.anexo:
            try:
                os.remove(os.path.join(_upload_folder(), item.anexo))
            except OSError:
                pass
            item.anexo = None

        db.session.commit()
        flash('Aviso salvo!', 'success')
        return redirect(url_for('gestao.quadro_avisos'))
    return render_template('gestao/quadro_aviso_form.html', item=item)


@gestao_bp.route('/quadro-avisos/<int:id>/excluir', methods=['POST'])
def quadro_aviso_excluir(id):
    item = Aviso.query.get_or_404(id)
    if item.anexo:
        try:
            os.remove(os.path.join(_upload_folder(), item.anexo))
        except OSError:
            pass
    db.session.delete(item)
    db.session.commit()
    flash('Aviso excluído.', 'success')
    return redirect(url_for('gestao.quadro_avisos'))


@gestao_bp.route('/quadro-avisos/anexo/<filename>')
def quadro_aviso_anexo(filename):
    """Serve arquivo anexo."""
    folder = _upload_folder()
    return send_from_directory(folder, filename, as_attachment=True)
