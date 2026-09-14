# -*- coding: utf-8 -*-
"""Identidade da instalação: município, secretaria, domínio de e-mail e assets."""
import time
from datetime import datetime
from types import SimpleNamespace
from flask import url_for
from app import db

IDENTIDADE_PADRAO = {
    'municipio': 'Sorocaba',
    'uf': 'SP',
    'secretaria': 'Secretaria da Saúde de Sorocaba',
    'orgao_curto': 'Saúde Digital',
    'nome_sistema': 'SIGUS',
    'slogan': 'Sistema Integrado de Gestão das Unidades de Saúde',
    'dominio_email': 'sorocaba.sp.gov.br',
    'cidade_padrao': 'Sorocaba',
}

ASSET_SLOTS = {
    'logo_escuro': {
        'label': 'Logo para fundo escuro',
        'uso': 'Login, sidebar e capas escuras',
        'fallback': 'img/logo-sd-branco.png',
        'tamanho': '900 × 390 px',
        'formato': 'PNG transparente, horizontal',
    },
    'logo_claro': {
        'label': 'Logo para fundo claro',
        'uso': 'Páginas e materiais em fundo claro',
        'fallback': 'img/logo-sd-colorido.png',
        'tamanho': '900 × 390 px',
        'formato': 'PNG transparente, horizontal',
    },
    'favicon': {
        'label': 'Favicon',
        'uso': 'Aba do navegador, PWA e ícone Apple',
        'fallback': 'img/favicon.png',
        'tamanho': '512 × 512 px',
        'formato': 'PNG quadrado, fundo transparente',
    },
    'brasao': {
        'label': 'Brasão',
        'uso': 'Cabeçalho de todos os impressos',
        'fallback': 'img/prefeitura-sorocaba.png',
        'tamanho': '400 × 160 px',
        'formato': 'PNG transparente, horizontal',
    },
}

_CACHE = {'view': None, 'ts': 0}
_CACHE_TTL = 60


class IdentidadeSistema(db.Model):
    """Uma linha só (id = 1): textos da instalação."""
    __tablename__ = 'identidade_sistema'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    municipio = db.Column(db.String(120), nullable=False)
    uf = db.Column(db.String(2), nullable=False)
    secretaria = db.Column(db.String(200), nullable=False)
    orgao_curto = db.Column(db.String(80), nullable=False)
    nome_sistema = db.Column(db.String(40), nullable=False)
    slogan = db.Column(db.String(200), nullable=False)
    dominio_email = db.Column(db.String(120), nullable=False)
    cidade_padrao = db.Column(db.String(120), nullable=False)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def garantir(cls):
        """Devolve a linha 1, criando-a com o padrão de Sorocaba se faltar."""
        row = db.session.get(cls, 1)
        if row:
            return row
        row = cls(id=1, **IDENTIDADE_PADRAO)
        db.session.add(row)
        db.session.flush()
        return row


class SistemaAsset(db.Model):
    """Arquivo enviado: slots oficiais (logo, favicon, brasão) ou extra:<slug>."""
    __tablename__ = 'sistema_assets'

    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(80), nullable=False, unique=True)
    titulo = db.Column(db.String(150))
    filename = db.Column(db.String(200), nullable=False)
    mime = db.Column(db.String(80))
    nome_original = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class IdentidadeView:
    """Snapshot estável para templates e Python (não guarda instâncias do SQLAlchemy)."""

    def __init__(self, row=None, assets=None):
        self._dados = {}
        if row is not None:
            for campo in IDENTIDADE_PADRAO:
                valor = getattr(row, campo, None)
                if isinstance(valor, str):
                    valor = valor.strip()
                if valor:
                    self._dados[campo] = valor
        self._assets = {}
        for a in assets or []:
            self._assets[a.chave] = SimpleNamespace(
                id=a.id,
                chave=a.chave,
                titulo=a.titulo,
                filename=a.filename,
                nome_original=a.nome_original,
            )

    def _texto(self, campo):
        return self._dados.get(campo) or IDENTIDADE_PADRAO[campo]

    @property
    def municipio(self):
        return self._texto('municipio')

    @property
    def uf(self):
        return self._texto('uf')

    @property
    def secretaria(self):
        return self._texto('secretaria')

    @property
    def orgao_curto(self):
        return self._texto('orgao_curto')

    @property
    def nome_sistema(self):
        return self._texto('nome_sistema')

    @property
    def slogan(self):
        return self._texto('slogan')

    @property
    def dominio_email(self):
        return self._texto('dominio_email').lstrip('@')

    @property
    def cidade_padrao(self):
        return self._texto('cidade_padrao')

    @property
    def alt_brasao(self):
        return f'Prefeitura de {self.municipio}'

    def asset(self, chave):
        return self._assets.get(chave)

    def tem_upload(self, chave):
        return chave in self._assets

    def extras(self):
        itens = [a for chave, a in self._assets.items() if chave.startswith('extra:')]
        itens.sort(key=lambda a: (a.titulo or a.nome_original or a.chave).lower())
        return itens

    def asset_url(self, chave, external=False):
        """URL do upload da chave, ou o static padrão do slot. Nada quebra se a galeria estiver vazia."""
        from flask import has_request_context
        from app.utils import prefixed_static_url
        asset = self._assets.get(chave)
        if asset and asset.filename:
            rel = f'uploads/identidade/{asset.filename}'
        else:
            rel = ASSET_SLOTS.get(chave, {}).get('fallback') or ''
            if not rel:
                return ''
        if has_request_context():
            return url_for('static', filename=rel, _external=bool(external))
        return prefixed_static_url(f'/static/{rel}')

    def completar_email(self, valor):
        email = (valor or '').strip().lower()
        if email and '@' not in email:
            return f'{email}@{self.dominio_email}'
        return email


def invalidar_cache_identidade():
    _CACHE['view'] = None


def obter_identidade():
    """Identidade em cache curto; invalida no save. Se a tabela ainda não existir, devolve o padrão."""
    agora = time.time()
    if _CACHE['view'] is not None and (agora - _CACHE['ts']) < _CACHE_TTL:
        return _CACHE['view']
    try:
        row = db.session.get(IdentidadeSistema, 1)
        assets = SistemaAsset.query.all()
    except Exception:
        db.session.rollback()
        return IdentidadeView(None, [])
    view = IdentidadeView(row, assets)
    _CACHE['view'] = view
    _CACHE['ts'] = agora
    return view


def completar_email(valor):
    return obter_identidade().completar_email(valor)


def cidade_padrao():
    return obter_identidade().cidade_padrao
