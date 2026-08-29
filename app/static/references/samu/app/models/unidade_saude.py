"""Unidades de Saúde (destinos regulados, hospitais, UBS, UPA, etc.)."""
from datetime import datetime
from app import db


class UnidadeSaude(db.Model):
    """Unidades de saúde para destinos de pacientes."""
    __tablename__ = 'unidades_saude'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    apelido = db.Column(db.String(100))
    sigla = db.Column(db.String(20))
    cnes = db.Column(db.String(7))
    tipo = db.Column(db.String(50))  # legado
    tipo_unidade_id = db.Column(db.Integer, db.ForeignKey('tipos_unidade_saude.id', ondelete='SET NULL'))
    tipo_unidade = db.relationship('TipoUnidadeSaude', backref='unidades')

    endereco = db.Column(db.String(300))  # legado
    logradouro = db.Column(db.String(300))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    municipio = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    uf = db.Column(db.String(2))
    cep = db.Column(db.String(9))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(200))
    link_google_maps = db.Column(db.String(500))

    hora_inicio = db.Column(db.Time)
    hora_fim = db.Column(db.Time)
    funcionamento_24h = db.Column(db.Boolean, nullable=False, default=False)

    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<UnidadeSaude {self.nome}>'

    @property
    def cidade_uf(self):
        c = self.cidade or self.municipio or ''
        u = self.uf or ''
        if c and u:
            return f'{c}/{u}'
        return c or u or '—'

    @property
    def endereco_completo(self):
        partes = []
        if self.logradouro:
            partes.append(self.logradouro)
        if self.numero:
            partes.append(f'nº {self.numero}')
        if self.complemento:
            partes.append(self.complemento)
        if self.bairro:
            partes.append(self.bairro)
        if partes:
            return ', '.join(partes)
        return self.endereco

    @property
    def hora_funcionamento(self):
        if self.funcionamento_24h:
            return '24h'
        if self.hora_inicio and self.hora_fim:
            return f'{self.hora_inicio.strftime("%H:%M")} – {self.hora_fim.strftime("%H:%M")}'
        return '—'
