import calendar
import csv
import io
import json
import os
import re
import time
import zipfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime, date

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from flask import Blueprint, render_template, request, abort, Response, url_for
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
            (str(e.data_aquisicao.year) if e.data_aquisicao else ''),
            str(e.valor_estimado) if e.valor_estimado else '',
        ])
    return linhas


def _linhas_chamados(chamados):
    cabecalho = [
        'Número', 'Unidade', 'Sala', 'Tipo', 'Título', 'Descrição',
        'Prioridade', 'Status', 'Aberto em', 'Fechado em'
    ]
    linhas = [cabecalho]
    for c in chamados:
        linhas.append([
            c.numero,
            c.unidade.nome if c.unidade else '',
            c.sala.nome if getattr(c, 'sala', None) else '',
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
        'Unidade', 'Sala', 'Tipo', 'Ramal', 'Máx. Pessoas',
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
            getattr(s, 'capacidade_maxima', 0),
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

    from app.models.chamado import TIPOS_CHAMADO_LABELS, PRIORIDADES_LABELS
    from app.models.status_chamado import StatusChamado
    status_labels_db = StatusChamado.como_dict_label()
    return render_template('relatorios/chamados.html',
                           chamados=chamados_lista,
                           unidades=unidades, tipos_unidade=tipos_unidade,
                           tipos_labels=TIPOS_CHAMADO_LABELS,
                           prioridades_labels=PRIORIDADES_LABELS,
                           status_labels=status_labels_db,
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
            'capacidade_maxima': getattr(s, 'capacidade_maxima', 0),
            'observacoes':     s.observacoes,
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


# ── RELATÓRIO: Mapa da Saúde ─────────────────────────────────────────────────

_SOROCABA_CENTER = (-23.5012, -47.4521)  # Aproximação (centro da cidade)
_SOROCABA_VIEWBOX = (-47.65, -23.65, -47.15, -23.25)  # left, bottom, right, top

# Cache simples em memória do contorno do município (GeoJSON)
_SOROCABA_BOUNDARY_CACHE = {
    'geojson': None,
    'cached_at': None,
}
_MAPA_GEOCODE_CACHE = {}
_GOOGLE_LINK_EXPAND_CACHE = {}
_MAPA_GEOCODE_CACHE_LOCK = Lock()
_MAPA_SAUDE_PAYLOAD_CACHE = {}
# Incrementar quando mudar formato do payload do mapa (invalida cache em memória).
_MAPA_SAUDE_CACHE_SCHEMA = 5

_MAPA_GEOCODE_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'instance',
    'mapa_saude_geocode_cache.json',
)


def _load_mapa_geocode_cache():
    try:
        if os.path.exists(_MAPA_GEOCODE_CACHE_PATH):
            with open(_MAPA_GEOCODE_CACHE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(k, str) and isinstance(v, (list, tuple)) and len(v) == 2:
                        try:
                            _MAPA_GEOCODE_CACHE[k] = (float(v[0]), float(v[1]))
                        except Exception:
                            continue
    except Exception:
        pass


def _persist_mapa_geocode_cache():
    try:
        base = os.path.dirname(_MAPA_GEOCODE_CACHE_PATH)
        os.makedirs(base, exist_ok=True)
        tmp = _MAPA_GEOCODE_CACHE_PATH + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(
                {k: [v[0], v[1]] if v else None for k, v in _MAPA_GEOCODE_CACHE.items()},
                f,
                ensure_ascii=False,
            )
        os.replace(tmp, _MAPA_GEOCODE_CACHE_PATH)
    except Exception:
        pass


_load_mapa_geocode_cache()


def invalidate_mapa_saude_payload_cache():
    """Zera o cache em memória do JSON do mapa. Use após alterar unidade/prédio usados no mapa."""
    _MAPA_SAUDE_PAYLOAD_CACHE.clear()


# Cache do GeoJSON de bairros (opcional; fornecido por arquivo local)
_SOROCABA_BAIRROS_CACHE = {
    'geojson': None,
    'cached_at': None,
}


def _carregar_geojson_bairros_sorocaba():
    """
    Carrega um GeoJSON de bairros de Sorocaba (se existir), a partir de:
      - instance/bairros_sorocaba.geojson
      - app/static/geo/bairros_sorocaba.geojson
    Retorna dict GeoJSON ou None.
    """
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'bairros_sorocaba.geojson'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'geo', 'bairros_sorocaba.geojson'),
    ]
    for path in candidates:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    geo = json.load(f)
                if isinstance(geo, dict) and geo.get('type') in ('FeatureCollection', 'Feature'):
                    return geo
        except Exception:
            continue
    return None


_OVERPASS_INTERPRETER_URLS = (
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
)


def _overpass_ways_to_geojson_feature_collection(elements):
    """Converte elementos `way` com geometry (out geom) em FeatureCollection."""
    features = []
    seen = set()
    for el in elements or []:
        if el.get('type') != 'way':
            continue
        wid = el.get('id')
        if wid in seen:
            continue
        seen.add(wid)
        geom = el.get('geometry')
        if not geom or len(geom) < 2:
            continue
        coords = []
        for pt in geom:
            lon = pt.get('lon')
            lat = pt.get('lat')
            if lon is None or lat is None:
                continue
            try:
                coords.append([float(lon), float(lat)])
            except (TypeError, ValueError):
                continue
        if len(coords) < 2:
            continue
        slim = [coords[0]]
        for c in coords[1:]:
            if abs(c[0] - slim[-1][0]) > 1e-9 or abs(c[1] - slim[-1][1]) > 1e-9:
                slim.append(c)
        coords = slim
        tags = el.get('tags') or {}
        name = (tags.get('name:pt') or tags.get('name') or '').strip()
        props = {}
        if name:
            props['name'] = name
        if len(coords) >= 3:
            if abs(coords[0][0] - coords[-1][0]) > 1e-9 or abs(coords[0][1] - coords[-1][1]) > 1e-9:
                ring = coords + [coords[0]]
            else:
                ring = coords
            features.append({
                'type': 'Feature',
                'properties': props,
                'geometry': {'type': 'Polygon', 'coordinates': [ring]},
            })
        else:
            features.append({
                'type': 'Feature',
                'properties': props,
                'geometry': {'type': 'LineString', 'coordinates': coords},
            })
    if not features:
        return None
    return {'type': 'FeatureCollection', 'features': features}


def _buscar_bairros_sorocaba_overpass_geojson():
    """
    Fallback quando não há bairros_sorocaba.geojson: limites no OSM (ways) via Overpass.
    Combina bairros (place) e, se existirem, divisões administrativas locais (admin_level 10).
    """
    query = """[out:json][timeout:90];
area[name="Sorocaba"]["admin_level"="8"]->.a;
(
  way(area.a)[place~"^(neighbourhood|suburb|quarter)$"];
  way(area.a)[boundary=administrative][admin_level=10];
);
out tags geom;
"""
    headers = {
        'User-Agent': 'SIGUS-MapaSaude/1.0 (overpass)',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
    }
    for endpoint in _OVERPASS_INTERPRETER_URLS:
        try:
            req = Request(endpoint, data=query.encode('utf-8'), headers=headers)
            with urlopen(req, timeout=100) as resp:
                payload = resp.read().decode('utf-8')
            data = json.loads(payload)
            fc = _overpass_ways_to_geojson_feature_collection(data.get('elements'))
            if fc and fc.get('features'):
                return fc
        except Exception:
            continue
    return None


def _obter_geojson_bairros_sorocaba():
    """Arquivo local (instance ou static/geo) ou fallback Overpass."""
    g = _carregar_geojson_bairros_sorocaba()
    if g:
        return g
    return _buscar_bairros_sorocaba_overpass_geojson()


def _obter_geojson_bairros_sorocaba_cached():
    """Mesmo GeoJSON que `/mapa-saude/bairros`: cache em memória ~24h."""
    now = datetime.utcnow()
    cached = _SOROCABA_BAIRROS_CACHE.get('geojson')
    cached_at = _SOROCABA_BAIRROS_CACHE.get('cached_at')
    if cached and cached_at and (now - cached_at).total_seconds() < 24 * 3600:
        return cached
    geo = _obter_geojson_bairros_sorocaba()
    if geo:
        _SOROCABA_BAIRROS_CACHE['geojson'] = geo
        _SOROCABA_BAIRROS_CACHE['cached_at'] = now
    return geo


# GeoJSON: app/static/references/Abrang 2021.kmz (abrangência interna; ajuste fino via env)
_ABRANG_KMZ_CACHE = {'geojson': None, 'cached_at': None, 'mtime': None, 'offset': None}
_ABRANG_KMZ_REL_PATH = os.path.join('static', 'references', 'Abrang 2021.kmz')


# Padrão: levemente oeste (esquerda na tela) e sul (baixo). Sobrescreva com env se precisar.
_ABRANG_KMZ_DEFAULT_DLNG = -0.000448
_ABRANG_KMZ_DEFAULT_DLAT = -0.000536


def _abrang_kmz_offset_deg():
    """
    Deslocamento em graus (WGS84) somado a todas as coordenadas do KMZ.
    Padrão: um pouco à esquerda e para baixo; env vazio usa o padrão.
    SIGUS_ABRANG_KMZ_OFFSET_LNG / SIGUS_ABRANG_KMZ_OFFSET_LAT (ex.: -0.00002 ou 0 para desligar).
    """
    def _parse(name, default):
        v = os.environ.get(name)
        if v is None or not str(v).strip():
            return default
        try:
            return float(str(v).strip())
        except (TypeError, ValueError):
            return default

    return (
        _parse('SIGUS_ABRANG_KMZ_OFFSET_LNG', _ABRANG_KMZ_DEFAULT_DLNG),
        _parse('SIGUS_ABRANG_KMZ_OFFSET_LAT', _ABRANG_KMZ_DEFAULT_DLAT),
    )


def _shift_position(pos, dlng, dlat):
    if not pos or len(pos) < 2:
        return pos
    return [float(pos[0]) + dlng, float(pos[1]) + dlat] + list(pos[2:])


def _shift_geometry(geom, dlng, dlat):
    if not geom or (abs(dlng) < 1e-15 and abs(dlat) < 1e-15):
        return geom
    t = geom.get('type')
    c = geom.get('coordinates')
    if t == 'Point':
        return {**geom, 'coordinates': _shift_position(c, dlng, dlat)}
    if t == 'LineString':
        return {**geom, 'coordinates': [_shift_position(p, dlng, dlat) for p in (c or [])]}
    if t == 'MultiLineString':
        return {
            **geom,
            'coordinates': [[_shift_position(p, dlng, dlat) for p in line] for line in (c or [])],
        }
    if t == 'Polygon':
        return {
            **geom,
            'coordinates': [[_shift_position(p, dlng, dlat) for p in ring] for ring in (c or [])],
        }
    if t == 'MultiPolygon':
        return {
            **geom,
            'coordinates': [
                [[_shift_position(p, dlng, dlat) for p in ring] for ring in poly]
                for poly in (c or [])
            ],
        }
    return geom


def _shift_feature_collection_coords(fc, dlng, dlat):
    if not fc or fc.get('type') != 'FeatureCollection':
        return fc
    if abs(dlng) < 1e-15 and abs(dlat) < 1e-15:
        return fc
    out = []
    for f in fc.get('features') or []:
        g = (f or {}).get('geometry')
        if g:
            out.append({**f, 'geometry': _shift_geometry(g, dlng, dlat)})
        else:
            out.append(f)
    return {**fc, 'features': out}


def _kml_localname(tag):
    if not tag:
        return ''
    if tag.startswith('{'):
        return tag.split('}', 1)[1]
    return tag


def _kml_coord_pairs(text):
    """KML coordinates: tokens lng,lat[,alt] separados por espaço ou newline (sem fechar anel)."""
    if not text or not str(text).strip():
        return []
    out = []
    for token in re.split(r'\s+', str(text).strip()):
        if not token:
            continue
        parts = [p.strip() for p in token.split(',')]
        if len(parts) < 2:
            continue
        try:
            lng = float(parts[0])
            lat = float(parts[1])
            out.append([lng, lat])
        except (ValueError, TypeError):
            continue
    return out


def _kml_ring_coords(text):
    """Anel de polígono: garante primeiro ponto = último (GeoJSON)."""
    out = _kml_coord_pairs(text)
    if len(out) < 3:
        return out
    a, b = out[0], out[-1]
    if abs(a[0] - b[0]) > 1e-7 or abs(a[1] - b[1]) > 1e-7:
        out = out + [out[0][:]]
    return out


def _kml_polygon_to_geojson(poly_el):
    outer = None
    holes = []
    for child in poly_el:
        ln = _kml_localname(child.tag)
        if ln == 'outerBoundaryIs':
            for sub in child.iter():
                if _kml_localname(sub.tag) == 'coordinates' and sub.text:
                    outer = _kml_ring_coords(sub.text)
                    break
        elif ln == 'innerBoundaryIs':
            for sub in child.iter():
                if _kml_localname(sub.tag) == 'coordinates' and sub.text:
                    holes.append(_kml_ring_coords(sub.text))
                    break
    if not outer or len(outer) < 4:
        return None
    rings = [outer]
    for h in holes:
        if len(h) >= 4:
            rings.append(h)
    return {'type': 'Polygon', 'coordinates': rings}


def _kml_multigeometry_to_geojson(mg_el):
    polys = []
    lines = []
    for child in mg_el:
        ln = _kml_localname(child.tag)
        if ln == 'Polygon':
            p = _kml_polygon_to_geojson(child)
            if p:
                polys.append(p['coordinates'])
        elif ln == 'LineString':
            for sub in child.iter():
                if _kml_localname(sub.tag) == 'coordinates' and sub.text:
                    c = _kml_coord_pairs(sub.text)
                    if len(c) >= 2:
                        lines.append(c)
                    break
    if polys:
        if len(polys) == 1:
            return {'type': 'Polygon', 'coordinates': polys[0]}
        return {'type': 'MultiPolygon', 'coordinates': polys}
    if lines:
        if len(lines) == 1:
            return {'type': 'LineString', 'coordinates': lines[0]}
        return {'type': 'MultiLineString', 'coordinates': lines}
    return None


def _kml_placemark_geometry(pm_el):
    for child in pm_el:
        ln = _kml_localname(child.tag)
        if ln == 'Polygon':
            return _kml_polygon_to_geojson(child)
        if ln == 'MultiGeometry':
            return _kml_multigeometry_to_geojson(child)
        if ln == 'LineString':
            for sub in child.iter():
                if _kml_localname(sub.tag) == 'coordinates' and sub.text:
                    c = _kml_coord_pairs(sub.text)
                    if len(c) >= 2:
                        return {'type': 'LineString', 'coordinates': c}
                    break
    return None


def _kml_root_to_feature_collection(root):
    features = []
    for pm in root.iter():
        if _kml_localname(pm.tag) != 'Placemark':
            continue
        name = ''
        for ch in pm:
            if _kml_localname(ch.tag) == 'name' and ch.text:
                name = (ch.text or '').strip()
                break
        geom = _kml_placemark_geometry(pm)
        if not geom:
            continue
        props = {}
        if name:
            props['name'] = name
        features.append({'type': 'Feature', 'properties': props, 'geometry': geom})
    if not features:
        return None
    return {'type': 'FeatureCollection', 'features': features}


def _ring_area_deg2(ring):
    """Área aproximada em grau² (fórmula do lacete); só para comparar polígonos no mesmo ficheiro."""
    if not ring or len(ring) < 3:
        return 0.0
    s = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = float(ring[i][0]), float(ring[i][1])
        x2, y2 = float(ring[i + 1][0]), float(ring[i + 1][1])
        s += x1 * y2 - x2 * y1
    return abs(s) * 0.5


def _geom_polygon_area_deg2(geom):
    """Soma das áreas dos anéis exteriores (Polygon / MultiPolygon)."""
    if not geom:
        return 0.0
    t = geom.get('type')
    if t == 'Polygon':
        coords = geom.get('coordinates') or []
        if not coords:
            return 0.0
        return _ring_area_deg2(coords[0])
    if t == 'MultiPolygon':
        total = 0.0
        for poly in geom.get('coordinates') or []:
            if poly and len(poly) > 0:
                total += _ring_area_deg2(poly[0])
        return total
    return 0.0


def _filtrar_abrang_kmz_sem_limite_externo(fc):
    """
    O KMZ costuma repetir o perímetro do município (menos alinhado ao mapa).
    Remove o polígono dominante por área; mantém LineString/MultiLineString e
    polígonos menores (divisões internas).
    """
    if not fc or fc.get('type') != 'FeatureCollection':
        return fc
    feats = fc.get('features') or []
    if len(feats) < 2:
        # Um único polígono: quase sempre só o contorno urbano; o contorno OSM cobre isso.
        if len(feats) == 1:
            g = (feats[0] or {}).get('geometry')
            if g and g.get('type') in ('Polygon', 'MultiPolygon'):
                return {'type': 'FeatureCollection', 'features': []}
        return fc

    indexed_areas = []
    for i, f in enumerate(feats):
        g = (f or {}).get('geometry')
        if not g:
            continue
        if g.get('type') in ('Polygon', 'MultiPolygon'):
            a = _geom_polygon_area_deg2(g)
            if a > 0:
                indexed_areas.append((i, a))

    if not indexed_areas:
        return fc

    indexed_areas.sort(key=lambda x: -x[1])
    max_idx, max_a = indexed_areas[0]
    total_a = sum(a for _, a in indexed_areas)
    second_a = indexed_areas[1][1] if len(indexed_areas) > 1 else 0.0

    remove_idx = None
    if max_a >= 0.60 * total_a:
        # O maior polígono cobre a maior parte da área total → típico limite municipal no KMZ.
        remove_idx = max_idx
    elif second_a > 0 and (max_a / second_a) >= 5.0:
        remove_idx = max_idx

    if remove_idx is None:
        return fc

    new_feats = [f for j, f in enumerate(feats) if j != remove_idx]
    return {'type': 'FeatureCollection', 'features': new_feats}


def _ler_kmz_abrangencia_geojson():
    """
    Lê app/static/references/Abrang 2021.kmz (primeiro .kml dentro do ZIP) e devolve FeatureCollection.
    """
    base = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, _ABRANG_KMZ_REL_PATH)
    if not os.path.isfile(path):
        return None
    try:
        mtime = os.path.getmtime(path)
        with zipfile.ZipFile(path, 'r') as zf:
            kml_names = sorted(
                n for n in zf.namelist()
                if n.lower().endswith('.kml') and not n.startswith('__')
            )
            if not kml_names:
                return None
            raw = zf.read(kml_names[0])
        root = ET.fromstring(raw)
        return _kml_root_to_feature_collection(root)
    except Exception:
        return None


def _obter_geojson_abrang_kmz():
    """Cache em memória; invalida se o KMZ ou o offset de ajuste mudarem."""
    now = time.time()
    base = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, _ABRANG_KMZ_REL_PATH)
    try:
        mtime = os.path.getmtime(path) if os.path.isfile(path) else None
    except OSError:
        mtime = None
    dlng, dlat = _abrang_kmz_offset_deg()
    cached = _ABRANG_KMZ_CACHE.get('geojson')
    cached_at = _ABRANG_KMZ_CACHE.get('cached_at')
    cached_mtime = _ABRANG_KMZ_CACHE.get('mtime')
    cached_offset = _ABRANG_KMZ_CACHE.get('offset')
    if (
        cached
        and cached_at
        and mtime is not None
        and cached_mtime == mtime
        and cached_offset == (dlng, dlat)
        and (now - cached_at) < 24 * 3600
    ):
        return cached
    geo = _ler_kmz_abrangencia_geojson()
    if geo:
        geo = _filtrar_abrang_kmz_sem_limite_externo(geo)
        geo = _shift_feature_collection_coords(geo, dlng, dlat)
    _ABRANG_KMZ_CACHE['geojson'] = geo
    _ABRANG_KMZ_CACHE['cached_at'] = now
    _ABRANG_KMZ_CACHE['mtime'] = mtime
    _ABRANG_KMZ_CACHE['offset'] = (dlng, dlat)
    return geo


def _extrair_coords_google_maps(url: str):
    """
    Tenta extrair lat/lng de URLs do Google Maps já resolvidas.
    Retorna (lat, lng) ou None.
    """
    if not url:
        return None

    s = str(url).strip()
    if not s:
        return None

    # Links curtos (maps.app.goo.gl) normalmente redirecionam para URL completa com @lat,lng.
    if 'maps.app.goo.gl' in s:
        expanded = _GOOGLE_LINK_EXPAND_CACHE.get(s)
        if expanded is None:
            try:
                req = Request(s, headers={'User-Agent': 'SIGUS-MapaSaude/1.0 (contato: sigus@localhost)'})
                resp = urlopen(req, timeout=8)
                expanded = resp.geturl() or s
            except Exception:
                expanded = s
            _GOOGLE_LINK_EXPAND_CACHE[s] = expanded
        s = expanded

    # Padrões comuns:
    # - @lat,lng
    # - !3dlat!4dlng
    # - q=lat,lng / center=lat,lng
    patterns = [
        r'@(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)',
        r'!3d(-?\d+(?:\.\d+)?)[^!]*!4d(-?\d+(?:\.\d+)?)',
        r'(?:q|center|ll)=(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)',
    ]

    for pat in patterns:
        m = re.search(pat, s)
        if m:
            try:
                lat = float(m.group(1))
                lng = float(m.group(2))
                return (lat, lng)
            except (ValueError, TypeError):
                return None

    return None


def _geocode_nominatim_ptbr(endereco: str, max_retries: int = 0, timeout_seconds: int = 8):
    """
    Geocodifica endereço via Nominatim (OpenStreetMap) retornando (lat, lng).
    """
    if not endereco:
        return None

    # Melhora a chance de dar certo usando um recorte aproximado de Sorocaba
    q = f'{endereco}, Sorocaba, SP'
    left, bottom, right, top = _SOROCABA_VIEWBOX
    # viewbox espera: left,top,right,bottom
    viewbox = f'{left},{top},{right},{bottom}'

    url = (
        'https://nominatim.openstreetmap.org/search?'
        'format=jsonv2&limit=1&addressdetails=0&accept-language=pt-BR&'
        f'q={quote_plus(q)}&viewbox={quote_plus(viewbox)}&bounded=1'
    )

    headers = {
        'User-Agent': 'SIGUS-MapaSaude/1.0 (contato: sigus@localhost)'
    }

    attempt = 0
    while attempt <= max_retries:
        attempt += 1
        try:
            req = Request(url, headers=headers)
            resp = urlopen(req, timeout=timeout_seconds)
            payload = resp.read().decode('utf-8')
            data = json.loads(payload)
            if not data:
                return None
            lat = float(data[0]['lat'])
            lng = float(data[0]['lon'])
            return (lat, lng)
        except HTTPError:
            # Em caso de rate limit, evita travar requisições longas.
            return None
        except URLError:
            return None
        except Exception:
            return None


def _buscar_contorno_sorocaba_geojson():
    """
    Busca o contorno do município via Nominatim (OSM) em formato GeoJSON.
    Retorna um GeoJSON (dict) ou None.
    """
    url = (
        'https://nominatim.openstreetmap.org/search?'
        'format=jsonv2&limit=1&polygon_geojson=1&addressdetails=0&accept-language=pt-BR&'
        f'q={quote_plus("Sorocaba, SP, Brasil")}'
    )
    headers = {'User-Agent': 'SIGUS-MapaSaude/1.0 (contato: sigus@localhost)'}
    try:
        req = Request(url, headers=headers)
        resp = urlopen(req, timeout=20)
        payload = resp.read().decode('utf-8')
        data = json.loads(payload)
        if not data:
            return None
        geo = data[0].get('geojson')
        if not geo:
            return None
        return geo
    except Exception:
        return None


def _mapa_row_tipo_fields(u):
    """Chave estável do tipo, sigla e nome para legenda SIGLA (NOME)."""
    if getattr(u, 'tipo_unidade', None) and u.tipo_unidade:
        tu = u.tipo_unidade
        sigla = (tu.sigla or '').strip() or '—'
        nome = (tu.nome or '').strip() or '—'
        tipo_key = str(tu.id)
    else:
        leg = (getattr(u, 'tipo', None) or '—') or '—'
        sigla = leg
        nome = leg
        tipo_key = f'legacy:{leg}'
    return tipo_key, sigla, nome


def _query_unidades_publicas():
    unidades = (
        Unidade.query
        .join(TipoUnidade, Unidade.tipo_unidade_id == TipoUnidade.id, isouter=True)
        .filter(Unidade.status == 'ativa')
        .order_by(
            db.func.coalesce(TipoUnidade.nome, Unidade.tipo).asc(),
            db.func.lower(Unidade.nome).asc()
        )
        .all()
    )

    rows = []
    for u in unidades:
        tipo_key, tipo_sigla, tipo_nome = _mapa_row_tipo_fields(u)

        partes_endereco = []
        if u.endereco:
            partes_endereco.append(u.endereco)
        if u.numero:
            partes_endereco.append(u.numero)
        if u.complemento:
            partes_endereco.append(u.complemento)
        if u.bairro:
            partes_endereco.append(u.bairro)
        if u.cep:
            partes_endereco.append(f'CEP {u.cep}')

        endereco_completo = ', '.join(partes_endereco) if partes_endereco else '—'
        if u.link_maps:
            endereco_link = u.link_maps
        elif partes_endereco:
            cidade = u.cidade or 'Sorocaba'
            endereco_query = '+'.join(partes_endereco + [cidade])
            endereco_link = f'https://www.google.com/maps/search/?api=1&query={endereco_query}'
        else:
            endereco_link = None

        rows.append({
            'id': u.id,
            'cnes': u.numero_cnes or '—',
            'nome': u.nome,
            'tipo': tipo_nome,
            'tipo_key': tipo_key,
            'tipo_sigla': tipo_sigla,
            'tipo_nome': tipo_nome,
            'endereco': endereco_completo,
            'endereco_link': endereco_link,
            'gestores_texto': '—',
            'telefone': u.telefone or '—',
            'email': u.email or '—',
        })
    return rows


def _build_mapa_saude_payload(rows, *, permitir_geocode: bool = True, max_geocodes: int = 60):
    total = len(rows)
    palette = [
        '#1A82B8', '#D97706', '#10B981', '#DC2626', '#7C3AED',
        '#F43F5E', '#0EA5E9', '#65A30D', '#F59E0B', '#4F46E5',
        '#2563EB', '#14B8A6', '#A21CAF', '#BE123C', '#64748B',
    ]

    def _row_tipo_key(r):
        tk = r.get('tipo_key')
        if tk is not None and str(tk).strip() != '':
            return str(tk)
        return r.get('tipo') or '—'

    nome_por_tk = {}
    for r in rows:
        tk = _row_tipo_key(r)
        if tk not in nome_por_tk:
            nome_por_tk[tk] = (r.get('tipo_nome') or r.get('tipo') or '—')

    tipos_presentes = sorted(
        nome_por_tk.keys(),
        key=lambda k: (nome_por_tk.get(k) or '').lower(),
    )
    tipo_cores = {t: palette[i % len(palette)] for i, t in enumerate(tipos_presentes)}

    def _cache_key(r):
        """Inclui predio_id para não reutilizar geocode/ponto de outro prédio com endereço parecido."""
        base = ((r.get('endereco_link') or '').strip().lower()
                or (r.get('endereco') or '').strip().lower()
                or str(r.get('id')))
        pid = r.get('predio_id')
        try:
            if pid is not None and str(pid).strip() != '':
                return f'p{int(pid)}|{base}'
        except (TypeError, ValueError):
            pass
        return base

    coords_cache_local = {}
    pendentes = {}
    for r in rows:
        key = _cache_key(r)
        # Se já vier coordenada do banco, usa direto (sem geocode).
        lat_in = r.get('latitude')
        lng_in = r.get('longitude')
        try:
            lat_in = float(lat_in) if lat_in is not None and str(lat_in).strip() != '' else None
            lng_in = float(lng_in) if lng_in is not None and str(lng_in).strip() != '' else None
        except Exception:
            lat_in = None
            lng_in = None
        if lat_in is not None and lng_in is not None:
            coords_cache_local[key] = (lat_in, lng_in)
            continue

        latlng = _extrair_coords_google_maps(r.get('endereco_link'))
        if latlng:
            coords_cache_local[key] = latlng
            continue
        if key in _MAPA_GEOCODE_CACHE:
            coords_cache_local[key] = _MAPA_GEOCODE_CACHE[key]
            continue
        endereco = (r.get('endereco') or '').strip()
        if endereco and endereco != '—':
            pendentes[key] = endereco

    geocodes_feitos = 0
    if permitir_geocode and pendentes:
        # Evita travar o carregamento do mapa: geocodifica um lote limitado por request.
        items = list(pendentes.items())[: max(0, int(max_geocodes or 0))]
        if items:
            workers = min(4, max(1, len(items)))
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(_geocode_nominatim_ptbr, endereco, 0, 4): key
                    for key, endereco in items
                }
                for future in as_completed(futures):
                    key = futures[future]
                    try:
                        latlng = future.result()
                    except Exception:
                        latlng = None
                    with _MAPA_GEOCODE_CACHE_LOCK:
                        _MAPA_GEOCODE_CACHE[key] = latlng
                    coords_cache_local[key] = latlng
                    geocodes_feitos += 1

            with _MAPA_GEOCODE_CACHE_LOCK:
                _persist_mapa_geocode_cache()

    markers = []
    nao_localizadas = 0
    for r in rows:
        key = _cache_key(r)
        latlng = coords_cache_local.get(key)
        if latlng is None:
            nao_localizadas += 1

        tk = _row_tipo_key(r)
        sigla = (r.get('tipo_sigla') or '—')
        nome = (r.get('tipo_nome') or r.get('tipo') or '—')
        tipo_display = f'{sigla} ({nome})'

        markers.append({
            'id': r.get('id'),
            'cnes': r.get('cnes'),
            'nome': r.get('nome'),
            'tipo': tipo_display,
            'tipo_key': tk,
            'tipo_sigla': sigla,
            'tipo_nome': nome,
            'endereco': r.get('endereco'),
            'endereco_link': r.get('endereco_link'),
            'gestores_texto': r.get('gestores_texto'),
            'telefone': r.get('telefone'),
            'email': r.get('email'),
            'lat': latlng[0] if latlng else None,
            'lng': latlng[1] if latlng else None,
            'cor': tipo_cores.get(tk, '#64748B'),
            'localizacao_approx': False,
            'predio_id': r.get('predio_id'),
            'predio_nome': r.get('predio_nome'),
            'predio_endereco': r.get('predio_endereco'),
            'predio_endereco_link': r.get('predio_endereco_link'),
        })

    return {
        'total': total,
        'tipos': tipos_presentes,
        'tipo_cores': tipo_cores,
        'markers': markers,
        'nao_localizadas': nao_localizadas,
        'geocodes_feitos': geocodes_feitos,
        'max_geocodes': int(max_geocodes or 0) if permitir_geocode else 0,
    }


@relatorios_bp.route('/mapa-saude')
@login_required
def mapa_saude():
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    filtro_tipo_unidades = _getlist('tipo_unidade')
    filtro_unidades = _getlist('unidade')

    # Opções para filtros
    if current_user.pode('ver_todas_unidades'):
        unidades_opcoes = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    else:
        ids_ativas = [uu.unidade_id for uu in current_user.unidades if uu.ativo]
        unidades_opcoes = Unidade.query.filter(Unidade.id.in_(ids_ativas)).order_by(Unidade.nome).all()

    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()

    return render_template(
        'relatorios/mapa_saude.html',
        unidades=unidades_opcoes,
        tipos_unidade=tipos_unidade,
        filtro_unidades=filtro_unidades,
        filtro_tipo_unidades=filtro_tipo_unidades,
        mapa_publico_url=url_for('mapa_da_saude'),
        url_mapa_abrang=url_for('relatorios.mapa_saude_abrang'),
    )


@relatorios_bp.route('/mapa-saude/dados')
@login_required
def mapa_saude_dados():
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    filtro_tipo_unidades = tuple(_getlist('tipo_unidade') or [])
    filtro_unidades = tuple(_getlist('unidade') or [])
    ids_permitidas = _ids_unidades_permitidas()
    key = (
        'privado',
        _MAPA_SAUDE_CACHE_SCHEMA,
        filtro_tipo_unidades,
        filtro_unidades,
        tuple(sorted(ids_permitidas)) if ids_permitidas is not None else None,
    )
    now = time.time()
    cached = _MAPA_SAUDE_PAYLOAD_CACHE.get(key)
    if cached and (now - cached.get('ts', 0)) < 600:
        payload = cached.get('payload')
    else:
        # Query leve (sem o bloco caro de gestores do relatório /unidades)
        rows = _query_unidades_mapa(publico=False)
        permitir_geocode = request.args.get('geocode') in ('1', 'true', 'True', 'sim', 'SIM')
        payload = _build_mapa_saude_payload(rows, permitir_geocode=permitir_geocode, max_geocodes=60)
        _MAPA_SAUDE_PAYLOAD_CACHE[key] = {'ts': now, 'payload': payload}
    return Response(json.dumps(payload), mimetype='application/json')


def _query_unidades_mapa(publico: bool = False):
    """Versão leve de unidades para o mapa (sem N+1 de gestores)."""
    filtro_tipo_unidades = _getlist('tipo_unidade')
    filtro_unidades = _getlist('unidade')

    # Join no prédio para permitir herança de coordenadas
    from app.models.predio import Predio
    q = Unidade.query.join(Predio, Unidade.predio_id == Predio.id, isouter=True)
    if not publico:
        ids_permitidas = _ids_unidades_permitidas()
        if ids_permitidas is not None:
            q = q.filter(Unidade.id.in_(ids_permitidas))

    if filtro_tipo_unidades:
        q = q.filter(Unidade.tipo_unidade_id.in_(filtro_tipo_unidades))
    if filtro_unidades:
        q = q.filter(Unidade.id.in_(filtro_unidades))

    q = q.join(TipoUnidade, Unidade.tipo_unidade_id == TipoUnidade.id, isouter=True)
    if publico:
        q = q.filter(Unidade.status == 'ativa')

    unidades = q.order_by(
        db.func.coalesce(TipoUnidade.nome, Unidade.tipo).asc(),
        db.func.lower(Unidade.nome).asc(),
    ).all()

    rows = []
    for u in unidades:
        tipo_key, tipo_sigla, tipo_nome = _mapa_row_tipo_fields(u)

        partes_endereco = []
        if u.endereco:
            partes_endereco.append(u.endereco)
        if u.numero:
            partes_endereco.append(u.numero)
        if u.complemento:
            partes_endereco.append(u.complemento)
        if u.bairro:
            partes_endereco.append(u.bairro)
        if u.cep:
            partes_endereco.append(f'CEP {u.cep}')

        endereco_completo = ', '.join(partes_endereco) if partes_endereco else '—'
        if u.link_maps:
            endereco_link = u.link_maps
        elif partes_endereco:
            cidade = u.cidade or 'Sorocaba'
            endereco_query = '+'.join(partes_endereco + [cidade])
            endereco_link = f'https://www.google.com/maps/search/?api=1&query={endereco_query}'
        else:
            endereco_link = None

        predio_id = u.predio_id
        predio_nome = u.predio.nome if u.predio else None
        predio_endereco = None
        predio_endereco_link = None
        if u.predio:
            partes_p = []
            if u.predio.endereco:
                partes_p.append(u.predio.endereco)
            if u.predio.numero:
                partes_p.append(u.predio.numero)
            if u.predio.complemento:
                partes_p.append(u.predio.complemento)
            if u.predio.bairro:
                partes_p.append(u.predio.bairro)
            if u.predio.cep:
                partes_p.append(f'CEP {u.predio.cep}')
            predio_endereco = ', '.join(partes_p) if partes_p else None
            lm = (u.predio.link_maps or '').strip()
            predio_endereco_link = lm if lm else None
        if not predio_endereco:
            predio_endereco = endereco_completo
        if not predio_endereco_link:
            predio_endereco_link = endereco_link

        rows.append({
            'id': u.id,
            'cnes': u.numero_cnes or '—',
            'nome': u.nome,
            'tipo': tipo_nome,
            'tipo_key': tipo_key,
            'tipo_sigla': tipo_sigla,
            'tipo_nome': tipo_nome,
            'endereco': endereco_completo,
            'endereco_link': endereco_link,
            'gestores_texto': '—',
            'telefone': u.telefone or '—',
            'email': u.email or '—',
            'latitude': (u.latitude if u.latitude is not None else (u.predio.latitude if u.predio and u.predio.latitude is not None else None)),
            'longitude': (u.longitude if u.longitude is not None else (u.predio.longitude if u.predio and u.predio.longitude is not None else None)),
            'predio_id': predio_id,
            'predio_nome': predio_nome,
            'predio_endereco': predio_endereco,
            'predio_endereco_link': predio_endereco_link,
        })
    return rows


def mapa_saude_publico():
    """Mapa público (sem login). Rotas registradas em app: /mapa-da-saude."""
    return render_template(
        'relatorios/mapa_saude_publico.html',
        url_mapa_dados=url_for('mapa_da_saude_dados'),
        url_mapa_abrang=url_for('mapa_da_saude_abrang'),
        favicon_href=url_for('static', filename='img/favicon.png'),
    )


def mapa_saude_publico_dados():
    # Público: cache curto também ajuda bastante.
    key = ('publico', _MAPA_SAUDE_CACHE_SCHEMA)
    now = time.time()
    cached = _MAPA_SAUDE_PAYLOAD_CACHE.get(key)
    if cached and (now - cached.get('ts', 0)) < 900:
        payload = cached.get('payload')
    else:
        rows = _query_unidades_mapa(publico=True)
        permitir_geocode = request.args.get('geocode') in ('1', 'true', 'True', 'sim', 'SIM')
        payload = _build_mapa_saude_payload(rows, permitir_geocode=permitir_geocode, max_geocodes=60)
        _MAPA_SAUDE_PAYLOAD_CACHE[key] = {'ts': now, 'payload': payload}
    return Response(json.dumps(payload), mimetype='application/json')


@relatorios_bp.route('/mapa-saude/contorno')
@login_required
def mapa_saude_contorno():
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    # Cache em memória por 24h (suficiente p/ reduzir chamadas externas)
    now = datetime.utcnow()
    cached = _SOROCABA_BOUNDARY_CACHE.get('geojson')
    cached_at = _SOROCABA_BOUNDARY_CACHE.get('cached_at')
    if cached and cached_at and (now - cached_at).total_seconds() < 24 * 3600:
        geo = cached
    else:
        geo = _buscar_contorno_sorocaba_geojson()
        if geo:
            _SOROCABA_BOUNDARY_CACHE['geojson'] = geo
            _SOROCABA_BOUNDARY_CACHE['cached_at'] = now

    return Response(
        json.dumps({'ok': bool(geo), 'geojson': geo}),
        mimetype='application/json'
    )


def mapa_saude_publico_contorno():
    now = datetime.utcnow()
    cached = _SOROCABA_BOUNDARY_CACHE.get('geojson')
    cached_at = _SOROCABA_BOUNDARY_CACHE.get('cached_at')
    if cached and cached_at and (now - cached_at).total_seconds() < 24 * 3600:
        geo = cached
    else:
        geo = _buscar_contorno_sorocaba_geojson()
        if geo:
            _SOROCABA_BOUNDARY_CACHE['geojson'] = geo
            _SOROCABA_BOUNDARY_CACHE['cached_at'] = now

    return Response(
        json.dumps({'ok': bool(geo), 'geojson': geo}),
        mimetype='application/json'
    )


@relatorios_bp.route('/mapa-saude/abrang')
@login_required
def mapa_saude_abrang():
    if not current_user.pode('emitir_relatorios'):
        abort(403)
    geo = _obter_geojson_abrang_kmz()
    return Response(
        json.dumps({'ok': bool(geo), 'geojson': geo}),
        mimetype='application/json'
    )


def mapa_saude_publico_abrang():
    geo = _obter_geojson_abrang_kmz()
    return Response(
        json.dumps({'ok': bool(geo), 'geojson': geo}),
        mimetype='application/json'
    )


@relatorios_bp.route('/mapa-saude/bairros')
@login_required
def mapa_saude_bairros():
    if not current_user.pode('emitir_relatorios'):
        abort(403)

    geo = _obter_geojson_bairros_sorocaba_cached()

    return Response(
        json.dumps({'ok': bool(geo), 'geojson': geo}),
        mimetype='application/json'
    )


def mapa_saude_publico_bairros():
    geo = _obter_geojson_bairros_sorocaba_cached()

    return Response(
        json.dumps({'ok': bool(geo), 'geojson': geo}),
        mimetype='application/json'
    )


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
    """Retorna 1 linha por matrícula ativa. Se o profissional tem duas matrículas, aparecem duas linhas."""
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

    # Uma linha por matrícula ativa
    linhas_flat = []
    for uid, uvinculos in por_usuario.items():
        u = uvinculos[0].usuario
        if u.perfil == 'administrador':
            continue
        if apenas_ativos == '1' and not u.ativo:
            continue
        if perfil_list and u.perfil not in perfil_list:
            continue

        # Busca todas as matrículas ativas deste profissional
        matriculas_ativas = MatriculaProfissional.query.filter_by(
            usuario_id=uid,
            ativo=True
        ).order_by(MatriculaProfissional.numero).all()

        # Se não tiver matrícula ativa, pula
        if not matriculas_ativas:
            continue

        # Para cada matrícula ativa, cria uma linha
        for mat in matriculas_ativas:
            # Busca o vínculo correspondente (pode ser o primeiro vínculo se não houver matrícula específica)
            v = None
            for vv in uvinculos:
                if vv.matricula_id == mat.id:
                    v = vv
                    break
            # Se não encontrou vínculo específico, usa o primeiro vínculo
            if not v:
                v = uvinculos[0]

            un = v.unidade
            ficha = _ultima_ficha_ativa(u.id, v.unidade_id)

            # CBO: prioriza da ficha, depois da matrícula
            cbo_label = (ficha.cbo_label if ficha and ficha.cbo else None) \
                        or (mat.cbo_label if mat and mat.cbo else None) \
                        or '—'

            # Número de conselho formatado: "{nome conselho} {numero conselho}"
            conselho_formatado = '—'
            if mat.reg_conselho:
                if mat.orgao_emissor:
                    conselho_formatado = f'{mat.orgao_emissor} {mat.reg_conselho}'
                else:
                    conselho_formatado = mat.reg_conselho

            # CPF formatado
            cpf_formatado = '—'
            if u.cpf:
                cpf_digits = ''.join(c for c in u.cpf if c.isdigit())
                if len(cpf_digits) == 11:
                    cpf_formatado = f'{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:]}'
                else:
                    cpf_formatado = u.cpf

            linhas_flat.append({
                'matricula':     mat.numero or 'Sem Matrícula',
                'nome':          u.nome,
                'foto_url':      u.foto_url if hasattr(u, 'foto_url') else None,
                'inicial':       u.inicial if hasattr(u, 'inicial') else (u.nome[0].upper() if u.nome else '?'),
                'cpf':           cpf_formatado,
                'whatsapp':      u.whatsapp or '—',
                'email':         u.email or '—',
                'cnes':          un.numero_cnes or '—' if un else '—',
                'unidade':       un.nome if un else '—',
                'cbo':           cbo_label,
                'conselho':      conselho_formatado,
                'ativo':         u.ativo,
                'id':            u.id,
            })

    linhas_flat.sort(key=lambda r: (r['unidade'], r['nome'], r['matricula']))
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
        'Matrícula', 'Profissional', 'CPF', 'Telefone',
        'E-mail', 'CNES', 'Unidade de Saúde', 'CBO', 'Nº do Conselho',
    ]
    linhas = [cabecalho]
    for r in rows:
        linhas.append([
            r['matricula'], r['nome'], r['cpf'],
            _fmt_fone(r['whatsapp']), r['email'],
            r['cnes'], r['unidade'], r['cbo'], r['conselho'],
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

    # Filtro de unidades: mostra apenas unidades que tenham ao menos 1 profissional vinculado (vínculo ativo),
    # limitado às unidades às quais o usuário está vinculado (independente do perfil).
    ids_permitidas = [uu.unidade_id for uu in current_user.unidades.filter_by(ativo=True).all()]

    q_un = (
        db.session.query(Unidade)
        .join(UsuarioUnidade, UsuarioUnidade.unidade_id == Unidade.id)
        .filter(
            Unidade.status == 'ativa',
            UsuarioUnidade.ativo == True,
        )
        .distinct()
    )
    if ids_permitidas:
        q_un = q_un.filter(Unidade.id.in_(ids_permitidas))
    unidades_opcoes = q_un.order_by(Unidade.nome).all()

    # Se nenhuma unidade específica foi selecionada, usa as unidades vinculadas do usuário
    if unidade_ids:
        _unidade_ids = unidade_ids
    else:
        _unidade_ids = ids_permitidas if ids_permitidas else None
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
    
    # Sempre limita às unidades vinculadas do usuário (independente do perfil)
    ids_permitidas = [uu.unidade_id for uu in current_user.unidades.filter_by(ativo=True).all()]
    
    # Se nenhuma unidade específica foi selecionada, usa as unidades vinculadas do usuário
    if unidade_ids:
        _unidade_ids = unidade_ids
    else:
        _unidade_ids = ids_permitidas if ids_permitidas else None

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


# ══════════════════════════════════════════════════════════════════════════════
#  RELATÓRIO DE UNIDADES
# ══════════════════════════════════════════════════════════════════════════════

def _query_unidades():
    """Query base para relatório de unidades."""
    filtro_tipo_unidades = _getlist('tipo_unidade')
    filtro_unidades = _getlist('unidade')
    
    q = Unidade.query
    
    # Restrição de visibilidade
    ids_permitidas = _ids_unidades_permitidas()
    if ids_permitidas is not None:
        q = q.filter(Unidade.id.in_(ids_permitidas))
    
    # Filtros de seleção múltipla
    if filtro_tipo_unidades:
        q = q.filter(Unidade.tipo_unidade_id.in_(filtro_tipo_unidades))
    if filtro_unidades:
        q = q.filter(Unidade.id.in_(filtro_unidades))
    
    # Filtros de texto (aplicados no template via JavaScript)
    # Ordena primeiro por tipo de unidade (sigla), depois por nome da unidade (case-insensitive)
    unidades = q.join(TipoUnidade, Unidade.tipo_unidade_id == TipoUnidade.id, isouter=True).order_by(
        db.func.coalesce(TipoUnidade.sigla, Unidade.tipo).asc(),
        db.func.lower(Unidade.nome).asc()
    ).all()
    
    # Monta dados para exibição
    rows = []
    for u in unidades:
        # CNES
        cnes = u.numero_cnes or '—'
        
        # Tipo (sigla)
        tipo_sigla = u.tipo_unidade.sigla if u.tipo_unidade else (u.tipo or '—')
        
        # Endereço completo
        partes_endereco = []
        if u.endereco:
            partes_endereco.append(u.endereco)
        if u.numero:
            partes_endereco.append(u.numero)
        if u.complemento:
            partes_endereco.append(u.complemento)
        if u.bairro:
            partes_endereco.append(u.bairro)
        if u.cep:
            partes_endereco.append(f'CEP {u.cep}')
        
        endereco_completo = ', '.join(partes_endereco) if partes_endereco else '—'
        
        # Link do Google Maps
        if u.link_maps:
            endereco_link = u.link_maps
        elif partes_endereco:
            # Monta link do Google Maps se não tiver link_maps
            endereco_query = '+'.join(partes_endereco + ([u.cidade or 'Sorocaba'] if u.cidade else ['Sorocaba']))
            endereco_link = f'https://www.google.com/maps/search/?api=1&query={endereco_query}'
        else:
            endereco_link = None
        
        # Gestores principais para contato:
        # - Usa campo `papel` de UsuarioUnidade ('gestor_principal' / 'gestor_secundario')
        # - Se não houver marcados, usa no máximo 2 gestores detectados por perfil/CBO
        gestores = []
        gestores_ids = set()  # Para evitar duplicatas

        # Busca última ficha CNES de cada profissional para verificar CBO
        ultima_ficha_por_usuario = {}
        fichas = (FichaCnesVinculo.query
                  .filter_by(unidade_id=u.id)
                  .order_by(FichaCnesVinculo.gerado_em.desc())
                  .all())
        for f in fichas:
            if f.usuario_id not in ultima_ficha_por_usuario:
                ultima_ficha_por_usuario[f.usuario_id] = f

        vinculos_ativos = [v for v in u.usuarios.filter_by(ativo=True).all() if v.usuario]

        # Primeiro tenta pegar explicitamente os marcados como principais
        principais = [v for v in vinculos_ativos if v.papel in ('gestor_principal', 'gestor_secundario')]
        # Ordena: principal antes do adicional
        principais = sorted(
            principais,
            key=lambda vv: 0 if vv.papel == 'gestor_principal' else 1
        )[:2]

        candidatos = principais if principais else vinculos_ativos

        for v in candidatos:
            if not v.usuario:
                continue

            # Verifica se é gestor por perfil
            is_gestor_perfil = v.usuario.perfil in ('coordenador', 'administrador')

            # Verifica se é gestor por CBO 131210
            is_gestor_cbo = False
            ficha = ultima_ficha_por_usuario.get(v.usuario_id)
            if ficha and ficha.cbo == '131210':
                is_gestor_cbo = True

            if not (is_gestor_perfil or is_gestor_cbo):
                continue

            # Evita duplicatas e limita a no máximo 2
            if v.usuario_id in gestores_ids or len(gestores_ids) >= 2:
                continue
            gestores_ids.add(v.usuario_id)

            nome_gestor = v.usuario.nome.split()[0] if v.usuario.nome else '—'
            telefone_gestor = v.usuario.whatsapp or v.usuario.telefone
            foto_gestor = v.usuario.foto_url if hasattr(v.usuario, 'foto_url') else None
            inicial_gestor = v.usuario.inicial if hasattr(v.usuario, 'inicial') else (nome_gestor[0].upper() if nome_gestor else '?')
            if telefone_gestor:
                telefone_formatado = telefone_gestor.replace('(', '').replace(')', '').replace(' ', '').replace('-', '')
                whatsapp_link = f'https://wa.me/55{telefone_formatado}'
            else:
                whatsapp_link = None
            gestores.append({
                'nome': nome_gestor,
                'telefone': telefone_gestor,
                'whatsapp_link': whatsapp_link,
                'foto_url': foto_gestor,
                'inicial': inicial_gestor
            })
        
        gestores_texto = '—'
        if gestores:
            gestores_parts = []
            for g in gestores:
                if g['whatsapp_link']:
                    gestores_parts.append(f"{g['nome']} — {g['telefone']}")
                else:
                    gestores_parts.append(g['nome'])
            gestores_texto = ' | '.join(gestores_parts)
        
        # Telefone da unidade
        telefone_unidade = u.telefone or '—'
        
        # Email da unidade
        email_unidade = u.email or '—'
        
        rows.append({
            'id': u.id,
            'cnes': cnes,
            'nome': u.nome,
            'tipo': tipo_sigla,
            'endereco': endereco_completo,
            'endereco_link': endereco_link,
            'gestores': gestores,
            'gestores_texto': gestores_texto,
            'telefone': telefone_unidade,
            'email': email_unidade,
        })
    
    return rows


def _linhas_unidades(rows):
    """Monta lista de linhas (cabeçalho + dados) para exportação.

    Observação: mantemos nas primeiras colunas os textos “limpos” e
    acrescentamos, AO FINAL, colunas extras apenas com os hyperlinks.
    """
    cabecalho = [
        'CNES',
        'Nome da Unidade',
        'Tipo',
        'Endereço',
        'Contato Gestor(a)',
        'Telefone',
        'E-mail',
        'Link CNES',
        'Link Google Maps',
        'WhatsApp Gestor 1',
        'WhatsApp Gestor 2',
        'Link E-mail Unidade',
    ]
    linhas = [cabecalho]
    for r in rows:
        gestores_str = ' | '.join(
            [f"{g['nome']} — {g['telefone']}" if g['telefone'] else g['nome'] for g in r['gestores']]
        ) if r['gestores'] else '—'

        # Monta links
        cnes_link = ''
        if r['cnes'] and r['cnes'] != '—':
            cnes_link = (
                f'https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp?search={r["cnes"]}'
            )

        maps_link = r.get('endereco_link') or ''

        whats1 = ''
        whats2 = ''
        if r['gestores']:
            if len(r['gestores']) >= 1 and r['gestores'][0].get('whatsapp_link'):
                whats1 = r['gestores'][0]['whatsapp_link']
            if len(r['gestores']) >= 2 and r['gestores'][1].get('whatsapp_link'):
                whats2 = r['gestores'][1]['whatsapp_link']

        email_link = f"mailto:{r['email']}" if r['email'] and r['email'] != '—' else ''

        linhas.append([
            r['cnes'],
            r['nome'],
            r['tipo'],
            r['endereco'],
            gestores_str,
            r['telefone'],
            r['email'],
            cnes_link,
            maps_link,
            whats1,
            whats2,
            email_link,
        ])
    return linhas


@relatorios_bp.route('/unidades')
@login_required
def unidades():
    if not current_user.pode('emitir_relatorios'):
        abort(403)
    
    filtro_tipo_unidades = _getlist('tipo_unidade')
    filtro_unidades = _getlist('unidade')
    
    rows = _query_unidades()
    
    # Opções para filtros
    if current_user.pode('ver_todas_unidades'):
        unidades_opcoes = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()
    else:
        ids_ativas = [uu.unidade_id for uu in current_user.unidades if uu.ativo]
        unidades_opcoes = Unidade.query.filter(Unidade.id.in_(ids_ativas)).order_by(Unidade.nome).all()
    
    tipos_unidade = TipoUnidade.query.filter_by(ativo=True).order_by(TipoUnidade.nome).all()
    
    return render_template('relatorios/unidades.html',
                           rows=rows,
                           unidades=unidades_opcoes,
                           tipos_unidade=tipos_unidade,
                           total=len(rows),
                           filtro_unidades=filtro_unidades,
                           filtro_tipo_unidades=filtro_tipo_unidades)


@relatorios_bp.route('/unidades/exportar/<formato>')
@login_required
def exportar_unidades(formato):
    if not current_user.pode('emitir_relatorios'):
        abort(403)
    
    rows = _query_unidades()
    linhas = _linhas_unidades(rows)
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    nome = f'unidades_{ts}'
    
    if formato == 'csv':
        return _csv_response(linhas, nome)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Unidades'
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