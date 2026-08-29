"""Motivo da ocorrência."""
from datetime import datetime
from app import db


class MotivoOcorrencia(db.Model):
    """Motivos da ocorrência."""
    __tablename__ = 'motivos_ocorrencia'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.String(300))
    tipo_ocorrencia_id = db.Column(db.Integer, db.ForeignKey('tipos_ocorrencia.id', ondelete='SET NULL'))
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    tipo_ocorrencia = db.relationship('TipoOcorrencia', backref='motivos')

    @property
    def tipo_nome(self):
        return (self.tipo_ocorrencia.nome if self.tipo_ocorrencia else None) or '—'

    def __repr__(self):
        return f'<MotivoOcorrencia {self.nome}>'
