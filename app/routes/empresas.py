# -*- coding: utf-8 -*-
"""Empresas Contratadas — Operações."""
import os
import re
import uuid
import mimetypes
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.empresa import EmpresaContratada

empresas_bp = Blueprint('empresas', __name__, url_prefix='/empresas')

_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'empresas')


def _cnpj_limpo(val):
    """Remove caracteres não numéricos do CNPJ."""
    return re.sub(r'\D', '', val or '')


def _digitos(val):
    """Retorna só os dígitos do valor."""
    return re.sub(r'\D', '', val or '') or None


@empresas_bp.route('/')
@login_required
def listar():
    if not current_user.pode('cadastrar_contrato') and not current_user.pode('editar_contrato'):
        abort(403)
    ativo = request.args.get('ativo', '')
    query = EmpresaContratada.query
    if ativo == '1':
        query = query.filter_by(ativo=True)
    elif ativo == '0':
        query = query.filter_by(ativo=False)
    empresas = query.order_by(EmpresaContratada.razao_social).all()
    return render_template('empresas/listar.html', empresas=empresas, filtro_ativo=ativo)


@empresas_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if not current_user.pode('cadastrar_contrato'):
        abort(403)
    if request.method == 'POST':
        cnpj = _cnpj_limpo(request.form.get('cnpj', ''))
        if not cnpj or len(cnpj) != 14:
            flash('CNPJ inválido. Informe 14 dígitos.', 'danger')
            return redirect(url_for('empresas.novo'))
        if EmpresaContratada.query.filter_by(cnpj=cnpj).first():
            flash('Já existe empresa cadastrada com este CNPJ.', 'danger')
            return redirect(url_for('empresas.novo'))
        emp = EmpresaContratada(
            cnpj=cnpj,
            razao_social=request.form.get('razao_social', '').strip(),
            logradouro=request.form.get('logradouro', '').strip() or None,
            numero=request.form.get('numero', '').strip() or None,
            complemento=request.form.get('complemento', '').strip() or None,
            bairro=request.form.get('bairro', '').strip() or None,
            cidade=request.form.get('cidade', '').strip() or None,
            estado=request.form.get('estado', '').strip() or None,
            cep=_digitos(request.form.get('cep', '')) or None,
            telefone=_digitos(request.form.get('telefone', '')) or None,
            email=request.form.get('email', '').strip() or None,
            nome_comum=request.form.get('nome_comum', '').strip() or None,
            email_suporte=request.form.get('email_suporte', '').strip() or None,
            telefone_suporte=_digitos(request.form.get('telefone_suporte', '')) or None,
        )
        db.session.add(emp)
        db.session.flush()
        # Foto/logo
        foto = request.files.get('logo')
        if foto and foto.filename:
            mime = foto.mimetype or mimetypes.guess_type(foto.filename)[0] or ''
            if mime.startswith('image/'):
                ext = os.path.splitext(foto.filename)[1].lower() or '.jpg'
                fn = f"{uuid.uuid4().hex}{ext}"
                os.makedirs(_UPLOAD_DIR, exist_ok=True)
                foto.save(os.path.join(_UPLOAD_DIR, fn))
                emp.logo_filename = fn
        db.session.commit()
        flash(f'Empresa {emp.razao_social} cadastrada!', 'success')
        return redirect(url_for('empresas.detalhe', id=emp.id))
    return render_template('empresas/form.html', empresa=None)


@empresas_bp.route('/<int:id>')
@login_required
def detalhe(id):
    from app.models.contrato import Contrato
    empresa = EmpresaContratada.query.get_or_404(id)
    if not current_user.pode('cadastrar_contrato') and not current_user.pode('editar_contrato'):
        abort(403)
    contratos = empresa.contratos.order_by(Contrato.data_fim.desc()).limit(50).all()
    return render_template('empresas/detalhe.html', empresa=empresa, contratos=contratos)


@empresas_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.pode('editar_contrato'):
        abort(403)
    empresa = EmpresaContratada.query.get_or_404(id)
    if request.method == 'POST':
        cnpj = _cnpj_limpo(request.form.get('cnpj', ''))
        if not cnpj or len(cnpj) != 14:
            flash('CNPJ inválido. Informe 14 dígitos.', 'danger')
            return redirect(url_for('empresas.editar', id=id))
        outro = EmpresaContratada.query.filter(EmpresaContratada.cnpj == cnpj, EmpresaContratada.id != id).first()
        if outro:
            flash('Já existe outra empresa com este CNPJ.', 'danger')
            return redirect(url_for('empresas.editar', id=id))
        empresa.cnpj = cnpj
        empresa.razao_social = request.form.get('razao_social', '').strip()
        empresa.logradouro = request.form.get('logradouro', '').strip() or None
        empresa.numero = request.form.get('numero', '').strip() or None
        empresa.complemento = request.form.get('complemento', '').strip() or None
        empresa.bairro = request.form.get('bairro', '').strip() or None
        empresa.cidade = request.form.get('cidade', '').strip() or None
        empresa.estado = request.form.get('estado', '').strip() or None
        empresa.cep = _digitos(request.form.get('cep', '')) or None
        empresa.telefone = _digitos(request.form.get('telefone', '')) or None
        empresa.email = request.form.get('email', '').strip() or None
        empresa.nome_comum = request.form.get('nome_comum', '').strip() or None
        empresa.email_suporte = request.form.get('email_suporte', '').strip() or None
        empresa.telefone_suporte = _digitos(request.form.get('telefone_suporte', '')) or None
        # Foto
        foto = request.files.get('logo')
        if foto and foto.filename:
            mime = foto.mimetype or mimetypes.guess_type(foto.filename)[0] or ''
            if mime.startswith('image/'):
                ext = os.path.splitext(foto.filename)[1].lower() or '.jpg'
                fn = f"{uuid.uuid4().hex}{ext}"
                os.makedirs(_UPLOAD_DIR, exist_ok=True)
                foto.save(os.path.join(_UPLOAD_DIR, fn))
                if empresa.logo_filename:
                    try:
                        os.remove(os.path.join(_UPLOAD_DIR, empresa.logo_filename))
                    except OSError:
                        pass
                empresa.logo_filename = fn
        db.session.commit()
        flash('Empresa atualizada!', 'success')
        return redirect(url_for('empresas.detalhe', id=id))
    return render_template('empresas/form.html', empresa=empresa)


@empresas_bp.route('/<int:id>/logo', methods=['POST'])
@login_required
def alterar_logo(id):
    if not current_user.pode('editar_contrato'):
        abort(403)
    empresa = EmpresaContratada.query.get_or_404(id)
    acao = request.form.get('acao')
    if acao == 'remover':
        if empresa.logo_filename:
            try:
                os.remove(os.path.join(_UPLOAD_DIR, empresa.logo_filename))
            except OSError:
                pass
            empresa.logo_filename = None
            db.session.commit()
            flash('Logo removido.', 'success')
        return redirect(url_for('empresas.detalhe', id=id))
    foto = request.files.get('logo')
    if foto and foto.filename:
        mime = foto.mimetype or mimetypes.guess_type(foto.filename)[0] or ''
        if mime.startswith('image/'):
            ext = os.path.splitext(foto.filename)[1].lower() or '.jpg'
            fn = f"{uuid.uuid4().hex}{ext}"
            os.makedirs(_UPLOAD_DIR, exist_ok=True)
            foto.save(os.path.join(_UPLOAD_DIR, fn))
            if empresa.logo_filename:
                try:
                    os.remove(os.path.join(_UPLOAD_DIR, empresa.logo_filename))
                except OSError:
                    pass
            empresa.logo_filename = fn
            db.session.commit()
            flash('Logo atualizado!', 'success')
    return redirect(url_for('empresas.detalhe', id=id))
