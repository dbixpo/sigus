from datetime import datetime
from app import db


class Sala(db.Model):
    __tablename__ = 'salas'

    id            = db.Column(db.Integer, primary_key=True)
    unidade_id    = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='CASCADE'), nullable=False)
    nome          = db.Column(db.String(150), nullable=False)
    tipo          = db.Column(db.String(100))  # legado — mantido para compatibilidade
    tipo_sala_id  = db.Column(db.Integer, db.ForeignKey('tipos_sala.id', ondelete='SET NULL'))
    responsavel   = db.Column(db.String(150))
    capacidade_maxima = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    ramal         = db.Column(db.String(20))
    ativo         = db.Column(db.Boolean, nullable=False, default=True)
    observacoes   = db.Column(db.Text)
    criado_em     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    unidade      = db.relationship('Unidade', back_populates='salas')
    tipo_sala    = db.relationship('TipoSala', back_populates='salas')
    equipamentos = db.relationship('Equipamento', back_populates='sala', lazy='dynamic')
    chamados     = db.relationship('Chamado', back_populates='sala', lazy='dynamic')

    @property
    def tipo_label(self):
        """Retorna o nome do tipo, preferindo tipo_sala (dinâmico) ao campo legado."""
        if self.tipo_sala:
            return self.tipo_sala.nome
        return self.tipo or '—'

    @property
    def tipo_icone(self):
        if self.tipo_sala:
            return self.tipo_sala.icone
        return 'bi-door-open'

    @property
    def total_equipamentos(self):
        return self.equipamentos.filter_by(ativo=True).count()

    def __repr__(self):
        return f'<Sala {self.nome} - {self.unidade.nome if self.unidade else "?"}>'
