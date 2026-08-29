import calendar
import csv
import io
from datetime import datetime, date

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from flask import Blueprint, render_template, request, abort, Response
from flask_login import login_required, current_user

from app import db
from app.models.equipamento import Equipamento, TipoEquipamento, STATUS_LABELS, CONDICAO_LABELS
from app.models.unidade import Unidade, UsuarioUnidade
from app.models.tipo_unidade import TipoUnidade
from app.models.sala import Sala
from app.models.tipo_sala import TipoSala
from app.models.chamado import Chamado
from app.models.contrato import Contrato, STATUS_CONTRATO_LABELS
from app.models.contrato_financeiro import ContratoFinanceiro
from app.models.usuario import Usuario, PERFIS
from app.models.ficha_cnes import FichaCnesVinculo
from app.models.matricula import MatriculaProfissional
from app.models.falta_abonada import FaltaAbonada

relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')

# ── Cabeçalho XLSX ─────────────────────────────────────────────────────────────
_HEADER_FILL  = PatternFill('solid', fgColor='1a56a0')
_HEADER_FONT  = Font(bold=True, color='FFFFFF')
_HEADER_ALIGN = Alignment(horizontal='center', vertical='center', wrap_text=True)

def _estilizar_cabecalho(ws, colunas):
    """Aplica estilo e largura automática no cabeçalho."""
    ws.append(colunas)
    for cell in ws[1]:
        cell.font  = _HEADER_FONT
        cell.fill  = _HEADER_FILL
        cell.alignment = _HEADER_ALIGN
    ws.row_dimensions[1].height = 22

def _autofit(ws):
    """Ajusta largura das colunas pela maior célula."""
    for col in ws.columns:
        max_len = max((len(str(c.value or '')) for c in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

def _xlsx_response(wb, nome_arquivo):
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{nome_arquivo}.xlsx"'}
    )

def _csv_response(linhas, nome_arquivo):
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=';', quoting=csv.QUOTE_ALL)
    for linha in linhas:
        writer.writerow(linha)
    return Response(
        '\ufeff' + buf.getvalue(),   # BOM para abrir corretamente no Excel BR
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{nome_arquivo}.csv"'}
    )


# ── Helpers de leitura de filtros multi-valor ──────────────────────────────────
def _getlist(param):
    """Retorna lista de inteiros para parâmetros repetidos ex: ?unidade=1&unidade=3"""
    return [int(v) for v in request.args.getlist(param) if v.isdigit()]

def _getstrlist(param):
    """Retorna lista de strings para parâmetros repetidos ex: ?status=aberto&status=concluido"""
    return [v for v in request.args.getlist(param) if v]

def _ids_unidades_permitidas():
    """Retorna lista de IDs de unidades que o usuário pode ver, ou None se pode ver tudo."""
    if current_user.pode('ver_todas_unidades'):
        return None
    return [uu.unidade_id for uu in current_user.unidades.filter_by(ativo=True).all()]

def _filtrar_por_tipo_unidade(query, model_unidade_id_col, tipo_unidade_ids):
    """Aplica filtro de tipo de unidade via join com Unidade."""
    if not tipo_unidade_ids:
        return query
    return query.join(Unidade, model_unidade_id_col == Unidade.id).filter(
        Unidade.tipo_unidade_id.in_(tipo_unidade_ids)
    )


# ── Query compartilhada ────────────────────────────────────────────────────────
def _query_inventario():
    unidade_ids      = _getlist('unidade')
    tipo_unidade_ids = _getlist('tipo_unidade')
    tipo_ids         = _getlist('tipo')
    status_list      = _getstrlist('status')
    condicao_list    = _getstrlist('condicao')
    sala_ids         = _getlist('sala')

    query = Equipamento.query.filter_by(ativo=True)

    permitidas = _ids_unidades_permitidas()
    if permitidas is not None:
        query = query.join(Sala, Equipamento.sala_id == Sala.id).filter(Sala.unidade_id.in_(permitidas))
    else:
        # join condicional para filtros de unidade/tipo_unidade
        if unidade_ids or tipo_unidade_ids:
            query = query.join(Sala, Equipamento.sala_id == Sala.id)

    if unidade_ids:
        query = query.filter(Sala.unidade_id.in_(unidade_ids))
    if tipo_unidade_ids:
        query = query.join(Unidade, Sala.unidade_id == Unidade.id).filter(
            Unidade.tipo_unidade_id.in_(tipo_unidade_ids)
        )
    if tipo_ids:
        query = query.filter(Equipamento.tipo_equipamento_id.in_(tipo_ids))
    if status_list:
        query = query.filter(Equipamento.status.in_(status_list))
    if condicao_list:
        query = query.filter(Equipamento.condicao.in_(condicao_list))
    if sala_ids:
        query = query.filter(Equipamento.sala_id.in_(sala_ids))

    return query.order_by(Equipamento.tipo_equipamento_id, Equipamento.id).all()


def _query_chamados():
    unidade_ids      = _getlist('unidade')
    tipo_unidade_ids = _getlist('tipo_unidade')
    status_list      = _getstrlist('status')
    tipo_list        = _getstrlist('tipo')
    prioridade_list  = _getstrlist('prioridade')

    query = Chamado.query

    permitidas = _ids_unidades_permitidas()
    if permitidas is not None:
        query = query.filter(Chamado.unidade_id.in_(permitidas))

    if unidade_ids:
        query = query.filter(Chamado.unidade_id.in_(unidade_ids))
    if tipo_unidade_ids:
        query = query.join(Unidade, Chamado.unidade_id == Unidade.id).filter(
            Unidade.tipo_unidade_id.in_(tipo_unidade_ids)
        )
    if status_list:
        query = query.filter(Chamado.status.in_(status_list))
    if tipo_list:
        query = query.filter(Chamado.tipo_chamado.in_(tipo_list))
    if prioridade_list:
        query = query.filter(Chamado.prioridade.in_(prioridade_list))

    return query.order_by(Chamado.criado_em.desc()).all()


def _query_contratos():
    lista = Contrato.query.order_by(Contrato.data_fim.asc()).all()
    for c in lista:
        c.atualizar_status()
    db.session.commit()
    return lista


# ── Helpers de linha ──────────────────────────────────────────────────────────
def _linhas_inventario(equipamentos):
    cabecalho = [
        'Patrimônio', 'Tipo', 'Marca', 'Modelo', 'Nº Série',
        'Unidade', 'Sala', 'Status', 'Condição',
        'Usuário(s) Vinculado(s)', 'Contrato (SEI)', 'Data Aquisição', 'Valor Estimado (R$)'
    ]
    linhas = [cabecalho]
    for e in equipamentos:
        usuarios = '; '.join(ev.usuario.nome for ev in e.usuarios_vinculados.all())
        c = e.contrato_vigente
        linhas.append([
            e.numero_patrimonio or '',
            e.tipo_equipamento.nome if e.tipo_equipamento else '',
            e.marca.nome if e.marca else '',
            e.modelo.nome if e.modelo else '',
            e.numero_serie or '',
            e.sala.unidade.nome if e.sala else '',
            e.sala.nome if e.sala else '',
            STATUS_LABELS.get(e.status, e.status),
            CONDICAO_LABELS.get(e.condicao, e.condicao),
            usuarios,
            (c.identificador if c else ''),
            str(e.data_aquisicao) if e.data_aquisicao else '',
            str(e.valor_estimado) if e.valor_estimado else '',
        ])
    return linhas


def _linhas_chamados(chamados):
    cabecalho = [
        'Número', 'Unidade', 'Tipo', 'Título', 'Descrição',
        'Prioridade', 'Status', 'Aberto em', 'Fechado em'
    ]
    linhas = [cabecalho]
    for c in chamados:
        linhas.append([
            c.numero,
            c.unidade.nome if c.unidade else '',
            c.tipo_label,
            c.titulo,
            c.descricao or '',
            c.prioridade_label,
            c.status_label,
            c.criado_em.strftime('%d/%m/%Y') if c.criado_em else '',
            c.fechado_em.strftime('%d/%m/%Y') if c.fechado_em else '',
        ])
    return linhas


def _query_salas():
    unidade_ids      = _getlist('unidade')
    tipo_unidade_ids = _getlist('tipo_unidade')
    tipo_sala_ids    = _getlist('tipo_sala')
    com_chamado      = request.args.get('com_chamado', '')

    query = Sala.query.filter_by(ativo=True)

    permitidas = _ids_unidades_permitidas()
    if permitidas is not None:
        query = query.filter(Sala.unidade_id.in_(permitidas))

    if unidade_ids:
        query = query.filter(Sala.unidade_id.in_(unidade_ids))
    if tipo_unidade_ids:
        query = query.join(Unidade, Sala.unidade_id == Unidade.id).filter(
            Unidade.tipo_unidade_id.in_(tipo_unidade_ids)
        )
    if tipo_sala_ids:
        query = query.filter(Sala.tipo_sala_id.in_(tipo_sala_ids))

    salas = query.order_by(Sala.unidade_id, Sala.nome).all()

    if com_chamado == 'sim':
        salas = [s for s in salas if s.chamados.filter(
            Chamado.status.notin_(['concluido', 'cancelado'])
        ).count() > 0]
    elif com_chamado == 'nao':
        salas = [s for s in salas if s.chamados.filter(
            Chamado.status.notin_(['concluido', 'cancelado'])
        ).count() == 0]

    return salas


def _linhas_salas(salas):
    cabecalho = [
        'Unidade', 'Sala', 'Tipo', 'Ramal',
        'Equipamentos Ativos', 'Chamados Abertos', 'Total Chamados', 'Observações'
    ]
    linhas = [cabecalho]
    for s in salas:
        chamados_abertos = s.chamados.filter(
            Chamado.status.notin_(['concluido', 'cancelado'])
        ).count()
        linhas.append([
            s.unidade.nome if s.unidade else '',
            s.nome,
            s.tipo_label,
            s.ramal or '',
            s.total_equipamentos,
            chamados_abertos,
            s.chamados.count(),
            s.observacoes or '',
        ])
    return linhas


def _linhas_contratos(contratos):
    cabecalho = [
        'Nº SEI', 'Empresa', 'Tipo', 'Objeto', 'Equipamentos cobertos',
        'Início', 'Vencimento', 'Dias Restantes', 'Status', 'Total de Itens'
    ]
    linhas = [cabecalho]
    for c in contratos:
        linhas.append([
            c.identificador or '',
            c.empresa_display or '',
            c.tipo_contrato or '',
            (c.objeto or '')[:500],
            c.equipamentos_cobertos_display or '',
            c.data_inicio.strftime('%d/%m/%Y') if c.data_inicio else '',
            c.data_fim.strftime('%d/%m/%Y') if c.data_fim else '',
            c.dias_restantes,
            c.status_label,
            c.total_itens,
        ])
    return linhas


def _cabecalho_contratos_planilha():
    """Cabeçalho da planilha CONTRATOS ATUAL."""
    return [
        'SEÇÃO', 'PRESTADOR', 'CPL', 'OBJETO', 'Nº DO CONTRA', 'CNPJ',
        'DATA DE INÍCIO', 'DATA DE ASSI', 'VIGÊNCIA', 'VENC', 'STATUS',
        'MANDADO JUDICIAL',
        'FONTE', 'VALOR INICIAL TOTAL DO CONTRATO', 'VALOR ATUAL DO CONTRATO',
        'VALOR MENSAL ATUAL DO CONTRATO', 'ADITIVO (DATA E %)',
        'REAJUSTE (DATA BASE E %)', 'FISCALIZAÇÃO', 'OBS',
        'SUPRESSÃO (DATA E %)', 'CONTATO (NOME E TELEFONE)', 'EMPENHOS',
        'DATA DA ATUALIZAÇÃO',
    ]


def _linha_contrato_planilha(c):
    """Uma linha no formato da planilha CONTRATOS ATUAL."""
    return [
        c.secao or '',
        c.empresa_display or '',
        c.cpl or '',
        (c.objeto or '')[:500],
        c.numero_contrato or c.identificador or '',
        c.cnpj_display or '',
        c.data_inicio.strftime('%d/%m/%Y') if c.data_inicio else '',
        c.data_assinatura.strftime('%d/%m/%Y') if c.data_assinatura else '',
        c.vigencia or '',
        c.data_fim.strftime('%d/%m/%Y') if c.data_fim else '',
        STATUS_CONTRATO_LABELS.get(c.status, c.status or ''),
        'Sim' if getattr(c, 'mandado_judicial', False) else 'Não',
        c.fonte or '',
        str(c.valor_inicial) if c.valor_inicial is not None else '',
        str(c.valor_atual) if c.valor_atual is not None else '',
        str(c.valor_mensal_atual) if c.valor_mensal_atual is not None else '',
        c.aditivo_data_pct or '',
        c.reajuste_data_base_pct or '',
        c.fiscalizacao or '',
        (c.observacoes or '')[:500],
        c.supressao_data_pct or '',
        c.contato_nome_telefone or '',
        (c.empenhos or '')[:500],
        c.atualizado_em.strftime('%d/%m/%Y %H:%M') if c.atualizado_em else '',
    ]


def _cabecalho_financeiro_dag():
    """Cabeçalho da planilha FINANCEIRO - DAG."""
    return [
        'TIPO', 'PROCESSO', 'MOTIVO', 'PRESTADOR', 'OBJETO', 'REFERÊNCIA',
        'VALOR TOTAL', 'ESPECIALIZADA', 'VIGILÂNCIA', 'ATENÇÃO BÁSICA', 'OUTROS',
        'TABELA SUS', 'COMPLEMENTO', 'EMENDA MUNICIPAL', 'EMENDA ESTADUAL',
        'EMENDA FEDERAL', 'OBSERVAÇÃO', 'DATA NECESSÁRIA',
        'DATA DE ENVIO PARA DIVISÃO', 'DATA DE ENVIO PARA FMS',
        'DATA DE DEVOLUÇÃO PARA O SETOR', 'RESERVAS',
    ]


def _linha_financeiro_dag(i):
    """Uma linha no formato da planilha FINANCEIRO - DAG."""
    return [
        i.tipo or '',
        i.processo_display if hasattr(i, 'processo_display') else (i.processo or ''),
        i.motivo or '',
        i.prestador_display if hasattr(i, 'prestador_display') else (i.prestador or ''),
        (i.objeto or '')[:500],
        i.referencia or '',
        str(i.valor_total) if i.valor_total is not None else '',
        i.especializada or '',
        i.vigilancia or '',
        i.atencao_basica or '',
        i.outros or '',
        i.tabela_sus or '',
        i.complemento or '',
        i.emenda_municipal or '',
        i.emenda_estadual or '',
        i.emenda_federal or '',
        (i.observacao or '')[:500],
        i.data_necessaria.strftime('%d/%m/%Y') if i.data_necessaria else '',
        i.data_envio_divisao.strftime('%d/%m/%Y') if i.data_envio_divisao else '',
        i.data_envio_fms.strftime('%d/%m/%Y') if i.data_envio_fms else '',
        i.data_devolucao_setor.strftime('%d/%m/%Y') if i.data_devolucao_setor else '',
        i.reservas or '',
    ]


# ══════════════════════════════════════════════════════════════════════════════
#  ROTAS PRINCIPAIS (HTML)
# ══════════════════════════════════════════════════════════════════════════════

@relatorios_bp.route('/')
@login_required
def index():
    if not current_user.pode('emitir_relatorios'):
        abort(403)
    return render_template('relatorios/index.html')


@relatorios_bp.route('/inventario')
@login_required
def inventario():
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    filtro_unidades      = _getlist('unidade')
    filtro_tipo_unidades = _getlist('tipo_unidade')
    filtro_tipos         = _getlist('tipo')
    filtro_status_list   = _getstrlist('status')
    filtro_condicao_list = _getstrlist('condicao')

    equipamentos = _query_inventario()
    unidades      = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()
    tipos         = TipoEquipamento.query.order_by(TipoEquipamento.nome).all()

    total        = len(equipamentos)
    por_status   = {}
    por_condicao = {}
    for e in equipamentos:
        por_status[e.status]   = por_status.get(e.status, 0) + 1
        por_condicao[e.condicao] = por_condicao.get(e.condicao, 0) + 1

    return render_template('relatorios/inventario.html',
                           equipamentos=equipamentos,
                           unidades=unidades, tipos_unidade=tipos_unidade, tipos=tipos,
                           status_labels=STATUS_LABELS, condicao_labels=CONDICAO_LABELS,
                           total=total, por_status=por_status, por_condicao=por_condicao,
                           filtro_unidades=filtro_unidades,
                           filtro_tipo_unidades=filtro_tipo_unidades,
                           filtro_tipos=filtro_tipos,
                           filtro_status_list=filtro_status_list,
                           filtro_condicao_list=filtro_condicao_list)


@relatorios_bp.route('/chamados')
@login_required
def chamados():
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    filtro_unidades      = _getlist('unidade')
    filtro_tipo_unidades = _getlist('tipo_unidade')
    filtro_status_list   = _getstrlist('status')
    filtro_tipo_list     = _getstrlist('tipo')
    filtro_prioridade_list = _getstrlist('prioridade')

    chamados_lista = _query_chamados()
    unidades      = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()

    from app.models.chamado import TIPOS_CHAMADO_LABELS, PRIORIDADES_LABELS, STATUS_CHAMADO_LABELS
    return render_template('relatorios/chamados.html',
                           chamados=chamados_lista,
                           unidades=unidades, tipos_unidade=tipos_unidade,
                           tipos_labels=TIPOS_CHAMADO_LABELS,
                           prioridades_labels=PRIORIDADES_LABELS,
                           status_labels=STATUS_CHAMADO_LABELS,
                           filtro_unidades=filtro_unidades,
                           filtro_tipo_unidades=filtro_tipo_unidades,
                           filtro_status_list=filtro_status_list,
                           filtro_tipo_list=filtro_tipo_list,
                           filtro_prioridade_list=filtro_prioridade_list)


@relatorios_bp.route('/contratos')
@login_required
def contratos():
    if not current_user.pode('emitir_relatorios'):
        abort(403)
    from app.models.contrato import STATUS_CONTRATO_LABELS
    status_list = _getstrlist('status')
    contratos_lista = _query_contratos()
    if status_list:
        contratos_lista = [c for c in contratos_lista if c.status in status_list]
    return render_template('relatorios/contratos.html',
                           contratos=contratos_lista,
                           status_labels=STATUS_CONTRATO_LABELS if 'STATUS_CONTRATO_LABELS' in dir() else {},
                           filtro_status_list=status_list)


# ══════════════════════════════════════════════════════════════════════════════
#  RELATÓRIO — SALAS
# ══════════════════════════════════════════════════════════════════════════════

@relatorios_bp.route('/salas')
@login_required
def salas():
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    filtro_unidades      = _getlist('unidade')
    filtro_tipo_unidades = _getlist('tipo_unidade')
    filtro_tipo_salas    = _getlist('tipo_sala')
    com_chamado          = request.args.get('com_chamado', '')

    salas_lista   = _query_salas()
    unidades      = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()
    tipos_sala    = TipoSala.query.filter_by(ativo=True).order_by(TipoSala.nome).all()

    # Pré-calcula contagens para não usar lazy queries no template
    STATUS_ABERTOS = ['concluido', 'cancelado']
    salas_data = []
    por_tipo   = {}
    tipo_ids   = {}   # nome_tipo -> tipo_sala_id (para links de filtro)
    total_equip = 0
    total_chamados_abertos = 0

    for s in salas_lista:
        ab = s.chamados.filter(Chamado.status.notin_(STATUS_ABERTOS)).count()
        tot = s.chamados.count()
        t = s.tipo_label
        por_tipo[t] = por_tipo.get(t, 0) + 1
        if s.tipo_sala_id and t not in tipo_ids:
            tipo_ids[t] = s.tipo_sala_id
        total_equip += s.total_equipamentos
        total_chamados_abertos += ab
        salas_data.append({
            'sala_id':         s.id,
            'unidade_nome':    s.unidade.nome if s.unidade else '—',
            'nome':            s.nome,
            'tipo':            t,
            'icone':           s.tipo_icone,
            'ramal':           s.ramal,
            'equip_ativos':    s.total_equipamentos,
            'chamados_abertos': ab,
            'chamados_total':  tot,
        })

    return render_template('relatorios/salas.html',
                           salas_data=salas_data,
                           unidades=unidades,
                           tipos_unidade=tipos_unidade,
                           tipos_sala=tipos_sala,
                           total=len(salas_data),
                           por_tipo=por_tipo,
                           tipo_ids=tipo_ids,
                           total_equip=total_equip,
                           total_chamados_abertos=total_chamados_abertos,
                           filtro_unidades=filtro_unidades,
                           filtro_tipo_unidades=filtro_tipo_unidades,
                           filtro_tipo_salas=filtro_tipo_salas,
                           filtro_com_chamado=com_chamado)


@relatorios_bp.route('/salas/exportar/<formato>')
@login_required
def exportar_salas(formato):
    if not current_user.pode('emitir_relatorios'):
        abort(403)
    salas_lista = _query_salas()
    linhas = _linhas_salas(salas_lista)
    ts   = datetime.now().strftime('%Y%m%d_%H%M')
    nome = f'salas_{ts}'

    if formato == 'csv':
        return _csv_response(linhas, nome)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Salas'
    _estilizar_cabecalho(ws, linhas[0])
    for linha in linhas[1:]:
        ws.append(linha)
    _autofit(ws)
    ws.freeze_panes = 'A2'

    if formato == 'xls':
        return Response(
            _xlsx_response(wb, nome).get_data(),
            mimetype='application/vnd.ms-excel',
            headers={'Content-Disposition': f'attachment; filename="{nome}.xls"'}
        )
    return _xlsx_response(wb, nome)


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORTAÇÃO — INVENTÁRIO
# ══════════════════════════════════════════════════════════════════════════════

@relatorios_bp.route('/inventario/exportar/<formato>')
@login_required
def exportar_inventario(formato):
    if not current_user.pode('emitir_relatorios'):
        abort(403)
    equipamentos = _query_inventario()
    linhas = _linhas_inventario(equipamentos)
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    nome = f'inventario_{ts}'

    if formato == 'csv':
        return _csv_response(linhas, nome)

    # XLSX (serve também para XLS — mesmo arquivo, extensão diferente)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Inventário'
    _estilizar_cabecalho(ws, linhas[0])
    for linha in linhas[1:]:
        ws.append(linha)
    _autofit(ws)
    ws.freeze_panes = 'A2'

    if formato == 'xls':
        # Mesmo arquivo XLSX, apenas extensão diferente (Excel abre sem problemas)
        return Response(
            _xlsx_response(wb, nome).get_data(),
            mimetype='application/vnd.ms-excel',
            headers={'Content-Disposition': f'attachment; filename="{nome}.xls"'}
        )
    return _xlsx_response(wb, nome)


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORTAÇÃO — CHAMADOS
# ══════════════════════════════════════════════════════════════════════════════

@relatorios_bp.route('/chamados/exportar/<formato>')
@login_required
def exportar_chamados(formato):
    if not current_user.pode('emitir_relatorios'):
        abort(403)
    chamados_lista = _query_chamados()
    linhas = _linhas_chamados(chamados_lista)
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    nome = f'chamados_{ts}'

    if formato == 'csv':
        return _csv_response(linhas, nome)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Chamados'
    _estilizar_cabecalho(ws, linhas[0])
    for linha in linhas[1:]:
        ws.append(linha)
    _autofit(ws)
    ws.freeze_panes = 'A2'

    if formato == 'xls':
        return Response(
            _xlsx_response(wb, nome).get_data(),
            mimetype='application/vnd.ms-excel',
            headers={'Content-Disposition': f'attachment; filename="{nome}.xls"'}
        )
    return _xlsx_response(wb, nome)


# ══════════════════════════════════════════════════════════════════════════════
#  RELATÓRIO — USUÁRIOS / PROFISSIONAIS
# ══════════════════════════════════════════════════════════════════════════════

def _ultima_ficha_ativa(usuario_id, unidade_id):
    """Retorna a ficha CNES mais recente de cadastro/alteração para um vínculo."""
    return (
        FichaCnesVinculo.query
        .filter(
            FichaCnesVinculo.usuario_id == usuario_id,
            FichaCnesVinculo.unidade_id == unidade_id,
            FichaCnesVinculo.tipo.in_(['cadastro', 'alteracao']),
        )
        .order_by(FichaCnesVinculo.gerado_em.desc())
        .first()
    )


def _query_usuarios():
    """Retorna 1 linha por pessoa. Para cada vínculo ativo a person possui, agrega:
    unidade | matrícula | CBO (da ficha) | conselho | órgão
    em listas, exibidas separadas por vírgula no relatório."""
    from app.models.matricula import MatriculaProfissional

    perfil_list      = _getstrlist('perfil')
    unidade_ids      = _getlist('unidade')
    tipo_unidade_ids = _getlist('tipo_unidade')
    apenas_ativos    = request.args.get('apenas_ativos', '1')

    # Restrição de visibilidade
    permitidas = _ids_unidades_permitidas()  # None = pode tudo

    # Todos os vínculos ativos respeitando filtros de unidade
    q_uu = UsuarioUnidade.query.filter_by(ativo=True)
    if permitidas is not None:
        q_uu = q_uu.filter(UsuarioUnidade.unidade_id.in_(permitidas))
    if unidade_ids:
        q_uu = q_uu.filter(UsuarioUnidade.unidade_id.in_(unidade_ids))

    vinculos = q_uu.all()

    # Filtro por tipo de unidade
    if tipo_unidade_ids:
        vinculos = [
            v for v in vinculos
            if v.unidade and v.unidade.tipo_unidade_id in tipo_unidade_ids
        ]

    # Agrupa vínculos por usuário
    from collections import defaultdict
    por_usuario = defaultdict(list)
    for v in vinculos:
        if v.usuario:
            por_usuario[v.usuario_id].append(v)

    # Uma entrada por vínculo (profissional × unidade)
    linhas_flat = []
    for uid, uvinculos in por_usuario.items():
        u = uvinculos[0].usuario
        if u.perfil == 'administrador':
            continue
        if apenas_ativos == '1' and not u.ativo:
            continue
        if perfil_list and u.perfil not in perfil_list:
            continue

        for v in uvinculos:
            un = v.unidade
            ficha  = _ultima_ficha_ativa(u.id, v.unidade_id)
            mat    = v.matricula

            cbo_label = (ficha.cbo_label if ficha and ficha.cbo else None) \
                        or (mat.cbo_label if mat and mat.cbo else None) \
                        or '—'

            # Endereço concatenado
            partes_end = [p for p in [
                un.endereco    if un else None,
                un.numero      if un else None,
                un.complemento if un else None,
                un.bairro      if un else None,
                un.cidade   if un else None,
                un.uf       if un else None,
            ] if p]
            endereco = ', '.join(partes_end) if partes_end else '—'

            linhas_flat.append({
                'cnes':          un.numero_cnes or '—' if un else '—',
                'unidade':       un.nome if un else '—',
                'email_unidade': un.email or '—' if un else '—',
                'tel_unidade':   un.telefone or '—' if un else '—',
                'end_unidade':   endereco,
                'nome':          u.nome,
                'whatsapp':      u.whatsapp or '—',
                'email':         u.email or '—',
                'cbo':           cbo_label,
                'ativo':         u.ativo,
                'id':            u.id,
            })

    linhas_flat.sort(key=lambda r: (r['unidade'], r['nome']))
    return linhas_flat


def _fmt_fone(valor):
    """Formata número de telefone/WhatsApp para (XX) XXXXX-XXXX."""
    if not valor or valor == '—':
        return valor
    digits = ''.join(c for c in str(valor) if c.isdigit())
    if len(digits) == 11:
        return f'({digits[:2]}) {digits[2:7]}-{digits[7:]}'
    if len(digits) == 10:
        return f'({digits[:2]}) {digits[2:6]}-{digits[6:]}'
    return valor


def _linhas_usuarios(rows):
    cabecalho = [
        'CNES', 'Unidade', 'E-mail da Unidade', 'Telefone da Unidade',
        'Endereço da Unidade', 'Nome do Profissional',
        'Telefone (WhatsApp)', 'E-mail do Profissional', 'CBO',
    ]
    linhas = [cabecalho]
    for r in rows:
        linhas.append([
            r['cnes'], r['unidade'], r['email_unidade'], r['tel_unidade'],
            r['end_unidade'], r['nome'],
            _fmt_fone(r['whatsapp']), r['email'], r['cbo'],
        ])
    return linhas


@relatorios_bp.route('/profissionais')
@login_required
def profissionais():
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    filtro_perfis        = _getstrlist('perfil')
    filtro_unidades      = _getlist('unidade')
    filtro_tipo_unidades = _getlist('tipo_unidade')
    apenas_ativos        = request.args.get('apenas_ativos', '1')

    rows          = _query_usuarios()
    unidades      = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()

    # Administrador não aparece como opção de filtro neste relatório
    perfis_relatorio = {k: v for k, v in PERFIS.items() if k != 'administrador'}

    return render_template('relatorios/profissionais.html',
                           rows=rows,
                           perfis=perfis_relatorio,
                           unidades=unidades,
                           tipos_unidade=tipos_unidade,
                           total=len(rows),
                           filtro_perfis=filtro_perfis,
                           filtro_unidades=filtro_unidades,
                           filtro_tipo_unidades=filtro_tipo_unidades,
                           apenas_ativos=apenas_ativos)


@relatorios_bp.route('/profissionais/exportar/<formato>')
@login_required
def exportar_profissionais(formato):
    if not current_user.pode('emitir_relatorios'):
        abort(403)
    rows   = _query_usuarios()
    linhas = _linhas_usuarios(rows)
    ts     = datetime.now().strftime('%Y%m%d_%H%M')
    nome   = f'profissionais_{ts}'

    if formato == 'csv':
        return _csv_response(linhas, nome)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Profissionais'
    _estilizar_cabecalho(ws, linhas[0])
    for linha in linhas[1:]:
        ws.append(linha)
    _autofit(ws)
    ws.freeze_panes = 'A2'

    if formato == 'xls':
        return Response(
            _xlsx_response(wb, nome).get_data(),
            mimetype='application/vnd.ms-excel',
            headers={'Content-Disposition': f'attachment; filename="{nome}.xls"'}
        )
    return _xlsx_response(wb, nome)


# ══════════════════════════════════════════════════════════════════════════════
#  RELATÓRIO DE USUÁRIOS (visão cadastral — igual à listagem)
# ══════════════════════════════════════════════════════════════════════════════

@relatorios_bp.route('/usuarios')
@login_required
def usuarios():
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    from app.models.matricula import MatriculaProfissional

    filtro_perfis    = _getstrlist('perfil')
    apenas_ativos    = request.args.get('apenas_ativos', '1')

    # Base — sem administradores
    q = Usuario.query.filter(Usuario.perfil != 'administrador')
    if apenas_ativos == '1':
        q = q.filter_by(ativo=True)
    if filtro_perfis:
        q = q.filter(Usuario.perfil.in_(filtro_perfis))

    # Restrição de visibilidade para não-admin
    if not current_user.pode('gerenciar_usuarios'):
        permitidas = _ids_unidades_permitidas() or []
        ids_vis = db.session.query(UsuarioUnidade.usuario_id).filter(
            UsuarioUnidade.unidade_id.in_(permitidas),
            UsuarioUnidade.ativo == True,
        ).distinct()
        q = q.filter(Usuario.id.in_(ids_vis))

    usuarios_lista = q.order_by(Usuario.nome).all()

    # Pré-carrega matrículas por usuário (evita N+1)
    ids_usuarios = [u.id for u in usuarios_lista]
    mats_por_usuario = {}
    if ids_usuarios:
        todas_mats = (MatriculaProfissional.query
                      .filter(MatriculaProfissional.usuario_id.in_(ids_usuarios))
                      .order_by(MatriculaProfissional.ativo.desc(), MatriculaProfissional.numero)
                      .all())
        for m in todas_mats:
            mats_por_usuario.setdefault(m.usuario_id, []).append(m)

    perfis_relatorio = {k: v for k, v in PERFIS.items() if k != 'administrador'}

    return render_template('relatorios/usuarios.html',
                           usuarios=usuarios_lista,
                           mats_por_usuario=mats_por_usuario,
                           perfis=perfis_relatorio,
                           total=len(usuarios_lista),
                           filtro_perfis=filtro_perfis,
                           apenas_ativos=apenas_ativos)


@relatorios_bp.route('/usuarios/exportar/<formato>')
@login_required
def exportar_usuarios(formato):
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    from app.models.matricula import MatriculaProfissional

    apenas_ativos = request.args.get('apenas_ativos', '1')
    filtro_perfis = _getstrlist('perfil')

    q = Usuario.query.filter(Usuario.perfil != 'administrador')
    if apenas_ativos == '1':
        q = q.filter_by(ativo=True)
    if filtro_perfis:
        q = q.filter(Usuario.perfil.in_(filtro_perfis))

    if not current_user.pode('gerenciar_usuarios'):
        permitidas = _ids_unidades_permitidas() or []
        ids_vis = db.session.query(UsuarioUnidade.usuario_id).filter(
            UsuarioUnidade.unidade_id.in_(permitidas),
            UsuarioUnidade.ativo == True,
        ).distinct()
        q = q.filter(Usuario.id.in_(ids_vis))

    usuarios_lista = q.order_by(Usuario.nome).all()
    ids_usuarios   = [u.id for u in usuarios_lista]
    mats_por_usuario = {}
    if ids_usuarios:
        todas_mats = (MatriculaProfissional.query
                      .filter(MatriculaProfissional.usuario_id.in_(ids_usuarios))
                      .order_by(MatriculaProfissional.ativo.desc(), MatriculaProfissional.numero)
                      .all())
        for m in todas_mats:
            mats_por_usuario.setdefault(m.usuario_id, []).append(m)

    # Monta linhas para exportação
    cabecalho = ['Nome', 'E-mail', 'WhatsApp', 'Perfil', 'Matrícula', 'CBO', 'Conselho',
                 'Órgão Emissor', 'Matrícula Ativa', 'Situação']
    linhas = [cabecalho]
    for u in usuarios_lista:
        mats = mats_por_usuario.get(u.id, [])
        situacao = 'Ativo' if u.ativo else 'Inativo'
        if mats:
            for m in mats:
                linhas.append([
                    u.nome, u.email, u.whatsapp or '',
                    u.perfil_label,
                    m.numero, m.cbo_label, m.reg_conselho or '',
                    m.orgao_emissor or '', 'Sim' if m.ativo else 'Não',
                    situacao,
                ])
        else:
            linhas.append([
                u.nome, u.email, u.whatsapp or '',
                u.perfil_label,
                '—', '—', '—', '—', '—', situacao,
            ])

    ts   = datetime.now().strftime('%Y%m%d_%H%M')
    nome = f'usuarios_{ts}'

    if formato == 'csv':
        return _csv_response(linhas, nome)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Usuários'
    _estilizar_cabecalho(ws, linhas[0])
    for linha in linhas[1:]:
        ws.append(linha)
    _autofit(ws)
    ws.freeze_panes = 'A2'

    if formato == 'xls':
        return Response(
            _xlsx_response(wb, nome).get_data(),
            mimetype='application/vnd.ms-excel',
            headers={'Content-Disposition': f'attachment; filename="{nome}.xls"'}
        )
    return _xlsx_response(wb, nome)


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORTAÇÃO — CONTRATOS
# ══════════════════════════════════════════════════════════════════════════════

@relatorios_bp.route('/contratos/exportar/<formato>')
@login_required
def exportar_contratos(formato):
    if not current_user.pode('emitir_relatorios'):
        abort(403)
    contratos_lista = _query_contratos()
    linhas = _linhas_contratos(contratos_lista)
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    nome = f'contratos_{ts}'

    if formato == 'csv':
        return _csv_response(linhas, nome)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Contratos'
    _estilizar_cabecalho(ws, linhas[0])
    for linha in linhas[1:]:
        ws.append(linha)
    _autofit(ws)
    ws.freeze_panes = 'A2'

    if formato == 'xls':
        return Response(
            _xlsx_response(wb, nome).get_data(),
            mimetype='application/vnd.ms-excel',
            headers={'Content-Disposition': f'attachment; filename="{nome}.xls"'}
        )
    return _xlsx_response(wb, nome)


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORTAÇÃO — CONTRATOS (formato planilha CONTRATOS ATUAL)
# ══════════════════════════════════════════════════════════════════════════════

@relatorios_bp.route('/contratos/exportar-planilha/<formato>')
@login_required
def exportar_contratos_planilha(formato):
    """Exporta contratos no formato da planilha CONTRATOS ATUAL (com abas por tag)."""
    if not current_user.pode('emitir_relatorios'):
        abort(403)
    contratos_lista = _query_contratos()
    status_list = _getstrlist('status')
    mandado_filter = request.args.get('mandado_judicial', '')
    if status_list:
        contratos_lista = [c for c in contratos_lista if c.status in status_list]
    if mandado_filter == '1':
        contratos_lista = [c for c in contratos_lista if c.mandado_judicial]
    elif mandado_filter == '0':
        contratos_lista = [c for c in contratos_lista if not c.mandado_judicial]

    ts = datetime.now().strftime('%Y%m%d_%H%M')
    nome = f'CONTRATOS_ATUAL_{ts}'

    cabecalho = _cabecalho_contratos_planilha()
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    # Sheet "Todos" primeiro
    ws_todos = wb.create_sheet('Todos', 0)
    _estilizar_cabecalho(ws_todos, cabecalho)
    for c in contratos_lista:
        ws_todos.append(_linha_contrato_planilha(c))
    _autofit(ws_todos)
    ws_todos.freeze_panes = 'A2'
    # Aba "Mandados Judiciais" se houver
    mj_lista = [c for c in contratos_lista if c.mandado_judicial]
    if mj_lista:
        ws_mj = wb.create_sheet('Mandados Judiciais', 1)
        _estilizar_cabecalho(ws_mj, cabecalho)
        for c in mj_lista:
            ws_mj.append(_linha_contrato_planilha(c))
        _autofit(ws_mj)
        ws_mj.freeze_panes = 'A2'

    if formato == 'csv':
        return _csv_response([cabecalho] + [_linha_contrato_planilha(c) for c in contratos_lista], nome)
    if formato == 'xls':
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype='application/vnd.ms-excel',
            headers={'Content-Disposition': f'attachment; filename="{nome}.xls"'}
        )
    return _xlsx_response(wb, nome)


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORTAÇÃO — FINANCEIRO DAG (empenhos, fontes e notas)
# ══════════════════════════════════════════════════════════════════════════════

@relatorios_bp.route('/financeiro-dag/exportar/<formato>')
@login_required
def exportar_financeiro_dag(formato):
    """Exporta empenhos/fontes no formato da planilha FINANCEIRO - DAG."""
    if not current_user.pode('emitir_relatorios'):
        abort(403)
    itens = ContratoFinanceiro.query.order_by(ContratoFinanceiro.criado_em.desc()).all()
    cabecalho = _cabecalho_financeiro_dag()
    linhas = [cabecalho] + [_linha_financeiro_dag(i) for i in itens]
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    nome = f'FINANCEIRO_DAG_{ts}'

    if formato == 'csv':
        return _csv_response(linhas, nome)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Financeiro DAG'
    _estilizar_cabecalho(ws, cabecalho)
    for linha in linhas[1:]:
        ws.append(linha)
    _autofit(ws)
    ws.freeze_panes = 'A2'

    if formato == 'xls':
        return Response(
            _xlsx_response(wb, nome).get_data(),
            mimetype='application/vnd.ms-excel',
            headers={'Content-Disposition': f'attachment; filename="{nome}.xls"'}
        )
    return _xlsx_response(wb, nome)


# ══════════════════════════════════════════════════════════════════════════════
#  ANIVERSARIANTES DO MÊS
# ══════════════════════════════════════════════════════════════════════════════

_MESES = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro',
}


def _query_aniversariantes(mes, unidade_ids=None):
    """
    Profissionais que fazem aniversário no mês (ou em todos os meses se mes=None/0).
    Vinculados a ao menos uma unidade ativa. Exclui administradores.
    Cada pessoa aparece uma única vez.
    """
    q = (
        db.session.query(Usuario, Unidade)
        .join(UsuarioUnidade, UsuarioUnidade.usuario_id == Usuario.id)
        .join(Unidade, Unidade.id == UsuarioUnidade.unidade_id)
        .filter(
            Usuario.ativo == True,
            Usuario.perfil != 'administrador',
            Usuario.data_nasc != None,
            UsuarioUnidade.ativo == True,
        )
    )
    if mes:
        q = q.filter(db.extract('month', Usuario.data_nasc) == mes)
    if unidade_ids:
        q = q.filter(Unidade.id.in_(unidade_ids))
    q = q.order_by(
        db.extract('month', Usuario.data_nasc),
        db.extract('day', Usuario.data_nasc),
        Usuario.nome,
    )
    # Pré-carrega CBOs de matrículas ativas agrupados por usuario_id
    mats = (
        MatriculaProfissional.query
        .filter_by(ativo=True)
        .filter(MatriculaProfissional.cbo != None)
        .all()
    )
    cbos_por_usuario: dict = {}
    for m in mats:
        cbos_por_usuario.setdefault(m.usuario_id, [])
        label = m.cbo_label
        if label and label not in cbos_por_usuario[m.usuario_id]:
            cbos_por_usuario[m.usuario_id].append(label)

    visto: set = set()
    resultado = []
    for usuario, unidade in q.all():
        if usuario.id in visto:
            continue
        visto.add(usuario.id)
        resultado.append({
            'dia':      int(usuario.data_nasc.day),
            'mes':      int(usuario.data_nasc.month),
            'nome':     usuario.nome,
            'email':    usuario.email or '',
            'wa':       usuario.whatsapp or '',
            'unidade':  unidade.nome,
            'foto_url': usuario.foto_url,
            'inicial':  usuario.inicial,
            'cbos':     cbos_por_usuario.get(usuario.id, []),
        })
    return resultado


def _linhas_aniversariantes(mes, unidade_ids=None):
    cabecalho = ['Data', 'Nome', 'Unidade', 'CBO(s)', 'E-mail', 'WhatsApp']
    linhas = [cabecalho]
    for r in _query_aniversariantes(mes, unidade_ids):
        linhas.append([
            f"{r['dia']:02d}/{r['mes']:02d}",
            r['nome'],
            r['unidade'],
            ' | '.join(r['cbos']) if r['cbos'] else '',
            r['email'],
            r['wa'],
        ])
    return linhas


@relatorios_bp.route('/aniversariantes')
@login_required
def aniversariantes():
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    hoje = datetime.now()
    _mes_raw = request.args.get('mes', str(hoje.month))
    mes_sel = int(_mes_raw) if _mes_raw.isdigit() else hoje.month
    # mes_sel = 0 significa "todos os meses"

    unidade_ids = [int(x) for x in request.args.getlist('unidade') if x]

    if current_user.pode('ver_todas_unidades'):
        unidades_opcoes = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    else:
        ids_ativas = [uu.unidade_id for uu in current_user.unidades if uu.ativo]
        unidades_opcoes = Unidade.query.filter(Unidade.id.in_(ids_ativas)).order_by(Unidade.nome).all()

    _unidade_ids = unidade_ids if unidade_ids else None
    dados = _query_aniversariantes(mes_sel or None, _unidade_ids)

    return render_template(
        'relatorios/aniversariantes.html',
        dados=dados,
        mes_sel=mes_sel,
        meses=_MESES,
        unidades_opcoes=unidades_opcoes,
        unidade_ids=unidade_ids,
        hoje=hoje,
    )


@relatorios_bp.route('/aniversariantes/exportar/<formato>')
@login_required
def exportar_aniversariantes(formato):
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    _mes_raw = request.args.get('mes', str(datetime.now().month))
    mes_sel = int(_mes_raw) if _mes_raw.isdigit() else datetime.now().month
    unidade_ids = [int(x) for x in request.args.getlist('unidade') if x]
    _unidade_ids = unidade_ids if unidade_ids else None

    linhas = _linhas_aniversariantes(mes_sel or None, _unidade_ids)
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    nome_mes = _MESES[mes_sel].lower() if mes_sel else 'todos'
    nome = f'aniversariantes_{nome_mes}_{ts}'

    if formato == 'csv':
        return _csv_response(linhas, nome)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Aniversariantes'
    _estilizar_cabecalho(ws, linhas[0])
    for linha in linhas[1:]:
        ws.append(linha)
    _autofit(ws)
    ws.freeze_panes = 'A2'

    if formato == 'xls':
        return Response(
            _xlsx_response(wb, nome).get_data(),
            mimetype='application/vnd.ms-excel',
            headers={'Content-Disposition': f'attachment; filename="{nome}.xls"'}
        )
    return _xlsx_response(wb, nome)


# ── Relatório de Faltas Abonadas ───────────────────────────────────────────────
_NOMES_MESES = [
    '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

@relatorios_bp.route('/faltas-abonadas')
@login_required
def faltas_abonadas():
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    hoje   = date.today()
    ano    = request.args.get('ano',  hoje.year,  type=int)
    mes    = request.args.get('mes',  hoje.month, type=int)

    # Unidade sempre fixada à unidade principal do usuário logado
    unidade = current_user.unidade_principal

    q = (
        FaltaAbonada.query
        .filter_by(status='ativa')
        .filter(
            db.extract('year',  FaltaAbonada.data_falta) == ano,
            db.extract('month', FaltaAbonada.data_falta) == mes,
        )
    )
    if unidade:
        q = q.filter_by(unidade_id=unidade.id)

    faltas = q.order_by(FaltaAbonada.data_falta).all()

    # Monta grade do calendário começando no domingo (SUNDAY=6)
    cal_obj = calendar.Calendar(firstweekday=6)
    cal_mensal = cal_obj.monthdayscalendar(ano, mes)
    dias_map   = {}   # dia -> [falta, ...]
    for f in faltas:
        dias_map.setdefault(f.data_falta.day, []).append(f)

    grade = []
    for semana in cal_mensal:
        linha = []
        for dia in semana:
            linha.append((dia if dia else None, dias_map.get(dia, [])))
        grade.append(linha)

    # Anos disponíveis (com pelo menos 1 falta) + ano atual
    anos_rows = (
        db.session.query(db.extract('year', FaltaAbonada.data_falta).label('a'))
        .distinct()
        .order_by(db.desc('a'))
        .all()
    )
    anos = sorted({int(r.a) for r in anos_rows} | {hoje.year}, reverse=True)

    return render_template(
        'relatorios/faltas_abonadas.html',
        unidade=unidade,
        faltas=faltas,
        grade=grade,
        ano=ano,
        mes=mes,
        anos=anos,
        nomes_meses=_NOMES_MESES,
        total=len(faltas),
        dias_semana=['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'],
    )


def _query_faltas_abonadas_exportar():
    """Retorna (faltas, unidade, ano, mes, nome_arquivo) para exportação."""
    hoje    = date.today()
    ano     = request.args.get('ano', hoje.year,  type=int)
    mes     = request.args.get('mes', hoje.month, type=int)
    unidade = current_user.unidade_principal

    q = (
        FaltaAbonada.query
        .filter_by(status='ativa')
        .filter(
            db.extract('year',  FaltaAbonada.data_falta) == ano,
            db.extract('month', FaltaAbonada.data_falta) == mes,
        )
    )
    if unidade:
        q = q.filter_by(unidade_id=unidade.id)

    faltas = q.order_by(FaltaAbonada.data_falta).all()
    nome_unidade = unidade.nome if unidade else 'SES'
    nome_arquivo = f'Faltas Abonadas {_NOMES_MESES[mes]} {ano} — {nome_unidade}'
    return faltas, unidade, ano, mes, nome_arquivo


def _linhas_faltas_abonadas(faltas):
    """Monta lista de linhas (cabecalho + dados) para exportação."""
    from datetime import timezone, timedelta
    _UTC3 = timedelta(hours=-3)
    dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    cabecalho = ['Data da Falta', 'Dia da Semana', 'Matrícula', 'Nome Completo', 'Unidade', 'Função Declarada', 'Registrado em']
    linhas = [cabecalho]
    for f in faltas:
        mats = f.usuario.matriculas.filter_by(ativo=True).all()
        mat_num = '; '.join(m.numero for m in mats) if mats else '—'
        criado = (f.criado_em + _UTC3).strftime('%d/%m/%Y %H:%M') if f.criado_em else '—'
        linhas.append([
            f.data_falta.strftime('%d/%m/%Y'),
            dias_semana[f.data_falta.weekday()],
            mat_num,
            f.usuario.nome,
            f.unidade.nome if f.unidade else '—',
            f.funcao,
            criado,
        ])
    return linhas


@relatorios_bp.route('/faltas-abonadas/exportar/<formato>')
@login_required
def exportar_faltas_abonadas(formato):
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    faltas, unidade, ano, mes, nome = _query_faltas_abonadas_exportar()
    linhas = _linhas_faltas_abonadas(faltas)

    if formato == 'csv':
        return _csv_response(linhas, nome)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Faltas Abonadas'
    _estilizar_cabecalho(ws, linhas[0])
    for linha in linhas[1:]:
        ws.append(linha)
    _autofit(ws)
    ws.freeze_panes = 'A2'

    if formato == 'xls':
        return Response(
            _xlsx_response(wb, nome).get_data(),
            mimetype='application/vnd.ms-excel',
            headers={'Content-Disposition': f'attachment; filename="{nome}.xls"'}
        )
    return _xlsx_response(wb, nome)
