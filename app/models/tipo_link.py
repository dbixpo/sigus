from datetime import datetime
from app import db


class TipoLink(db.Model):
    """Categoria/tipo de link útil (ex: Sistemas, Portais, Comunicação)."""
    __tablename__ = 'tipos_link'

    id            = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(100), nullable=False)
    descricao     = db.Column(db.String(300))
    icone         = db.Column(db.String(60), nullable=False, default='bi-folder')
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

    def __repr__(self):
        return f'<TipoLink {self.nome}>'
