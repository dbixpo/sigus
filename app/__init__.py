from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


class PrefixMiddleware:
    """WSGI middleware para rodar a app sob um prefixo (ex: /sigus)."""
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix.rstrip('/')

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if self.prefix:
            if path.startswith(self.prefix):
                environ['PATH_INFO'] = path[len(self.prefix):] or '/'
            environ['SCRIPT_NAME'] = self.prefix
        return self.app(environ, start_response)


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Prefixo de aplicação (ex: /sigus) — usado quando atrás de proxy reverso
    import os
    app_root = os.environ.get('APPLICATION_ROOT', '').rstrip('/')
    if app_root:
        app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=app_root)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'

    # Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.unidades import unidades_bp
    from app.routes.salas import salas_bp
    from app.routes.equipamentos import equipamentos_bp
    from app.routes.chamados import chamados_bp
    from app.routes.contratos import contratos_bp
    from app.routes.contrato_financeiro import contrato_financeiro_bp
    from app.routes.usuarios import usuarios_bp
    from app.routes.relatorios import relatorios_bp
    from app.routes.configuracoes import configuracoes_bp
    from app.routes.transferencias import transferencias_bp
    from app.routes.predios import predios_bp
    from app.routes.links import links_bp
    from app.routes.solicitacoes import solicitacoes_bp
    from app.routes.notificacoes import notificacoes_bp
    from app.routes.rh import rh_bp
    from app.routes.planejamentos import planejamentos_bp
    from app.routes.empresas import empresas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(predios_bp)
    app.register_blueprint(unidades_bp)
    app.register_blueprint(salas_bp)
    app.register_blueprint(equipamentos_bp)
    app.register_blueprint(chamados_bp)
    app.register_blueprint(contratos_bp)
    app.register_blueprint(contrato_financeiro_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(configuracoes_bp)
    app.register_blueprint(transferencias_bp)
    app.register_blueprint(links_bp)
    app.register_blueprint(solicitacoes_bp)
    app.register_blueprint(notificacoes_bp)
    app.register_blueprint(rh_bp)
    app.register_blueprint(planejamentos_bp)
    app.register_blueprint(empresas_bp)

    # Filtros Jinja2
    from app.utils import registrar_filtros
    registrar_filtros(app)

    # PWA: manifest para instalação no celular
    @app.route('/manifest.json')
    def manifest():
        import json
        base = app.config.get('APPLICATION_ROOT', '').rstrip('/') or ''
        data = {
            'name': 'SIGUS — Sistema de Gestão de Unidades de Saúde',
            'short_name': 'SIGUS',
            'description': 'Sistema Integrado de Gestão de Unidades de Saúde',
            'start_url': base + '/' if base else '/',
            'display': 'standalone',
            'background_color': '#1E3A50',
            'theme_color': '#1A82B8',
            'orientation': 'portrait-primary',
            'scope': base + '/' if base else '/',
            'icons': [
                {'src': base + '/static/img/favicon.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
                {'src': base + '/static/img/favicon.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            ],
        }
        return app.response_class(
            json.dumps(data, ensure_ascii=False),
            mimetype='application/manifest+json',
        )

    # Context processor: unidades para seletor de unidade padrão
    @app.context_processor
    def inject_unidades_seletor():
        from flask_login import current_user
        opcoes = []
        if current_user.is_authenticated:
            if current_user.pode('ver_todas_unidades'):
                from app.models.unidade import Unidade
                opcoes = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
            elif current_user.requer_vinculo:
                opcoes = current_user.unidades_ativas
        return {'unidades_seletor': opcoes}

    # ── Guarda de acesso: perfis que precisam de vínculo ────────────────
    from flask import redirect, url_for, request as req
    from flask_login import current_user as cu

    # Endpoints que sempre são permitidos (login, logout, assets, sem-vinculo)
    _ENDPOINTS_LIVRES = {
        'auth.login', 'auth.logout', 'auth.index',
        'static',
        'unidades.sem_vinculo',
        'solicitacoes.formulario', 'solicitacoes.confirmacao',
        'notificacoes.recentes', 'notificacoes.contagem',
        'notificacoes.marcar_lida', 'notificacoes.marcar_todas_lidas',
    }

    @app.before_request
    def verificar_vinculo_unidade():
        if not cu.is_authenticated:
            return
        if req.endpoint in _ENDPOINTS_LIVRES:
            return
        # Administrador e Gestor Central não precisam de vínculo
        if not cu.requer_vinculo:
            return
        if not cu.tem_vinculo:
            return redirect(url_for('unidades.sem_vinculo'))

    # ── Auditoria: registra todas as requisições (exceto static) ─────────────
    @app.after_request
    def registrar_auditoria(response):
        from flask import g, request
        from flask_login import current_user

        # Não auditar static
        if request.endpoint == 'static' or request.endpoint is None:
            return response

        try:
            # Inferir ação
            acao = 'view'
            if request.endpoint == 'auth.login' and request.method == 'POST':
                acao = 'login'
            elif request.method == 'GET':
                url_lower = (request.url or '').lower()
                if 'xlsx' in url_lower or 'csv' in url_lower or 'export' in url_lower:
                    acao = 'export'
                elif 'imprimir' in url_lower or (request.endpoint and 'imprimir' in request.endpoint):
                    acao = 'print'
                elif request.args and (request.endpoint or '').endswith('listar'):
                    acao = 'search'
            elif request.method == 'POST':
                endpoint = request.endpoint or ''
                url_lower = (request.url or '').lower()
                if 'excluir' in endpoint or 'excluir' in url_lower or 'delete' in url_lower:
                    acao = 'delete'
                elif 'novo' in endpoint or 'novo' in url_lower or 'criar' in url_lower:
                    acao = 'create'
                else:
                    acao = 'update'

            # Inferir módulo
            modulo = (request.endpoint or 'unknown').split('.')[0] if request.endpoint else 'unknown'

            # Sanitizar parâmetros (não gravar senhas)
            parametros = {}
            if request.args:
                parametros['args'] = dict(request.args)
            if request.form and request.method in ('POST', 'PUT', 'PATCH'):
                form_safe = {}
                for k, v in request.form.items():
                    if k.lower() not in ('senha', 'password', 'csrf_token', 'nova_senha', 'senha_atual'):
                        form_safe[k] = v
                if form_safe:
                    parametros['form'] = form_safe
            if not parametros:
                parametros = None

            usuario_id = current_user.id if current_user.is_authenticated else None
            ip = request.remote_addr or request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
            user_agent = (request.headers.get('User-Agent') or '')[:500]

            from app.models.auditoria import Auditoria
            rec = Auditoria(
                usuario_id=usuario_id,
                acao=acao,
                modulo=modulo,
                endpoint=request.endpoint or '',
                url=(request.url or '')[:500],
                method=request.method or '',
                parametros=parametros,
                ip_address=ip[:45] if ip else None,
                user_agent=user_agent or None,
                response_status=response.status_code if response else None,
            )
            db.session.add(rec)
            db.session.commit()
            g._auditoria_done = True
        except Exception:
            db.session.rollback()
        return response

    @app.teardown_request
    def auditoria_teardown(exc=None):
        """Registra auditoria em caso de exceção (after_request não roda)."""
        from flask import g, request
        from flask_login import current_user
        if getattr(g, '_auditoria_done', False):
            return
        try:
            if request.endpoint == 'static' or request.endpoint is None:
                return
            modulo = (request.endpoint or 'unknown').split('.')[0] if request.endpoint else 'unknown'
            usuario_id = current_user.id if current_user.is_authenticated else None
            ip = request.remote_addr or request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
            user_agent = (request.headers.get('User-Agent') or '')[:500]
            from app.models.auditoria import Auditoria
            rec = Auditoria(
                usuario_id=usuario_id,
                acao='view',
                modulo=modulo,
                endpoint=request.endpoint or '',
                url=(request.url or '')[:500],
                method=request.method or '',
                ip_address=ip[:45] if ip else None,
                user_agent=user_agent or None,
                response_status=500 if exc else None,
                detalhes=str(exc)[:2000] if exc else None,
            )
            db.session.add(rec)
            db.session.commit()
        except Exception:
            db.session.rollback()

    return app
