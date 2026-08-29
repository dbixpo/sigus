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
app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    debug = os.environ.get('FLASK_ENV') == 'development'

    if debug:
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        # Produção: Waitress (já em requirements.txt)
        from waitress import serve
        serve(app, host='0.0.0.0', port=5000, url_scheme='https', threads=4)
