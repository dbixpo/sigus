from datetime import datetime
from app import db
from app.models.usuario import VINCULOS, TIPOS_VINCULO, CBOS
from app.models.cbo import CBO


class MatriculaProfissional(db.Model):
    """Cada matrícula de um profissional no serviço público.
    Uma pessoa (Usuario) pode ter N matrículas — cada uma com seu próprio
    número, vínculo, tipo de vínculo, CBO e conselho de classe.
    A carga horária é definida no momento do vínculo com a unidade (FichaCnesVinculo).
    """
    __tablename__ = 'matriculas_profissionais'

    id              = db.Column(db.Integer, primary_key=True)
    usuario_id      = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    numero          = db.Column(db.String(50), nullable=True)  # Nullable para permitir Contrato por Prazo Determinado sem matrícula
    vinculo         = db.Column(db.String(1))       # 1=Empregatício, 5=Residência, 6=Estágio
    tipo_vinculo    = db.Column(db.String(1))       # 1=Estatutário, 3=Determinado, 0=Sem tipo
    cbo             = db.Column(db.String(10))
    reg_conselho    = db.Column(db.String(30))
    orgao_emissor   = db.Column(db.String(50))
    ativo           = db.Column(db.Boolean, nullable=False, default=True)
    criado_em       = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                                onupdate=datetime.utcnow)

    usuario         = db.relationship('Usuario', back_populates='matriculas')

    @property
    def cbo_label(self):
        if not self.cbo:
            return '—'
        # Busca do banco de dados primeiro
        cbo_obj = CBO.query.filter_by(codigo=self.cbo).first()
        if cbo_obj:
            return f'{cbo_obj.codigo} – {cbo_obj.descricao}'
        # Fallback para a lista hardcoded (caso o CBO não esteja no banco ainda)
        for cod, desc in CBOS:
            if cod == self.cbo:
                return f'{cod} – {desc}'
        return self.cbo or '—'

    @property
    def cbo_desc(self):
        if not self.cbo:
            return '—'
        # Busca do banco de dados primeiro
        cbo_obj = CBO.query.filter_by(codigo=self.cbo).first()
        if cbo_obj:
            return cbo_obj.descricao
        # Fallback para a lista hardcoded (caso o CBO não esteja no banco ainda)
        for cod, desc in CBOS:
            if cod == self.cbo:
                return desc
        return self.cbo or '—'

    @property
    def vinculo_label(self):
        return VINCULOS.get(self.vinculo, '—')

    @property
    def tipo_vinculo_label(self):
        return TIPOS_VINCULO.get(self.tipo_vinculo, '—')

    def __repr__(self):
        return f'<Matricula {self.numero} u={self.usuario_id}>'
