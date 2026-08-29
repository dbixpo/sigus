"""
Importação do CID-10 e CID-O a partir dos arquivos XML oficiais do DATASUS.
Os arquivos devem estar em assets/references/CID10XML/
"""
import os
import xml.etree.ElementTree as ET


def _limpar_codigo(cod):
    """Remove pontuação do código: só letras e números. Ex: A00.0 -> A000, J46.9 -> J469, M8000/0 -> M80000."""
    if not cod:
        return ''
    return ''.join(c for c in (cod or '').strip() if c.isalnum())


def _text(el, default=''):
    if el is None:
        return default
    return (el.text or '').strip() or default


def _extrair_cid10_recursivo(parent, itens):
    """Percorre grupos e categorias recursivamente no CID10.xml."""
    for cat in parent.findall('categoria'):
        codcat = cat.get('codcat', '')
        nome_el = cat.find('nome')
        nome = _text(nome_el)
        if codcat and nome:
            itens.append((_limpar_codigo(codcat), nome))
        for sub in cat.findall('subcategoria'):
            codsub = sub.get('codsubcat', '')
            nome_sub_el = sub.find('nome')
            nome_sub = _text(nome_sub_el)
            if codsub and nome_sub:
                itens.append((_limpar_codigo(codsub), nome_sub))
    for grupo in parent.findall('grupo'):
        _extrair_cid10_recursivo(grupo, itens)


def importar_cid10_xml(caminho_arquivo):
    """
    Lê o arquivo CID10.XML e retorna lista de (codigo, descricao).
    Encoding: ISO-8859-1 (usado pelo DATASUS).
    Entidades DTD (&cruz;, &aster;) são substituídas antes do parse.
    """
    itens = []
    if not os.path.exists(caminho_arquivo):
        return itens, f"Arquivo não encontrado: {caminho_arquivo}"

    try:
        with open(caminho_arquivo, 'r', encoding='iso-8859-1', errors='replace') as f:
            texto = f.read()
        texto = texto.replace('&cruz;', '\u2020').replace('&aster;', '*')
        tree = ET.fromstring(texto)
    except ET.ParseError as e:
        return itens, f"Erro ao ler XML: {e}"
    except Exception as e:
        return itens, f"Erro: {e}"

    root = tree
    if root.tag != 'cid10':
        return itens, "Arquivo XML inválido: elemento raiz deve ser 'cid10'"

    for capitulo in root.findall('capitulo'):
        _extrair_cid10_recursivo(capitulo, itens)

    return itens, None


def _extrair_cido_recursivo(parent, itens):
    """Percorre grupos e categorias no CID-O.xml."""
    for cat in parent.findall('categoria'):
        codcat = cat.get('codcat', '')
        nome_el = cat.find('nome')
        nome = _text(nome_el)
        if codcat and nome:
            itens.append((_limpar_codigo(codcat), nome))
    for grupo in parent.findall('grupo'):
        _extrair_cido_recursivo(grupo, itens)


def importar_cido_xml(caminho_arquivo):
    """
    Lê o arquivo CID-O.XML e retorna lista de (codigo, descricao).
    """
    itens = []
    if not os.path.exists(caminho_arquivo):
        return itens, f"Arquivo não encontrado: {caminho_arquivo}"

    try:
        with open(caminho_arquivo, 'r', encoding='iso-8859-1', errors='replace') as f:
            tree = ET.parse(f)
    except ET.ParseError as e:
        return itens, f"Erro ao ler XML: {e}"
    except Exception as e:
        return itens, f"Erro: {e}"

    root = tree.getroot()
    if root.tag != 'cid-o':
        return itens, "Arquivo XML inválido: elemento raiz deve ser 'cid-o'"

    for grupo in root.findall('grupo'):
        _extrair_cido_recursivo(grupo, itens)

    return itens, None


def _diretorio_xml(app):
    """Retorna o diretório absoluto dos XMLs."""
    base = os.path.dirname(app.root_path)
    return os.path.join(base, 'assets', 'references', 'CID10XML')


def importar_todos(app):
    """
    Importa CID10.xml e CID-O.xml para o banco.
    Retorna dict com 'cid10': {novos, atualizados}, 'cido': {novos, atualizados}, 'erros': []
    """
    from app import db
    from app.models.cid10 import CID10
    from app.models.cido import CidO

    db.create_all()

    base_dir = _diretorio_xml(app)
    resultado = {'cid10': {'novos': 0, 'atualizados': 0}, 'cido': {'novos': 0, 'atualizados': 0}, 'erros': []}

    # CID-10
    xml_cid10 = os.path.join(base_dir, 'CID10.xml')
    itens, erro = importar_cid10_xml(xml_cid10)
    if erro:
        resultado['erros'].append(f"CID-10: {erro}")
    else:
        for codigo, descricao in itens:
            codigo = (codigo or '').strip()[:20]
            descricao = (descricao or '').strip()[:300]
            if not codigo or not descricao:
                continue
            rec = CID10.query.filter_by(codigo=codigo).first()
            if rec:
                rec.descricao = descricao
                rec.ativo = True
                resultado['cid10']['atualizados'] += 1
            else:
                db.session.add(CID10(codigo=codigo, descricao=descricao, ativo=True))
                resultado['cid10']['novos'] += 1

    # CID-O
    xml_cido = os.path.join(base_dir, 'CID-O.xml')
    itens, erro = importar_cido_xml(xml_cido)
    if erro:
        resultado['erros'].append(f"CID-O: {erro}")
    else:
        for codigo, descricao in itens:
            codigo = (codigo or '').strip()[:20]
            descricao = (descricao or '').strip()[:300]
            if not codigo or not descricao:
                continue
            rec = CidO.query.filter_by(codigo=codigo).first()
            if rec:
                rec.descricao = descricao
                rec.ativo = True
                resultado['cido']['atualizados'] += 1
            else:
                db.session.add(CidO(codigo=codigo, descricao=descricao, ativo=True))
                resultado['cido']['novos'] += 1

    db.session.commit()
    return resultado
