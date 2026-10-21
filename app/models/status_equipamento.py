"""Status do equipamento cadastrados em Configurações.

A condição do bem continua sendo só Boa, Regular ou Ruim.
O status diz se essa condição é pedida e se o item pode ser transferido.
"""
import re
import unicodedata

from app import db
from app.models.status_chamado import BADGE_CORES
from app.utils import agora_local

CONDICOES_EQUIPAMENTO = ('boa', 'regular', 'ruim')
CONDICAO_LABELS = {
    'boa': 'Boa',
    'regular': 'Regular',
    'ruim': 'Ruim',
}
CONDICAO_BADGE = {
    'boa': 'success',
    'regular': 'primary',
    'ruim': 'warning',
}
_CONDICAO_LEGADA = {
    'em_condicoes_uso': 'boa',
    'excelente': 'boa',
    'necessita_manutencao': 'ruim',
    'inservivel': 'ruim',
}

_PADRAO = (
    ('ativo', 'Ativo', 'success', True, True, 1),
    ('inservivel', 'Inservível/Sem Recuperação', 'dark', False, False, 2),
    ('aguardando_instalacao', 'Aguardando Instalação', 'info', False, True, 3),
    ('disponivel_transferencia', 'Disponível/Transferência', 'primary', True, True, 4),
    ('sobressalente', 'Sobressalente/Reserva', 'secondary', True, True, 5),
)


class StatusEquipamento(db.Model):
    __tablename__ = 'status_de_equipamento'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(40), nullable=False, unique=True)
    nome = db.Column(db.String(80), nullable=False)
    badge_cor = db.Column(db.String(20), nullable=False, default='secondary')
    pede_condicao = db.Column(db.Boolean, nullable=False, default=True)
    pode_transferir = db.Column(db.Boolean, nullable=False, default=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    ordem = db.Column(db.Integer, nullable=False, default=0)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local)

    def __repr__(self):
        return f'<StatusEquipamento {self.codigo}>'


def garantir_status_equipamento():
    """Cria a tabela, grava os status que já existiam e junta a condição nas três."""
    StatusEquipamento.__table__.create(db.engine, checkfirst=True)
    if StatusEquipamento.query.count() == 0:
        for codigo, nome, cor, pede, transfere, ordem in _PADRAO:
            db.session.add(StatusEquipamento(
                codigo=codigo, nome=nome, badge_cor=cor,
                pede_condicao=pede, pode_transferir=transfere,
                ativo=True, ordem=ordem,
            ))
        db.session.commit()
    from app.models.equipamento import Equipamento
    for antiga, nova in _CONDICAO_LEGADA.items():
        Equipamento.query.filter_by(condicao=antiga).update({Equipamento.condicao: nova})
    db.session.commit()


def mapa_status():
    from flask import g, has_request_context
    if has_request_context():
        cache = getattr(g, '_mapa_status_equipamento', None)
        if cache is not None:
            return cache
    garantir_status_equipamento()
    cache = {s.codigo: s for s in StatusEquipamento.query.all()}
    if has_request_context():
        g._mapa_status_equipamento = cache
    return cache


def limpar_cache_status():
    from flask import g, has_request_context
    if has_request_context() and hasattr(g, '_mapa_status_equipamento'):
        del g._mapa_status_equipamento


def opcoes_status(atual=None):
    garantir_status_equipamento()
    itens = (StatusEquipamento.query
             .filter_by(ativo=True)
             .order_by(StatusEquipamento.ordem, StatusEquipamento.nome)
             .all())
    if atual and all(s.codigo != atual for s in itens):
        extra = StatusEquipamento.query.filter_by(codigo=atual).first()
        if extra:
            itens.append(extra)
    return itens


def normalizar_condicao(valor):
    if not valor:
        return None
    valor = _CONDICAO_LEGADA.get(valor, valor)
    return valor if valor in CONDICOES_EQUIPAMENTO else None


def codigo_status(nome, ignorar_id=None):
    base = unicodedata.normalize('NFKD', nome or '').encode('ascii', 'ignore').decode().lower()
    base = re.sub(r'[^a-z0-9]+', '_', base).strip('_')[:36] or 'status'
    codigo = base
    n = 2
    while True:
        q = StatusEquipamento.query.filter_by(codigo=codigo)
        if ignorar_id:
            q = q.filter(StatusEquipamento.id != ignorar_id)
        if not q.first():
            return codigo
        codigo = f'{base[:34]}_{n}'
        n += 1
