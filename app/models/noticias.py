# -*- coding: utf-8 -*-
"""Comunicados com ciência e mural de ações locais da rede."""
from datetime import datetime
from app import db
from app.utils import prefixed_static_url


DESCRICAO_ACAO_MAX = 400
FOTOS_ACAO_MAX = 4
ANEXOS_COMUNICADO_MAX = 5

PERFIS_PUBLICAR = (
    'administrativo',
    'coordenador',
    'gestor_secretaria',
    'administrador',
)
PERFIS_COMPARTILHAR = ('gestor_secretaria', 'administrador')


def _cpf_digitos(valor):
    return ''.join(c for c in (valor or '') if c.isdigit())[:11]


def _cpf_anonimizado_lgpd(valor):
    """LGPD: 000.***.**0-00 — 3 primeiros, 9º e os 2 dígitos finais visíveis."""
    d = _cpf_digitos(valor)
    if len(d) != 11:
        return ''
    return f'{d[:3]}.***.**{d[8]}-{d[9:]}'


comunicado_unidades = db.Table(
    'comunicado_unidades',
    db.Column(
        'comunicado_id',
        db.Integer,
        db.ForeignKey('comunicados.id', ondelete='CASCADE'),
        primary_key=True,
    ),
    db.Column(
        'unidade_id',
        db.Integer,
        db.ForeignKey('unidades.id', ondelete='CASCADE'),
        primary_key=True,
    ),
)


class TipoAcao(db.Model):
    """Tema de ação local (seed inicial: temas para saúde da FAC e-SUS APS)."""
    __tablename__ = 'tipos_acao'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, unique=True)
    codigo_esus = db.Column(db.Integer)
    descricao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    ordem = db.Column(db.Integer, nullable=False, default=0)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    acoes = db.relationship('AcaoLocal', back_populates='tipo', lazy='dynamic')

    def __repr__(self):
        return f'<TipoAcao {self.nome}>'


class Comunicado(db.Model):
    __tablename__ = 'comunicados'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    texto = db.Column(db.Text)
    autor_id = db.Column(
        db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL')
    )
    unidade_origem_id = db.Column(
        db.Integer, db.ForeignKey('unidades.id', ondelete='SET NULL')
    )
    exige_ciencia = db.Column(db.Boolean, nullable=False, default=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    autor = db.relationship('Usuario', foreign_keys=[autor_id])
    unidade_origem = db.relationship('Unidade', foreign_keys=[unidade_origem_id])
    unidades_alvo = db.relationship(
        'Unidade',
        secondary=comunicado_unidades,
        lazy='joined',
    )
    anexos = db.relationship(
        'ComunicadoAnexo',
        back_populates='comunicado',
        cascade='all, delete-orphan',
        order_by='ComunicadoAnexo.id',
    )
    ciencias = db.relationship(
        'ComunicadoCiencia',
        back_populates='comunicado',
        cascade='all, delete-orphan',
        lazy='dynamic',
    )

    def usuario_cientificou(self, usuario_id):
        if not usuario_id:
            return False
        return self.ciencias.filter_by(usuario_id=usuario_id).first() is not None

    def ids_unidades_alvo(self):
        return [u.id for u in (self.unidades_alvo or [])]

    def __repr__(self):
        return f'<Comunicado {self.id} {self.titulo!r}>'


class ComunicadoAnexo(db.Model):
    __tablename__ = 'comunicado_anexos'

    id = db.Column(db.Integer, primary_key=True)
    comunicado_id = db.Column(
        db.Integer,
        db.ForeignKey('comunicados.id', ondelete='CASCADE'),
        nullable=False,
    )
    filename = db.Column(db.String(200), nullable=False)
    original = db.Column(db.String(255))
    mime_type = db.Column(db.String(80))
    tamanho_bytes = db.Column(db.Integer)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    comunicado = db.relationship('Comunicado', back_populates='anexos')

    @property
    def url(self):
        return prefixed_static_url(f'/static/uploads/comunicados/{self.filename}')

    @property
    def is_imagem(self):
        mime = (self.mime_type or '').lower()
        if mime.startswith('image/'):
            return True
        nome = (self.original or self.filename or '').lower()
        return nome.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))

    @property
    def tamanho_fmt(self):
        n = self.tamanho_bytes or 0
        if n < 1024:
            return f'{n} B'
        if n < 1024 * 1024:
            return f'{n / 1024:.0f} KB'
        return f'{n / (1024 * 1024):.1f} MB'


class ComunicadoCiencia(db.Model):
    __tablename__ = 'comunicado_ciencias'
    __table_args__ = (
        db.UniqueConstraint('comunicado_id', 'usuario_id', name='uq_comunicado_ciencia'),
    )

    id = db.Column(db.Integer, primary_key=True)
    comunicado_id = db.Column(
        db.Integer,
        db.ForeignKey('comunicados.id', ondelete='CASCADE'),
        nullable=False,
    )
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id', ondelete='CASCADE'),
        nullable=False,
    )
    ciencia_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip = db.Column(db.String(45))
    user_agent = db.Column(db.String(400))
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='SET NULL'))
    assinatura_base64 = db.Column(db.Text)
    origem = db.Column(db.String(20))
    cpf = db.Column(db.String(11))

    comunicado = db.relationship('Comunicado', back_populates='ciencias')
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    unidade = db.relationship('Unidade', foreign_keys=[unidade_id])

    ORIGENS = {
        'formulario': 'Assinatura na tela',
        'publicacao': 'Autor na publicação',
        'dashboard': 'Dashboard',
    }

    @property
    def origem_label(self):
        if not self.origem:
            return ''
        return self.ORIGENS.get(self.origem) or self.origem

    @property
    def cpf_lgpd(self):
        """CPF no formato LGPD 000.***.**0-00 (registro ou cadastro do usuário)."""
        mascarado = _cpf_anonimizado_lgpd(self.cpf)
        if mascarado:
            return mascarado
        if self.usuario:
            return _cpf_anonimizado_lgpd(self.usuario.cpf)
        return ''


class AcaoLocal(db.Model):
    __tablename__ = 'acoes_locais'

    id = db.Column(db.Integer, primary_key=True)
    unidade_id = db.Column(
        db.Integer, db.ForeignKey('unidades.id', ondelete='CASCADE'), nullable=False
    )
    autor_id = db.Column(
        db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL')
    )
    tipo_acao_id = db.Column(
        db.Integer, db.ForeignKey('tipos_acao.id', ondelete='SET NULL')
    )
    descricao = db.Column(db.String(DESCRICAO_ACAO_MAX), nullable=False)
    data_acao = db.Column(db.Date, nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    unidade = db.relationship('Unidade', foreign_keys=[unidade_id])
    autor = db.relationship('Usuario', foreign_keys=[autor_id])
    tipo = db.relationship('TipoAcao', back_populates='acoes')
    fotos = db.relationship(
        'AcaoLocalFoto',
        back_populates='acao',
        cascade='all, delete-orphan',
        order_by='AcaoLocalFoto.ordem',
    )

    @property
    def capa(self):
        return self.fotos[0] if self.fotos else None

    def __repr__(self):
        return f'<AcaoLocal {self.id} u={self.unidade_id}>'


class AcaoLocalFoto(db.Model):
    __tablename__ = 'acao_local_fotos'

    id = db.Column(db.Integer, primary_key=True)
    acao_id = db.Column(
        db.Integer,
        db.ForeignKey('acoes_locais.id', ondelete='CASCADE'),
        nullable=False,
    )
    filename = db.Column(db.String(200), nullable=False)
    original = db.Column(db.String(255))
    mime_type = db.Column(db.String(80))
    ordem = db.Column(db.Integer, nullable=False, default=0)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    acao = db.relationship('AcaoLocal', back_populates='fotos')

    @property
    def url(self):
        return prefixed_static_url(f'/static/uploads/acoes/{self.filename}')
