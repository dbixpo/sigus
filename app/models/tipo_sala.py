from datetime import datetime
from app.utils import agora_local
from app import db


class TipoSala(db.Model):
    __tablename__ = 'tipos_sala'

    id        = db.Column(db.Integer, primary_key=True)
    nome      = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    icone     = db.Column(db.String(50), nullable=False, default='fas fa-door-open')
    ativo     = db.Column(db.Boolean, nullable=False, default=True)
    # Ambiente padrão (AMB-xx), classificação funcional e ordem do catálogo.
    # Sem código = tipo fora do padrão de ambientes, sem kit.
    codigo    = db.Column(db.String(20), unique=True)
    grupo     = db.Column(db.String(120))
    ordem     = db.Column(db.Integer)
    # Salas deste tipo podem ser reservadas na agenda (sala de reunião, auditório).
    reservavel = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    criado_em     = db.Column(db.DateTime, nullable=False, default=agora_local)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=agora_local, onupdate=agora_local)

    salas = db.relationship('Sala', back_populates='tipo_sala', lazy='dynamic')
    kit = db.relationship('KitPadraoSala', back_populates='tipo_sala', lazy='dynamic',
                          cascade='all, delete-orphan')

    @property
    def nome_com_codigo(self):
        return f'{self.codigo} · {self.nome}' if self.codigo else self.nome

    def __repr__(self):
        return f'<TipoSala {self.nome}>'


class KitPadraoSala(db.Model):
    """Quantidade de cada tipo de equipamento esperada em UMA sala do tipo."""
    __tablename__ = 'kit_padrao_sala'

    id                  = db.Column(db.Integer, primary_key=True)
    tipo_sala_id        = db.Column(db.Integer, db.ForeignKey('tipos_sala.id', ondelete='CASCADE'), nullable=False)
    tipo_equipamento_id = db.Column(db.Integer, db.ForeignKey('tipos_equipamento.id', ondelete='CASCADE'), nullable=False)
    quantidade          = db.Column(db.Integer, nullable=False, default=1)
    # Quantidade por profissional: multiplica pelo "máx. profissionais simultâneos" da sala (0 = espera 0).
    por_profissional    = db.Column(db.Boolean, nullable=False, default=False, server_default='false')
    observacao          = db.Column(db.String(300))
    criado_em     = db.Column(db.DateTime, nullable=False, default=agora_local)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=agora_local, onupdate=agora_local)

    tipo_sala        = db.relationship('TipoSala', back_populates='kit')
    tipo_equipamento = db.relationship('TipoEquipamento')

    __table_args__ = (db.UniqueConstraint('tipo_sala_id', 'tipo_equipamento_id', name='uq_kit_padrao_sala'),)

    def esperado_na_sala(self, sala):
        if self.por_profissional:
            return self.quantidade * (sala.capacidade_maxima or 0)
        return self.quantidade

    def __repr__(self):
        return f'<KitPadraoSala sala={self.tipo_sala_id} eq={self.tipo_equipamento_id} x{self.quantidade}>'
