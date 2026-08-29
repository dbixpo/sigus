from datetime import datetime
from app import db
from app.models.usuario import CBOS, VINCULOS, TIPOS_VINCULO


class SolicitacaoVinculo(db.Model):
    """Solicitação de auto-cadastro feita por um profissional externo via link público.

    O profissional preenche seus dados e escolhe a unidade.
    O coordenador/administrativo aprova — o sistema então cria o usuário,
    faz o vínculo e gera a ficha CNES automaticamente.
    """
    __tablename__ = 'solicitacoes_vinculo'

    id               = db.Column(db.Integer, primary_key=True)
    unidade_id       = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='CASCADE'), nullable=False)

    # Status do fluxo
    status           = db.Column(db.String(20), nullable=False, default='pendente')
    # pendente | aprovado | rejeitado

    # Dados pessoais
    nome             = db.Column(db.String(200), nullable=False)
    email            = db.Column(db.String(200), nullable=False)
    cpf              = db.Column(db.String(20))
    cns              = db.Column(db.String(20))
    sexo             = db.Column(db.String(1))
    data_nasc        = db.Column(db.Date)
    nome_mae         = db.Column(db.String(200))
    nome_pai         = db.Column(db.String(200))
    nacionalidade    = db.Column(db.String(20))
    municipio_nasc   = db.Column(db.String(100))
    uf_nasc          = db.Column(db.String(2))
    # Estrangeiros: data de entrada no Brasil e país de origem
    dt_entrada_pais  = db.Column(db.Date)
    pais_origem      = db.Column(db.String(100))

    # Documento de identidade
    rg               = db.Column(db.String(30))
    rg_uf            = db.Column(db.String(2))
    rg_orgao         = db.Column(db.String(30))
    rg_emissao       = db.Column(db.Date)

    # Escolaridade
    escolaridade     = db.Column(db.String(2))

    # Endereço
    end_logradouro   = db.Column(db.String(200))
    end_numero       = db.Column(db.String(10))
    end_bairro       = db.Column(db.String(100))
    end_municipio    = db.Column(db.String(100))
    end_uf           = db.Column(db.String(2))
    end_cep          = db.Column(db.String(10))
    telefone         = db.Column(db.String(20))

    # Dados profissionais
    orgao_emissor    = db.Column(db.String(50))
    reg_conselho     = db.Column(db.String(50))
    cbo              = db.Column(db.String(10))
    vinculo          = db.Column(db.String(1))
    tipo_vinculo     = db.Column(db.String(1))
    carga_horaria    = db.Column(db.SmallInteger)
    cnpj_empresa     = db.Column(db.String(20))
    nome_empresa     = db.Column(db.String(200))
    dt_entrada       = db.Column(db.Date)

    # Controle
    criado_em        = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    aprovado_por     = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    aprovado_em      = db.Column(db.DateTime)
    usuario_criado   = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    observacao       = db.Column(db.Text)  # motivo de rejeição ou nota do aprovador
    assinatura_base64 = db.Column(db.Text)  # imagem PNG em base64 da assinatura do profissional

    unidade  = db.relationship('Unidade',  foreign_keys=[unidade_id],  backref=db.backref('solicitacoes_vinculo', lazy='dynamic'))
    aprovador = db.relationship('Usuario', foreign_keys=[aprovado_por])
    usuario_gerado = db.relationship('Usuario', foreign_keys=[usuario_criado])

    @property
    def status_label(self):
        return {'pendente': 'Pendente', 'aprovado': 'Aprovado', 'rejeitado': 'Rejeitado'}.get(self.status, self.status)

    @property
    def status_badge(self):
        return {'pendente': 'warning', 'aprovado': 'success', 'rejeitado': 'danger'}.get(self.status, 'secondary')

    @property
    def cbo_label(self):
        for cod, desc in CBOS:
            if cod == self.cbo:
                return f'{cod} – {desc}'
        return self.cbo or '—'

    @property
    def vinculo_label(self):
        return VINCULOS.get(self.vinculo, '—')

    @property
    def tipo_vinculo_label(self):
        return TIPOS_VINCULO.get(self.tipo_vinculo, '—')

    @property
    def is_externo(self):
        return self.vinculo == '6' or self.tipo_vinculo == '3'

    def __repr__(self):
        return f'<SolicitacaoVinculo {self.id} {self.nome} → unidade {self.unidade_id} [{self.status}]>'
