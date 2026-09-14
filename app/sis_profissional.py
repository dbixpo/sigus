# -*- coding: utf-8 -*-
"""Importa cadastro de profissional para o SIGUS (SIS pessoa/operador/profissional, CADSUS, CNES).

Só leitura. Não altera o SIS. Campos do formulário continuam editáveis.
"""
from __future__ import annotations

import re
from html import unescape
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

from app.models.usuario import ESCOLARIDADES
from app.sis_consulta import _data_iso, _so_digitos, abrir_cliente, configurado

_PADRAO_DIGITO = re.compile(r'\D+')
_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/152.0.0.0 Safari/537.36'
)

_CAMPOS_IDENTIDADE = (
    'nome', 'cpf', 'data_nasc', 'sexo', 'nome_mae', 'nome_pai',
    'rg', 'rg_uf', 'rg_orgao', 'rg_emissao', 'escolaridade',
    'frequenta_escola', 'nacionalidade', 'uf_nasc', 'municipio_nasc',
)
_CAMPOS_ENDERECO = (
    'end_logradouro', 'end_numero', 'end_complemento',
    'end_bairro', 'end_municipio', 'end_uf', 'end_cep',
)
_CAMPOS_CONTATO = ('whatsapp', 'telefone')
_CAMPOS_EMAIL = ('email',)
_CAMPOS_CNS = ('cns',)


def _vazio(valor: Any) -> Any:
    if valor is None:
        return None
    if isinstance(valor, str):
        texto = unescape(valor).replace('\xa0', ' ').strip()
        if not texto or texto.lower() in {'selecione...', 'selecione'}:
            return None
        return texto
    return valor


def _tem(valor: Any) -> bool:
    if valor is None:
        return False
    if isinstance(valor, str) and not valor.strip():
        return False
    return True


def _digitos(valor: str | None) -> str:
    return _PADRAO_DIGITO.sub('', valor or '')


def _cpf_fmt(valor: str) -> str:
    d = _digitos(valor)
    if len(d) == 11:
        return f'{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}'
    return (valor or '').strip()


def _validar_cpf(valor: str) -> str:
    d = _digitos(valor)
    if len(d) != 11:
        raise ValueError('Informe um CPF com 11 números.')
    return d


def _uf(valor: str | None) -> str | None:
    texto = _vazio(valor)
    if not texto:
        return None
    letras = re.sub(r'[^A-Za-z]', '', texto).upper()
    if len(letras) == 2:
        return letras
    return None


def _escolaridade(codigo: str | None) -> str | None:
    bruto = _vazio(codigo)
    if not bruto:
        return None
    if bruto in ESCOLARIDADES:
        return bruto
    if bruto.isdigit():
        padded = bruto.zfill(2)
        if padded in ESCOLARIDADES:
            return padded
    return None


def _sexo(valor: str | None) -> str | None:
    texto = (_vazio(valor) or '').upper()
    if texto in {'M', 'F'}:
        return texto
    if 'FEM' in texto:
        return 'F'
    if 'MASC' in texto:
        return 'M'
    return None


def _nacionalidade(valor: str | None) -> str | None:
    texto = (_vazio(valor) or '').lower()
    if not texto:
        return None
    if texto in {'b', 'br', 'brasileira', 'brasileiro'}:
        return 'brasileira'
    if texto in {'e', 'estrangeira', 'estrangeiro'}:
        return 'estrangeira'
    if 'brasil' in texto:
        return 'brasileira'
    if 'estrang' in texto:
        return 'estrangeira'
    return None


def _sim_nao(valor: Any) -> str | None:
    if valor is True:
        return '1'
    if valor is False:
        return '0'
    texto = (_vazio(str(valor) if valor is not None else '') or '').upper()
    if texto in {'S', 'SIM', '1', 'TRUE'}:
        return '1'
    if texto in {'N', 'NAO', 'NÃO', '0', 'FALSE'}:
        return '0'
    return None


def _cep(valor: str | None) -> str | None:
    d = _digitos(valor)
    if len(d) == 8:
        return f'{d[:5]}-{d[5:]}'
    return _vazio(valor)


def _logradouro(*partes: str | None) -> str | None:
    bits = [_vazio(p) for p in partes if _vazio(p)]
    if not bits:
        return None
    return ' '.join(bits)


def _aplicar(dest: dict, origem: dict | None, campos: tuple[str, ...], fonte: str, fontes: dict) -> None:
    if not origem:
        return
    for campo in campos:
        valor = origem.get(campo)
        if _tem(valor) and not _tem(dest.get(campo)):
            dest[campo] = valor
            fontes[campo] = fonte


def _sobrescrever(dest: dict, origem: dict | None, campos: tuple[str, ...], fonte: str, fontes: dict) -> None:
    if not origem:
        return
    for campo in campos:
        valor = origem.get(campo)
        if _tem(valor):
            dest[campo] = valor
            fontes[campo] = fonte


class PaginaAdm:
    """Lê um formulário SIS (pessoa, profissional ou operador) e resolve lookups."""

    def __init__(self, cliente, soup: BeautifulSoup, prefixo: str, referer: str) -> None:
        self.cliente = cliente
        self.soup = soup
        self.prefixo = prefixo
        self.referer = referer
        self._lookups: dict[str, dict[str, Any]] = {}

    def _nome(self, campo: str) -> str:
        return f'{self.prefixo}[{campo}]'

    def input(self, campo: str, *, incluir_hidden: bool = False) -> str | None:
        nome = self._nome(campo)
        for inp in self.soup.find_all('input', {'name': nome}):
            tipo = (inp.get('type') or 'text').lower()
            if tipo in {'checkbox', 'radio', 'submit', 'button'}:
                continue
            if tipo == 'hidden' and not incluir_hidden:
                continue
            valor = _vazio(inp.get('value'))
            if valor:
                return valor
        ta = self.soup.find('textarea', {'name': nome})
        if ta:
            return _vazio(ta.get_text() or ta.string)
        return None

    def select(self, campo: str) -> dict[str, Any]:
        sel = self.soup.find('select', {'name': self._nome(campo)})
        if not sel:
            return {'codigo': None, 'descricao': None}
        opt = sel.find('option', selected=True)
        if not opt:
            return {'codigo': None, 'descricao': None}
        codigo = _vazio(opt.get('value'))
        descricao = _vazio(opt.get_text())
        return {'codigo': codigo, 'descricao': descricao or codigo}

    def radio(self, campo: str) -> str | None:
        for inp in self.soup.find_all('input', {'name': self._nome(campo)}):
            if (inp.get('type') or '').lower() == 'radio' and inp.has_attr('checked'):
                return _vazio(inp.get('value'))
        return None

    def lookup(self, campo: str) -> dict[str, Any]:
        if campo in self._lookups:
            return self._lookups[campo]
        nome = self._nome(campo)
        inp = self.soup.find('input', attrs={'name': nome, 'data-lookup': 'true'})
        if not inp:
            inp = self.soup.find('input', {'name': nome, 'id': f'{self.prefixo}_{campo}'})
        if not inp:
            inp = self.soup.find('input', {'name': nome})
        codigo = _vazio(inp.get('value')) if inp else None
        descricao = None
        if inp and codigo:
            descricao = self._resolver_lookup(inp, codigo)
        resultado = {'id': codigo, 'descricao': descricao}
        self._lookups[campo] = resultado
        return resultado

    def _resolver_lookup(self, inp: Tag, codigo: str) -> str | None:
        model = inp.get('data-lookup-model') or ''
        scope = inp.get('data-lookup-scope') or ''
        key = inp.get('data-lookup-key') or 'id'
        name = inp.get('data-lookup-name') or 'nome'
        where = self._where_lookup(inp)
        rows = self._lookup_http(model, scope, codigo, key, name, where)
        if not rows and where:
            rows = self._lookup_http(model, scope, codigo, key, name, '')
        if not rows:
            return None
        row = rows[0]
        for candidato in (name.split('|')[0], 'name', 'descricao', 'text', 'nomconselho', 'nommunicipio', 'nompessoa', 'desperfil', 'desorgao', 'desescolaridade', 'nomlogradouro', 'nombairro'):
            if row.get(candidato):
                return _vazio(str(row[candidato]))
        for chave, valor in row.items():
            if chave != key and valor not in (None, '', codigo):
                return _vazio(str(valor))
        return None

    def _lookup_http(self, model: str, scope: str, query: str, key: str, name: str, where: str) -> list[dict]:
        if not (query or '').strip() or not (model or scope):
            return []
        params = {
            'query': query.strip(),
            'page': '1',
            'limit': '20',
            'model': model,
            'scope': scope,
            'key': key,
            'name': name.split('|')[0],
            'type': 'key',
            'where': where,
            'columns': f'{key},{name.split("|")[0]},{key}',
            'sort_by': '',
            'similarity': 'false',
            'cache': 'true',
            'cache_expires': '',
        }
        try:
            resp = self.cliente.get(
                '/fwk/lookup_edit_v3',
                params=params,
                headers=self.cliente.headers_ajax(self.referer),
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception:
            return []
        rows = payload.get('rows') if isinstance(payload, dict) else payload
        if rows is None and isinstance(payload, dict):
            rows = payload.get('data')
        if isinstance(rows, dict):
            return [rows]
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
        return []

    def _where_lookup(self, inp: Tag) -> str:
        masters = (inp.get('data-lookup-master') or '').strip()
        options = (inp.get('data-lookup-master-options') or '').strip()
        if not masters:
            return ''
        campos = [p.lstrip(':').strip() for p in masters.split(',') if p.strip()]
        mapa_fk: dict[str, str] = {}
        for bloco in options.split('|'):
            partes = dict(item.split(':', 1) for item in bloco.split(',') if ':' in item)
            origem = partes.get('key')
            fk = partes.get('foreign_key')
            if origem and fk:
                mapa_fk[origem] = fk
        pedacos: list[str] = []
        for campo in campos:
            outro = self.soup.find('input', {'name': self._nome(campo), 'id': f'{self.prefixo}_{campo}'})
            if not outro:
                outro = self.soup.find('input', attrs={'name': self._nome(campo), 'data-lookup': 'true'})
            valor = _vazio(outro.get('value')) if outro else None
            if not valor:
                continue
            fk = mapa_fk.get(campo, campo)
            pedacos.append(f'{fk}={valor}')
        return (',' + ','.join(pedacos)) if pedacos else ''


def _datatable(cliente, path: str, referer: str, filtro: dict[str, str]) -> list[dict]:
    params = {
        'draw': '1',
        'order[0][column]': '0',
        'order[0][dir]': 'asc',
        'start': '0',
        'length': '20',
        'search[value]': '',
        'search[regex]': 'false',
        'search_operator': '',
        'workMode': 'wmSearchResult',
        'oldWorkMode': 'wmSearch',
        **filtro,
    }
    resp = cliente.get(path, params=params, headers=cliente.headers_ajax(referer))
    resp.raise_for_status()
    body = resp.json()
    data = body.get('data') if isinstance(body, dict) else None
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _abrir(cliente, path: str, referer: str) -> None:
    resp = cliente.get(path, headers=cliente.headers_ajax(referer, json_accept=False))
    resp.raise_for_status()
    try:
        from sis.cliente import extrair_csrf
        cliente.csrf = extrair_csrf(resp.text)
    except Exception:
        pass


def _browse(cliente, path: str, referer: str) -> BeautifulSoup:
    resp = cliente.get(
        path,
        params={'workMode': 'wmBrowse', 'oldWorkMode': 'wmSearchResult'},
        headers=cliente.headers_ajax(referer, json_accept=False),
    )
    resp.raise_for_status()
    return BeautifulSoup(resp.text, 'html.parser')


def _buscar_pessoa(cliente, cpf: str) -> dict | None:
    _abrir(cliente, '/adm/pessoa', '/adm/pessoa')
    rows = _datatable(cliente, '/adm/pessoa.json', '/adm/pessoa', {'adm_pessoa[numcpf]': _cpf_fmt(cpf)})
    if not rows:
        rows = _datatable(cliente, '/adm/pessoa.json', '/adm/pessoa', {'adm_pessoa[numcpf]': cpf})
    if not rows:
        return None
    row = rows[0]
    pid = str(row.get('DT_RowId') or '').strip()
    if not pid:
        return None
    pagina = PaginaAdm(cliente, _browse(cliente, f'/adm/pessoa/{pid}', '/adm/pessoa'), 'adm_pessoa', '/adm/pessoa')
    mun = pagina.lookup('codmunicipionascimento')
    orgao = pagina.lookup('codorgaoemissorident')
    uf_org = pagina.lookup('sgluforgaoemissorident')
    escol = pagina.lookup('codescolaridade')
    sexo = pagina.select('indsexo')
    nac = pagina.select('indnacionalidade')
    freq = pagina.select('sitescolar')
    return {
        'id_interno': pid,
        'numpessoa': pagina.input('numpessoa'),
        'nome': pagina.input('nompessoa'),
        'data_nasc': _data_iso(pagina.input('datnascimento')),
        'sexo': _sexo(sexo.get('codigo') or sexo.get('descricao')),
        'nome_mae': pagina.input('nommae'),
        'nome_pai': pagina.input('nompai'),
        'cpf': _digitos(pagina.input('numcpf') or cpf),
        'rg': pagina.input('numdoctoidentidade'),
        'rg_orgao': orgao.get('descricao') or orgao.get('id'),
        'rg_uf': _uf(uf_org.get('id') or uf_org.get('descricao')),
        'rg_emissao': _data_iso(pagina.input('datemissaoident')),
        'escolaridade': _escolaridade(escol.get('id')),
        'escolaridade_label': escol.get('descricao'),
        'frequenta_escola': _sim_nao(freq.get('codigo') or freq.get('descricao')),
        'nacionalidade': _nacionalidade(nac.get('codigo') or nac.get('descricao')),
        'municipio_nasc': mun.get('descricao'),
        'uf_nasc': None,
    }


def _montar_conselho(pagina: PaginaAdm) -> dict:
    cons = pagina.lookup('codorgaoemissorcons')
    uf = pagina.lookup('sglufdocumentocons')
    numero = pagina.input('numdocumentocons')
    nome = cons.get('descricao')
    sgl = _uf(uf.get('id') or uf.get('descricao'))
    orgao = None
    if nome and sgl:
        orgao = f'{nome}-{sgl}'
    elif nome:
        orgao = nome
    elif sgl:
        orgao = sgl
    return {
        'reg_conselho': numero,
        'orgao_emissor': orgao,
        'conselho_nome': nome,
        'conselho_uf': sgl,
        'conselho_id': cons.get('id'),
    }


def _buscar_profissionais(cliente, cpf: str) -> list[dict]:
    _abrir(cliente, '/adm/profissional', '/adm/profissional')
    rows = _datatable(cliente, '/adm/profissional.json', '/adm/profissional', {'adm_profissional[numcpf]': cpf})
    if not rows:
        rows = _datatable(
            cliente, '/adm/profissional.json', '/adm/profissional',
            {'adm_profissional[numcpf]': _cpf_fmt(cpf)},
        )
    saida = []
    for row in rows:
        pid = str(row.get('DT_RowId') or '').strip()
        if not pid:
            continue
        pagina = PaginaAdm(
            cliente,
            _browse(cliente, f'/adm/profissional/{pid}', '/adm/profissional'),
            'adm_profissional',
            '/adm/profissional',
        )
        mun = pagina.lookup('codmunicipiores')
        logr = pagina.lookup('codlogradouro')
        bairro = pagina.lookup('codbairro')
        cep = pagina.lookup('codcep')
        pessoa = pagina.lookup('numpessoa')
        conselho = _montar_conselho(pagina)
        celular = _digitos(pagina.input('celcontato'))
        telefone = _digitos(pagina.input('telcontato'))
        item = {
            'id_interno': pid,
            'codprofissional': pagina.input('codprofissional') or pid,
            'numpessoa': pagina.input('numpessoa') or pessoa.get('id'),
            'nome': pessoa.get('descricao'),
            'data_nasc': _data_iso(pagina.input('datnascimento')),
            'email': _vazio(pagina.input('email')),
            'cpf': _digitos(pagina.input('numcpf') or cpf),
            'rg': pagina.input('numdoctoidentidade'),
            'cns': _digitos(pagina.input('numcns')),
            'whatsapp': celular or None,
            'telefone': telefone or None,
            'end_logradouro': logr.get('descricao'),
            'end_numero': pagina.input('numimovel'),
            'end_complemento': pagina.input('cplimovel'),
            'end_bairro': bairro.get('descricao'),
            'end_municipio': mun.get('descricao'),
            'end_uf': 'SP' if (mun.get('descricao') or '').upper().find('SOROCABA') >= 0 else None,
            'end_cep': _cep(cep.get('id') or cep.get('descricao') or pagina.input('codcep')),
            'endereco_descritivo': pagina.input('desenderecores'),
            **conselho,
        }
        saida.append(item)
    return saida


def _buscar_operador(cliente, numpessoa: str | None) -> dict | None:
    if not numpessoa:
        return None
    _abrir(cliente, '/seg/operador', '/seg/operador')
    rows = _datatable(
        cliente, '/seg/operador.json', '/seg/operador',
        {'seg_operador[numpessoa]': str(numpessoa)},
    )
    if not rows:
        return None
    oid = str(rows[0].get('DT_RowId') or '').strip()
    if not oid:
        return None
    pagina = PaginaAdm(
        cliente,
        _browse(cliente, f'/seg/operador/{oid}', '/seg/operador'),
        'seg_operador',
        '/seg/operador',
    )
    pessoa = pagina.lookup('numpessoa')
    perfil = pagina.lookup('perfilid')
    afastado = pagina.select('indafastado')
    return {
        'id_interno': oid,
        'codigo': pagina.input('id'),
        'login': pagina.input('codlogin'),
        'numpessoa': pagina.input('numpessoa') or pessoa.get('id'),
        'nome': pessoa.get('descricao'),
        'email': _vazio(pagina.input('emlprincipal')),
        'email_alternativo': _vazio(pagina.input('emlalternativo')),
        'perfil_id': perfil.get('id'),
        'perfil': perfil.get('descricao'),
        'afastado': _vazio(afastado.get('descricao') or afastado.get('codigo')),
    }


def _parsear_cadsus(texto: str) -> dict | None:
    html = texto.replace('\\/', '/').replace('\\"', '"')
    soup = BeautifulSoup(html, 'html.parser')
    btn = soup.find('button', class_=re.compile(r'btnAmbPacienteAtualizar'))
    if not btn:
        btn = soup.find(attrs={'data-cns': True})
    rows = soup.select('table.table_result_cadsus_class tbody tr')
    escolhido = None
    if rows:
        for tr in rows:
            tds = [td.get_text(' ', strip=True) for td in tr.find_all('td')]
            if len(tds) >= 21 and 'ativo' in (tds[-1] or '').lower():
                escolhido = (tr, tds)
                break
        if escolhido is None:
            tds = [td.get_text(' ', strip=True) for td in rows[0].find_all('td')]
            escolhido = (rows[0], tds)
    data_attr = {}
    if btn:
        data_attr = {k.replace('data-', ''): _vazio(v) for k, v in btn.attrs.items() if str(k).startswith('data-')}
    elif escolhido:
        btn = escolhido[0].find(attrs={'data-cns': True})
        if btn:
            data_attr = {k.replace('data-', ''): _vazio(v) for k, v in btn.attrs.items() if str(k).startswith('data-')}
    if not data_attr and not escolhido:
        return None
    tds = escolhido[1] if escolhido else []

    def col(idx: int) -> str | None:
        if idx < len(tds):
            return _vazio(tds[idx])
        return None

    descritivo = data_attr.get('endereco-descritivo') or ''
    partes_end = [p.strip() for p in descritivo.split(' - ') if p.strip()] if descritivo else []
    return {
        'cns': _digitos(data_attr.get('cns') or col(1)),
        'nome': data_attr.get('nomecompleto') or col(2),
        'data_nasc': _data_iso(data_attr.get('datanascimento') or col(3)),
        'nome_mae': data_attr.get('nomemae') or col(4),
        'nome_pai': data_attr.get('nomepai') or col(5),
        'sexo': _sexo(data_attr.get('sexo') or col(6)),
        'whatsapp': _digitos(data_attr.get('telcontato') or col(7)) or None,
        'raca': col(8),
        'cpf': _digitos(data_attr.get('cpf') or col(9)),
        'municipio_nasc': col(11),
        'uf_nasc': _uf(col(12)),
        'pais_origem': col(13),
        'end_cep': _cep(data_attr.get('codcep') or col(14)),
        'end_municipio': col(15) or (partes_end[1] if len(partes_end) > 1 else None),
        'end_bairro': col(16) or (partes_end[2] if len(partes_end) > 2 else None),
        'end_logradouro': _logradouro(col(17), col(18)) or (partes_end[3] if len(partes_end) > 3 else None),
        'end_numero': data_attr.get('numimovel') or col(19) or (partes_end[4] if len(partes_end) > 4 else None),
        'end_uf': _uf(col(12)) if col(15) else None,
        'situacao': col(20),
        'nacionalidade': 'brasileira' if (col(13) or '').upper().find('BRASIL') >= 0 else None,
    }


def _buscar_cadsus(cliente, cpf: str) -> dict | None:
    _abrir(cliente, '/amb/paciente', '/amb/paciente')
    resp = cliente.get(
        '/int/data_sus/cad_sus/pesquisar',
        params={
            'amb_paciente[nome_completo_cadsus]': '',
            'amb_paciente[nome_mae_cadsus]': '',
            'amb_paciente[nome_pai_cadsus]': '',
            'amb_paciente[data_nascimento_cadsus]': '',
            'amb_paciente[cpf_cadsus]': _cpf_fmt(cpf),
            'amb_paciente[cns_cadsus]': '',
            'amb_paciente[tela]': 'paciente',
        },
        headers=cliente.headers_ajax('/amb/paciente', json_accept=False),
    )
    resp.raise_for_status()
    return _parsear_cadsus(resp.text)


def _buscar_usuario_sis(cliente, cpf: str) -> dict | None:
    from sis.paciente import buscar_paciente_id, carregar_browse
    try:
        pid, _consulta, _row = buscar_paciente_id(cliente, cpf=cpf)
        pagina = carregar_browse(cliente, pid)
    except Exception:
        return None
    mun = pagina.lookup('codmunicipiores')
    tipo_log = pagina.lookup('codtipologradouro_desc')
    logr = pagina.lookup('codlogradouro')
    bairro = pagina.lookup('codbairro')
    cep = pagina.lookup('codcep')
    tel = _digitos(pagina.input('telcontato'))
    return {
        'id_interno': pid,
        'nome': pagina.input('nompaciente'),
        'data_nasc': _data_iso(pagina.input('datnascimento')),
        'sexo': _sexo(pagina.select('indsexo').get('codigo')),
        'nome_mae': pagina.input('nommae'),
        'nome_pai': pagina.input('nompai'),
        'cpf': _digitos(pagina.input('numcpf') or cpf),
        'cns': _digitos(pagina.input('numcartao')),
        'rg': pagina.input('numdocumento'),
        'email': _vazio(pagina.input('email')),
        'whatsapp': tel or None,
        'telefone': tel or None,
        'end_logradouro': _logradouro(tipo_log.get('descricao'), logr.get('descricao')),
        'end_numero': pagina.input('numimovel'),
        'end_complemento': pagina.input('cplimovel'),
        'end_bairro': bairro.get('descricao'),
        'end_municipio': mun.get('descricao'),
        'end_uf': 'SP' if (mun.get('descricao') or '').upper().find('SOROCABA') >= 0 else None,
        'end_cep': _cep(cep.get('id') or cep.get('descricao') or pagina.input('codcep')),
    }


def buscar_cnes(cpf: str) -> dict | None:
    d = _digitos(cpf)
    if len(d) != 11:
        return None
    try:
        resp = requests.get(
            'https://cnes.datasus.gov.br/services/profissionais',
            params={'cpf': d},
            headers={
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': _USER_AGENT,
                'Referer': f'https://cnes.datasus.gov.br/pages/profissionais/consulta.jsp?search={d}',
            },
            timeout=25,
        )
        resp.raise_for_status()
        body = resp.json()
    except Exception:
        return None
    itens = body if isinstance(body, list) else []
    if not itens:
        return None
    primeiro = itens[0] if isinstance(itens[0], dict) else None
    if not primeiro:
        return None
    return {
        'id': primeiro.get('id'),
        'nome': _vazio(primeiro.get('nome')),
        'cns': _digitos(primeiro.get('cns')),
        'n': len(itens),
    }


def _rotulo_fonte(chave: str) -> str:
    return {
        'pessoa': 'cadastro de pessoa do SIS',
        'cadsus': 'CADSUS',
        'profissional': 'cadastro de profissional do SIS',
        'operador': 'cadastro de operador do SIS',
        'cnes': 'CNES',
        'usuario_sis': 'cadastro de usuário do SIS',
    }.get(chave, chave)


def _bloco(titulo: str, encontrado: bool, pares: list[tuple[str, Any]], extra: str | None = None) -> dict:
    campos = [{'label': k, 'valor': v} for k, v in pares if _tem(v)]
    return {
        'titulo': titulo,
        'encontrado': encontrado,
        'campos': campos,
        'extra': extra,
    }


def importar_cadastro(cpf: str) -> dict:
    """Busca o CPF nas fontes e devolve campos prontos para o formulário do SIGUS."""
    if not configurado():
        raise RuntimeError('Consulta ao SIS não configurada (SIS_USUARIO / SIS_SENHA no .env).')
    cpf = _validar_cpf(cpf)
    cliente = abrir_cliente()
    erros: list[str] = []
    pessoa = profissionais = operador = cadsus = usuario_sis = None
    try:
        try:
            pessoa = _buscar_pessoa(cliente, cpf)
        except Exception as exc:
            erros.append(f'Pessoa: {exc}')
        try:
            profissionais = _buscar_profissionais(cliente, cpf)
        except Exception as exc:
            erros.append(f'Profissional: {exc}')
        numpessoa = None
        if pessoa:
            numpessoa = pessoa.get('numpessoa')
        elif profissionais:
            numpessoa = profissionais[0].get('numpessoa')
        try:
            operador = _buscar_operador(cliente, numpessoa)
        except Exception as exc:
            erros.append(f'Operador: {exc}')
        try:
            cadsus = _buscar_cadsus(cliente, cpf)
        except Exception as exc:
            erros.append(f'CADSUS: {exc}')
        try:
            usuario_sis = _buscar_usuario_sis(cliente, cpf)
        except Exception as exc:
            erros.append(f'Usuário SIS: {exc}')
    finally:
        try:
            cliente.logout()
        except Exception:
            pass

    cnes = None
    try:
        cnes = buscar_cnes(cpf)
    except Exception as exc:
        erros.append(f'CNES: {exc}')

    prof = profissionais[0] if profissionais else None
    campos: dict[str, Any] = {'cpf': _cpf_fmt(cpf)}
    fontes: dict[str, str] = {'cpf': 'informado'}

    _aplicar(campos, pessoa, _CAMPOS_IDENTIDADE, 'pessoa', fontes)
    _aplicar(campos, cadsus, _CAMPOS_IDENTIDADE + _CAMPOS_ENDERECO + _CAMPOS_CONTATO + _CAMPOS_CNS, 'cadsus', fontes)
    _aplicar(campos, prof, _CAMPOS_IDENTIDADE + _CAMPOS_EMAIL + _CAMPOS_CNS + _CAMPOS_CONTATO, 'profissional', fontes)
    _aplicar(campos, operador, _CAMPOS_EMAIL, 'operador', fontes)
    _aplicar(campos, usuario_sis, _CAMPOS_IDENTIDADE + _CAMPOS_EMAIL, 'usuario_sis', fontes)
    _sobrescrever(campos, usuario_sis, _CAMPOS_ENDERECO + _CAMPOS_CONTATO, 'usuario_sis', fontes)
    _sobrescrever(campos, {'cns': (cnes or {}).get('cns')}, _CAMPOS_CNS, 'cnes', fontes)

    if _tem(campos.get('end_municipio')) and not _tem(campos.get('end_uf')):
        if str(campos['end_municipio']).upper().find('SOROCABA') >= 0:
            campos['end_uf'] = 'SP'
            fontes['end_uf'] = fontes.get('end_municipio', 'cadsus')

    conselhos = []
    for item in profissionais or []:
        if item.get('reg_conselho') or item.get('orgao_emissor'):
            conselhos.append({
                'id': item.get('id_interno'),
                'codprofissional': item.get('codprofissional'),
                'nome': item.get('nome'),
                'reg_conselho': item.get('reg_conselho'),
                'orgao_emissor': item.get('orgao_emissor'),
                'cns': item.get('cns'),
            })

    encontrado = any([pessoa, cadsus, prof, operador, cnes, usuario_sis])
    return {
        'ok': encontrado,
        'campos': campos,
        'fontes': fontes,
        'fontes_label': {k: _rotulo_fonte(v) for k, v in fontes.items()},
        'conselho': conselhos,
        'sis': {
            'pessoa': {'encontrado': bool(pessoa), 'numpessoa': (pessoa or {}).get('numpessoa')},
            'cadsus': {'encontrado': bool(cadsus), 'situacao': (cadsus or {}).get('situacao')},
            'cnes': {'encontrado': bool(cnes), 'cns': (cnes or {}).get('cns')},
            'profissional': {'encontrado': bool(profissionais), 'n': len(profissionais or [])},
            'operador': {
                'encontrado': bool(operador),
                'login': (operador or {}).get('login'),
                'perfil': (operador or {}).get('perfil'),
            },
            'usuario_sis': {'encontrado': bool(usuario_sis)},
        },
        'avisos': erros,
    }


def consultar_conselho(cpf: str) -> dict:
    if not configurado():
        raise RuntimeError('Consulta ao SIS não configurada (SIS_USUARIO / SIS_SENHA no .env).')
    cpf = _validar_cpf(cpf)
    cliente = abrir_cliente()
    try:
        profissionais = _buscar_profissionais(cliente, cpf)
    finally:
        try:
            cliente.logout()
        except Exception:
            pass
    lista = []
    for item in profissionais or []:
        lista.append({
            'id': item.get('id_interno'),
            'codprofissional': item.get('codprofissional'),
            'nome': item.get('nome'),
            'reg_conselho': item.get('reg_conselho'),
            'orgao_emissor': item.get('orgao_emissor'),
            'cns': item.get('cns'),
        })
    return {'ok': True, 'encontrado': bool(lista), 'profissionais': lista}


def consultar_cadastro_sis(cpf: str) -> dict:
    """Consulta só-leitura para a tela de perfil."""
    if not configurado():
        raise RuntimeError('Consulta ao SIS não configurada (SIS_USUARIO / SIS_SENHA no .env).')
    cpf = _validar_cpf(cpf)
    cliente = abrir_cliente()
    pessoa = profissionais = operador = cadsus = usuario_sis = None
    erros: list[str] = []
    try:
        try:
            pessoa = _buscar_pessoa(cliente, cpf)
        except Exception as exc:
            erros.append(f'Pessoa: {exc}')
        try:
            profissionais = _buscar_profissionais(cliente, cpf)
        except Exception as exc:
            erros.append(f'Profissional: {exc}')
        numpessoa = (pessoa or {}).get('numpessoa') or ((profissionais or [{}])[0].get('numpessoa') if profissionais else None)
        try:
            operador = _buscar_operador(cliente, numpessoa)
        except Exception as exc:
            erros.append(f'Operador: {exc}')
        try:
            cadsus = _buscar_cadsus(cliente, cpf)
        except Exception as exc:
            erros.append(f'CADSUS: {exc}')
        try:
            usuario_sis = _buscar_usuario_sis(cliente, cpf)
        except Exception as exc:
            erros.append(f'Usuário SIS: {exc}')
    finally:
        try:
            cliente.logout()
        except Exception:
            pass
    cnes = None
    try:
        cnes = buscar_cnes(cpf)
    except Exception as exc:
        erros.append(f'CNES: {exc}')

    prof = profissionais[0] if profissionais else None
    blocos = [
        _bloco('Cadastro de pessoa (SIS)', bool(pessoa), [
            ('Nº pessoa', (pessoa or {}).get('numpessoa')),
            ('Nome', (pessoa or {}).get('nome')),
            ('Nascimento', (pessoa or {}).get('data_nasc')),
            ('Sexo', (pessoa or {}).get('sexo')),
            ('Nome da mãe', (pessoa or {}).get('nome_mae')),
            ('Nome do pai', (pessoa or {}).get('nome_pai')),
            ('RG', (pessoa or {}).get('rg')),
            ('Órgão emissor', (pessoa or {}).get('rg_orgao')),
            ('Escolaridade', (pessoa or {}).get('escolaridade_label')),
            ('Município de nascimento', (pessoa or {}).get('municipio_nasc')),
        ], 'Não encontrado no cadastro de pessoa do SIS.' if not pessoa else None),
        _bloco('Operador (SIS)', bool(operador), [
            ('Login', (operador or {}).get('login')),
            ('Código', (operador or {}).get('codigo')),
            ('Perfil', (operador or {}).get('perfil')),
            ('E-mail principal', (operador or {}).get('email')),
            ('E-mail alternativo', (operador or {}).get('email_alternativo')),
            ('Afastado', (operador or {}).get('afastado')),
        ], 'Não há operador SIS para esta pessoa.' if not operador else None),
        _bloco('Profissional (SIS)', bool(prof), [
            ('Cód. profissional', (prof or {}).get('codprofissional')),
            ('E-mail', (prof or {}).get('email')),
            ('CNS', (prof or {}).get('cns')),
            ('Conselho', (prof or {}).get('orgao_emissor')),
            ('Nº do conselho', (prof or {}).get('reg_conselho')),
            ('Celular', (prof or {}).get('whatsapp')),
            ('Telefone', (prof or {}).get('telefone')),
        ], 'Não há cadastro de profissional no SIS para este CPF.' if not prof else None),
        _bloco('CADSUS', bool(cadsus), [
            ('CNS', (cadsus or {}).get('cns')),
            ('Nome', (cadsus or {}).get('nome')),
            ('Nascimento', (cadsus or {}).get('data_nasc')),
            ('Nome da mãe', (cadsus or {}).get('nome_mae')),
            ('Raça', (cadsus or {}).get('raca')),
            ('Município de nascimento', (cadsus or {}).get('municipio_nasc')),
            ('Endereço', ' '.join(filter(None, [
                (cadsus or {}).get('end_logradouro'),
                (cadsus or {}).get('end_numero'),
                (cadsus or {}).get('end_bairro'),
                (cadsus or {}).get('end_municipio'),
                (cadsus or {}).get('end_cep'),
            ])) or None),
            ('Situação', (cadsus or {}).get('situacao')),
        ], 'CADSUS não devolveu registro para este CPF.' if not cadsus else None),
        _bloco('CNES', bool(cnes), [
            ('Nome', (cnes or {}).get('nome')),
            ('CNS', (cnes or {}).get('cns')),
        ], 'CNES não devolveu profissional para este CPF.' if not cnes else None),
        _bloco('Cadastro de usuário (SIS)', bool(usuario_sis), [
            ('Nome', (usuario_sis or {}).get('nome')),
            ('E-mail', (usuario_sis or {}).get('email')),
            ('Telefone', (usuario_sis or {}).get('telefone')),
            ('Endereço', ' '.join(filter(None, [
                (usuario_sis or {}).get('end_logradouro'),
                (usuario_sis or {}).get('end_numero'),
                (usuario_sis or {}).get('end_bairro'),
                (usuario_sis or {}).get('end_municipio'),
                (usuario_sis or {}).get('end_cep'),
            ])) or None),
        ], 'Não há cadastro de usuário/paciente no SIS para este CPF.' if not usuario_sis else None),
    ]
    return {
        'ok': True,
        'cpf': _cpf_fmt(cpf),
        'blocos': blocos,
        'avisos': erros,
    }
