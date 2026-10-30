# -*- coding: utf-8 -*-
"""Painéis do Metabase incorporados no SIGUS.

A chave de incorporação fica nesta tabela (e, na instalação, no .env).
O navegador só recebe o endereço já assinado, nunca a chave.
"""
import ast
import html
import re
import time

import jwt

from app import db
from app.utils import agora_local

# O relógio do Metabase está horas à frente deste PC. Dez minutos já nasce
# vencido. Dez anos cobre essa diferença e a apresentação fica aberta.
EXP_SEGUNDOS = 60 * 60 * 24 * 365 * 10

# O IIS na frente do Metabase recusa um pedaço de endereço maior que 260
# caracteres e devolve "Bad Request - Invalid URL". O token vai nesse pedaço.
LIMITE_TOKEN_IIS = 250


def _pular_string(texto, i):
    aspas = texto[i]
    i += 1
    while i < len(texto):
        if texto[i] == '\\':
            i += 2
            continue
        if texto[i] == aspas:
            return i + 1
        i += 1
    return i


def _extrair_chaves(texto, inicio):
    profundidade = 0
    i = inicio
    while i < len(texto):
        caractere = texto[i]
        if caractere in ('"', "'"):
            i = _pular_string(texto, i)
            continue
        if caractere == '{':
            profundidade += 1
        elif caractere == '}':
            profundidade -= 1
            if profundidade == 0:
                return texto[inicio:i + 1]
        i += 1
    return None


def _bloco_payload(texto):
    achado = re.search(r'\bpayload\s*=\s*\{', texto)
    if achado:
        return _extrair_chaves(texto, texto.find('{', achado.start()))
    recurso = re.search(r'["\']resource["\']\s*:', texto)
    if not recurso:
        return None
    abre = texto.rfind('{', 0, recurso.start())
    if abre < 0:
        return None
    return _extrair_chaves(texto, abre)


def _neutralizar_exp(bloco):
    """Troca o valor de exp (a conta com time.time) por 0, para o dicionário poder ser lido."""
    achado = re.search(r'["\']exp["\']\s*:', bloco)
    if not achado:
        return bloco
    i = achado.end()
    while i < len(bloco) and bloco[i] in ' \t':
        i += 1
    inicio = i
    profundidade = 0
    while i < len(bloco):
        caractere = bloco[i]
        if caractere in ('"', "'"):
            i = _pular_string(bloco, i)
            continue
        if caractere in '([{':
            profundidade += 1
        elif caractere in ')]}':
            if profundidade == 0:
                break
            profundidade -= 1
        elif caractere in ',#' and profundidade == 0:
            break
        i += 1
    return bloco[:inicio] + '0' + bloco[i:]


def _sem_comentarios(bloco):
    saida = []
    i = 0
    while i < len(bloco):
        caractere = bloco[i]
        if caractere in ('"', "'"):
            fim = _pular_string(bloco, i)
            saida.append(bloco[i:fim])
            i = fim
            continue
        if caractere == '#':
            while i < len(bloco) and bloco[i] != '\n':
                i += 1
            continue
        saida.append(caractere)
        i += 1
    return ''.join(saida)


def _flags_do_html(codigo):
    """Título, download e parâmetros iniciais, se o texto colado também tiver o componente."""
    saida = {'titled': None, 'with_downloads': None, 'initial_parameters': None}
    for nome, chave in (('with-title', 'titled'), ('with-downloads', 'with_downloads')):
        achado = re.search(
            rf'\b{nome}\s*=\s*(["\'])(true|false)\1',
            codigo,
            re.IGNORECASE,
        )
        if achado:
            saida[chave] = achado.group(2).lower() == 'true'
    if saida['titled'] is None:
        na_url = re.search(r'[#&]titled=(true|false)', codigo, re.IGNORECASE)
        if na_url:
            saida['titled'] = na_url.group(1).lower() == 'true'
    iniciais = re.search(
        r'\binitial-parameters\s*=\s*(["\'])(.*?)\1',
        codigo,
        re.IGNORECASE | re.DOTALL,
    )
    if not iniciais:
        return saida, None
    bruto = html.unescape(iniciais.group(2)).strip()
    if not bruto:
        saida['initial_parameters'] = {}
        return saida, None
    try:
        valor = json_loads_objeto(bruto)
    except ValueError as exc:
        return None, str(exc)
    saida['initial_parameters'] = valor
    return saida, None


def json_loads_objeto(bruto):
    import json
    try:
        valor = json.loads(bruto)
    except json.JSONDecodeError as exc:
        raise ValueError(
            'Os parâmetros iniciais do componente não fecharam. Confira o initial-parameters.'
        ) from exc
    if not isinstance(valor, dict):
        raise ValueError('Os parâmetros iniciais precisam ser um objeto, entre chaves.')
    return valor


def interpretar_codigo_metabase(codigo):
    """Lê o Python que o Metabase entrega. A linha do exp é descartada.

    Devolve resource_id, params e _embedding_params. A validade de 10 anos
    entra depois, na assinatura, e não no texto colado.
    """
    texto = (codigo or '').replace('\r\n', '\n')
    if 'resource' not in texto and 'dashboard' not in texto:
        return None, 'Cole o Python do Metabase, com o payload do token.'
    bloco = _bloco_payload(texto)
    if not bloco:
        return None, 'Não achei o payload do token nesse código.'
    bloco = _sem_comentarios(_neutralizar_exp(bloco))
    try:
        dados = ast.literal_eval(bloco)
    except (SyntaxError, ValueError):
        return None, (
            'Não consegui ler o payload. Pode colar o código como veio, '
            'com a linha do exp intacta.'
        )
    if not isinstance(dados, dict):
        return None, 'O payload precisa ser um dicionário.'
    resource = dados.get('resource')
    if not isinstance(resource, dict) or 'dashboard' not in resource:
        return None, 'Esse código não traz um dashboard. O SIGUS incorpora o número do dashboard.'
    try:
        resource_id = int(resource.get('dashboard'))
    except (TypeError, ValueError):
        return None, 'O número do dashboard no código não é válido.'
    if resource_id < 1:
        return None, 'O número do dashboard no código não é válido.'
    params = dados.get('params') if 'params' in dados else {}
    embedding = dados.get('_embedding_params') if '_embedding_params' in dados else {}
    if not isinstance(params, dict) or not isinstance(embedding, dict):
        return None, 'params e _embedding_params precisam ser dicionários.'
    flags, erro = _flags_do_html(texto)
    if erro:
        return None, erro
    return {
        'resource_id': resource_id,
        'params': params,
        'embedding_params': embedding,
        'titled': flags['titled'],
        'with_downloads': flags['with_downloads'],
        'initial_parameters': flags['initial_parameters'],
    }, None


def token_excede_iis(resource_id, params, embedding):
    """True quando o JWT não cabe no endereço que o IIS do Metabase aceita."""
    payload = {
        'resource': {'dashboard': int(resource_id)},
        'params': params or {},
        'exp': 1,
    }
    if embedding:
        payload['_embedding_params'] = embedding
    token = jwt.encode(payload, 'x' * 32, algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('ascii')
    return len(token) > LIMITE_TOKEN_IIS


def rotulo_cbo(codigo):
    if not codigo:
        return '—'
    from app.models.cbo import CBO
    cbo = CBO.query.filter_by(codigo=codigo).first()
    if cbo:
        return cbo.label
    return codigo


def cbo_na_unidade(usuario, unidade):
    """CBO que a pessoa usa na unidade (última ficha CNES, senão a matrícula do vínculo)."""
    if not usuario or not unidade:
        return None
    from app.models.ficha_cnes import FichaCnesVinculo
    from app.models.unidade import UsuarioUnidade

    ficha = (FichaCnesVinculo.query
             .filter_by(usuario_id=usuario.id, unidade_id=unidade.id)
             .order_by(FichaCnesVinculo.gerado_em.desc())
             .first())
    if ficha and ficha.cbo and ficha.tipo != 'descadastro':
        return ficha.cbo
    vinculo = UsuarioUnidade.query.filter_by(
        usuario_id=usuario.id, unidade_id=unidade.id, ativo=True,
    ).first()
    if vinculo and vinculo.matricula and vinculo.matricula.cbo:
        return vinculo.matricula.cbo
    return None


def cbos_da_pessoa(usuario):
    """CBO do cadastro e o CBO da unidade em que a pessoa está agora."""
    codigos = set()
    if usuario.cbo:
        codigos.add(str(usuario.cbo).strip())
    unidade = usuario.unidade_logada
    na_unidade = cbo_na_unidade(usuario, unidade)
    if na_unidade:
        codigos.add(str(na_unidade).strip())
    codigos.discard('')
    return codigos


class MetabaseConfig(db.Model):
    """Uma linha só: endereço do Metabase, chave e tempo da apresentação."""
    __tablename__ = 'metabase_config'

    id = db.Column(db.Integer, primary_key=True)
    site_url = db.Column(db.String(300), nullable=False, default='')
    secret_key = db.Column(db.String(200), nullable=False, default='')
    intervalo_segundos = db.Column(db.Integer, nullable=False, default=40)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=agora_local, onupdate=agora_local)

    @property
    def pronta(self):
        url = (self.site_url or '').strip()
        chave = (self.secret_key or '').strip()
        return bool(chave) and (url.startswith('http://') or url.startswith('https://'))

    @property
    def chave_gravada(self):
        return bool((self.secret_key or '').strip())


class MetabasePainel(db.Model):
    """Um dashboard do Metabase liberado para perfis, tipos de unidade e CBOs."""
    __tablename__ = 'metabase_paineis'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.String(300))
    resource_id = db.Column(db.Integer, nullable=False)
    bordered = db.Column(db.Boolean, nullable=False, default=True)
    titled = db.Column(db.Boolean, nullable=False, default=True)
    with_downloads = db.Column(db.Boolean, nullable=False, default=False)
    embedding_params = db.Column(db.JSON, nullable=False, default=dict)
    initial_parameters = db.Column(db.JSON, nullable=False, default=dict)
    params = db.Column(db.JSON, nullable=False, default=dict)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    ordem = db.Column(db.Integer, nullable=False, default=0)
    perfis_acesso = db.Column(db.JSON, nullable=False, default=lambda: ['todos'])
    tipos_unidade_ids = db.Column(db.JSON, nullable=False, default=list)
    cbos = db.Column(db.JSON, nullable=False, default=list)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    criado_em = db.Column(db.DateTime, nullable=False, default=agora_local)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=agora_local, onupdate=agora_local)

    criador = db.relationship('Usuario', foreign_keys=[criado_por])

    def _tipos(self):
        saida = []
        for item in self.tipos_unidade_ids or []:
            try:
                saida.append(int(item))
            except (TypeError, ValueError):
                continue
        return saida

    def _cbos(self):
        return [str(c).strip() for c in (self.cbos or []) if str(c).strip()]

    def visivel_para(self, usuario) -> bool:
        """Perfil da sessão, tipo da unidade logada e CBO (cadastro ou da unidade)."""
        if not self.ativo:
            return False
        perfis = self.perfis_acesso or ['todos']
        if 'todos' not in perfis and usuario.perfil not in perfis:
            return False
        tipos = self._tipos()
        if tipos:
            unidade = usuario.unidade_logada
            tipo_id = unidade.tipo_unidade_id if unidade else None
            if tipo_id not in tipos:
                return False
        cbos = self._cbos()
        if cbos and not set(cbos).intersection(cbos_da_pessoa(usuario)):
            return False
        return True

    def emitir_token(self, config):
        """JWT com validade de 10 anos. O navegador nunca recebe a chave."""
        expira = int(time.time()) + EXP_SEGUNDOS
        filtros = self.params if isinstance(self.params, dict) else {}
        payload = {
            'resource': {'dashboard': int(self.resource_id)},
            'params': filtros,
            'exp': expira,
        }
        extras = self.embedding_params if isinstance(self.embedding_params, dict) else {}
        if extras:
            payload['_embedding_params'] = extras
        token = jwt.encode(payload, config.secret_key, algorithm='HS256')
        if isinstance(token, bytes):
            token = token.decode('ascii')
        return token, expira

    def __repr__(self):
        return f'<MetabasePainel {self.nome}>'
