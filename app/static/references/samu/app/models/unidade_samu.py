"""Unidades SAMU: Central de Regulação ou Viatura."""
from datetime import datetime
from app import db


class UnidadeSamu(db.Model):
    """Unidade SAMU: Central (com endereço) ou Viatura (vinculada a Base + Tipo)."""
    __tablename__ = 'unidades_samu'

    id = db.Column(db.Integer, primary_key=True)
    tipo_registro = db.Column(db.String(20), nullable=False, default='central')  # 'central' | 'viatura'
    cnes = db.Column(db.String(7))
    nome = db.Column(db.String(200), nullable=False)
    apelido = db.Column(db.String(100))  # como chamam / exibido no sistema
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Central: endereço completo
    logradouro = db.Column(db.String(300))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    uf = db.Column(db.String(2))
    cep = db.Column(db.String(9))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(200))
    link_google_maps = db.Column(db.String(500))

    # Viatura: base + tipo
    base_id = db.Column(db.Integer, db.ForeignKey('bases_descentralizadas.id', ondelete='SET NULL'))
    base = db.relationship('BaseDescentralizada', back_populates='viaturas', foreign_keys=[base_id])
    tipo_unidade_id = db.Column(db.Integer, db.ForeignKey('tipos_unidade_samu.id', ondelete='SET NULL'))
    tipo_unidade = db.relationship('TipoUnidadeSamu', backref='unidades')

    faltas_abonadas = db.relationship('FaltaAbonada', back_populates='unidade_samu', foreign_keys='FaltaAbonada.unidade_samu_id')

    def __repr__(self):
        return f'<UnidadeSamu {self.nome}>'

    @property
    def e_central(self):
        return self.tipo_registro == 'central'

    @property
    def e_viatura(self):
        return self.tipo_registro == 'viatura'

    @property
    def tipo_label(self):
        if self.e_central:
            return 'Central'
        return (self.tipo_unidade.sigla if self.tipo_unidade else '—')

    @property
    def nome_exibicao(self):
        """Nome exibido no sistema: apelido se houver, senão nome."""
        return self.apelido or self.nome

    @property
    def localizacao(self):
        """Para listagem: cidade (central) ou base (viatura)."""
        if self.e_central:
            return self.cidade
        return (self.base.nome if self.base else '—')

    @property
    def endereco_completo(self):
        """Endereço: Central usa próprios campos; Viatura usa da base."""
        if self.e_central:
            partes = []
            if self.logradouro:
                partes.append(self.logradouro)
            if self.numero:
                partes.append(f'nº {self.numero}')
            if self.complemento:
                partes.append(self.complemento)
            if self.bairro:
                partes.append(self.bairro)
            return ', '.join(partes) if partes else None
        return self.base.endereco_completo if self.base else None

    @property
    def link_google_maps_url(self):
        """Link Maps: Central usa próprio; Viatura usa da base."""
        if self.e_central:
            return self.link_google_maps
        return self.base.link_google_maps if self.base else None

    @property
    def base_nome(self):
        """Nome da base (viatura) ou — (central)."""
        return self.base.nome if self.base else '—'

    @property
    def telefone_exibicao(self):
        """Telefone: Central usa próprio; Viatura usa da base."""
        if self.e_central:
            return self.telefone
        return self.base.telefone if self.base else None

    @property
    def cidade_uf(self):
        """Cidade/UF: Central usa próprios; Viatura usa da base."""
        if self.e_central:
            if self.cidade and self.uf:
                return f'{self.cidade}/{self.uf}'
            return self.cidade or self.uf or '—'
        if self.base and (self.base.cidade or self.base.uf):
            if self.base.cidade and self.base.uf:
                return f'{self.base.cidade}/{self.base.uf}'
            return self.base.cidade or self.base.uf
        return '—'
