from datetime import datetime
from app import db


ICONES_MARCA_FA = {'wpforms', 'google', 'facebook', 'facebook-f', 'whatsapp', 'youtube',
                   'twitter', 'instagram', 'linkedin', 'github', 'wikipedia-w', 'wordpress',
                   'chrome', 'firefox', 'microsoft', 'apple', 'android'}


def _icone_para_fontawesome(icone):
    """Converte ícone (bi-xxx ou fas fa-xxx) para classes Font Awesome."""
    if not icone:
        return 'fas fa-folder'
    icone = (icone or '').strip()
    if icone.startswith('bi-'):
        biv = icone[3:].replace('-fill', '')
        mapa = {'folder': 'folder', 'link': 'link', 'link-45deg': 'link', 'gear': 'gear',
                'house': 'house', 'envelope': 'envelope', 'people': 'users', 'globe': 'globe',
                'file-earmark': 'file', 'calendar': 'calendar', 'star': 'star',
                'bookmark': 'bookmark', 'graph-up': 'chart-line', 'briefcase': 'briefcase',
                'collection': 'folder', 'box': 'box', 'cpu': 'microchip'}
        nome = mapa.get(biv, biv.split('-')[0] if '-' in biv else biv)
        return 'fas fa-' + nome
    # Extrai o nome do ícone (ex: wpforms de "fas fa-wpforms" ou "fa-wpforms")
    if ' ' in icone:
        parts = icone.split()
        nome = parts[-1].lstrip('fa-') if parts[-1].startswith('fa-') else parts[-1]
    else:
        nome = icone.lstrip('fa-') if icone.startswith('fa-') else icone
    if nome in ICONES_MARCA_FA:
        return 'fab fa-' + nome
    if any(icone.startswith(p) for p in ('fas ', 'far ', 'fab ', 'fal ', 'fad ')):
        return icone
    return 'fas fa-' + nome


class TipoLink(db.Model):
    """Categoria/tipo de link útil (ex: Sistemas, Portais, Comunicação)."""
    __tablename__ = 'tipos_link'

    id            = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(100), nullable=False)
    descricao     = db.Column(db.String(300))
    icone         = db.Column(db.String(60), nullable=False, default='fas fa-folder')
    cor           = db.Column(db.String(7), nullable=False, default='#1a6abf')  # hex
    ordem         = db.Column(db.Integer, nullable=False, default=0)
    ativo         = db.Column(db.Boolean, nullable=False, default=True)
    criado_em     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                              onupdate=datetime.utcnow)

    links = db.relationship(
        'LinkUtil',
        backref='tipo_link',
        lazy='dynamic',
        order_by='LinkUtil.ordem',
        foreign_keys='LinkUtil.tipo_link_id',
    )

    @property
    def icone_fa(self):
        """Retorna as classes do ícone em Font Awesome (para exibição)."""
        return _icone_para_fontawesome(self.icone)

    def __repr__(self):
        return f'<TipoLink {self.nome}>'
