"""Modelo de usuário do sistema SAMU com perfis específicos."""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


# Perfis do SAMU conforme portaria ministerial
PERFIS = {
    'administrador': 'Administrador',
    'tarm': 'TARM',
    'radio_operador': 'Rádio Operador',
    'medico_regulador': 'Médico Regulador',
    'medico_intervencionista': 'Médico Intervencionista',
    'enfermeiro': 'Enfermeiro',
    'aux_tec_enfermagem': 'Aux./Téc. Enfermagem',
    'condutor': 'Condutor',
}

ESCOLARIDADES = {
    '01': 'Não sabe ler/escrever',
    '02': 'Alfabetizado',
    '03': '1º grau incompleto',
    '04': '1º grau concluído',
    '05': '2º grau incompleto',
    '06': '2º grau completo',
    '07': 'Superior incompleto',
    '08': 'Superior completo',
    '09': 'Especialização / Residência',
    '10': 'Mestrado',
    '11': 'Doutorado',
}

VINCULOS = {
    '1': 'Vínculo Empregatício',
    '5': 'Residência',
    '6': 'Estágio',
}

TIPOS_VINCULO = {
    '1': 'Estatutário',
    '3': 'Contrato por Prazo Determinado',
    '0': 'Sem Tipo',
}

# CBOs — lista igual à do SIGUS
CBOS = [
    ('252105', 'Administrador'),
    ('515105', 'Agente Comunitário de Saúde'),
    ('515310', 'Agente de Ação Social'),
    ('352210', 'Agente de Saúde Pública'),
    ('517310', 'Agente de Segurança'),
    ('414105', 'Almoxarife'),
    ('411010', 'Assistente Administrativo'),
    ('251605', 'Assistente Social'),
    ('515110', 'Atendente de Enfermagem'),
    ('521130', 'Atendente de Farmácia - Balconista'),
    ('252205', 'Auditor (Contadores e Afins)'),
    ('322430', 'Auxiliar de Consultório Dentário de Saúde da Família'),
    ('322230', 'Auxiliar de Enfermagem'),
    ('322250', 'Auxiliar de Enfermagem da Estratégia de Saúde da Família'),
    ('322235', 'Auxiliar de Enfermagem do Trabalho'),
    ('411005', 'Auxiliar de Escritório, em Geral'),
    ('515215', 'Auxiliar de Laboratório de Análises Clínicas'),
    ('322420', 'Auxiliar de Prótese Dentária'),
    ('766420', 'Auxiliar de Radiologia (Revelação Fotográfica)'),
    ('322415', 'Auxiliar em Saúde Bucal'),
    ('322430', 'Auxiliar em Saúde Bucal da Estratégia de Saúde da Família'),
    ('324210', 'Auxiliar Técnico em Patologia Clínica'),
    ('221105', 'Biólogo'),
    ('221205', 'Biomédico'),
    ('223204', 'Cirurgião Dentista - Auditor'),
    ('223208', 'Cirurgião Dentista - Clínico Geral'),
    ('223280', 'Cirurgião Dentista - Dentística'),
    ('223212', 'Cirurgião Dentista - Endodontista'),
    ('223220', 'Cirurgião Dentista - Estomatologista'),
    ('223288', 'Cirurgião Dentista - Odontologia para Pacientes com Necessidades Especiais'),
    ('223232', 'Cirurgião Dentista - Odontologista Legal'),
    ('223240', 'Cirurgião Dentista - Ortopedista e Ortodontista'),
    ('223244', 'Cirurgião Dentista - Patologista Bucal'),
    ('223248', 'Cirurgião Dentista - Periodontista'),
    ('223256', 'Cirurgião Dentista - Protesista'),
    ('223268', 'Cirurgião Dentista - Traumatologista Bucomaxilofacial'),
    ('223293', 'Cirurgião-Dentista da Estratégia de Saúde da Família'),
    ('354205', 'Comprador'),
    ('516220', 'Cuidador em Saúde'),
    ('123105', 'Diretor Administrativo'),
    ('131205', 'Diretor de Serviços de Saúde'),
    ('111415', 'Dirigente do Serviço Público Municipal'),
    ('512115', 'Empregado Doméstico Faxineiro'),
    ('223505', 'Enfermeiro'),
    ('223510', 'Enfermeiro Auditor'),
    ('223565', 'Enfermeiro da Estratégia de Saúde da Família'),
    ('223525', 'Enfermeiro de Terapia Intensiva'),
    ('223530', 'Enfermeiro do Trabalho'),
    ('223545', 'Enfermeiro Obstétrico'),
    ('223555', 'Enfermeiro Puericultor e Pediátrico'),
    ('214915', 'Engenheiro de Segurança do Trabalho'),
    ('223405', 'Farmacêutico'),
    ('223410', 'Farmacêutico Bioquímico'),
    ('514320', 'Faxineiro'),
    ('223605', 'Fisioterapeuta Geral'),
    ('223635', 'Fisioterapeuta Traumato-Ortopédica Funcional'),
    ('223810', 'Fonoaudiólogo'),
    ('142105', 'Gerente Administrativo'),
    ('131210', 'Gerente de Serviços de Saúde'),
    ('131220', 'Gerontólogo'),
    ('225110', 'Médico Alergista e Imunologista'),
    ('225148', 'Médico Anatomopatologista'),
    ('225151', 'Médico Anestesiologista'),
    ('225115', 'Médico Angiologista'),
    ('225120', 'Médico Cardiologista'),
    ('225210', 'Médico Cirurgião Cardiovascular'),
    ('225215', 'Médico Cirurgião de Cabeça e Pescoço'),
    ('225225', 'Médico Cirurgião Geral'),
    ('225230', 'Médico Cirurgião Pediátrico'),
    ('225235', 'Médico Cirurgião Plástico'),
    ('225240', 'Médico Cirurgião Torácico'),
    ('225125', 'Médico Clínico'),
    ('225280', 'Médico Coloproctologista'),
    ('225142', 'Médico da Estratégia de Saúde da Família'),
    ('225130', 'Médico de Família e Comunidade'),
    ('225135', 'Médico Dermatologista'),
    ('225140', 'Médico do Trabalho'),
    ('225203', 'Médico em Cirurgia Vascular'),
    ('225310', 'Médico em Endoscopia'),
    ('225320', 'Médico em Radiologia e Diagnóstico por Imagem'),
    ('225155', 'Médico Endocrinologista e Metabologista'),
    ('225160', 'Médico Fisiatra'),
    ('225165', 'Médico Gastroenterologista'),
    ('225170', 'Médico Generalista'),
    ('225175', 'Médico Geneticista'),
    ('225180', 'Médico Geriatra'),
    ('225250', 'Médico Ginecologista e Obstetra'),
    ('2231A2', 'Médico Hansenologista'),
    ('225185', 'Médico Hematologista'),
    ('225103', 'Médico Infectologista'),
    ('225255', 'Médico Mastologista'),
    ('225109', 'Médico Nefrologista'),
    ('225260', 'Médico Neurocirurgião'),
    ('225112', 'Médico Neurologista'),
    ('225265', 'Médico Oftalmologista'),
    ('225121', 'Médico Oncologista Clínico'),
    ('225270', 'Médico Ortopedista e Traumatologista'),
    ('225275', 'Médico Otorrinolaringologista'),
    ('225325', 'Médico Patologista'),
    ('225335', 'Médico Patologista Clínico / Medicina Laboratorial'),
    ('225124', 'Médico Pediatra'),
    ('225127', 'Médico Pneumologista'),
    ('223152', 'Médico Proctologista'),
    ('225133', 'Médico Psiquiatra'),
    ('2231F9', 'Médico Residente'),
    ('225136', 'Médico Reumatologista'),
    ('225139', 'Médico Sanitarista'),
    ('225285', 'Médico Urologista'),
    ('223305', 'Médico Veterinário'),
    ('782305', 'Motorista de Carro de Passeio'),
    ('782310', 'Motorista de Furgão ou Veículo Similar'),
    ('223710', 'Nutricionista'),
    ('322110', 'Podólogo'),
    ('517410', 'Porteiro de Edifícios'),
    ('224120', 'Preparador Físico'),
    ('234410', 'Professor de Educação Física no Ensino Superior'),
    ('224140', 'Profissional de Educação Física na Saúde'),
    ('251550', 'Psicanalista'),
    ('251510', 'Psicólogo Clínico'),
    ('251540', 'Psicólogo do Trabalho'),
    ('251520', 'Psicólogo Hospitalar'),
    ('251530', 'Psicólogo Social'),
    ('422110', 'Recepcionista de Consultório Médico ou Dentário'),
    ('422105', 'Recepcionista, em Geral'),
    ('371410', 'Recreador'),
    ('111220', 'Secretário-Executivo'),
    ('515135', 'Socorrista (Exceto Médicos e Enfermeiros)'),
    ('3222B3', 'Socorrista Habilitado'),
    ('410105', 'Supervisor Administrativo'),
    ('322205', 'Técnico de Enfermagem'),
    ('322245', 'Técnico de Enfermagem da Estratégia de Saúde da Família'),
    ('301110', 'Técnico de Laboratório de Análises Físico-Químicas'),
    ('312105', 'Técnico de Obras Civis'),
    ('351305', 'Técnico em Administração'),
    ('325115', 'Técnico em Farmácia'),
    ('325110', 'Técnico em Laboratório de Farmácia'),
    ('324205', 'Técnico em Patologia Clínica'),
    ('324115', 'Técnico em Radiologia e Imagenologia'),
    ('422205', 'Telefonista'),
    ('422210', 'Teleoperador'),
    ('223905', 'Terapeuta Ocupacional'),
    ('514225', 'Trabalhador de Serviços de Limpeza e Conservação de Áreas Públicas'),
    ('517420', 'Vigia'),
    ('517330', 'Vigilante'),
    ('515120', 'Visitador Sanitário'),
    ('514120', 'Zelador de Edifício'),
]


class Usuario(UserMixin, db.Model):
    """Usuário/profissional do sistema SAMU. Login por usuário de acesso."""
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    # Acesso: usuário de acesso (login) e senha
    usuario = db.Column(db.String(80), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(256), nullable=False)
    perfil = db.Column(db.String(200), nullable=False, default='tarm')  # perfil único (select)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    nome = db.Column(db.String(150), nullable=False)
    apelido = db.Column(db.String(80))
    email = db.Column(db.String(200))
    foto_perfil = db.Column(db.String(200))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unidade SAMU de lotação
    unidade_samu_id = db.Column(db.Integer, db.ForeignKey('unidades_samu.id', ondelete='SET NULL'))
    unidade_samu = db.relationship('UnidadeSamu', backref=db.backref('usuarios', lazy='dynamic'))

    # Dados pessoais
    cpf = db.Column(db.String(14))
    cns = db.Column(db.String(20))
    sexo = db.Column(db.String(1))
    data_nasc = db.Column(db.Date)
    nome_mae = db.Column(db.String(200))
    nome_pai = db.Column(db.String(200))
    nacionalidade = db.Column(db.String(20), default='brasileira')
    uf_nasc = db.Column(db.String(2))
    municipio_nasc = db.Column(db.String(100))
    dt_entrada_pais = db.Column(db.Date)
    pais_origem = db.Column(db.String(100))
    rg = db.Column(db.String(20))
    rg_uf = db.Column(db.String(2))
    rg_orgao = db.Column(db.String(50))
    rg_emissao = db.Column(db.Date)
    escolaridade = db.Column(db.String(2))
    frequenta_escola = db.Column(db.Boolean)

    # Endereço
    end_logradouro = db.Column(db.String(300))
    end_numero = db.Column(db.String(20))
    end_complemento = db.Column(db.String(100))
    end_bairro = db.Column(db.String(100))
    end_municipio = db.Column(db.String(100))
    end_uf = db.Column(db.String(2))
    end_cep = db.Column(db.String(9))
    telefone = db.Column(db.String(20))
    whatsapp = db.Column(db.String(20))

    # Dados profissionais
    reg_conselho = db.Column(db.String(30))
    orgao_emissor = db.Column(db.String(50))
    vinculo = db.Column(db.String(1))
    tipo_vinculo = db.Column(db.String(1))
    carga_horaria = db.Column(db.SmallInteger)
    cbo = db.Column(db.String(10))
    especialidade_residencia = db.Column(db.String(200))
    dt_entrada_unidade = db.Column(db.Date)
    matricula = db.Column(db.String(50))

    matriculas = db.relationship('MatriculaProfissional', back_populates='usuario', lazy='dynamic',
                                 cascade='all, delete-orphan')

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def perfis_list(self):
        """Lista de códigos de perfil (ex: ['tarm', 'enfermeiro'])."""
        if not self.perfil:
            return ['tarm']
        return [p.strip() for p in self.perfil.split(',') if p.strip()]

    @property
    def perfil_label(self):
        """Labels dos perfis separados por vírgula."""
        return ', '.join(PERFIS.get(p, p) for p in self.perfis_list) or '—'

    @property
    def perfil_primario(self):
        """Primeiro perfil da lista."""
        return self.perfis_list[0] if self.perfis_list else 'tarm'

    @property
    def matricula_principal(self):
        """Primeira matrícula ativa (para Ficha CNES e listagem)."""
        return self.matriculas.filter_by(ativo=True).first()

    @property
    def foto_url(self):
        if self.foto_perfil:
            return f'/static/uploads/perfis/{self.foto_perfil}'
        return None

    @property
    def inicial(self):
        return (self.nome or '?')[0].upper()

    @property
    def nome_exibicao(self):
        return self.apelido or (self.nome.split()[0] if self.nome else '?')

    @property
    def escolaridade_label(self):
        return ESCOLARIDADES.get(self.escolaridade, '—')

    @property
    def vinculo_label(self):
        return VINCULOS.get(self.vinculo, '—')

    @property
    def tipo_vinculo_label(self):
        return TIPOS_VINCULO.get(self.tipo_vinculo, '—')

    @property
    def cbo_label(self):
        for cod, desc in CBOS:
            if cod == self.cbo:
                return f'{cod} – {desc}'
        return self.cbo or '—'

    def pode(self, acao):
        perfis = set(self.perfis_list)
        regras = {
            'configuracoes': 'administrador' in perfis,
            'gerenciar_usuarios': 'administrador' in perfis,
            'rh_faltas_abonadas': True,
            'rh_gerenciar_faltas': 'administrador' in perfis,
            'regulacao_medica': 'medico_regulador' in perfis or 'administrador' in perfis,
            'despacho_viaturas': 'radio_operador' in perfis or 'administrador' in perfis,
        }
        return regras.get(acao, False)

    def __repr__(self):
        return f'<Usuario {self.usuario} [{self.perfil}]>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))
