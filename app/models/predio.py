from datetime import datetime
from app import db


class Predio(db.Model):
    """Prédio físico que pode abrigar múltiplas unidades/setores.

    Chamados PREDIAIS (elétrico, hidráulico, estrutural) são registrados
    no prédio e vão para o responsável predial do prédio.
    Cada unidade dentro do prédio mantém seus próprios equipamentos e
    pode abrir chamados de equipamento de forma independente.
    """
    __tablename__ = 'predios'

    id                     = db.Column(db.Integer, primary_key=True)
    nome                   = db.Column(db.String(200), nullable=False)
    endereco               = db.Column(db.String(300))
    numero                 = db.Column(db.String(20))
    complemento            = db.Column(db.String(100))
    bairro                 = db.Column(db.String(100))
    cidade                 = db.Column(db.String(100), default='Sorocaba')
    uf                     = db.Column(db.String(2), default='SP')
    cep                    = db.Column(db.String(9))
    telefone               = db.Column(db.String(20))
    link_maps              = db.Column(db.Text)
    latitude               = db.Column(db.Float)
    longitude              = db.Column(db.Float)
    responsavel_predial_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    observacoes            = db.Column(db.Text)
    ativo                  = db.Column(db.Boolean, nullable=False, default=True)
    criado_em              = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em          = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    unidades             = db.relationship('Unidade', back_populates='predio', lazy='dynamic')
    responsavel_predial  = db.relationship('Usuario', foreign_keys=[responsavel_predial_id])

    @property
    def total_unidades(self):
        return self.unidades.filter_by(status='ativa').count()

    @property
    def total_equipamentos(self):
        from app.models.equipamento import Equipamento
        from app.models.sala import Sala
        return (
            db.session.query(Equipamento)
            .join(Sala)
            .join(Sala.unidade)
            .filter(
                Sala.unidade.has(predio_id=self.id),
                Equipamento.ativo == True,
            )
            .count()
        )

    @property
    def endereco_completo(self):
        partes = [p for p in [self.endereco, self.numero, self.complemento,
                               self.bairro, self.cidade, self.uf] if p]
        return ', '.join(partes) if partes else '—'

    def __repr__(self):
        return f'<Predio {self.nome}>'
