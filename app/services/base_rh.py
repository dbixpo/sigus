# -*- coding: utf-8 -*-
"""Base de servidores do RH (aba "Banco de Dados" da planilha de frequência) e de-para função → CBO."""
import difflib
import re
import unicodedata

from app import db
from app.models.cbo import CBO
from app.models.frequencia import RhFuncaoCbo, RhServidor, normalizar_matricula
from app.models.matricula import MatriculaProfissional

VINCULO_EMPREGATICIO = '1'
TIPO_ESTATUTARIO = '1'


def _sem_acento(txt):
    return unicodedata.normalize('NFKD', txt or '').encode('ascii', 'ignore').decode()


_IGNORAR = {'DE', 'DA', 'DO', 'DOS', 'DAS', 'E', 'EM', 'I', 'II', 'III', 'IV', 'FG', 'F'}
_ABREVIACOES = {
    'AUX': 'AUXILIAR', 'TEC': 'TECNICO', 'ASSIST': 'ASSISTENTE', 'MED': 'MEDICO', 'ENFERM': 'ENFERMAGEM',
    'COORD': 'COORDENADOR', 'RECEP': 'RECEPCIONISTA', 'ENG': 'ENGENHEIRO', 'LAB': 'LABORATORIO',
    'ANAL': 'ANALISES', 'CLIN': 'CLINICAS', 'VIG': 'VIGILANCIA', 'SEG': 'SEGURANCA', 'SUPERV': 'SUPERVISOR',
}


def _chave(txt):
    s = _sem_acento(txt).upper()
    s = re.sub(r'\b\d+\s*H\b', ' ', s)
    s = re.sub(r'[^A-Z ]', ' ', s)
    return ' '.join(_ABREVIACOES.get(p, p) for p in s.split() if p not in _IGNORAR)


def mapa_funcao_cbo():
    return {f.funcao: f.cbo for f in RhFuncaoCbo.query.filter(RhFuncaoCbo.cbo.isnot(None)).all()}


def sugerir_cbo(funcao, cbos):
    """Melhor CBO pelo nome da função; cbos = [(codigo, descricao)]. None se nada parecido."""
    alvo = _chave(funcao)
    if not alvo:
        return None
    primeira = alvo.split()[0]
    melhor, nota = None, 0.0
    for cod, desc in cbos:
        d = _chave(desc)
        if primeira not in d.split():
            continue
        r = difflib.SequenceMatcher(None, alvo, d).ratio()
        if d.startswith(alvo) or alvo.startswith(d):
            r += 0.1
        if r > nota:
            melhor, nota = cod, r
    return melhor if nota >= 0.75 else None


def donos_matriculas(numeros):
    """{matrícula normalizada: Usuario} para as matrículas já cadastradas no SIGUS."""
    alvo = {normalizar_matricula(n) for n in numeros}
    alvo.discard('')
    if not alvo:
        return {}
    donos = {}
    for m in MatriculaProfissional.query.filter(MatriculaProfissional.numero.isnot(None)).all():
        n = normalizar_matricula(m.numero)
        if n in alvo and n not in donos:
            donos[n] = m.usuario
    return donos


def buscar_servidores(q, limite=15):
    q = (q or '').strip()
    if not q:
        return []
    digitos = normalizar_matricula(q) if re.fullmatch(r'[\d.\-/ ]+', q) else ''
    base = RhServidor.query
    if digitos:
        exato = base.filter(RhServidor.matricula == digitos).all()
        resto = (base.filter(RhServidor.matricula.like(digitos + '%'), RhServidor.matricula != digitos)
                 .order_by(RhServidor.matricula).limit(limite).all())
        return (exato + resto)[:limite]
    tokens = [t for t in _sem_acento(q).upper().split() if len(t) > 1]
    if not tokens:
        return []
    for t in tokens:
        base = base.filter(RhServidor.nome.ilike(f'%{t}%'))
    return base.order_by(RhServidor.nome).limit(limite).all()


def servidores_json(servidores, usuario_atual_id=None):
    mapa = mapa_funcao_cbo()
    descs = dict(db.session.query(CBO.codigo, CBO.descricao).all())
    donos = donos_matriculas([s.matricula for s in servidores])
    itens = []
    for s in servidores:
        cbo = mapa.get(s.funcao)
        dono = donos.get(s.matricula)
        itens.append({
            'matricula': s.matricula,
            'nome': s.nome,
            'funcao': s.funcao or '',
            'local': s.local or '',
            'cbo': cbo or '',
            'cbo_desc': descs.get(cbo, '') if cbo else '',
            'usuario_id': dono.id if dono else None,
            'usuario_nome': dono.nome if dono else '',
            'eh_do_usuario': bool(dono and usuario_atual_id and dono.id == usuario_atual_id),
        })
    return itens


def cadastrar_matriculas_rh(usuario, numeros):
    """Cria as matrículas escolhidas da base do RH no cadastro do usuário, com o CBO do de-para.
    Ignora as que não estão na base ou que já pertencem a alguém."""
    numeros = [n for n in {normalizar_matricula(x) for x in numeros} if n]
    if not numeros:
        return [], []
    donos = donos_matriculas(numeros)
    mapa = mapa_funcao_cbo()
    criadas, ignoradas = [], []
    for num in sorted(numeros):
        srv = RhServidor.query.filter_by(matricula=num).first()
        if not srv or num in donos:
            ignoradas.append(num)
            continue
        db.session.add(MatriculaProfissional(
            usuario_id=usuario.id, numero=srv.matricula, vinculo=VINCULO_EMPREGATICIO,
            tipo_vinculo=TIPO_ESTATUTARIO, cbo=mapa.get(srv.funcao), ativo=True,
        ))
        criadas.append(num)
    return criadas, ignoradas
