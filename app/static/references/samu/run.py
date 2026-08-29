"""
Sistema SAMU — Entry point para desenvolvimento e produção.
"""
import os
import sys

# Evita UnicodeDecodeError no psycopg2 em Windows (locale não-UTF-8)
os.environ.setdefault('PGCLIENTENCODING', 'UTF8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    port = int(os.environ.get('HTTP_PLATFORM_PORT', os.environ.get('PORT', 5192)))
    debug = os.environ.get('FLASK_ENV') == 'development'

    if debug:
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        from waitress import serve
        serve(app, host='0.0.0.0', port=port, url_scheme='https', threads=4)
