from datetime import datetime
from app import db

# Cores Bootstrap disponíveis para badge
BADGE_CORES = [
    ('danger',    'Vermelho'),
    ('warning',   'Amarelo'),
    ('info',      'Azul claro'),
    ('primary',   'Azul'),
    ('success',   'Verde'),
    ('secondary', 'Cinza'),
    ('dark',      'Preto'),
]


class StatusChamado(db.Model):
    __tablename__ = 'status_chamados'

    id               = db.Column(db.Integer, primary_key=True)
    slug             = db.Column(db.String(30), nullable=False, unique=True)
    label            = db.Column(db.String(80), nullable=False)
    badge_cor        = db.Column(db.String(20), nullable=False, default='secondary')
    ativo            = db.Column(db.Boolean, nullable=False, default=True)
    padrao_listagem  = db.Column(db.Boolean, nullable=False, default=False)
    # indica se este status encerra o chamado (define fechado_em)
    encerra_chamado  = db.Column(db.Boolean, nullable=False, default=False)
    ordem            = db.Column(db.Integer, nullable=False, default=0)
    criado_em        = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<StatusChamado {self.slug}>'

    @classmethod
    def ativos(cls):
        return cls.query.filter_by(ativo=True).order_by(cls.ordem).all()

    @classmethod
    def como_dict_label(cls):
        """Retorna {slug: label} para todos os status ativos."""
        return {s.slug: s.label for s in cls.ativos()}

    @classmethod
    def como_dict_badge(cls):
        """Retorna {slug: badge_cor} para todos os status ativos."""
        return {s.slug: s.badge_cor for s in cls.ativos()}

    @classmethod
    def slugs_padrao(cls):
        """Slugs marcados como padrão de listagem."""
        return [s.slug for s in cls.query.filter_by(ativo=True, padrao_listagem=True)
                                         .order_by(cls.ordem).all()]
