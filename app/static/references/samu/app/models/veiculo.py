"""Veículos SAMU — conforme CRLV (Denatran)."""
from datetime import datetime
from app import db


# Tipos de veículo conforme CRLV/Denatran (Res. CONTRAN 916/2022)
TIPOS_VEICULO = [
    'AUTOMÓVEL', 'AMBULÂNCIA', 'VEÍCULO ESPECIAL', 'BONDE', 'CAMINHÃO',
    'CAMINHÃO TRATOR', 'REBOQUE', 'SEMI-REBOQUE', 'CAMINHONETE', 'CAMIONETA',
    'UTILITÁRIO', 'CHASSI PLATAFORMA', 'MICROÔNIBUS', 'ÔNIBUS',
    'CICLOMOTOR', 'MOTONETA', 'MOTOCICLETA', 'TRICICLO', 'QUADRICICLO',
    'SIDE CAR', 'TRATOR RODAS', 'TRATOR ESTEIRA', 'OUTROS'
]

# Combustível conforme CRLV
COMBUSTIVEIS = [
    'Gasolina', 'Álcool/Etanol', 'Diesel', 'GNV', 'Flex', 'Elétrico',
    'Híbrido', 'Biodiesel', 'Outros'
]


class Veiculo(db.Model):
    """Veículo com dados do CRLV e anexo do documento."""
    __tablename__ = 'veiculos'

    id = db.Column(db.Integer, primary_key=True)
    prefixo = db.Column(db.String(30), nullable=False)  # identificação (ex: ALFA 1)
    marca = db.Column(db.String(100))
    modelo = db.Column(db.String(150))
    placa = db.Column(db.String(7))
    renavam = db.Column(db.String(11))
    tipo = db.Column(db.String(50))  # TIPOS_VEICULO
    combustivel = db.Column(db.String(30))  # COMBUSTIVEIS
    ano_fabricacao = db.Column(db.Integer)
    ano_modelo = db.Column(db.Integer)
    crlv_anexo = db.Column(db.String(255))  # filename do PDF
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Veiculo {self.prefixo}>'

    @property
    def crlv_url(self):
        """URL para download do CRLV anexado."""
        if self.crlv_anexo:
            return f'/static/uploads/veiculos/{self.crlv_anexo}'
        return None
