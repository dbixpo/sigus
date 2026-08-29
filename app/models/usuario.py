from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from app.utils import prefixed_static_url


PERFIS = {
    'administrador': 'Administrador',
    'gestor_secretaria': 'Gestor Central',
    'coordenador': 'Gestor de Área',
    'administrativo': 'Apoio Administrativo',
    'profissional': 'Operador Padrão',
}

HIERARQUIA = {
    'administrador': 5,
    'gestor_secretaria': 4,
    'coordenador': 3,
    'administrativo': 2,
    'profissional': 1,
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
    ('317110', 'Programador de sistemas de informação'),
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
    __tablename__ = 'usuarios'

    id            = db.Column(db.Integer, primary_key=True)
    nome          = db.Column(db.String(150), nullable=False)
    email         = db.Column(db.String(200), nullable=False, unique=True)
    senha_hash    = db.Column(db.String(256), nullable=False)
    perfil        = db.Column(db.String(30), nullable=False, default='profissional')
    whatsapp      = db.Column(db.String(20))
    foto_perfil   = db.Column(db.String(200))   # filename em static/uploads/perfis/
    ativo         = db.Column(db.Boolean, nullable=False, default=True)
    criado_em     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Dados pessoais
    cpf            = db.Column(db.String(14))
    cns            = db.Column(db.String(20))
    sexo           = db.Column(db.String(1))          # M / F
    data_nasc      = db.Column(db.Date)
    nome_mae       = db.Column(db.String(200))
    nome_pai       = db.Column(db.String(200))
    nacionalidade  = db.Column(db.String(20), default='brasileira')
    uf_nasc        = db.Column(db.String(2))
    municipio_nasc = db.Column(db.String(100))
    dt_entrada_pais = db.Column(db.Date)
    pais_origem    = db.Column(db.String(100))
    rg             = db.Column(db.String(20))
    rg_uf          = db.Column(db.String(2))
    rg_orgao       = db.Column(db.String(50))
    rg_emissao     = db.Column(db.Date)
    escolaridade   = db.Column(db.String(2))
    frequenta_escola = db.Column(db.Boolean)

    # Endereço
    end_logradouro   = db.Column(db.String(300))
    end_numero       = db.Column(db.String(20))
    end_complemento  = db.Column(db.String(100))
    end_bairro       = db.Column(db.String(100))
    end_municipio    = db.Column(db.String(100))
    end_uf           = db.Column(db.String(2))
    end_cep          = db.Column(db.String(9))
    telefone         = db.Column(db.String(20))

    # Dados profissionais
    reg_conselho             = db.Column(db.String(30))
    orgao_emissor            = db.Column(db.String(50))
    vinculo                  = db.Column(db.String(1))
    tipo_vinculo             = db.Column(db.String(1))
    carga_horaria            = db.Column(db.SmallInteger)
    cbo                      = db.Column(db.String(10))
    especialidade_residencia = db.Column(db.String(200))
    dt_entrada_unidade       = db.Column(db.Date)
    matricula                = db.Column(db.String(50))

    unidades              = db.relationship('UsuarioUnidade', back_populates='usuario', lazy='dynamic')
    matriculas            = db.relationship('MatriculaProfissional', back_populates='usuario', lazy='dynamic',
                                            order_by='MatriculaProfissional.numero')
    unidade_padrao_id     = db.Column(db.Integer, db.ForeignKey('unidades.id', ondelete='SET NULL'))
    unidade_padrao        = db.relationship('Unidade', foreign_keys=[unidade_padrao_id])
    chamados_abertos      = db.relationship('Chamado', foreign_keys='Chamado.aberto_por', back_populates='solicitante', lazy='dynamic')
    chamados_responsavel  = db.relationship('Chamado', foreign_keys='Chamado.responsavel_id', back_populates='responsavel', lazy='dynamic')

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def perfil_label(self):
        return PERFIS.get(self.perfil, self.perfil)

    @property
    def nivel(self):
        return HIERARQUIA.get(self.perfil, 0)

    @property
    def foto_url(self):
        if self.foto_perfil:
            return prefixed_static_url(f'/static/uploads/perfis/{self.foto_perfil}')
        return None

    @property
    def inicial(self):
        return (self.nome or '?')[0].upper()

    @property
    def notificacoes_nao_lidas(self):
        try:
            from app.models.notificacao import Notificacao
            return Notificacao.query.filter_by(usuario_id=self.id, lida=False).count()
        except Exception:
            return 0

    @property
    def cbo_label(self):
        for cod, desc in CBOS:
            if cod == self.cbo:
                return f'{cod} - {desc}'
        return self.cbo or '—'

    @property
    def vinculo_label(self):
        return VINCULOS.get(self.vinculo, '—')

    @property
    def tipo_vinculo_label(self):
        return TIPOS_VINCULO.get(self.tipo_vinculo, '—')

    @property
    def escolaridade_label(self):
        return ESCOLARIDADES.get(self.escolaridade, '—')

    @property
    def requer_vinculo(self):
        """Retorna True para perfis que precisam obrigatoriamente de vínculo com unidade."""
        return self.perfil not in ('administrador', 'gestor_secretaria')

    @property
    def unidades_ativas(self):
        """Lista de objetos Unidade às quais o usuário está vinculado e ativas."""
        from app.models.unidade import Unidade, UsuarioUnidade
        return (
            Unidade.query
            .join(UsuarioUnidade, UsuarioUnidade.unidade_id == Unidade.id)
            .filter(
                UsuarioUnidade.usuario_id == self.id,
                UsuarioUnidade.ativo == True,
                Unidade.status == 'ativa',
            )
            .order_by(Unidade.nome)
            .all()
        )

    @property
    def tem_vinculo(self):
        """Retorna True se o usuário tem pelo menos uma unidade ativa vinculada."""
        if not self.requer_vinculo:
            return True
        return len(self.unidades_ativas) > 0

    @property
    def unidade_principal(self):
        """Retorna a primeira unidade ativa vinculada (exibida na navbar).
        Para perfis que não requerem vínculo retorna None."""
        lista = self.unidades_ativas
        return lista[0] if lista else None

    def ids_unidades_efetivos(self):
        """Retorna lista de ids de unidades para ações (aceitar transferência, lojinha, etc.).
        Considera unidade_padrao_id: gestor central em 'Todas' retorna None; com unidade
        selecionada retorna [id]. Usuários com vínculos: retorna unidade_padrao se definida
        e válida, senão todas as vinculadas."""
        if self.pode('ver_todas_unidades'):
            if self.unidade_padrao_id:
                un = self.unidade_padrao
                if un and un.status == 'ativa':
                    return [self.unidade_padrao_id]
            return None  # Todas
        ids = [uu.unidade_id for uu in self.unidades.filter_by(ativo=True).all()]
        if not ids:
            return None
        if self.unidade_padrao_id and self.unidade_padrao_id in ids:
            return [self.unidade_padrao_id]
        return ids

    @property
    def setores_vinculados(self):
        """Lista de SetorManutencao aos quais o usuário está vinculado."""
        from app.models.chamado import UsuarioSetor
        vinculos = UsuarioSetor.query.filter_by(usuario_id=self.id).all()
        return [v.setor for v in vinculos if v.setor]

    @property
    def divisoes_vinculadas(self):
        """Divisões às quais o usuário pertence (via setores)."""
        divs = []
        seen = set()
        for s in self.setores_vinculados:
            if s and s.divisao and s.divisao.ativo and s.divisao.id not in seen:
                seen.add(s.divisao.id)
                divs.append(s.divisao)
        return divs

    @property
    def tipos_chamado_divisoes(self):
        """Tipos de chamado que as divisões do usuário cuidam."""
        out = set()
        for d in self.divisoes_vinculadas:
            out.update(d.tipos_chamado or [])
        return list(out)

    @property
    def tipos_unidade_ids_divisoes(self):
        """IDs de TipoUnidade que as divisões do usuário supervisionam."""
        out = set()
        for d in self.divisoes_vinculadas:
            out.update(d.tipos_unidade_ids or [])
        return list(out)

    @property
    def tem_setor(self):
        """True se o usuário está vinculado a pelo menos um setor de manutenção,
        ou se tem perfil que vê todos os chamados (admin, gestor central)."""
        if self.perfil in ('administrador', 'gestor_secretaria'):
            return True
        return len(self.setores_vinculados) > 0

    def pode(self, acao):
        # Administrador tem acesso total (não consulta DB)
        if self.perfil == 'administrador':
            return True
        # Gestão de perfis — apenas administrador
        if acao == 'gerenciar_perfis':
            return False
        # Casos especiais que dependem de outros fatores
        if acao == 'gerir_chamados_setor':
            return self.tem_setor
        # Demais ações: consulta perfil_permissoes
        from app.models.perfil_permissao import PerfilPermissao, ACAO_PARA_SECAO_TIPO
        mapeamento = ACAO_PARA_SECAO_TIPO.get(acao)
        if not mapeamento:
            return False
        secao, tipo = mapeamento
        return PerfilPermissao.tem_permissao(self.perfil, secao, tipo)

    def __repr__(self):
        return f'<Usuario {self.email} [{self.perfil}]>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))
