"""
Configuração do Sistema SAMU — desenvolvimento e produção.
Credenciais PostgreSQL iguais ao projeto SIGUS.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Carrega .env sempre da raiz do projeto (não depende do CWD)
_root = Path(__file__).resolve().parent
load_dotenv(_root / '.env')


def _get_database_uri():
    """
    Monta a URL do banco com URL.create() para tratar corretamente
    senhas com caracteres especiais (ex: @).
    """
    from sqlalchemy import URL

    # DATABASE_URL tem prioridade (ex: Heroku, Docker)
    raw = os.environ.get('DATABASE_URL', '')
    if raw and 'postgres' in raw.lower():
        if raw.startswith('postgres://'):
            raw = raw.replace('postgres://', 'postgresql://', 1)
        if raw.startswith('postgresql://') and '+pg8000' not in raw:
            raw = raw.replace('postgresql://', 'postgresql+pg8000://', 1)
        return raw

    # Monta a partir de variáveis separadas (evita problemas com @ na senha)
    return str(URL.create(
        drivername='postgresql+pg8000',
        username=os.environ.get('DB_USER', 'sa'),
        password=os.environ.get('DB_PASSWORD', '@Qweszxc7895123'),
        host=os.environ.get('DB_HOST', 'localhost'),
        database=os.environ.get('DB_NAME', 'samu'),
    ))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'samu-dev-key-insegura')
    # Sessão expira ao fechar o navegador (não persiste login)
    SESSION_PERMANENT = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Ignora cookie "Lembrar-me" antigo (nome diferente = cookie anterior invalidado)
    REMEMBER_COOKIE_NAME = 'samu_remember_disabled'
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    # Subpath quando atrás de proxy (ex: saudedigital.../samu). Deixe vazio para localhost:5192.
    APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', '').rstrip('/') or ''
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '')  # vazio = instance/uploads


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
