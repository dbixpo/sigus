from datetime import datetime
from app import db
from app.utils import agora_local_callable


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
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    status = db.Column(db.String(10), nullable=False, default='ativa')
    observacoes = db.Column(db.Text)
    # Tipos de chamado que esta unidade/setor recebe e trata na fila de gestão
    tipos_chamado_recebe = db.Column(db.JSON, default=list)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable, onupdate=agora_local_callable)

    salas = db.relationship('Sala', back_populates='unidade', lazy='dynamic', cascade='all, delete-orphan')
    usuarios = db.relationship('UsuarioUnidade', back_populates='unidade', lazy='dynamic')
    chamados = db.relationship('Chamado', back_populates='unidade', lazy='dynamic',
                               foreign_keys='Chamado.unidade_id')
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
        """Retorna os vínculos cujo usuário tem perfil 'coordenador'/'administrador' OU CBO 131210 (Gerente de Serviços de Saúde)."""
        from app.models.ficha_cnes import FichaCnesVinculo
        
        # Busca última ficha CNES de cada profissional para verificar CBO
        ultima_ficha_por_usuario = {}
        fichas = (FichaCnesVinculo.query
                  .filter_by(unidade_id=self.id)
                  .order_by(FichaCnesVinculo.gerado_em.desc())
                  .all())
        for f in fichas:
            if f.usuario_id not in ultima_ficha_por_usuario:
                ultima_ficha_por_usuario[f.usuario_id] = f
        
        gerentes_list = []
        for v in self.usuarios.filter_by(ativo=True).all():
            if not v.usuario:
                continue
            
            # Verifica se é gestor por perfil
            is_gestor_perfil = v.usuario.perfil in ('coordenador', 'administrador')
            
            # Verifica se é gestor por CBO 131210
            is_gestor_cbo = False
            ficha = ultima_ficha_por_usuario.get(v.usuario_id)
            if ficha and ficha.cbo == '131210':
                is_gestor_cbo = True
            
            if is_gestor_perfil or is_gestor_cbo:
                gerentes_list.append(v)
        
        # Ordena trazendo primeiro os marcados como gestores principais/secundários
        def _peso(vv):
            if vv.papel == 'gestor_principal':
                return 0
            if vv.papel == 'gestor_secundario':
                return 1
            return 2

        return sorted(gerentes_list, key=_peso)

    @property
    def gestores_principais(self):
        """
        Retorna até dois vínculos (UsuarioUnidade) marcados como principais para contato da unidade.
        Usa o campo `papel` de UsuarioUnidade:
          - 'gestor_principal'
          - 'gestor_secundario'
        """
        principais = []
        for v in self.usuarios.filter_by(ativo=True).all():
            if v.papel in ('gestor_principal', 'gestor_secundario'):
                principais.append(v)
        # Garante no máximo 2
        principais = sorted(
            principais,
            key=lambda vv: 0 if vv.papel == 'gestor_principal' else 1
        )[:2]
        return principais

    @property
    def trata_chamados(self):
        return bool(self.tipos_chamado_recebe)

    def trata_tipo_chamado(self, tipo):
        return tipo in (self.tipos_chamado_recebe or [])

    @classmethod
    def que_tratam_tipo(cls, tipo, apenas_ativas=True):
        """Unidades ativas configuradas para receber/tratar um tipo de chamado."""
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy import cast

        q = cls.query
        if apenas_ativas:
            q = q.filter_by(status='ativa')
        q = q.order_by(cls.nome)
        return q.filter(
            cast(cls.tipos_chamado_recebe, JSONB).contains([tipo])
        ).all()

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
    vinculado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable)

    usuario   = db.relationship('Usuario', back_populates='unidades')
    unidade   = db.relationship('Unidade', back_populates='usuarios')
    matricula = db.relationship('MatriculaProfissional', foreign_keys=[matricula_id])

    __table_args__ = (db.UniqueConstraint('usuario_id', 'unidade_id'),)
