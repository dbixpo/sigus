import os
import uuid
import mimetypes

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, Response, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse

from app import db
from app.models.usuario import Usuario, PERFIS

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/manifest.webmanifest')
def manifest_webmanifest():
    """Web App Manifest para instalação como PWA."""
    # Ícone PWA: prefira favicon; fallback para logo SVG
    icon_fn = 'img/samu-favicon.png'
    favicon_path = os.path.join(current_app.static_folder or '', 'img', 'samu-favicon.png')
    if not os.path.isfile(favicon_path):
        icon_fn = 'img/samu-logo.svg'
    icon_url = url_for('static', filename=icon_fn, _external=True)
    icon_type = 'image/svg+xml' if icon_fn.endswith('.svg') else 'image/png'
    start_url = url_for('auth.index', _external=True)
    return Response(
        jsonify({
            'name': 'Sistema SAMU 192',
            'short_name': 'SAMU',
            'description': 'Serviço de Atendimento Móvel de Urgência',
            'start_url': start_url,
            'scope': '/',
            'display': 'standalone',
            'background_color': '#c20d2f',
            'theme_color': '#c20d2f',
            'orientation': 'portrait-primary',
            'icons': [
                {'src': icon_url, 'sizes': '192x192', 'type': icon_type, 'purpose': 'any'},
                {'src': icon_url, 'sizes': '512x512', 'type': icon_type, 'purpose': 'any'}
            ]
        }).get_data(as_text=True),
        mimetype='application/manifest+json',
        headers={'Cache-Control': 'public, max-age=86400'}
    )


@auth_bp.route('/sw.js')
def sw():
    """Service Worker — necessário para o prompt de instalação no Chrome/Android."""
    # Script inline para não depender de arquivo estático (evita problema de escopo)
    script = '''// Service Worker SAMU - PWA
const CACHE = 'samu-v1';
self.addEventListener('install', function(e) {
  e.waitUntil(caches.open(CACHE).then(function(c) {
    return c.addAll([]);
  }).then(function() { return self.skipWaiting(); }));
});
self.addEventListener('activate', function(e) {
  e.waitUntil(caches.keys().then(function(keys) {
    return Promise.all(keys.filter(function(k) { return k !== CACHE; }).map(function(k) { return caches.delete(k); }));
  }).then(function() { return self.clients.claim(); }));
});
self.addEventListener('fetch', function(e) { e.respondWith(fetch(e.request)); });
'''
    return Response(script, mimetype='application/javascript', headers={'Service-Worker-Allowed': '/'})


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
        usuario_acesso = request.form.get('usuario', '').strip().lower()
        senha = request.form.get('senha', '')

        usuario = Usuario.query.filter_by(usuario=usuario_acesso, ativo=True).first()
        if usuario and usuario.check_senha(senha):
            # remember=False: login encerra ao fechar o navegador (sem cookie persistente)
            login_user(usuario, remember=False)
            proxima = request.args.get('next')
            # Segurança: só redireciona para URL relativa (evita open redirect)
            if proxima:
                p = urlparse(proxima)
                if p.netloc or (p.path and not p.path.startswith('/')):
                    proxima = None
            return redirect(proxima or url_for('dashboard.index'))
        flash('Usuário ou senha inválidos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Página do usuário: foto, dados pessoais, alterar senha (como SIGUS)."""
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
                upload_dir = os.path.join(current_app.static_folder, 'uploads', 'perfis')
                os.makedirs(upload_dir, exist_ok=True)
                foto.save(os.path.join(upload_dir, filename))
                if current_user.foto_perfil:
                    try:
                        old_path = os.path.join(upload_dir, current_user.foto_perfil)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except OSError:
                        pass
                current_user.foto_perfil = filename
                db.session.commit()
            return redirect(url_for('auth.perfil'))

        if acao == 'remover_foto':
            if current_user.foto_perfil:
                upload_dir = os.path.join(current_app.static_folder, 'uploads', 'perfis')
                try:
                    old_path = os.path.join(upload_dir, current_user.foto_perfil)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                except OSError:
                    pass
                current_user.foto_perfil = None
                db.session.commit()
            return redirect(url_for('auth.perfil'))

        # acao == 'dados'
        nome = request.form.get('nome', '').strip()
        apelido = request.form.get('apelido', '').strip() or None
        email = request.form.get('email', '').strip().lower() or None
        whatsapp = request.form.get('whatsapp', '').strip() or None

        if nome:
            current_user.nome = nome
        current_user.apelido = apelido
        if email is not None:
            # Verifica conflito de e-mail com outro usuário
            outro = Usuario.query.filter(Usuario.email == email, Usuario.id != current_user.id).first()
            if outro:
                flash('Este e-mail já está em uso por outro usuário.', 'danger')
                return redirect(url_for('auth.perfil'))
            current_user.email = email
        if whatsapp is not None:
            # Remove caracteres não numéricos para salvar
            current_user.whatsapp = ''.join(c for c in whatsapp if c.isdigit()) if whatsapp else None

        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')

        if senha_atual and nova_senha:
            if current_user.check_senha(senha_atual):
                current_user.set_senha(nova_senha)
            else:
                flash('Senha atual incorreta.', 'danger')
                return redirect(url_for('auth.perfil'))

        db.session.commit()
        return redirect(url_for('auth.perfil'))

    return render_template('auth/perfil.html')


@auth_bp.route('/trocar-perfil')
@login_required
def trocar_perfil():
    """Alterna o perfil ativo (em sessão) quando o usuário tem múltiplos perfis."""
    perfil = request.args.get('perfil', '').strip()
    if perfil == 'administrador' and not current_user.pode('configuracoes'):
        flash('Apenas administrador pode assumir esse perfil.', 'warning')
        return redirect(request.referrer or url_for('dashboard.index'))
    if perfil in PERFIS and perfil in current_user.perfis_list:
        session['perfil_ativo'] = perfil
    return redirect(request.referrer or url_for('dashboard.index'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    resp = redirect(url_for('auth.login'))
    # Limpa cookie "Lembrar-me" antigo (caso exista de versão anterior)
    cookie_path = current_app.config.get('APPLICATION_ROOT') or '/'
    resp.delete_cookie('remember_token', path=cookie_path)
    return resp
