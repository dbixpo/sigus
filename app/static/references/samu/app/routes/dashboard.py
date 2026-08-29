from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required

from app import db
from app.models.aviso import Aviso
from app.models.feriado import Feriado, TIPOS_FOLGA, NATUREZAS
from app.models.ocorrencia import Ocorrencia
from app.models.tipo_ligacao import TipoLigacao
from app.models.origem_ligacao import OrigemLigacao
from app.models.algoritmo_acolhimento import AlgoritmoAcolhimento
from app.models.unidade_saude import UnidadeSaude
from app.utils import hoje_brasil_utc_range, br_fone, br_datetime_local

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    inicio, fim = hoje_brasil_utc_range()
    ligacoes_hoje = Ocorrencia.query.filter(
        Ocorrencia.iniciada_em >= inicio,
        Ocorrencia.iniciada_em < fim
    ).count()
    trotes_hoje = Ocorrencia.query.join(TipoLigacao).filter(
        Ocorrencia.iniciada_em >= inicio,
        Ocorrencia.iniciada_em < fim,
        TipoLigacao.eh_trote == True
    ).all()
    telefones_trotes = list({(o.telefone, br_fone(o.telefone)) for o in trotes_hoje if o.telefone})
    avisos = Aviso.query.filter_by(ativo=True).options(db.joinedload(Aviso.criado_por)).order_by(Aviso.ordem, Aviso.id).all()
    return render_template('dashboard/index.html',
        ligacoes_hoje=ligacoes_hoje,
        trotes_hoje=len(trotes_hoje),
        telefones_trotes=telefones_trotes,
        avisos=avisos,
    )


@dashboard_bp.route('/relatorios/total-ligacoes')
@login_required
def relatorio_total_ligacoes():
    """Relatório de total de ligações com filtros e período."""
    tipos = TipoLigacao.query.filter_by(ativo=True).order_by(TipoLigacao.nome).all()
    origens = OrigemLigacao.query.filter_by(ativo=True).order_by(OrigemLigacao.nome).all()
    algoritmos = AlgoritmoAcolhimento.query.filter_by(ativo=True).order_by(AlgoritmoAcolhimento.nome).all()

    hoje = date.today()
    data_inicio = request.args.get('data_inicio', hoje.strftime('%Y-%m-%d'))
    data_fim = request.args.get('data_fim', hoje.strftime('%Y-%m-%d'))
    filtro_numero = request.args.get('numero', '').strip()
    filtro_telefone = request.args.get('telefone', '').strip()
    filtro_solicitante = request.args.get('solicitante', '').strip()
    filtro_protocolo = request.args.get('protocolo', type=int)
    filtro_tipo = request.args.get('tipo_ligacao', type=int)
    filtro_origem = request.args.get('origem_ligacao', type=int)
    filtro_endereco = request.args.get('endereco', '').strip()

    try:
        di = datetime.strptime(data_inicio, '%Y-%m-%d')
        df = datetime.strptime(data_fim, '%Y-%m-%d')
        inicio_utc = datetime(di.year, di.month, di.day, 3, 0, 0)
        fim_utc = datetime(df.year, df.month, df.day, 23, 59, 59) + timedelta(hours=3) + timedelta(seconds=1)
    except (ValueError, TypeError):
        inicio_utc, fim_utc = hoje_brasil_utc_range()

    q = Ocorrencia.query.filter(
        Ocorrencia.iniciada_em >= inicio_utc,
        Ocorrencia.iniciada_em < fim_utc
    ).options(
        db.joinedload(Ocorrencia.tipo_ligacao),
        db.joinedload(Ocorrencia.origem_ligacao),
        db.joinedload(Ocorrencia.algoritmo),
        db.joinedload(Ocorrencia.unidade_saude),
    )
    if filtro_numero:
        q = q.filter(Ocorrencia.numero.ilike(f'%{filtro_numero}%'))
    if filtro_telefone:
        dig = ''.join(c for c in filtro_telefone if c.isdigit())
        if dig:
            q = q.filter(Ocorrencia.telefone.ilike(f'%{dig}%'))
    if filtro_solicitante:
        q = q.filter(Ocorrencia.nome_solicitante.ilike(f'%{filtro_solicitante}%'))
    if filtro_protocolo:
        q = q.filter(Ocorrencia.algoritmo_id == filtro_protocolo)
    if filtro_tipo:
        q = q.filter(Ocorrencia.tipo_ligacao_id == filtro_tipo)
    if filtro_origem:
        q = q.filter(Ocorrencia.origem_ligacao_id == filtro_origem)
    if filtro_endereco:
        termo = f'%{filtro_endereco}%'
        from sqlalchemy import or_
        q = q.outerjoin(UnidadeSaude, Ocorrencia.unidade_saude_id == UnidadeSaude.id)
        q = q.filter(
            or_(
                Ocorrencia.end_logradouro.ilike(termo),
                Ocorrencia.end_bairro.ilike(termo),
                Ocorrencia.end_cidade.ilike(termo),
                Ocorrencia.end_uf.ilike(termo),
                UnidadeSaude.nome.ilike(termo),
                UnidadeSaude.apelido.ilike(termo),
            )
        )

    itens = q.order_by(Ocorrencia.iniciada_em.desc()).all()
    total = len(itens)

    return render_template('dashboard/relatorio_total_ligacoes.html',
        itens=itens, total=total,
        tipos=tipos, origens=origens, algoritmos=algoritmos,
        data_inicio=data_inicio, data_fim=data_fim,
        filtro_numero=filtro_numero, filtro_telefone=filtro_telefone,
        filtro_solicitante=filtro_solicitante, filtro_protocolo=filtro_protocolo,
        filtro_tipo=filtro_tipo, filtro_origem=filtro_origem, filtro_endereco=filtro_endereco,
    )


@dashboard_bp.route('/api/feriado-hoje')
@login_required
def api_feriado_hoje():
    """Retorna o feriado do dia em JSON (para atualização sem refresh à meia-noite)."""
    data_str = request.args.get('data')
    if data_str:
        try:
            d = date.fromisoformat(data_str)
        except (ValueError, TypeError):
            d = date.today()
    else:
        d = date.today()
    f = Feriado.query.filter_by(data=d, ativo=True).first() if d else None
    if not f:
        return jsonify(feriado=None)
    is_comemorativa = f.tipo_folga == 'data_comemorativa' and f.cor_primaria
    logo_samu = 'colorido'
    logo_saude_digital = 'colorido'
    if is_comemorativa:
        if (f.cor_fonte_primaria or '').lower() in ('#000000', '#000', 'black'):
            logo_samu = 'colorido'
        else:
            logo_samu = 'branco'
        if (f.cor_secundaria or '').lower() in ('#000000', '#000', 'black'):
            logo_saude_digital = 'branco'
        else:
            logo_saude_digital = 'colorido'
    return jsonify(feriado={
        'id': f.id,
        'nome': f.nome,
        'tipo_folga': f.tipo_folga,
        'tipo_folga_label': TIPOS_FOLGA.get(f.tipo_folga, f.tipo_folga or '—'),
        'natureza_label': NATUREZAS.get(f.natureza, f.natureza or '—'),
        'emoji': f.emoji or '',
        'link_decreto': f.link_decreto or '',
        'cor_primaria': f.cor_primaria or '#c20d2f',
        'cor_secundaria': f.cor_secundaria or f.cor_primaria or '#c20d2f',
        'cor_fonte_primaria': f.cor_fonte_primaria or '#ffffff',
        'cor_fonte_secundaria': f.cor_fonte_secundaria or '#000000',
        'logo_samu': logo_samu,
        'logo_saude_digital': logo_saude_digital,
    }, is_comemorativa=is_comemorativa)
