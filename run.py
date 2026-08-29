"""
SIGUS — Entry point para desenvolvimento e produção (IIS, Waitress).
"""
import os
import sys

# Garantir que o diretório do projeto esteja no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Prefixo /sigus para rodar atrás do reverse proxy do IIS
# O app usa PrefixMiddleware quando APPLICATION_ROOT está definido
os.environ.setdefault('APPLICATION_ROOT', '/sigus')

from werkzeug.middleware.proxy_fix import ProxyFix
from app import create_app

# FLASK_ENV: development | production
app = create_app(os.environ.get('FLASK_ENV', 'development'))
app.config["APPLICATION_ROOT"] = "/sigus"
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# IIS faz rewrite para localhost sem repassar Host — CSRF falha no POST.
# Desative com SIGUS_BEHIND_PROXY=0 ao rodar só em localhost (sem proxy).
if os.environ.get('SIGUS_BEHIND_PROXY', '1') != '0':
    _public_host = os.environ.get('SIGUS_PUBLIC_HOST', 'saudedigital.sorocaba.sp.gov.br').strip()
    if _public_host:
        _orig_wsgi = app.wsgi_app

        def _inject_forwarded_host(environ, start_response):
            host = (environ.get('HTTP_HOST') or '').split(':')[0]
            if host in ('localhost', '127.0.0.1', '::1'):
                if not environ.get('HTTP_X_FORWARDED_HOST'):
                    environ['HTTP_X_FORWARDED_HOST'] = _public_host
                if not environ.get('HTTP_X_FORWARDED_PROTO'):
                    environ['HTTP_X_FORWARDED_PROTO'] = 'https'
            return _orig_wsgi(environ, start_response)

        app.wsgi_app = _inject_forwarded_host

if __name__ == '__main__':
    debug = os.environ.get('FLASK_ENV') == 'development'
    # IIS injeta HTTP_PLATFORM_PORT; em dev use PORT ou SIGUS_PORT (padrão 5001).
    # Não usar 5000 — pode conflitar com outros serviços no mesmo servidor.
    port = int(os.environ.get(
        'HTTP_PLATFORM_PORT',
        os.environ.get('PORT', os.environ.get('SIGUS_PORT', '5001')),
    ))

    if debug:
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        # Produção: Waitress (já em requirements.txt)
        from waitress import serve
        serve(app, host='0.0.0.0', port=port, url_scheme='https', threads=4)
