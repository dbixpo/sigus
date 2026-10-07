# -*- coding: utf-8 -*-
"""Frequência mensal enviada ao RH: siglas, importações e apontamentos por matrícula."""
from app import db
from app.utils import agora_local_callable

# Tabela de Legendas da aba "Instruções" da planilha de frequência.
# grupo: holerite = falta legal lançada no holerite; legal = falta legal fora do holerite; desconto
SIGLAS_JUSTIFICATIVA = {
    'FA':   ('Falta abonada', 'holerite'),
    'AM':   ('Atestado médico', 'holerite'),
    'AMM':  ('Atestado médico (manhã)', 'holerite'),
    'AMT':  ('Atestado médico (tarde)', 'holerite'),
    'LTPF': ('Licença para tratamento de pessoa da família', 'holerite'),
    'JE':   ('Justiça Eleitoral', 'legal'),
    'DS':   ('Doação de sangue', 'legal'),
    'DCM':  ('Declaração médica, odontológica ou de exames', 'legal'),
    'LN':   ('Licença nojo', 'legal'),
    'LNS':  ('Licença nojo sogro(a)', 'legal'),
    'LG':   ('Licença gala', 'legal'),
    'LP':   ('Licença paternidade', 'legal'),
    'FJ':   ('Falta justificada', 'desconto'),
    'FI':   ('Falta injustificada', 'desconto'),
    'FIM':  ('Falta injustificada (manhã)', 'desconto'),
    'FIT':  ('Falta injustificada (tarde)', 'desconto'),
}

GRUPOS_JUSTIFICATIVA = {
    'holerite': 'Faltas legais lançadas no holerite',
    'legal':    'Ausências legais fora do holerite',
    'desconto': 'Descontos',
}

# Ausências que a planilha registra na coluna "Complemento", com início e fim.
AFASTAMENTOS_COMPLEMENTO = {
    'FERIAS':      'Férias',
    'ACIDENTE':    'Acidente de trabalho',
    'AUX_DOENCA':  'Auxílio-doença',
    'JUDICIARIO':  'Convocação do Poder Judiciário',
    'CURSO':       'Reunião, curso ou treinamento (autorizado pela SES)',
    'JUBILEU':     'Jubileu de prata',
    'MATERNIDADE': 'Licença-maternidade ou adoção',
    'PREMIO':      'Licença-prêmio',
}


def motivo_ausencia_label(codigo):
    if not codigo:
        return ''
    if codigo in AFASTAMENTOS_COMPLEMENTO:
        return AFASTAMENTOS_COMPLEMENTO[codigo]
    if codigo in SIGLAS_JUSTIFICATIVA:
        return SIGLAS_JUSTIFICATIVA[codigo][0]
    if codigo == 'OUTRO':
        return 'Outro motivo'
    return codigo


def motivos_ausencia_agrupados():
    """Opções do campo Motivo da ausência na agenda, na ordem em que aparecem."""
    return [
        ('Afastamentos', list(AFASTAMENTOS_COMPLEMENTO.items())),
        (GRUPOS_JUSTIFICATIVA['holerite'], [(k, v[0]) for k, v in SIGLAS_JUSTIFICATIVA.items() if v[1] == 'holerite']),
        (GRUPOS_JUSTIFICATIVA['legal'], [(k, v[0]) for k, v in SIGLAS_JUSTIFICATIVA.items() if v[1] == 'legal']),
        (GRUPOS_JUSTIFICATIVA['desconto'], [(k, v[0]) for k, v in SIGLAS_JUSTIFICATIVA.items() if v[1] == 'desconto']),
        ('Outros', [('OUTRO', 'Outro motivo')]),
    ]


def motivo_ausencia_valido(codigo):
    return codigo in AFASTAMENTOS_COMPLEMENTO or codigo in SIGLAS_JUSTIFICATIVA or codigo == 'OUTRO'


# Colunas de totais da aba "Capa" (em dias).
TOTAIS_CAPA = [
    ('FA', 'Falta abonada'),
    ('AM', 'Atestado médico'),
    ('LTPF', 'LTPF'),
    ('JE', 'Justiça Eleitoral'),
    ('DS', 'Doação de sangue'),
    ('LN', 'Licença nojo'),
    ('LG', 'Licença gala'),
    ('LP', 'Licença paternidade'),
    ('FJ', 'Falta justificada'),
    ('FI', 'Falta injustificada'),
    ('DSR', 'Falta DSR'),
]

TIPOS_HORA_EXTRA = [
    ('he50', 'HE 50%'),
    ('he100', 'HE 100%'),
    ('he50_not', 'HE 50% noturna'),
    ('he100_not', 'HE 100% noturna'),
]

MESES_PT = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho',
            'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']


def competencia_label(d):
    return f'{MESES_PT[d.month - 1].capitalize()}/{d.year}' if d else ''


def normalizar_matricula(valor):
    """'578495', 578495.0, ' 0578495 ' → '578495'. Devolve '' se não houver dígitos."""
    if valor is None:
        return ''
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    digitos = ''.join(ch for ch in str(valor) if ch.isdigit())
    return digitos.lstrip('0')


PERFIS_RH_TOTAL = ('administrador', 'gestor_secretaria')
PAPEIS_GESTOR_UNIDADE = ('gestor_principal', 'gestor_secundario')


def unidades_gestao_rh(usuario):
    """Unidades cujos apontamentos o usuário gere. None = todas; set() vazio = nenhuma."""
    if usuario.perfil in PERFIS_RH_TOTAL:
        return None
    from app.models.unidade import UsuarioUnidade
    q = usuario.unidades.filter_by(ativo=True)
    if usuario.perfil != 'coordenador':
        q = q.filter(UsuarioUnidade.papel.in_(PAPEIS_GESTOR_UNIDADE))
    return {uu.unidade_id for uu in q.all()}


def matriculas_do_usuario(usuario):
    """Matrículas normalizadas do usuário (cadastro de matrículas + campo legado)."""
    nums = {normalizar_matricula(m.numero) for m in usuario.matriculas.filter_by(ativo=True).all()}
    nums.add(normalizar_matricula(usuario.matricula))
    nums.discard('')
    return nums


class RhLocal(db.Model):
    """De-para: nome do local na planilha do RH → unidade do SIGUS."""
    __tablename__ = 'rh_locais'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable,
                              onupdate=agora_local_callable)

    unidade = db.relationship('Unidade')


class RhServidor(db.Model):
    """Base de servidores que o RH manda na aba oculta "Banco de Dados"."""
    __tablename__ = 'rh_servidores'

    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(20), nullable=False, unique=True, index=True)
    nome = db.Column(db.String(200), nullable=False)
    funcao = db.Column(db.String(120))
    local = db.Column(db.String(120))
    competencia = db.Column(db.Date)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable,
                              onupdate=agora_local_callable)


class RhFuncaoCbo(db.Model):
    """De-para: função de concurso (como vem do RH) → CBO usado no CNES."""
    __tablename__ = 'rh_funcao_cbo'

    id = db.Column(db.Integer, primary_key=True)
    funcao = db.Column(db.String(120), nullable=False, unique=True)
    cbo = db.Column(db.String(10))
    atualizado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable,
                              onupdate=agora_local_callable)


class FreqImportacao(db.Model):
    """Cada planilha mensal importada. Reimportar o mesmo mês e local substitui a anterior."""
    __tablename__ = 'freq_importacoes'

    STATUS_ATIVA = 'ativa'
    STATUS_SUBSTITUIDA = 'substituida'

    id = db.Column(db.Integer, primary_key=True)
    competencia = db.Column(db.Date, nullable=False)
    local = db.Column(db.String(120), nullable=False)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='SET NULL'))
    arquivo = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False, default=STATUS_ATIVA)
    n_profissionais = db.Column(db.Integer, nullable=False, default=0)
    n_horas_extras = db.Column(db.Integer, nullable=False, default=0)
    n_servidores_base = db.Column(db.Integer, nullable=False, default=0)
    importado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    importado_em = db.Column(db.DateTime, nullable=False, default=agora_local_callable)
    substituida_em = db.Column(db.DateTime)

    unidade = db.relationship('Unidade')
    importador = db.relationship('Usuario', foreign_keys=[importado_por])
    lancamentos = db.relationship('FreqLancamento', back_populates='importacao',
                                  cascade='all, delete-orphan', lazy='dynamic')
    horas_extras = db.relationship('FreqHoraExtra', back_populates='importacao',
                                   cascade='all, delete-orphan', lazy='dynamic')

    @property
    def competencia_label(self):
        return competencia_label(self.competencia)

    @property
    def ativa(self):
        return self.status == self.STATUS_ATIVA


class FreqLancamento(db.Model):
    """Uma matrícula numa planilha: Capa + Justificativas + Banco de Horas + Horário."""
    __tablename__ = 'freq_lancamentos'

    id = db.Column(db.Integer, primary_key=True)
    importacao_id = db.Column(db.Integer, db.ForeignKey('freq_importacoes.id', ondelete='CASCADE'),
                              nullable=False, index=True)
    matricula = db.Column(db.String(20), nullable=False, index=True)
    nome = db.Column(db.String(200))
    funcao = db.Column(db.String(120))
    regime = db.Column(db.String(80))
    condicao = db.Column(db.String(40))
    tipo_jornada = db.Column(db.String(20))
    horas_mensais = db.Column(db.Float)
    vencimento = db.Column(db.Float)
    hora_noturna = db.Column(db.Float)
    totais = db.Column(db.JSON, default=dict)
    dias = db.Column(db.JSON, default=dict)
    complemento = db.Column(db.Text)
    horario = db.Column(db.Text)
    banco_saldo_anterior = db.Column(db.Float)
    banco_realizadas = db.Column(db.Float)
    banco_utilizadas = db.Column(db.Float)
    banco_saldo_atual = db.Column(db.Float)
    banco_obs = db.Column(db.Text)

    importacao = db.relationship('FreqImportacao', back_populates='lancamentos')

    @property
    def tem_banco(self):
        return self.banco_saldo_atual is not None

    @property
    def banco_confere(self):
        """Saldo atual = anterior + realizadas − utilizadas (tolerância de meia hora)."""
        if self.banco_saldo_atual is None:
            return True
        esperado = (self.banco_saldo_anterior or 0) + (self.banco_realizadas or 0) - (self.banco_utilizadas or 0)
        return abs(esperado - self.banco_saldo_atual) < 0.01


class FreqHoraExtra(db.Model):
    """Horas extras lançadas por uma unidade para uma matrícula (pode ser de outra lotação)."""
    __tablename__ = 'freq_horas_extras'

    id = db.Column(db.Integer, primary_key=True)
    importacao_id = db.Column(db.Integer, db.ForeignKey('freq_importacoes.id', ondelete='CASCADE'),
                              nullable=False, index=True)
    matricula = db.Column(db.String(20), nullable=False, index=True)
    nome = db.Column(db.String(200))
    funcao = db.Column(db.String(120))
    he50 = db.Column(db.Float, nullable=False, default=0)
    he100 = db.Column(db.Float, nullable=False, default=0)
    he50_not = db.Column(db.Float, nullable=False, default=0)
    he100_not = db.Column(db.Float, nullable=False, default=0)

    importacao = db.relationship('FreqImportacao', back_populates='horas_extras')

    @property
    def total(self):
        return (self.he50 or 0) + (self.he100 or 0) + (self.he50_not or 0) + (self.he100_not or 0)
