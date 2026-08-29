from datetime import datetime
from app import db
from app.utils import prefixed_static_url
from app.models.tipo_link import _icone_para_fontawesome

# Perfis que podem ver links
PERFIS_LINK = [
    ('todos',              'Todos os perfis'),
    ('administrador',      'Administrador'),
    ('gestor_secretaria',  'Gestor Central'),
    ('coordenador',        'Gestor de Área'),
    ('administrativo',     'Apoio Administrativo'),
    ('profissional',       'Operador Padrão'),
]


class LinkUtil(db.Model):
    """Link útil exibido na página Links Úteis, agrupado por TipoLink."""
    __tablename__ = 'links_uteis'

    id          = db.Column(db.Integer, primary_key=True)

    # FK para categoria
    tipo_link_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_link.id', ondelete='SET NULL'),
        nullable=True,
    )

    nome        = db.Column(db.String(150), nullable=False)
    descricao   = db.Column(db.String(300))
    url         = db.Column(db.String(500))
    imagem_url  = db.Column(db.String(500))          # URL externa (alternativo)
    imagem_path = db.Column(db.String(300))          # caminho em static/uploads/links/
    icone       = db.Column(db.String(60), default='fas fa-link')
    nova_aba    = db.Column(db.Boolean, nullable=False, default=True)
    ativo       = db.Column(db.Boolean, nullable=False, default=True)
    ordem       = db.Column(db.Integer, nullable=False, default=0)

    perfis_acesso = db.Column(db.JSON, nullable=False, default=lambda: ['todos'])

    criado_por    = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                              onupdate=datetime.utcnow)

    criador = db.relationship('Usuario', foreign_keys=[criado_por])

    @property
    def icone_fa(self):
        """Retorna as classes do ícone em Font Awesome (para exibição)."""
        return _icone_para_fontawesome(self.icone or 'fas fa-link')

    @property
    def imagem_src(self) -> str | None:
        if self.imagem_path:
            return prefixed_static_url(f'/static/uploads/links/{self.imagem_path}')
        return self.imagem_url or None

    def visivel_para(self, perfil: str) -> bool:
        if not self.ativo:
            return False
        pa = self.perfis_acesso or ['todos']
        return 'todos' in pa or perfil in pa

    def __repr__(self):
        return f'<LinkUtil {self.nome}>'
