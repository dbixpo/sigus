"""Inventário patrimonial no padrão do SEI! Cidades (manual 2025).

A planilha segue a relação enviada pela Divisão de Administração de Materiais.
Os textos seguem os formulários exportados do SEI, já preenchidos com a unidade.
"""
import re
import unicodedata
import zipfile
from io import BytesIO

from markupsafe import Markup, escape

from app.models.cbo import CBO
from app.models.equipamento import Equipamento
from app.models.sala import Sala
from app.utils import agora_local

SITUACAO_PLANILHA = {
    'ativo': 'EM USO',
    'aguardando_instalacao': 'EM USO',
    'em_manutencao': 'EM MANUTENÇÃO',
    'disponivel_transferencia': 'SEM USO NA UNIDADE',
    'sobressalente': 'SEM USO NA UNIDADE',
    'inservivel': 'IRRECUPERÁVEL',
    'baixado': 'BAIXADO',
}

_CBO_AUXILIAR_ESCRITORIO = '411005'
_STATUS_SEM_USO = ('disponivel_transferencia', 'sobressalente')
_FORMAS_COMODATO = ('comodato', 'cessao_uso')


def montar_inventario_sei(unidade, equipamentos=None, fichas_por_usuario=None):
    ano = agora_local().year
    hoje = agora_local().strftime('%d/%m/%Y')
    bens = list(equipamentos) if equipamentos is not None else equipamentos_da_unidade(unidade)
    bens = [e for e in bens if e.ativo and e.status != 'baixado']

    com = [e for e in bens if _tem_patrimonio(e)]
    sem = [e for e in bens if not _tem_patrimonio(e)]
    sucata_com = [e for e in com if e.status == 'inservivel']
    sucata_sem = [e for e in sem if e.status == 'inservivel']
    disponibilizar = [e for e in bens if e.status in _STATUS_SEM_USO]

    com.sort(key=lambda e: ((e.numero_patrimonio or '').strip(), e.id))
    sem.sort(key=lambda e: (_descricao(e), e.id))
    sucata_com.sort(key=lambda e: ((e.numero_patrimonio or '').strip(), e.id))
    sucata_sem.sort(key=lambda e: (_descricao(e), e.id))
    disponibilizar.sort(key=lambda e: (_descricao(e), e.id))

    equipe = _equipe(unidade, fichas_por_usuario or {})
    responsavel = equipe['responsavel']
    cabecalho = {
        'unidade': unidade.nome or '',
        'responsavel': responsavel['nome'] if responsavel else '',
        'matricula': responsavel['matricula'] if responsavel else '',
        'endereco': _endereco(unidade),
        'telefone': _telefone(unidade),
        'email': unidade.email or '',
        'ano': ano,
        'hoje': hoje,
        'setores': unidade.salas.filter_by(ativo=True).count(),
        'bens': len(bens),
    }
    numeros = _quantitativo(bens)

    return {
        'ano': ano,
        'numeros': numeros,
        'n_sucata_com': len(sucata_com),
        'n_sucata_sem': len(sucata_sem),
        'n_disp': len(disponibilizar),
        'n_equipe': len(equipe['integrantes']),
        'html_sucata_com': _html_sucata(cabecalho, sucata_com, com_patrimonio=True),
        'html_sucata_sem': _html_sucata(cabecalho, sucata_sem, com_patrimonio=False),
        'html_disponibilizacao': _html_disponibilizacao(cabecalho, disponibilizar),
        'html_relatorio': _html_relatorio(cabecalho, numeros),
        'html_equipe': _html_equipe(cabecalho, equipe['integrantes']),
    }


def equipamentos_da_unidade(unidade):
    return (Equipamento.query
            .join(Sala, Equipamento.sala_id == Sala.id)
            .filter(Sala.unidade_id == unidade.id,
                    Sala.ativo == True,
                    Equipamento.ativo == True,
                    Equipamento.status != 'baixado')
            .order_by(Equipamento.id)
            .all())


def gerar_ods_inventario(unidade, ano=None):
    ano = ano or agora_local().year
    bens = equipamentos_da_unidade(unidade)
    com = [e for e in bens if _tem_patrimonio(e)]
    sem = [e for e in bens if not _tem_patrimonio(e)]
    com.sort(key=lambda e: (_sala_nome(e), (e.numero_patrimonio or '').strip(), e.id))
    sem.sort(key=lambda e: (_sala_nome(e), _descricao(e), e.id))

    linhas_com = [_linha_com(e, faixa) for e, faixa in _faixas(com)]
    linhas_sem = [_linha_sem(e, faixa) for e, faixa in _faixas(sem)]
    xml = _content_xml(
        f'Itens com chapinha {ano}',
        linhas_com,
        len(com),
        len(sem),
        f'Itens sem chapinha {ano}',
        linhas_sem,
    )
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w') as pacote:
        info = zipfile.ZipInfo('mimetype')
        info.compress_type = zipfile.ZIP_STORED
        info.external_attr = 0o644 << 16
        pacote.writestr(info, 'application/vnd.oasis.opendocument.spreadsheet')
        pacote.writestr('META-INF/manifest.xml', _MANIFEST)
        pacote.writestr('styles.xml', _STYLES)
        pacote.writestr('content.xml', xml.encode('utf-8'))
    buf.seek(0)
    nome = f'Inventario-{_slug(unidade.nome)}-{ano}.ods'
    return buf, nome


def _sala_nome(equipamento):
    sala = equipamento.sala
    return (sala.nome or '') if sala else ''


def _faixas(itens):
    """Alterna branco e pêssego a cada sala, como os blocos da planilha modelo."""
    faixa = False
    sala_atual = None
    for item in itens:
        sala_id = item.sala_id
        if sala_atual is None:
            sala_atual = sala_id
        elif sala_id != sala_atual:
            faixa = not faixa
            sala_atual = sala_id
        yield item, faixa


def _linha_com(equipamento, faixa):
    return {
        'faixa': faixa,
        'valores': [
            (equipamento.numero_patrimonio or '').strip(),
            _descricao(equipamento),
            SITUACAO_PLANILHA.get(equipamento.status, (equipamento.status or '').upper()),
            (equipamento.numero_processo or '').strip(),
        ],
    }


def _linha_sem(equipamento, faixa):
    return {
        'faixa': faixa,
        'valores': [
            'SEM PATRIMONIO',
            _descricao(equipamento),
            _especificar(equipamento),
        ],
    }


def _tem_patrimonio(equipamento):
    return bool((equipamento.numero_patrimonio or '').strip())


def _quantitativo(bens):
    """Cada bem entra numa linha só. A soma, fora 'não localizados', é o inventário da unidade.

    O quadro da planilha continua do outro jeito: localizados lá são todos os que têm chapinha,
    inclusive irrecuperável. Aqui o irrecuperável sai dessa conta e vai para a linha 4.
    """
    numeros = {
        'localizados': 0,
        'sem_etiqueta': 0,
        'nao_localizados': 0,
        'irrecuperaveis': 0,
        'sem_uso': 0,
        'particulares': 0,
        'comodato': 0,
        'total': len(bens),
        'com_chapinha': 0,
        'sem_chapinha': 0,
    }
    for bem in bens:
        if not _tem_patrimonio(bem):
            numeros['sem_etiqueta'] += 1
            numeros['sem_chapinha'] += 1
            continue
        numeros['com_chapinha'] += 1
        if bem.status == 'inservivel':
            numeros['irrecuperaveis'] += 1
        elif bem.status in _STATUS_SEM_USO:
            numeros['sem_uso'] += 1
        elif bem.proprio is False:
            numeros['particulares'] += 1
        elif bem.forma_incorporacao in _FORMAS_COMODATO:
            numeros['comodato'] += 1
        else:
            numeros['localizados'] += 1
    return numeros


def _descricao(equipamento):
    tipo = equipamento.tipo_equipamento
    nome = tipo.nome if tipo and tipo.nome else 'Equipamento'
    return nome.upper()


def _especificar(equipamento):
    partes = []
    if equipamento.marca and equipamento.marca.nome:
        partes.append(equipamento.marca.nome)
    if equipamento.modelo and equipamento.modelo.nome:
        partes.append(equipamento.modelo.nome)
    if (equipamento.numero_serie or '').strip():
        partes.append(f"nº série {equipamento.numero_serie.strip()}")
    return ', '.join(partes)


def _classe_disponibilizacao(equipamento):
    if equipamento.condicao in ('boa', 'em_condicoes_uso'):
        return 'A'
    return 'B'


def _endereco(unidade):
    rua = ' '.join(p for p in (unidade.endereco, unidade.numero) if p)
    if unidade.complemento:
        rua = f'{rua}, {unidade.complemento}' if rua else unidade.complemento
    local = ' - '.join(p for p in (unidade.cidade, unidade.uf) if p)
    if unidade.bairro:
        local = f'{unidade.bairro}, {local}' if local else unidade.bairro
    cep = f'CEP {unidade.cep}' if unidade.cep else ''
    return ' — '.join(p for p in (rua, local, cep) if p)


def _telefone(unidade):
    tel = (unidade.telefone or '').strip()
    if (unidade.ramal or '').strip():
        tel = f'{tel} ramal {unidade.ramal.strip()}'.strip()
    return tel


def _equipe(unidade, fichas_por_usuario):
    codigos = {c.codigo for c in CBO.query.filter(CBO.descricao.ilike('%auxiliar de escrit%')).all()}
    codigos.add(_CBO_AUXILIAR_ESCRITORIO)
    descricoes = {c.codigo: c.descricao for c in CBO.query.filter(CBO.codigo.in_(codigos)).all()}

    integrantes = []
    vistos = set()
    for vinculo in unidade.gerentes:
        usuario = vinculo.usuario
        if not usuario or usuario.id in vistos:
            continue
        vistos.add(usuario.id)
        integrantes.append({
            'nome': usuario.nome or '',
            'matricula': _matricula(vinculo),
            'funcao': 'Gerente da unidade',
        })

    for vinculo in unidade.usuarios.filter_by(ativo=True).all():
        usuario = vinculo.usuario
        if not usuario or usuario.id in vistos:
            continue
        codigo = _cbo(vinculo, fichas_por_usuario)
        if codigo not in codigos:
            continue
        vistos.add(usuario.id)
        integrantes.append({
            'nome': usuario.nome or '',
            'matricula': _matricula(vinculo),
            'funcao': descricoes.get(codigo) or 'Auxiliar de escritório',
        })

    return {
        'responsavel': integrantes[0] if integrantes and integrantes[0]['funcao'] == 'Gerente da unidade' else (
            next((p for p in integrantes if p['funcao'] == 'Gerente da unidade'), None)
        ),
        'integrantes': integrantes,
    }


def _cbo(vinculo, fichas_por_usuario):
    ficha = fichas_por_usuario.get(vinculo.usuario_id)
    if ficha and ficha.cbo:
        return str(ficha.cbo).strip()
    if vinculo.matricula and vinculo.matricula.cbo:
        return str(vinculo.matricula.cbo).strip()
    if vinculo.usuario and vinculo.usuario.cbo:
        return str(vinculo.usuario.cbo).strip()
    return ''


def _matricula(vinculo):
    if vinculo.matricula and vinculo.matricula.numero:
        return vinculo.matricula.numero
    return (vinculo.usuario.matricula or '') if vinculo.usuario else ''


def _html_sucata(cab, itens, com_patrimonio):
    if com_patrimonio:
        titulo = 'FORMULÁRIO DE SUCATA C/ NÚMERO DE PATRIMÔNIO'
        colunas = [
            ('Qt.', 42, '16.0pt'),
            ('Descrição do material', 267, '16.0pt'),
            ('Nº Patrimônio', 302, '16.0pt'),
        ]
        linhas = [['1', _descricao(e), (e.numero_patrimonio or '').strip()] for e in itens]
        largura = 612
        data_emissao = '&nbsp;&nbsp; &nbsp;/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; /&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        data_retirada = '&nbsp; &nbsp;/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; /&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        aviso = ''
    else:
        titulo = 'FORMULÁRIO DE SUCATA SEM NÚMERO DE PATRIMÔNIO'
        colunas = [
            ('Qt.', 42, '14.0pt'),
            ('Item', 192, '14.0pt'),
            ('Especificação: marca, modelo, cor, dimensões, nº série.', 444, '14.0pt'),
        ]
        linhas = [['1', _descricao(e), _especificar(e)] for e in itens]
        largura = 678
        data_emissao = '___ /___ /___'
        data_retirada = '___ /___ /___'
        aviso = (
            '<p align="center" class="MsoNormal" style="text-align:center;margin:0">'
            '<span style="font-size:10pt"><b><u><span style="font-size:8.0pt">'
            '<span style="background:yellow">IMPORTANTE: FAVOR DESCREVER CORRETAMENTE O MATERIAL '
            'E MANDAR FOTO DO(S) ITEM(NS) ABAIXO POR E-MAIL</span></span></u></b></span></p>'
        )
    corpo = (
        _titulo_16(titulo)
        + Markup(aviso)
        + _linha_unidade(cab['unidade'])
        + _linha_14('Responsável:', cab['responsavel'])
        + _linha_14('Endereço:', cab['endereco'])
        + _linha_14('Telefone:', cab['telefone'])
        + _linha_14('E-mail:', cab['email'])
        + _vazio()
        + _grade_sucata(colunas, linhas, largura)
        + _vazio()
        + Markup(
            '<p class="MsoNormal" style="margin:0"><span style="font-size:10pt">'
            '<b><u><span style="font-size:12.0pt">OBS.:</span></u></b>'
            '<span style="font-size:12.0pt"> <i>CONFIRMO QUE OS ITENS LISTADOS NESSE DOCUMENTO '
            'SÃO BENS PERMANENTES DA PREFEITURA MUNICIPAL DE SOROCABA.</i></span></span></p>'
        )
        + _vazio()
        + _linha_12(f'DATA DA EMISSÃO: {data_emissao}')
        + _vazio()
        + _linha_12('RESPONSÁVEL PELA UNIDADE:.......................................................................................................')
        + _linha_12('(Assinatura legível por extenso)')
        + _vazio()
        + _vazio()
        + _linha_12(f'DATA DA RETIRADA: {data_retirada}')
        + _vazio()
        + _linha_12('EMPRESA RESPONSÁVEL PELA RETIRADA:......................................................................................')
        + _linha_12('(Assinatura legível por extenso com número de documento).')
    )
    return _folha(corpo)


def _html_disponibilizacao(cab, itens):
    linhas = [[_descricao(e), (e.numero_patrimonio or '').strip(), _classe_disponibilizacao(e)] for e in itens]
    while len(linhas) < 3:
        linhas.append(['', '', ''])
    grade = Markup(
        '<table align="center" border="1" cellpadding="0" style="border-collapse:collapse;border:none;margin-left:auto;margin-right:auto">'
        '<tbody><tr>'
        '<td colspan="3" style="border:1px solid black;width:640px;padding:0cm 7px" valign="top">'
        '<p align="center" class="MsoNormal" style="text-align:center;margin:0">'
        '<b><span style="font-size:14.0pt;font-family:Calibri,sans-serif;color:black">Materiais</span></b></p>'
        '</td></tr><tr>'
    )
    grade += _td_disp('Material', 283, '12.0pt', esquerda=True, cabeca=True)
    grade += _td_disp('N° Patrimônio', 157, '12.0pt', cabeca=True)
    grade += _td_disp('Classificação*', 136, '12.0pt', cabeca=True)
    grade += Markup('</tr>')
    for linha in linhas:
        grade += Markup('<tr>')
        grade += _td_disp(linha[0], 283, '12.0pt', esquerda=True, centro=False)
        grade += _td_disp(linha[1], 157, '12.0pt', centro=False)
        grade += _td_disp(linha[2], 136, '12.0pt')
        grade += Markup('</tr>')
    grade += Markup('</tbody></table>')
    pares = (
        ('LOCAL:', cab['unidade']),
        ('RESPONSÁVEL:', cab['responsavel']),
        ('ENDEREÇO:', cab['endereco']),
        ('TELEFONE:', cab['telefone']),
        ('E-MAIL:', cab['email']),
    )
    ficha = Markup('<table align="center" border="1" cellpadding="4" style="border-collapse:collapse;width:716px;margin-left:auto;margin-right:auto"><tbody>')
    for rotulo, valor in pares:
        ficha += Markup(
            '<tr><td style="width:102px"><b><span style="font-size:12.0pt;font-family:Calibri,sans-serif">'
            f'{escape(rotulo)}</span></b></td>'
            '<td style="width:592px"><span style="font-size:12.0pt;font-family:Calibri,sans-serif">'
        )
        ficha += escape(valor) if valor else Markup('&nbsp;')
        ficha += Markup('</span></td></tr>')
    ficha += Markup('</tbody></table>')
    corpo = (
        Markup(
            '<div style="border:solid windowtext 1.0pt;padding:1.0pt 4.0pt">'
            '<p align="center" class="MsoNormal" style="text-align:center;margin:0;border:none">'
            '<b><span style="font-size:16.0pt;font-family:Calibri,sans-serif">'
            'FORMULÁRIO DE DISPONIBILIZAÇÃO DE MATERIAIS</span></b></p></div>'
        )
        + _vazio() + _vazio()
        + ficha
        + _vazio()
        + grade
        + _vazio()
        + _linha_12('* A - Em ótimo estado')
        + Markup('<p class="MsoNormal" style="margin:0"><span style="font-size:12.0pt;font-family:Calibri,sans-serif">* B – Em bom estado</span></p>')
        + Markup(
            '<p class="MsoNormal" style="margin:0"><span style="font-size:10pt">'
            '<b><span style="font-size:12.0pt">Obs</span></b>'
            '<span style="font-size:12.0pt">.: Fica a encargo da SACMP, decidir a redistribuição de todo Material disponibilizado.</span>'
            '</span></p>'
        )
        + _vazio()
        + Markup(
            '<p class="Tabela_Texto_Alinhado_Direita" style="font-size:11pt;font-family:\'Times New Roman\',serif;'
            'text-align:right;margin:0 3pt">Sorocaba, na data da assinatura digital.</p>'
        )
    )
    return _folha(corpo)


def _html_relatorio(cab, numeros):
    linhas = [
        ['1', 'Nº de bens localizados', numeros['localizados']],
        ['2', 'Nº de bens sem etiqueta de tombo (sobra física)', numeros['sem_etiqueta']],
        ['3', 'Nº de bens não localizados (sobra patrimonial)', numeros['nao_localizados']],
        ['4', 'Nº de bens em estado de conservação irrecuperável', numeros['irrecuperaveis']],
        ['5', 'Nº de bens em bom estado, mas sem uso na unidade', numeros['sem_uso']],
        ['6', 'Nº de bens particulares', numeros['particulares']],
        ['7', 'Nº de bens em condição de comodato/convênio', numeros['comodato']],
    ]
    paragrafo = (
        f"Considerando o resumo acima, informamos que o inventário do ano de {cab['ano']} "
        "foi realizado em minha unidade entre os dias _______________________________, "
        "sendo que o resultado final do levantamento geral está representado na planilha _____________ , "
        "o(s) formulário(s) de sucata está(ão) no(s) documento(s) _____________ (e _______________), "
        "e os demais documentos que comprovam as movimentações ainda não formalizadas no anexo _________________."
    )
    corpo = (
        _anexo('ANEXO IV')
        + _anexo('RELATÓRIO SINTÉTICO DE INVENTÁRIO PATRIMONIAL')
        + _cabecalho_anexo(cab, com_responsavel=False)
        + _grade_quantitativa(
            [('ITEM', 71), ('ATIVIDADES', 393), ('QUANT./SALDO', 113)],
            linhas,
            negrito_primeira=True,
        )
        + Markup('<p class="MsoNormal" style="text-align:justify;margin:0 0 13px">&nbsp;</p>')
        + _paragrafo_11(paragrafo)
        + _paragrafo_11(
            'Confirmo que os itens pertencem a Prefeitura de Sorocaba, sendo que algum item que, '
            'por ventura não faça parte do Patrimônio Municipal será anexado a esse relatório, indicando a quem pertence.'
        )
        + _paragrafo_11(
            'Dou fé pública nas declarações prestadas e estou ciente de que informações erradas ou '
            'situações não declaradas poderão gerar futuros procedimentos administrativos para a '
            'unidade administrativa ao qual faço parte.'
        )
        + Markup(
            '<p class="Tabela_Texto_Alinhado_Direita" style="font-size:11pt;font-family:\'Times New Roman\',serif;'
            'text-align:right;margin:0 3pt">&nbsp;</p>'
            '<p class="Tabela_Texto_Alinhado_Direita" style="font-size:11pt;font-family:\'Times New Roman\',serif;'
            'text-align:right;margin:0 3pt">Sorocaba, na data da assinatura digital.</p>'
        )
    )
    return _folha(corpo)


def _html_equipe(cab, integrantes):
    linhas = [[str(i), pessoa['nome'], pessoa['funcao']] for i, pessoa in enumerate(integrantes, start=1)]
    while len(linhas) < 6:
        linhas.append([str(len(linhas) + 1), '', ''])
    if len(integrantes) <= 6:
        linhas.append(['', '', ''])
    obs = (
        'A Autoridade Máxima da Unidade (chefia de seção/divisão, supervisor, coordenador, '
        'diretor de escola, etc.) poderá realizar o inventário sozinha ou nomear alguns servidores '
        'para a realização do levantamento geral em sua unidade, sendo que nessa situação é obrigatório '
        'o preenchimento do formulário acima de modo que sejam indicados todos os servidores envolvidos '
        'dentro desse procedimento e as funções (levantamento físico ou cadastro). É importante ressaltar '
        'que apensar das atribuições distribuídas entre a equipe, a responsabilidade da carga patrimonial '
        'da unidade cabe ao responsável da unidade, sendo essa a Autoridade Máxima da Unidade.'
    )
    corpo = (
        _anexo('ANEXO V')
        + _anexo('CRIAÇÃO DA EQUIPE DE INVENTÁRIO LOCAL')
        + _cabecalho_anexo(cab, com_responsavel=True)
        + _grade_quantitativa(
            [('QTD', 39), ('INTEGRANTES', 399), ('FUNÇÃO', 135)],
            linhas,
            negrito_primeira=True,
        )
        + Markup(
            '<p class="MsoNormal" style="text-align:justify;margin:0 0 13px">'
            '<span style="font-size:11pt;line-height:150%;font-family:Calibri,sans-serif">'
            '<b><u>Obs.:</u></b> <i><span style="font-size:10.0pt;line-height:150%">'
        )
        + escape(obs)
        + Markup('</span></i></span></p>')
        + Markup('<p class="MsoNormal" style="text-align:justify;margin:0 0 13px">&nbsp;</p>')
        + Markup(
            '<p class="Texto_Alinhado_Direita_GESP" style="font-size:12pt;font-family:Calibri,sans-serif;'
            'text-align:right;margin:6pt">Sorocaba, na data da assinatura digital.</p>'
        )
    )
    return _folha(corpo)


def _folha(corpo):
    return (
        Markup('<div style="font-family:Calibri,sans-serif;color:#000000;font-size:12pt">')
        + Markup(
            '<p class="Texto_Centralizado_Maiusculas_Negrito_GESP" '
            'style="font-weight:bold;font-size:13pt;font-family:Calibri,sans-serif;'
            'text-align:center;text-transform:uppercase;margin:0">PREFEITURA MUNICIPAL DE SOROCABA</p>'
        )
        + corpo
        + Markup('</div>')
    )


def _titulo_16(texto):
    return Markup(
        '<p align="center" class="MsoNormal" style="text-align:center;margin:0">'
        '<span style="font-size:10pt"><b><u><span style="font-size:16.0pt;font-family:Calibri,sans-serif">'
        f'{escape(texto)}</span></u></b></span></p>'
    )


def _anexo(texto):
    return Markup(
        '<p align="center" class="MsoNormal" style="text-align:center;margin:0 0 13px">'
        '<span style="font-size:11pt;line-height:150%;font-family:Calibri,sans-serif"><b>'
        f'{escape(texto)}</b></span></p>'
    )


def _linha_unidade(valor):
    return Markup(
        '<p class="MsoNormal" style="margin:0;font-family:Calibri,sans-serif">'
        '<span style="font-size:10pt"><b><span style="font-size:14.0pt">Unidade</span></b>'
        '<b><span style="font-size:18.0pt">: </span></b></span>'
        f'<span style="font-size:14.0pt;font-family:Calibri,sans-serif">{_txt(valor)}</span></p>'
    )


def _linha_14(rotulo, valor):
    return Markup(
        '<p class="MsoNormal" style="margin:0;font-family:Calibri,sans-serif">'
        f'<span style="font-size:10pt"><b><span style="font-size:14.0pt">{escape(rotulo)}</span></b> </span>'
        f'<span style="font-size:14.0pt;font-family:Calibri,sans-serif">{_txt(valor)}</span></p>'
    )


def _linha_12(texto):
    return Markup(
        '<p class="MsoNormal" style="margin:0"><span style="font-size:10pt">'
        f'<span style="font-size:12.0pt;font-family:Calibri,sans-serif">{Markup(texto) if "&nbsp;" in texto or "___" in texto else escape(texto)}</span>'
        '</span></p>'
    )


def _vazio():
    return Markup('<p class="MsoNormal" style="margin:0">&nbsp;</p>')


def _paragrafo_11(texto):
    return Markup(
        '<p class="MsoNormal" style="text-align:justify;margin:0 0 13px">'
        '<span style="font-size:11pt;line-height:150%;font-family:Calibri,sans-serif">'
        f'{escape(texto)}</span></p>'
    )


def _txt(valor):
    texto = '' if valor is None else str(valor).strip()
    return escape(texto) if texto else Markup('&nbsp;')


def _celula_borda(largura, texto, tamanho, esquerda=False, cabeca=False, altura=None, centro=True, negrito=False):
    topo = '1px solid black' if cabeca else 'none'
    lado = '1px solid black' if esquerda else 'none'
    altura_css = f'height:{altura}px;' if altura else ''
    alinhamento = 'center' if centro else 'left'
    peso = '<b>' if negrito else ''
    peso_fim = '</b>' if negrito else ''
    miolo = _txt(texto)
    return Markup(
        f'<td style="border-bottom:1px solid black;width:{largura}px;padding:0cm 7px;{altura_css}'
        f'border-top:{topo};border-right:1px solid black;border-left:{lado}" valign="top">'
        f'<p align="{alinhamento}" class="MsoNormal" style="text-align:{alinhamento};margin:0">'
        f'<span style="font-size:10pt">{peso}<span style="font-size:{tamanho};font-family:Calibri,sans-serif">'
        f'{miolo}</span>{peso_fim}</span></p></td>'
    )


def _grade_sucata(colunas, linhas, largura):
    alturas = (42, 47, 46)
    while len(linhas) < 9:
        linhas.append([''] * len(colunas))
    html = Markup(f'<table align="center" border="1" cellpadding="0" style="border-collapse:collapse;border:none;width:{largura}px;margin-left:auto;margin-right:auto"><tbody><tr>')
    for indice, (titulo, largura_col, tamanho) in enumerate(colunas):
        html += _celula_borda(largura_col, titulo, tamanho, esquerda=indice == 0, cabeca=True, negrito=True)
    html += Markup('</tr>')
    for i, linha in enumerate(linhas):
        html += Markup('<tr>')
        for indice, valor in enumerate(linha):
            html += _celula_borda(
                colunas[indice][1], valor, '12.0pt',
                esquerda=indice == 0, altura=alturas[i % 3], negrito=False,
            )
        html += Markup('</tr>')
    html += Markup('</tbody></table>')
    return html


def _td_disp(texto, largura, tamanho, esquerda=False, cabeca=False, centro=True):
    return _celula_borda(largura, texto, tamanho, esquerda=esquerda, cabeca=cabeca, centro=centro, negrito=cabeca)


def _cabecalho_anexo(cab, com_responsavel):
    def celula(largura, texto, negrito=False, centro=False, altura=20, span=1):
        peso = '<b>' if negrito else ''
        peso_fim = '</b>' if negrito else ''
        alinhamento = 'center' if centro else 'left'
        colspan = f' colspan="{span}"' if span > 1 else ''
        return Markup(
            f'<td{colspan} style="border:1px solid black;width:{largura}px;padding:0cm 5px;height:{altura}px" valign="bottom">'
            f'<p class="MsoNormal" style="text-align:{alinhamento};margin:0">'
            f'<span style="font-size:11pt;font-family:Calibri,sans-serif;color:black">{peso}'
            f'{_txt(texto)}{peso_fim}</span></p></td>'
        )

    html = Markup('<table align="center" border="0" cellpadding="0" style="border-collapse:collapse;width:577px;margin-left:auto;margin-right:auto"><tbody>')
    html += Markup('<tr>')
    html += celula(101 if com_responsavel else 71, 'UNIDADE:', negrito=True)
    html += celula(344 if com_responsavel else 393, cab['unidade'], centro=True, span=1)
    html += celula(38 if com_responsavel else 47, 'ANO:', negrito=True)
    html += celula(89 if com_responsavel else 66, cab['ano'])
    html += Markup('</tr>')
    if com_responsavel:
        html += Markup('<tr>')
        html += celula(101, 'RESPONSÁVEL:', negrito=True)
        html += celula(344, cab['responsavel'], centro=True)
        html += celula(38, 'MAT.', negrito=True)
        html += celula(89, cab['matricula'])
        html += Markup('</tr>')
    html += Markup('<tr>')
    html += celula(133 if com_responsavel else 124, 'Total de Setores da Unidade', negrito=True, centro=True, altura=40)
    html += celula(209 if com_responsavel else 189, cab['setores'], altura=40)
    html += celula(95, 'Total de Bens da Unidade', negrito=True, centro=True, altura=40)
    html += celula(135 if com_responsavel else 170, cab['bens'], altura=40)
    html += Markup('</tr></tbody></table>')
    html += Markup('<p class="MsoNormal" style="margin:0;height:20px">&nbsp;</p>')
    return html


def _grade_quantitativa(colunas, linhas, negrito_primeira=False):
    html = Markup('<table align="center" border="0" cellpadding="0" style="border-collapse:collapse;margin-left:auto;margin-right:auto"><tbody><tr>')
    for indice, (titulo, largura) in enumerate(colunas):
        html += _celula_anexo(largura, titulo, negrito=True, centro=True, cabeca=True)
    html += Markup('</tr>')
    for linha in linhas:
        html += Markup('<tr>')
        for indice, valor in enumerate(linha):
            centro = indice != 1
            negrito = negrito_primeira and indice == 0 and str(valor).strip() != ''
            html += _celula_anexo(colunas[indice][1], valor, negrito=negrito, centro=centro)
        html += Markup('</tr>')
    html += Markup('</tbody></table>')
    return html


def _celula_anexo(largura, texto, negrito=False, centro=False, cabeca=False):
    peso = '<b>' if negrito else ''
    peso_fim = '</b>' if negrito else ''
    alinhamento = 'center' if centro else 'left'
    return Markup(
        f'<td style="border:1px solid black;width:{largura}px;padding:0cm 5px;height:20px" valign="bottom">'
        f'<p align="{alinhamento}" class="MsoNormal" style="text-align:{alinhamento};margin:0">'
        f'<span style="font-size:11pt;line-height:normal;font-family:Calibri,sans-serif;color:black">{peso}'
        f'{_txt(texto)}{peso_fim}</span></p></td>'
    )


def _slug(nome):
    base = unicodedata.normalize('NFKD', nome or '').encode('ascii', 'ignore').decode()
    base = re.sub(r'[^A-Za-z0-9]+', '-', base).strip('-')
    return base or 'unidade'


def _estilo_celula(nome, fundo, alinhamento, negrito=False, numero=False, cor='#000000'):
    peso = ' fo:font-weight="bold"' if negrito else ''
    dados = ' style:data-style-name="N0"' if numero else ''
    return (
        f'<style:style style:name="{nome}" style:family="table-cell"'
        f' style:parent-style-name="Default"{dados}>'
        f'<style:table-cell-properties fo:border="0.74pt solid #000000"'
        f' fo:background-color="{fundo}" style:vertical-align="middle"'
        f' fo:wrap-option="wrap" fo:padding="0.071cm"/>'
        f'<style:paragraph-properties fo:text-align="{alinhamento}"/>'
        f'<style:text-properties style:font-name="Calibri" fo:font-size="11pt"'
        f' fo:color="{cor}"{peso}/>'
        '</style:style>'
    )


def _estilo_coluna(nome, largura):
    return (
        f'<style:style style:name="{nome}" style:family="table-column">'
        f'<style:table-column-properties style:column-width="{largura}"/>'
        '</style:style>'
    )


_ESTILOS_AUTOMATICOS = (
    '<office:automatic-styles>'
    '<number:number-style style:name="N0">'
    '<number:number number:decimal-places="0" number:min-integer-digits="1"/>'
    '</number:number-style>'
    '<style:style style:name="rh" style:family="table-row">'
    '<style:table-row-properties style:row-height="0.53cm" style:use-optimal-row-height="false"/>'
    '</style:style>'
    + ''.join(_estilo_coluna(f'c{i}', largura) for i, largura in enumerate(
        ('2.37cm', '6.31cm', '2.87cm', '5.41cm', '0.70cm', '4.35cm', '3.20cm')
    ))
    + ''.join(_estilo_coluna(f's{i}', largura) for i, largura in enumerate(
        ('3.20cm', '6.80cm', '14.50cm')
    ))
    + _estilo_celula('cab', '#333399', 'center', negrito=True, cor='#FFFFFF')
    + _estilo_celula('ce0', '#FFFFFF', 'center')
    + _estilo_celula('es0', '#FFFFFF', 'left')
    + _estilo_celula('ce1', '#FFCC99', 'center')
    + _estilo_celula('es1', '#FFCC99', 'left')
    + _estilo_celula('tit', '#FFFFFF', 'center', negrito=True)
    + _estilo_celula('lab', '#FFFFFF', 'left', negrito=True)
    + _estilo_celula('val', '#FFFFFF', 'center', numero=True)
    + '</office:automatic-styles>'
)


def _content_xml(nome_com, linhas_com, localizados, sem_chapinha, nome_sem, linhas_sem):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-content'
        ' xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
        ' xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"'
        ' xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"'
        ' xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"'
        ' xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"'
        ' xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"'
        ' xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"'
        ' office:version="1.2">'
        '<office:font-face-decls>'
        '<style:font-face style:name="Calibri" svg:font-family="Calibri" style:font-family-generic="swiss"/>'
        '</office:font-face-decls>'
        + _ESTILOS_AUTOMATICOS
        + '<office:body><office:spreadsheet>'
        + _aba_com_chapinha(nome_com, linhas_com, localizados, sem_chapinha)
        + _aba_sem_chapinha(nome_sem, linhas_sem)
        + '</office:spreadsheet></office:body></office:document-content>'
    )


def _aba_com_chapinha(nome, linhas, localizados, sem_chapinha):
    """Mesma grade do modelo: quatro colunas, um vão e o quadro de totais à direita."""
    larguras = ('2.37cm', '6.31cm', '2.87cm', '5.41cm', '0.70cm', '4.35cm', '3.20cm')
    xml = f'<table:table table:name="{_xa(nome)}">'
    for i, largura in enumerate(larguras):
        xml += f'<table:table-column table:style-name="c{i}"/>'
    xml += _linha_altura()
    for titulo in ('PATRIMONIO', 'DESCRIÇÃO DO BEM', 'SITUAÇÃO', 'DOCUMENTO COMPLEMENTAR'):
        xml += _celula(titulo, 'cab')
    xml += '</table:table-row>'

    totais = {
        2: ('titulo', 'TOTAL DE ITENS NA UNIDADE', None),
        3: ('valor', 'LOCALIZADOS', localizados),
        4: ('valor', 'NÃO LOCALIZADOS', 0),
        5: ('valor', 'NÃO CONSTAM NA LISTA', 0),
        6: ('valor', 'ITENS SEM CHAPINHA', sem_chapinha),
    }
    ultima = max(len(linhas), 6)
    for i in range(ultima):
        xml += _linha_altura()
        if i < len(linhas):
            faixa = '1' if linhas[i]['faixa'] else '0'
            valores = linhas[i]['valores']
            xml += _celula(valores[0], f'ce{faixa}')
            xml += _celula(valores[1], f'es{faixa}')
            xml += _celula(valores[2], f'es{faixa}')
            xml += _celula(valores[3], f'es{faixa}')
        else:
            xml += '<table:table-cell/><table:table-cell/><table:table-cell/><table:table-cell/>'
        total = totais.get(i + 1)
        if total:
            xml += '<table:table-cell/>'
            if total[0] == 'titulo':
                xml += (
                    f'<table:table-cell table:style-name="tit" table:number-columns-spanned="2"'
                    f' office:value-type="string"><text:p>{_x(total[1])}</text:p></table:table-cell>'
                    '<table:covered-table-cell/>'
                )
            else:
                xml += _celula(total[1], 'lab')
                xml += _celula_numero(total[2])
        xml += '</table:table-row>'
    xml += '</table:table>'
    return xml


def _aba_sem_chapinha(nome, linhas):
    xml = f'<table:table table:name="{_xa(nome)}">'
    xml += ''.join(f'<table:table-column table:style-name="s{i}"/>' for i in range(3))
    xml += _linha_altura()
    for titulo in ('SITUAÇÃO', 'DESCRIÇÃO DO BEM', 'MARCA, MODELO, TAMANHO, NÚMERO DE SÉRIE'):
        xml += _celula(titulo, 'cab')
    xml += '</table:table-row>'
    for linha in linhas:
        faixa = '1' if linha['faixa'] else '0'
        xml += _linha_altura()
        for valor in linha['valores']:
            xml += _celula(valor, f'es{faixa}')
        xml += '</table:table-row>'
    xml += '</table:table>'
    return xml


def _linha_altura():
    return '<table:table-row table:style-name="rh">'


def _celula(valor, estilo):
    return (
        f'<table:table-cell table:style-name="{estilo}" office:value-type="string">'
        f'<text:p>{_x(valor)}</text:p></table:table-cell>'
    )


def _celula_numero(valor):
    return (
        f'<table:table-cell table:style-name="val" office:value-type="float" office:value="{int(valor)}">'
        f'<text:p>{int(valor)}</text:p></table:table-cell>'
    )


def _x(valor):
    texto = '' if valor is None else str(valor)
    return (texto.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def _xa(valor):
    return _x(valor).replace('"', '&quot;')


_MANIFEST = '''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">
 <manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/>
 <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
</manifest:manifest>
'''

_STYLES = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" office:version="1.2">
 <office:font-face-decls>
  <style:font-face style:name="Calibri" svg:font-family="Calibri" style:font-family-generic="swiss"/>
 </office:font-face-decls>
 <office:styles>
  <style:default-style style:family="table-cell">
   <style:text-properties style:font-name="Calibri" fo:font-size="11pt" fo:color="#000000"/>
  </style:default-style>
  <style:style style:name="Default" style:family="table-cell">
   <style:table-cell-properties style:vertical-align="middle"/>
   <style:text-properties style:font-name="Calibri" fo:font-size="11pt" fo:color="#000000"/>
  </style:style>
 </office:styles>
</office:document-styles>
'''
