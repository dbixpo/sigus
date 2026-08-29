import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


class SubpathMiddleware:
    """Define SCRIPT_NAME para app em subpath (ex: /samu) atrás de proxy reverso."""
    def __init__(self, app, subpath):
        self.app = app
        self.subpath = subpath.rstrip('/') if subpath else ''

    def __call__(self, environ, start_response):
        if self.subpath:
            environ['SCRIPT_NAME'] = self.subpath
            path = environ.get('PATH_INFO', '')
            if path.startswith(self.subpath):
                environ['PATH_INFO'] = path[len(self.subpath):] or '/'
        return self.app(environ, start_response)


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faça login para acessar o sistema.'
    login_manager.login_message_category = 'warning'

    # Proteção global: TUDO exige login, exceto login e arquivos estáticos.
    # Assim, mesmo que alguém tenha o link direto, sem usuário/senha não acessa.
    from flask import request, redirect, url_for
    @app.before_request
    def _exigir_login_global():
        from flask_login import current_user
        # Permitir apenas: página de login e arquivos estáticos
        if request.endpoint in ('auth.index', 'auth.login', 'auth.manifest_webmanifest', 'auth.sw', 'static', 'assets.static'):
            return None
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.full_path))

    # Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.atendimento import atendimento_bp
    from app.routes.configuracoes import configuracoes_bp
    from app.routes.rh import rh_bp
    from app.routes.gestao import gestao_bp

    app.register_blueprint(auth_bp)
    assets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
    from flask import Blueprint
    assets_bp = Blueprint('assets', __name__, static_folder=assets_path, static_url_path='/assets')
    app.register_blueprint(assets_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(atendimento_bp)
    app.register_blueprint(configuracoes_bp)
    app.register_blueprint(rh_bp)
    app.register_blueprint(gestao_bp)

    # Filtros Jinja2
    from app.utils import registrar_filtros
    registrar_filtros(app)

    # Context processor: PERFIS, perfil_ativo e navbar_user
    # navbar_user: carregado diretamente da sessão (user_id) para evitar que
    # Usuario.query.all() em telas de configuração altere o objeto exibido na navbar
    from flask import session
    from app.models.usuario import Usuario, PERFIS
    @app.context_processor
    def inject_perfis():
        from flask_login import current_user
        perfil_ativo = None
        user_id = session.get('_user_id')
        navbar_user = current_user
        if user_id:
            try:
                u = db.session.get(Usuario, int(user_id))
                if u:
                    navbar_user = u
            except (ValueError, TypeError):
                pass
        if current_user.is_authenticated:
            perfil_ativo = session.get('perfil_ativo') or (current_user.perfil_primario if hasattr(current_user, 'perfil_primario') else current_user.perfil)
        from datetime import date
        from app.models.feriado import Feriado
        feriado_hoje = Feriado.query.filter_by(data=date.today(), ativo=True).first() if current_user.is_authenticated else None
        return dict(perfis=PERFIS, perfil_ativo=perfil_ativo, navbar_user=navbar_user, feriado_hoje=feriado_hoje)

    # User loader
    login_manager.user_loader(lambda uid: db.session.get(Usuario, int(uid)))

    # Evita cache de páginas autenticadas (fix: nome/foto trocando para outro usuário)
    @app.after_request
    def no_cache_se_autenticado(response):
        from flask_login import current_user
        if current_user.is_authenticated:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    # Comando CLI: flask seed-tipos-motivos
    @app.cli.command('seed-tipos-motivos')
    def cmd_seed_tipos_motivos():
        """Cadastra tipos e motivos de ocorrência padrão."""
        from app.seed_tipos_motivos import run_seed
        r = run_seed(app)
        print(f"Tipos: {r['tipos']}. Motivos criados: {r['motivos_criados']}.")

    # Comando CLI: flask seed-intercorrencias
    @app.cli.command('seed-intercorrencias')
    def cmd_seed_intercorrencias():
        """Cadastra intercorrências padrão."""
        from app.seed_intercorrencias import run_seed
        r = run_seed(app)
        print(f"Intercorrências criadas: {r}.")

    # Comando CLI: flask cid-import
    @app.cli.command('cid-import')
    def cmd_cid_import():
        """Importa CID-10 e CID-O dos XML em assets/references/CID10XML/"""
        from app.cid10_import import importar_todos
        r = importar_todos(app)
        if r['erros']:
            for e in r['erros']:
                print(f"ERRO: {e}")
        else:
            c10, co = r['cid10'], r['cido']
            print(f"CID-10: {c10['novos']} novos, {c10['atualizados']} atualizados")
            print(f"CID-O:  {co['novos']} novos, {co['atualizados']} atualizados")
            print("Importação concluída.")

    # Proxy reverso (IIS etc.): X-Forwarded-For, X-Forwarded-Proto
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    # Subpath (ex: /samu em saudedigital.../samu)
    app_root = app.config.get('APPLICATION_ROOT')
    if app_root:
        app.wsgi_app = SubpathMiddleware(app.wsgi_app, app_root)
        app.config['SESSION_COOKIE_PATH'] = app_root or '/'

    return app
