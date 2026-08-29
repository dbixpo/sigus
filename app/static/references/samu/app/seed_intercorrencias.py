"""Seed de Intercorrências para o SAMU."""


def _titulo(s):
    """Primeira letra maiúscula, resto minúsculo."""
    if not s or not s.strip():
        return s
    return s.strip()[0].upper() + s.strip()[1:].lower()


INTERCORRENCIAS = """
NAO HOUVE INTERCORRENCIA
CANCELAMENTO PELO MEDICO REGULADOR
EQUIPE DE PLANTÃO SAMU RECUSOU RECEBER O CASO APOS REGULADO
DIFICULDADE DE ACESSO
PACIENTE REMOVIDO PELO CORPO DE BOMBEIROS
SOLICITANTE NAO ATENDE O TELEFONE
UNIDADE NAO ATENDE O TELEFONE
CRU SEM RECURSO TECNICO ESPECIFICO
ESTABELECIMENTO DE SAUDE SEM RECURSO TECNICO ESPECIFICO
EQUIPAMENTO DA UNIDADE MOVEL RETIDO EM ESTABELECIMENTO DE SAUDE
ACIDENTE UNIDADE MOVEL SAMU
PROBLEMA MECANICO DA UNIDADE MOVEL/EQUIPAMENTOS SAMU
PROBLEMA DE SAUDE DE EQUIPE DURANTE OCORRENCIA
DIFICULDADE DE COMUNICAÇÃO
EQUIPE DE ESTABELECIMENTO DE SAUDE RECUSOU RECEBER O PACIENTE
OBITO CONSTATADO NA CHEGADA DA EQUIPE
OBITO NO LOCAL DO EVENTO DURANTE O ATENDIMENTO
OBITO DURANTE O TRANSPORTE
ENDEREÇO DA OCORRÊNCIA NAO ENCONTRADO
PACIENTE JA ATENDIDO POR OUTRO SERVIÇO DE APH
CANCELADO PELO SOLICITANTE
PACIENTE RECUSOU REMOCAO
PACIENTE EVADIU-SE DO LOCAL
AREA DE RISCO A EQUIPE
INDISPONIBILIDADE DE ACESSO
REMOVIDO POR TERCEIROS
TROTE
""".strip()


def run_seed(app):
    """Executa o seed de intercorrências."""
    from app import db
    from app.models.intercorrencia import Intercorrencia

    with app.app_context():
        criados = 0
        for linha in INTERCORRENCIAS.split('\n'):
            nome = _titulo(linha.strip())
            if not nome:
                continue
            if not Intercorrencia.query.filter_by(nome=nome).first():
                i = Intercorrencia(nome=nome, ativo=True)
                db.session.add(i)
                criados += 1
        db.session.commit()
        return criados
