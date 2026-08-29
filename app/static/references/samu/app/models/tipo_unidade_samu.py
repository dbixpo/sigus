"""Tipos de Unidade SAMU (CRU, ALFA, BETA, VIR, etc.) — para faturamento e estatísticas."""
from datetime import datetime
from app import db


# IDs fixos dos tipos pré-cadastrados (permite editar só a sigla)
CRU, ALFA, BETA, VIR, MOT, AER, EMB, USR = 1, 2, 3, 4, 5, 6, 7, 8
TIPOS_PREDEFINIDOS = {CRU, ALFA, BETA, VIR, MOT, AER, EMB, USR}


class TipoUnidadeSamu(db.Model):
    """Tipo de unidade (Central, ALFA, BETA, VIR, etc.)."""
    __tablename__ = 'tipos_unidade_samu'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    sigla = db.Column(db.String(20), nullable=False)
    ordem_prioridade = db.Column(db.Integer, default=0)  # ordem de importância para regulação
    icon = db.Column(db.String(50))  # Font Awesome: fa-solid fa-ambulance | Bootstrap Icons: bi bi-truck
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    predefinido = db.Column(db.Boolean, nullable=False, default=False)  # True = só edita sigla
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TipoUnidadeSamu {self.sigla}>'

    @property
    def pode_editar_nome(self):
        """Tipos pré-definidos: só permitem editar a sigla."""
        return not self.predefinido
