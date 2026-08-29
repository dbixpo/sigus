"""
Configuração do SIGUS — desenvolvimento e produção.
Em produção, use variáveis de ambiente (.env ou servidor).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Heroku e outros PaaS usam DATABASE_URL; Postgres pode vir com postgres://
def _normalizar_database_url(url):
    """Garante que postgres:// vire postgresql:// (psycopg2 exige)."""
    if url and url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sigus-dev-key-insegura')
    # Mapa abrangência (KMZ): SIGUS_ABRANG_KMZ_OFFSET_LNG / _LAT (graus); vazio = padrão no código.
    SQLALCHEMY_DATABASE_URI = _normalizar_database_url(
        os.environ.get('DATABASE_URL', 'postgresql://postgres@localhost/sigus')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
