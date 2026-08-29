from datetime import datetime
from app import db
from app.models.usuario import CBOS, VINCULOS, TIPOS_VINCULO


class FichaCnesVinculo(db.Model):
    """Registro de cada ficha CNES gerada (cadastro ou descadastro) para um
    profissional em uma unidade específica.

    Cada vez que alguém clica em 'Vincular' ou 'Descadastrar', o sistema
    preenche um formulário modal e grava aqui — preservando os dados
    exatamente como foram informados naquele momento.
    """
    __tablename__ = 'ficha_cnes_vinculo'

    id                       = db.Column(db.Integer, primary_key=True)
    usuario_id               = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    unidade_id               = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='CASCADE'), nullable=False)
    tipo                     = db.Column(db.String(20), nullable=False, default='cadastro')  # cadastro | descadastro
    vinculo                  = db.Column(db.String(1))
    tipo_vinculo             = db.Column(db.String(1))
    carga_horaria            = db.Column(db.SmallInteger)
    cbo                      = db.Column(db.String(10))
    especialidade_residencia = db.Column(db.String(200))
    dt_entrada_unidade       = db.Column(db.Date)
    cns_profissional         = db.Column(db.String(20))
    cnpj_empresa             = db.Column(db.String(20))   # obrigatório quando tipo_vinculo=3 ou vinculo=6
    nome_empresa             = db.Column(db.String(200))  # razão social da empresa contratante/estágio
    observacoes              = db.Column(db.Text)
    gerado_por               = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    gerado_em                = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    emails_enviados          = db.Column(db.Boolean, nullable=False, default=False)

    usuario   = db.relationship('Usuario', foreign_keys=[usuario_id], backref=db.backref('fichas_cnes', lazy='dynamic'))
    unidade   = db.relationship('Unidade',  foreign_keys=[unidade_id], backref=db.backref('fichas_cnes', lazy='dynamic'))
    gerador   = db.relationship('Usuario',  foreign_keys=[gerado_por])

    @property
    def tipo_label(self):
        return {'cadastro': 'Cadastro', 'alteracao': 'Alteração', 'descadastro': 'Descadastro'}.get(self.tipo, self.tipo)

    @property
    def tipo_badge(self):
        return {'cadastro': 'success', 'alteracao': 'warning', 'descadastro': 'danger'}.get(self.tipo, 'secondary')

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

    def __repr__(self):
        return f'<FichaCnesVinculo {self.tipo} u={self.usuario_id} un={self.unidade_id}>'
