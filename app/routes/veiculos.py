# -*- coding: utf-8 -*-
"""Veículos da unidade: cadastro próprio (fora dos equipamentos), usos do mês e RDV."""
from datetime import date, datetime, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models.agenda import AgendaEvento
from app.models.unidade import Unidade
from app.models.veiculo import (CATEGORIAS_VEICULO, COMBUSTIVEIS_VEICULO, PREFIXO_MAX_DIGITOS, ModeloVeiculo,
                                Veiculo, normalizar_placa, normalizar_prefixo)
from app.services import reservas
from app.utils import agora_brasilia, agora_local

veiculos_bp = Blueprint('veiculos', __name__, url_prefix='/veiculos')

MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho',
         'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']


def _acesso_unidade(unidade_id):
    if current_user.pode('ver_todas_unidades'):
        return True
    return unidade_id in {uu.unidade_id for uu in current_user.unidades.filter_by(ativo=True).all()}


def _veiculo_ou_404(id):
    veiculo = Veiculo.query.get_or_404(id)
    if not _acesso_unidade(veiculo.unidade_id):
        doc = reservas.emprestimo_ativo(veiculo.id)
        if not doc or not _acesso_unidade(doc.unidade_destino_id):
            abort(403)
    return veiculo


def _veiculo_dono_ou_403(id):
    veiculo = Veiculo.query.get_or_404(id)
    if not _acesso_unidade(veiculo.unidade_id):
        abort(403)
    return veiculo


def _mes_param():
    texto = request.values.get('mes') or ''
    try:
        ano, mes = (int(p) for p in texto.split('-')[:2])
        return date(ano, mes, 1)
    except (TypeError, ValueError):
        hoje = agora_brasilia().date()
        return date(hoje.year, hoje.month, 1)


def _proximo_mes(d):
    return date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def _usos_do_mes(veiculo, mes):
    ini = datetime.combine(mes, datetime.min.time())
    fim = datetime.combine(_proximo_mes(mes), datetime.min.time())
    return (AgendaEvento.query
            .filter(AgendaEvento.veiculo_id == veiculo.id, AgendaEvento.inicio >= ini, AgendaEvento.inicio < fim)
            .order_by(AgendaEvento.inicio)
            .all())


def _finalidade(ev, rotulo):
    titulo = ev.titulo or ''
    return '' if titulo.startswith(rotulo) else titulo


def _inteiro(texto):
    digitos = ''.join(ch for ch in (texto or '') if ch.isdigit())
    return int(digitos) if digitos else None


def _data(texto):
    try:
        return datetime.strptime((texto or '').strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def _duplicado(veiculo, placa, prefixo, alugado):
    """Placa e prefixo não se repetem entre veículos ativos (383 e AL-383 são carros diferentes)."""
    outros = Veiculo.query.filter(Veiculo.ativo.is_(True), Veiculo.id != (veiculo.id or 0))
    mesmo = outros.filter(Veiculo.placa == placa).first()
    if mesmo:
        return f'Já existe um veículo ativo com a placa {mesmo.placa_exibicao} ({mesmo.unidade.nome}).'
    mesmo = outros.filter(Veiculo.prefixo == prefixo, Veiculo.alugado.is_(alugado)).first()
    if mesmo:
        return f'O prefixo {mesmo.prefixo_exibicao} já é do veículo {mesmo.placa_exibicao} ({mesmo.unidade.nome}).'
    return None


def _preencher(veiculo, form):
    """Copia o formulário para o veículo. Devolve a mensagem de erro, se houver."""
    prefixo, digitou_al = normalizar_prefixo(form.get('prefixo'))
    placa = normalizar_placa(form.get('placa'))
    if not prefixo:
        return 'Informe o prefixo do veículo.'
    if not prefixo.isdigit() or len(prefixo) > PREFIXO_MAX_DIGITOS:
        return f'O prefixo tem só números, até {PREFIXO_MAX_DIGITOS} dígitos (ex.: 383 ou 1024). Alugado é o check abaixo.'
    if len(placa) != 7:
        return 'Informe a placa com 7 caracteres (ex.: ABC1D23 ou ABC1234).'
    categoria = form.get('categoria') or ''
    if categoria not in CATEGORIAS_VEICULO:
        return 'Escolha a categoria do veículo.'
    alugado = digitou_al or form.get('alugado') == 'on'
    erro = _duplicado(veiculo, placa, prefixo, alugado)
    if erro:
        return erro

    combustivel = form.get('combustivel') or ''
    veiculo.prefixo = prefixo
    veiculo.alugado = alugado
    veiculo.locadora = ((form.get('locadora') or '').strip()[:150] or None) if alugado else None
    veiculo.placa = placa
    veiculo.marca = (form.get('marca') or '').strip()[:60] or None
    veiculo.modelo = (form.get('modelo') or '').strip()[:80] or None
    veiculo.categoria = categoria
    veiculo.ano = (form.get('ano') or '').strip()[:9] or None
    veiculo.cor = (form.get('cor') or '').strip()[:30] or None
    veiculo.combustivel = combustivel if combustivel in COMBUSTIVEIS_VEICULO else None
    veiculo.lotacao = _inteiro(form.get('lotacao'))
    veiculo.renavam = ''.join(ch for ch in (form.get('renavam') or '') if ch.isdigit())[:20] or None
    veiculo.chassi = normalizar_placa(form.get('chassi'))[:30] or None
    veiculo.km_cadastro = _inteiro(form.get('km_cadastro'))
    veiculo.licenciamento_vencimento = _data(form.get('licenciamento_vencimento'))
    veiculo.observacoes = (form.get('observacoes') or '').strip() or None
    return None


def _render_form(unidade, veiculo):
    modelos = ModeloVeiculo.query.order_by(ModeloVeiculo.marca, ModeloVeiculo.nome).all()
    return render_template(
        'veiculos/form.html', unidade=unidade, veiculo=veiculo, editando=veiculo.id is not None,
        dados_form=request.form if request.method == 'POST' else None,
        categorias=CATEGORIAS_VEICULO, combustiveis=COMBUSTIVEIS_VEICULO,
        marcas=sorted({m.marca for m in modelos}),
        modelos=[{'marca': m.marca, 'nome': m.nome, 'categoria': m.categoria} for m in modelos],
    )


@veiculos_bp.route('/novo/<int:unidade_id>', methods=['GET', 'POST'])
@login_required
def novo(unidade_id):
    if not current_user.pode('cadastrar_veiculo'):
        abort(403)
    unidade = Unidade.query.get_or_404(unidade_id)
    if not _acesso_unidade(unidade.id):
        abort(403)
    veiculo = Veiculo(unidade_id=unidade.id, criado_por=current_user.id)
    if request.method == 'POST':
        erro = _preencher(veiculo, request.form)
        if erro:
            flash(erro, 'danger')
        else:
            db.session.add(veiculo)
            db.session.commit()
            flash(f'Veículo {veiculo.prefixo_exibicao} cadastrado. Ele já pode ser reservado na agenda.', 'success')
            return redirect(url_for('unidades.detalhe', id=unidade.id, _anchor='tab-veiculos'))
    return _render_form(unidade, veiculo)


@veiculos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.pode('editar_veiculo'):
        abort(403)
    veiculo = _veiculo_dono_ou_403(id)
    if request.method == 'POST':
        erro = _preencher(veiculo, request.form)
        if erro:
            flash(erro, 'danger')
        else:
            db.session.commit()
            flash('Veículo atualizado.', 'success')
            return redirect(url_for('veiculos.usos', id=veiculo.id))
    return _render_form(veiculo.unidade, veiculo)


@veiculos_bp.route('/<int:id>/ativo', methods=['POST'])
@login_required
def alternar_ativo(id):
    if not current_user.pode('editar_veiculo'):
        abort(403)
    veiculo = _veiculo_dono_ou_403(id)
    if not veiculo.ativo:
        erro = _duplicado(veiculo, veiculo.placa, veiculo.prefixo, veiculo.alugado)
        if erro:
            flash(f'Não deu para reativar: {erro}', 'danger')
            return redirect(url_for('veiculos.usos', id=veiculo.id))
    veiculo.ativo = not veiculo.ativo
    db.session.commit()
    flash('Veículo reativado.' if veiculo.ativo else
          'Veículo desativado: sai da lista da unidade e da agenda, mas o histórico de usos continua aqui.', 'success')
    return redirect(url_for('veiculos.usos', id=veiculo.id))


@veiculos_bp.route('/<int:id>')
@login_required
def usos(id):
    veiculo = _veiculo_ou_404(id)
    mes = _mes_param()
    rotulo = veiculo.rotulo
    lista = _usos_do_mes(veiculo, mes)
    agora = agora_brasilia()
    situacao = reservas.situacao_veiculos([veiculo], agora)[veiculo.id]
    anterior = date(mes.year - (mes.month == 1), (mes.month - 2) % 12 + 1, 1)
    emprestimo = reservas.emprestimo_ativo(veiculo.id)
    return render_template(
        'veiculos/usos.html',
        emprestimo=emprestimo,
        pode_devolver=bool(emprestimo) and current_user.pode('ver_transferencias') and (
            _acesso_unidade(emprestimo.unidade_origem_id) or _acesso_unidade(emprestimo.unidade_destino_id)),
        veiculo=veiculo, rotulo=rotulo, usos=lista, mes=mes,
        mes_nome=f'{MESES[mes.month - 1]}/{mes.year}',
        mes_anterior=anterior.strftime('%Y-%m'), mes_seguinte=_proximo_mes(mes).strftime('%Y-%m'),
        situacao=situacao, km_atual=reservas.km_atual(veiculo),
        total_km=sum(ev.km_rodados or 0 for ev in lista),
        finalidade=lambda ev: _finalidade(ev, rotulo),
        agora=agora,
        pode_reservar=veiculo.ativo and current_user.pode('adicionar_agenda'),
        unidade_reserva_id=(emprestimo.unidade_destino_id
                            if emprestimo and not _acesso_unidade(veiculo.unidade_id) else veiculo.unidade_id),
        pode_editar=current_user.pode('editar_veiculo') and _acesso_unidade(veiculo.unidade_id),
    )


@veiculos_bp.route('/<int:id>/km/<int:evento_id>', methods=['POST'])
@login_required
def salvar_km(id, evento_id):
    veiculo = _veiculo_ou_404(id)
    ev = AgendaEvento.query.filter_by(id=evento_id, veiculo_id=veiculo.id).first_or_404()

    def _km(nome):
        bruto = ''.join(ch for ch in (request.form.get(nome) or '') if ch.isdigit())
        return int(bruto) if bruto else None

    km_saida, km_chegada = _km('km_saida'), _km('km_chegada')
    if km_saida is not None and km_chegada is not None and km_chegada < km_saida:
        flash('O km de chegada não pode ser menor que o de saída.', 'danger')
    else:
        ev.km_saida = km_saida
        ev.km_chegada = km_chegada
        ev.devolvido_em = agora_local() if km_chegada is not None else None
        ev.atualizado_em = agora_local()
        db.session.commit()
        flash('Km registrado.', 'success')
    return redirect(url_for('veiculos.usos', id=veiculo.id, mes=ev.inicio.strftime('%Y-%m')))


RDV_LINHAS_FRENTE = 12
RDV_LINHAS_VERSO = 23


def _matricula(usuario):
    if not usuario:
        return ''
    mats = [m for m in usuario.matriculas if m.numero]
    ativas = [m for m in mats if m.ativo]
    return (ativas or mats)[0].numero if mats else ''


def _linha_rdv(ev, unidade):
    ini, fim = reservas.intervalo_evento(ev)
    ultimo_dia = (fim - timedelta(microseconds=1)).date()
    dia = f'{ini.day:02d}' if ultimo_dia <= ini.date() else f'{ini.day:02d} a {ultimo_dia.day:02d}'
    condutor = ev.condutor or ev.criador
    return {
        'dia': dia,
        'condutor': condutor.nome.upper() if condutor else '',
        'matricula': _matricula(condutor),
        'setor': (ev.condutor_unidade or ev.unidade or unidade).nome,
        'km_saida': ev.km_saida,
        'hora_saida': '' if ev.dia_inteiro else ini.strftime('%H:%M'),
        'destino': (ev.local or _finalidade(ev, ev.veiculo.rotulo if ev.veiculo else '') or '').upper(),
        'km_chegada': ev.km_chegada,
        'hora_chegada': '' if ev.dia_inteiro else fim.strftime('%H:%M'),
    }


def _paginas_rdv(linhas):
    """Frente com 12 linhas, versos com 23; sempre em número par para sair em frente e verso."""
    paginas = [linhas[:RDV_LINHAS_FRENTE]]
    resto = linhas[RDV_LINHAS_FRENTE:]
    while resto or len(paginas) % 2:
        paginas.append(resto[:RDV_LINHAS_VERSO])
        resto = resto[RDV_LINHAS_VERSO:]
    return paginas


@veiculos_bp.route('/<int:id>/rdv')
@login_required
def rdv(id):
    """RDV (Mapa de Uso Diário do Veículo) para imprimir em A4 paisagem, frente e verso."""
    veiculo = _veiculo_ou_404(id)
    mes = _mes_param()
    em_branco = request.args.get('branco') == '1'
    lista = [] if em_branco else _usos_do_mes(veiculo, mes)
    linhas = [_linha_rdv(ev, veiculo.unidade) for ev in lista]
    saidas = [ev.km_saida for ev in lista if ev.km_saida is not None]
    chegadas = [ev.km_chegada for ev in lista if ev.km_chegada is not None]
    km_inicial = saidas[0] if saidas else None
    km_final = chegadas[-1] if chegadas else None
    placa = veiculo.placa or ''
    return render_template(
        'veiculos/rdv.html',
        veiculo=veiculo, mes=mes, em_branco=em_branco,
        mes_nome=MESES[mes.month - 1].upper(),
        placa=f'{placa[:3]}-{placa[3:]}' if len(placa) == 7 else placa,
        paginas=_paginas_rdv(linhas),
        linhas_frente=RDV_LINHAS_FRENTE, linhas_verso=RDV_LINHAS_VERSO,
        km_inicial=km_inicial, km_final=km_final,
        total_km=km_final - km_inicial if km_inicial is not None and km_final is not None and km_final >= km_inicial else None,
    )
