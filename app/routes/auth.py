from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
import os, uuid, mimetypes
from app import db
from app.models.usuario import Usuario
from app.models.notificacao import Notificacao
from app.models.unidade import Unidade

auth_bp = Blueprint('auth', __name__)

_UPLOAD_PERFIS = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                               'static', 'uploads', 'perfis')


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        from app.models.identidade import completar_email
        email = completar_email(request.form.get('email', ''))
        senha = request.form.get('senha', '')
        lembrar = request.form.get('lembrar') == 'on'

        usuario = Usuario.query.filter_by(email=email, ativo=True).first()
        if usuario and usuario.check_senha(senha):
            login_user(usuario, remember=lembrar)
            proxima = request.args.get('next')
            flash(f'Bem-vindo, {usuario.nome.split()[0]}!', 'success')
            return redirect(proxima or url_for('dashboard.index'))
        flash('E-mail ou senha inválidos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/unidade-padrao', methods=['POST'])
@login_required
def definir_unidade_padrao():
    """Define a unidade padrão do usuário. Apenas unidades vinculadas (opção 'Todas' removida)."""
    unidade_id = request.form.get('unidade_id')
    if unidade_id == '' or unidade_id is None:
        # Sempre define a primeira unidade vinculada (opção "Todas" não existe mais)
        up = getattr(current_user, 'unidade_principal', None)
        if up:
            current_user.unidade_padrao_id = up.id
            db.session.commit()
            flash(f'Unidade padrão definida: {up.nome}.', 'success')
        else:
            flash('Você não possui unidade ativa vinculada.', 'danger')
    else:
        try:
            uid = int(unidade_id)
        except (ValueError, TypeError):
            flash('Unidade inválida.', 'danger')
            return redirect(url_for('dashboard.index'))
        un = Unidade.query.get(uid)
        if not un or un.status != 'ativa':
            flash('Unidade não encontrada.', 'danger')
            return redirect(url_for('dashboard.index'))
        ids = [uu.unidade_id for uu in current_user.unidades.filter_by(ativo=True).all()]
        if uid not in ids:
            flash('Você não está vinculado a essa unidade.', 'danger')
            return redirect(url_for('dashboard.index'))
        current_user.unidade_padrao_id = uid
        db.session.commit()
        flash(f'Unidade padrão definida: {un.nome}.', 'success')
    return redirect(url_for('dashboard.index'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        acao = request.form.get('acao', 'dados')

        if acao == 'foto':
            foto = request.files.get('foto')
            if foto and foto.filename:
                mime = foto.mimetype or mimetypes.guess_type(foto.filename)[0] or ''
                if not mime.startswith('image/'):
                    flash('Apenas imagens são permitidas.', 'danger')
                    return redirect(url_for('auth.perfil'))
                ext = os.path.splitext(foto.filename)[1].lower() or '.jpg'
                filename = f"{uuid.uuid4().hex}{ext}"
                os.makedirs(_UPLOAD_PERFIS, exist_ok=True)
                foto.save(os.path.join(_UPLOAD_PERFIS, filename))
                # Remove foto antiga se existir
                if current_user.foto_perfil:
                    try:
                        os.remove(os.path.join(_UPLOAD_PERFIS, current_user.foto_perfil))
                    except OSError:
                        pass
                current_user.foto_perfil = filename
                db.session.commit()
                flash('Foto atualizada com sucesso!', 'success')
            return redirect(url_for('auth.perfil'))

        if acao == 'remover_foto':
            if current_user.foto_perfil:
                try:
                    os.remove(os.path.join(_UPLOAD_PERFIS, current_user.foto_perfil))
                except OSError:
                    pass
                current_user.foto_perfil = None
                db.session.commit()
                flash('Foto removida.', 'success')
            return redirect(url_for('auth.perfil'))

        # acao == 'dados'
        nome = request.form.get('nome', '').strip()
        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')

        if nome:
            current_user.nome = nome

        if senha_atual and nova_senha:
            if current_user.check_senha(senha_atual):
                current_user.set_senha(nova_senha)
                flash('Senha alterada com sucesso.', 'success')
            else:
                flash('Senha atual incorreta.', 'danger')
                return redirect(url_for('auth.perfil'))

        db.session.commit()
        flash('Perfil atualizado com sucesso.', 'success')
        return redirect(url_for('auth.perfil'))

    notificacoes = (Notificacao.query
                    .filter_by(usuario_id=current_user.id)
                    .order_by(Notificacao.criado_em.desc())
                    .limit(50).all())
    from app.sis_consulta import configurado as sis_configurado
    return render_template(
        'auth/perfil.html',
        notificacoes=notificacoes,
        sis_ok=sis_configurado(),
    )


@auth_bp.route('/perfil/consultar-sis', methods=['POST'])
@login_required
def consultar_sis_perfil():
    from app.sis_profissional import consultar_cadastro_sis
    cpf = (current_user.cpf or '').strip()
    if not cpf:
        return jsonify(
            ok=False,
            erro='Seu cadastro no SIGUS ainda não tem CPF. Peça à coordenação para completar ou abra um chamado.',
        ), 400
    try:
        return jsonify(consultar_cadastro_sis(cpf))
    except ValueError as exc:
        return jsonify(ok=False, erro=str(exc)), 400
    except Exception as exc:
        return jsonify(ok=False, erro=str(exc) or 'Não foi possível consultar o SIS.'), 502
