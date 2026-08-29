from datetime import datetime
from app import db


class Unidade(db.Model):
    __tablename__ = 'unidades'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(30), nullable=False, default='UBS')
    tipo_unidade_id = db.Column(db.Integer, db.ForeignKey('tipos_unidade.id', ondelete='SET NULL'))
    predio_id = db.Column(db.Integer, db.ForeignKey('predios.id', ondelete='SET NULL'))
    endereco = db.Column(db.String(300))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100), default='Sorocaba')
    uf = db.Column(db.String(2), default='SP')
    cep = db.Column(db.String(9))
    telefone = db.Column(db.String(20))
    ramal    = db.Column(db.String(20))
    email = db.Column(db.String(200))
    numero_cnes = db.Column(db.String(20))
    link_maps = db.Column(db.String(500))
    status = db.Column(db.String(10), nullable=False, default='ativa')
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    salas = db.relationship('Sala', back_populates='unidade', lazy='dynamic', cascade='all, delete-orphan')
    usuarios = db.relationship('UsuarioUnidade', back_populates='unidade', lazy='dynamic')
    chamados = db.relationship('Chamado', back_populates='unidade', lazy='dynamic')
    tipo_unidade = db.relationship('TipoUnidade', back_populates='unidades')
    predio = db.relationship('Predio', back_populates='unidades')

    @property
    def total_salas(self):
        return self.salas.filter_by(ativo=True).count()

    @property
    def total_equipamentos(self):
        from app.models.equipamento import Equipamento
        from app.models.sala import Sala
        return db.session.query(Equipamento).join(Sala).filter(
            Sala.unidade_id == self.id,
            Equipamento.ativo == True
        ).count()

    @property
    def chamados_abertos(self):
        return self.chamados.filter_by(status='aberto').count()

    @property
    def gerentes(self):
        """Retorna os vínculos cujo usuário tem perfil 'coordenador' ou 'administrador'."""
        return [
            v for v in self.usuarios.filter_by(ativo=True).all()
            if v.usuario and v.usuario.perfil in ('coordenador', 'administrador')
        ]

    def __repr__(self):
        return f'<Unidade {self.nome}>'


class UsuarioUnidade(db.Model):
    __tablename__ = 'usuario_unidade'

    id           = db.Column(db.Integer, primary_key=True)
    usuario_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    unidade_id   = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='CASCADE'), nullable=False)
    matricula_id = db.Column(db.Integer, db.ForeignKey('matriculas_profissionais.id', ondelete='SET NULL'))
    papel        = db.Column(db.String(50))
    ativo        = db.Column(db.Boolean, nullable=False, default=True)
    vinculado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    usuario   = db.relationship('Usuario', back_populates='unidades')
    unidade   = db.relationship('Unidade', back_populates='usuarios')
    matricula = db.relationship('MatriculaProfissional', foreign_keys=[matricula_id])

    __table_args__ = (db.UniqueConstraint('usuario_id', 'unidade_id'),)
