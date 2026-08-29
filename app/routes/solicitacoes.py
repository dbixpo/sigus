# -*- coding: utf-8 -*-
"""Rotas de auto-cadastro de profissionais externos via link público.

Fluxo:
  1. Profissional acessa /solicitar  (sem login)
  2. Preenche formulário com dados pessoais + escolhe unidade
  3. Sistema grava SolicitacaoVinculo com status='pendente'
  4. Coordenador/Administrativo da unidade vê na aba "Solicitações"
  5. Ao aprovar: cria Usuario (perfil=profissional), UsuarioUnidade, FichaCnesVinculo
  6. Ao rejeitar: marca como rejeitado com observação opcional
"""
import secrets
from datetime import date, datetime

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, abort)
from flask_login import login_required, current_user

from app import db
from app.models.unidade import Unidade, UsuarioUnidade
from app.models.usuario import Usuario, CBOS, VINCULOS, TIPOS_VINCULO, ESCOLARIDADES
from app.models.cbo import CBO
from app.models.solicitacao_vinculo import SolicitacaoVinculo
from app.models.ficha_cnes import FichaCnesVinculo
from app.models.notificacao import Notificacao

solicitacoes_bp = Blueprint('solicitacoes', __name__, url_prefix='/solicitar-vinculo-profissional')


def _validar_cpf(digits: str) -> bool:
    """Valida CPF pelos dígitos verificadores. Recebe só os 11 dígitos."""
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    # Primeiro dígito verificador
    s = sum(int(digits[i]) * (10 - i) for i in range(9))
    if (s * 10 % 11) % 10 != int(digits[9]):
        return False
    # Segundo dígito verificador
    s = sum(int(digits[i]) * (11 - i) for i in range(10))
    return (s * 10 % 11) % 10 == int(digits[10])


# ─── helpers ──────────────────────────────────────────────────────────────────

def _pode_aprovar(unidade):
    """Verifica se o usuário logado pode aprovar solicitações desta unidade."""
    if current_user.perfil in ('administrador', 'gestor_secretaria'):
        return True
    if current_user.perfil in ('coordenador', 'administrativo'):
        return current_user.unidades.filter_by(unidade_id=unidade.id, ativo=True).first() is not None
    return False


def _notificar_gestores(unidade, solicitacao):
    """Envia notificação a coordenadores e administrativos da unidade."""
    gestores = (
        UsuarioUnidade.query
        .filter_by(unidade_id=unidade.id, ativo=True)
        .join(Usuario, Usuario.id == UsuarioUnidade.usuario_id)
        .filter(Usuario.perfil.in_(['coordenador', 'administrativo', 'administrador', 'gestor_secretaria']))
        .all()
    )
    for v in gestores:
        db.session.add(Notificacao(
            usuario_id=v.usuario_id,
            tipo='pedido_info',
            titulo=f'Nova solicitação de vínculo — {solicitacao.nome}',
            texto=f'{solicitacao.nome} solicitou vínculo como profissional na unidade {unidade.nome}.',
        ))


def _cpf_digitos(cpf):
    """Remove formatação do CPF — retorna só os 11 dígitos."""
    return ''.join(c for c in (cpf or '') if c.isdigit())


def _cnpj_limpo(val):
    """Remove caracteres não numéricos do CNPJ."""
    import re
    return re.sub(r'\D', '', val or '')


# ─── Rota pública ─────────────────────────────────────────────────────────────

@solicitacoes_bp.route('/', methods=['GET', 'POST'])
def formulario():
    """Formulário público de auto-cadastro (sem necessidade de login)."""
    unidades = Unidade.query.filter_by(status='ativa').order_by(Unidade.nome).all()

    if request.method == 'POST':
        nome  = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()

        cpf_raw   = request.form.get('cpf', '').strip()
        cpf_digits = ''.join(c for c in cpf_raw if c.isdigit())

        # Busca CBOs ativos do banco de dados
        cbos_ativos = [(c.codigo, c.descricao) for c in CBO.query.filter_by(ativo=True).order_by(CBO.codigo).all()]
        if not nome or not email:
            flash('Nome e e-mail são obrigatórios.', 'danger')
            return render_template('solicitacoes/formulario.html',
                                   unidades=unidades, cbos=cbos_ativos,
                                   vinculos=VINCULOS, tipos_vinculo=TIPOS_VINCULO,
                                   escolaridades=ESCOLARIDADES,
                                   form=request.form)

        if cpf_digits and not _validar_cpf(cpf_digits):
            flash('CPF inválido. Verifique os dígitos e tente novamente.', 'danger')
            return render_template('solicitacoes/formulario.html',
                                   unidades=unidades, cbos=cbos_ativos,
                                   vinculos=VINCULOS, tipos_vinculo=TIPOS_VINCULO,
                                   escolaridades=ESCOLARIDADES,
                                   form=request.form)

        unidade_id = request.form.get('unidade_id', type=int)
        if not unidade_id or not Unidade.query.get(unidade_id):
            flash('Selecione uma unidade válida.', 'danger')
            return render_template('solicitacoes/formulario.html',
                                   unidades=unidades, cbos=cbos_ativos,
                                   vinculos=VINCULOS, tipos_vinculo=TIPOS_VINCULO,
                                   escolaridades=ESCOLARIDADES,
                                   form=request.form)

        def _d(field):
            v = request.form.get(field, '').strip()
            if v:
                try:
                    return date.fromisoformat(v)
                except ValueError:
                    pass
            return None

        def _s(field):
            return request.form.get(field, '').strip() or None

        ch_str = request.form.get('carga_horaria', '').strip()

        sol = SolicitacaoVinculo(
            unidade_id    = unidade_id,
            nome          = nome,
            email         = email,
            cpf           = _s('cpf'),
            cns           = _s('cns'),
            sexo          = _s('sexo'),
            data_nasc     = _d('data_nasc'),
            nome_mae      = _s('nome_mae'),
            nome_pai      = _s('nome_pai'),
            nacionalidade = _s('nacionalidade') or 'brasileira',
            municipio_nasc= _s('municipio_nasc'),
            uf_nasc       = _s('uf_nasc'),
            dt_entrada_pais = _d('dt_entrada_pais'),
            pais_origem     = _s('pais_origem'),
            rg            = _s('rg'),
            rg_uf         = _s('rg_uf'),
            rg_orgao      = _s('rg_orgao'),
            rg_emissao    = _d('rg_emissao'),
            escolaridade  = _s('escolaridade'),
            end_logradouro= _s('end_logradouro'),
            end_numero    = _s('end_numero'),
            end_bairro    = _s('end_bairro'),
            end_municipio = _s('end_municipio'),
            end_uf        = _s('end_uf'),
            end_cep       = _s('end_cep'),
            telefone      = _s('telefone'),
            orgao_emissor = _s('orgao_emissor'),
            reg_conselho  = _s('reg_conselho'),
            cbo           = _s('cbo'),
            vinculo       = _s('vinculo'),
            tipo_vinculo  = _s('tipo_vinculo'),
            carga_horaria = int(ch_str) if ch_str.isdigit() else None,
            dt_entrada    = _d('dt_entrada'),
            assinatura_base64 = _s('assinatura_base64') or None,
        )
        
        # Se empresa_id foi selecionado, busca dados da empresa
        empresa_id = request.form.get('empresa_id', type=int)
        if empresa_id:
            from app.models.empresa import EmpresaContratada
            empresa = EmpresaContratada.query.get(empresa_id)
            if empresa:
                sol.cnpj_empresa = empresa.cnpj  # Já está sem máscara no banco
                sol.nome_empresa = empresa.razao_social
            else:
                sol.cnpj_empresa = _cnpj_limpo(_s('cnpj_empresa')) or None
                sol.nome_empresa = _s('nome_empresa')
        else:
            sol.cnpj_empresa = _cnpj_limpo(_s('cnpj_empresa')) or None
            sol.nome_empresa = _s('nome_empresa')
        db.session.add(sol)
        db.session.flush()  # garante sol.id antes de notificar

        unidade = Unidade.query.get(unidade_id)
        _notificar_gestores(unidade, sol)
        db.session.commit()

        return redirect(url_for('solicitacoes.confirmacao', id=sol.id))

    # Busca CBOs ativos do banco de dados
    cbos_ativos = [(c.codigo, c.descricao) for c in CBO.query.filter_by(ativo=True).order_by(CBO.codigo).all()]
    return render_template('solicitacoes/formulario.html',
                           unidades=unidades, cbos=cbos_ativos,
                           vinculos=VINCULOS, tipos_vinculo=TIPOS_VINCULO,
                           escolaridades=ESCOLARIDADES,
                           form={})


@solicitacoes_bp.route('/confirmacao/<int:id>')
def confirmacao(id):
    sol = SolicitacaoVinculo.query.get_or_404(id)
    return render_template('solicitacoes/confirmacao.html', sol=sol)


# ─── Rotas internas (requerem login) ──────────────────────────────────────────

@solicitacoes_bp.route('/<int:id>/aprovar', methods=['POST'])
@login_required
def aprovar(id):
    sol = SolicitacaoVinculo.query.get_or_404(id)
    if sol.status != 'pendente':
        flash('Esta solicitação já foi processada.', 'warning')
        return redirect(url_for('unidades.detalhe', id=sol.unidade_id))

    if not _pode_aprovar(sol.unidade):
        abort(403)

    # 1. Verificar se já existe usuário com esse e-mail ou CPF
    usuario = Usuario.query.filter_by(email=sol.email).first()
    if not usuario and sol.cpf:
        usuario = Usuario.query.filter_by(cpf=sol.cpf).first()

    usuario_ja_existia = usuario is not None

    if not usuario:
        # 2. Criar o usuário — senha = CPF (só dígitos)
        senha_cpf = _cpf_digitos(sol.cpf) or secrets.token_urlsafe(8)
        usuario = Usuario(
            nome             = sol.nome,
            email            = sol.email,
            perfil           = 'profissional',
            cpf              = sol.cpf,
            cns              = sol.cns,
            sexo             = sol.sexo,
            data_nasc        = sol.data_nasc,
            nome_mae         = sol.nome_mae,
            nome_pai         = sol.nome_pai,
            nacionalidade    = sol.nacionalidade,
            municipio_nasc   = sol.municipio_nasc,
            uf_nasc          = sol.uf_nasc,
            dt_entrada_pais  = sol.dt_entrada_pais,
            pais_origem      = sol.pais_origem,
            rg               = sol.rg,
            rg_uf            = sol.rg_uf,
            rg_orgao         = sol.rg_orgao,
            rg_emissao       = sol.rg_emissao,
            escolaridade     = sol.escolaridade,
            end_logradouro   = sol.end_logradouro,
            end_numero       = sol.end_numero,
            end_bairro       = sol.end_bairro,
            end_municipio    = sol.end_municipio,
            end_uf           = sol.end_uf,
            end_cep          = sol.end_cep,
            telefone         = sol.telefone,
            orgao_emissor    = sol.orgao_emissor,
            reg_conselho     = sol.reg_conselho,
            cbo              = sol.cbo,
            vinculo          = sol.vinculo,
            tipo_vinculo     = sol.tipo_vinculo,
            carga_horaria    = sol.carga_horaria,
            ativo            = True,
        )
        usuario.set_senha(senha_cpf)
        db.session.add(usuario)
        db.session.flush()

    # 3. Criar vínculo (se não existir)
    vinculo_existente = UsuarioUnidade.query.filter_by(
        usuario_id=usuario.id, unidade_id=sol.unidade_id
    ).first()

    if not vinculo_existente:
        vinculo_obj = UsuarioUnidade(
            usuario_id = usuario.id,
            unidade_id = sol.unidade_id,
            ativo      = True,
        )
        db.session.add(vinculo_obj)
    elif not vinculo_existente.ativo:
        vinculo_existente.ativo = True

    db.session.flush()

    # 4. Gerar Ficha CNES de cadastro
    # Obtém vínculo e tipo da solicitação
    vinculo_ficha = sol.vinculo
    tipo_vinculo = sol.tipo_vinculo
    
    # Se vínculo é Residência (5) ou Estágio (6), tipo deve ser automaticamente "3 - Contrato por Prazo Determinado"
    if vinculo_ficha in ('5', '6'):
        tipo_vinculo = '3'
    
    ficha = FichaCnesVinculo(
        usuario_id       = usuario.id,
        unidade_id       = sol.unidade_id,
        tipo             = 'cadastro',
        vinculo          = vinculo_ficha,
        tipo_vinculo     = tipo_vinculo,
        carga_horaria    = sol.carga_horaria,
        cbo              = sol.cbo,
        dt_entrada_unidade = sol.dt_entrada,
        cns_profissional = sol.cns,
        cnpj_empresa     = sol.cnpj_empresa,
        nome_empresa     = sol.nome_empresa,
        gerado_por       = current_user.id,
    )
    db.session.add(ficha)

    # 5. Atualizar solicitação
    sol.status       = 'aprovado'
    sol.aprovado_por = current_user.id
    sol.aprovado_em  = datetime.utcnow()
    sol.usuario_criado = usuario.id
    if request.form.get('observacao'):
        sol.observacao = request.form.get('observacao').strip()

    db.session.commit()

    # Se for gestor/admin, notifica sobre chamados em aberto da unidade
    if usuario.perfil in ('coordenador', 'administrativo', 'administrador', 'gestor_secretaria'):
        from app.models.chamado import Chamado as _Chamado
        chamados_abertos = (_Chamado.query
                            .filter_by(unidade_id=sol.unidade_id)
                            .filter(~_Chamado.status.in_(['cancelado', 'concluido']))
                            .order_by(_Chamado.criado_em.desc())
                            .limit(20).all())
        for c in chamados_abertos:
            db.session.add(Notificacao(
                usuario_id=usuario.id,
                tipo='chamado_aberto',
                titulo=f'Chamado em aberto: {c.numero}',
                texto=c.titulo,
                chamado_id=c.id,
            ))
        db.session.commit()

    if usuario_ja_existia:
        flash(f'Solicitação de {sol.nome} aprovada. Usuário já existia no sistema — vínculo criado e ficha CNES gerada.', 'success')
    else:
        flash(f'Solicitação de {sol.nome} aprovada. Usuário criado com senha = CPF (só dígitos). Oriente-o a trocar a senha no primeiro acesso.', 'success')


    return redirect(url_for('unidades.detalhe', id=sol.unidade_id))


@solicitacoes_bp.route('/<int:id>/rejeitar', methods=['POST'])
@login_required
def rejeitar(id):
    sol = SolicitacaoVinculo.query.get_or_404(id)
    if sol.status != 'pendente':
        flash('Esta solicitação já foi processada.', 'warning')
        return redirect(url_for('unidades.detalhe', id=sol.unidade_id))

    if not _pode_aprovar(sol.unidade):
        abort(403)

    sol.status       = 'rejeitado'
    sol.aprovado_por = current_user.id
    sol.aprovado_em  = datetime.utcnow()
    sol.observacao   = request.form.get('observacao', '').strip() or None
    db.session.commit()

    flash(f'Solicitação de {sol.nome} rejeitada.', 'warning')
    return redirect(url_for('unidades.detalhe', id=sol.unidade_id))
