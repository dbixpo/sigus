import os
import base64
import uuid
from io import BytesIO

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, abort, jsonify, current_app)
from flask_login import login_required, current_user
from PIL import Image, ImageDraw

from app import db
from app.models.tipo_link import TipoLink
from app.models.link_util import LinkUtil, PERFIS_LINK

links_bp = Blueprint('links', __name__, url_prefix='/links')

_UPLOAD_DIR = os.path.join('app', 'static', 'uploads', 'links')
_IMG_SIZE   = (200, 200)


def _pode_gerir():
    return current_user.pode('editar_links_uteis') or current_user.pode('adicionar_links_uteis')
    return current_user.perfil in ('administrador', 'gestor_secretaria')


def _normalizar_icone_fontawesome(valor):
    """Normaliza o ícone para Font Awesome (fas fa-xxx). Converte bi- (Bootstrap) para fa-."""
    if not valor:
        return ''
    valor = valor.strip()
    if not valor:
        return ''
    
    import re
    # Converter Bootstrap Icons (bi-xxx) para Font Awesome
    if valor.startswith('bi-'):
        biv = valor[3:].replace('-fill', '')
        mapa = {'folder': 'folder', 'link': 'link', 'link-45deg': 'link', 'gear': 'gear',
                'house': 'house', 'envelope': 'envelope', 'people': 'users', 'globe': 'globe',
                'file-earmark': 'file', 'calendar': 'calendar', 'star': 'star',
                'bookmark': 'bookmark', 'graph-up': 'chart-line', 'briefcase': 'briefcase',
                'collection': 'folder', 'box': 'box', 'cpu': 'microchip'}
        return 'fas fa-' + mapa.get(biv, biv.split('-')[0] if '-' in biv else biv)
    
    # Se já tem prefixo (fas, far, fab, fal, fad), retorna como está
    if re.match(r'^(fas|far|fab|fal|fad)\s+fa-', valor):
        return valor
    
    # Ícones de marca (Font Awesome Brands) — precisam de fab
    icones_marca = {'wpforms', 'google', 'facebook', 'facebook-f', 'whatsapp', 'youtube',
                    'twitter', 'instagram', 'linkedin', 'github', 'wikipedia-w', 'wordpress',
                    'chrome', 'firefox', 'microsoft', 'apple', 'android'}
    nome_sem_prefixo = valor.replace('fa-', '', 1) if valor.startswith('fa-') else valor
    if nome_sem_prefixo in icones_marca:
        return 'fab fa-' + nome_sem_prefixo
    
    # Se começa com fa- mas não tem prefixo, adiciona fas
    if valor.startswith('fa-'):
        return 'fas ' + valor
    
    # Se não começa com fa- e não tem prefixo, adiciona fas fa-
    if not re.match(r'^(fas|far|fab|fal|fad)\s+', valor):
        nome_icone = re.sub(r'^fa-', '', valor)
        return 'fas fa-' + nome_icone
    
    return valor


# ─────────────────────────────────────────────────────────────────────
#  Helpers de imagem
# ─────────────────────────────────────────────────────────────────────
def _salvar_imagem_base64(data_url: str) -> str | None:
    try:
        if ',' not in data_url:
            return None
        _, b64data = data_url.split(',', 1)
        img = Image.open(BytesIO(base64.b64decode(b64data))).convert('RGBA')
        img = img.resize(_IMG_SIZE, Image.LANCZOS)
        os.makedirs(_UPLOAD_DIR, exist_ok=True)
        filename = f'{uuid.uuid4().hex}.png'
        img.save(os.path.join(_UPLOAD_DIR, filename), 'PNG')
        return filename
    except Exception as e:
        current_app.logger.warning(f'Erro ao salvar imagem do link: {e}')
        return None


def _apagar_imagem(filename: str | None):
    if filename:
        try:
            os.remove(os.path.join(_UPLOAD_DIR, filename))
        except FileNotFoundError:
            pass


def _processar_form_link(item: LinkUtil | None) -> dict:
    perfis      = request.form.getlist('perfis_acesso') or ['todos']
    imagem_path = item.imagem_path if item else None
    data_url    = request.form.get('imagem_cropped', '').strip()
    if data_url.startswith('data:'):
        novo = _salvar_imagem_base64(data_url)
        if novo:
            _apagar_imagem(imagem_path)
            imagem_path = novo
    if request.form.get('imagem_remover') == '1':
        _apagar_imagem(imagem_path)
        imagem_path = None

    tipo_link_id = request.form.get('tipo_link_id') or None
    if tipo_link_id:
        tipo_link_id = int(tipo_link_id)

    return {
        'tipo_link_id': tipo_link_id,
        'nome':         request.form['nome'].strip(),
        'descricao':    request.form.get('descricao', '').strip() or None,
        'url':          request.form.get('url', '').strip() or None,
        'imagem_url':   request.form.get('imagem_url', '').strip() or None,
        'imagem_path':  imagem_path,
        'icone':        _normalizar_icone_fontawesome(request.form.get('icone', 'fas fa-link')) or 'fas fa-link',
        'nova_aba':     request.form.get('nova_aba') == 'on',
        'ativo':        request.form.get('ativo') == 'on',
        'perfis_acesso': perfis,
    }


# ─────────────────────────────────────────────────────────────────────
#  Página pública
# ─────────────────────────────────────────────────────────────────────
@links_bp.route('/')
@login_required
def index():
    if not current_user.pode('ver_links_uteis'):
        abort(403)
    tipos = (TipoLink.query
             .filter_by(ativo=True)
             .order_by(TipoLink.ordem)
             .all())
    # Para cada tipo, pega os links visíveis para o perfil
    dados = []
    for t in tipos:
        links = [l for l in
                 t.links.filter_by(ativo=True).order_by(LinkUtil.ordem).all()
                 if l.visivel_para(current_user.perfil)]
        dados.append({'tipo': t, 'links': links})

    # Links sem categoria
    sem_cat = [l for l in
               LinkUtil.query
               .filter_by(ativo=True, tipo_link_id=None)
               .order_by(LinkUtil.ordem).all()
               if l.visivel_para(current_user.perfil)]

    return render_template('links/index.html',
                           dados=dados,
                           sem_cat=sem_cat,
                           tipos=tipos)


# ─────────────────────────────────────────────────────────────────────
#  Admin: listagem geral de links
# ─────────────────────────────────────────────────────────────────────
@links_bp.route('/admin')
@login_required
def admin():
    if not _pode_gerir():
        abort(403)
    itens = LinkUtil.query.order_by(LinkUtil.tipo_link_id.nullslast(), LinkUtil.ordem).all()
    tipos = TipoLink.query.order_by(TipoLink.ordem).all()
    return render_template('links/admin.html', itens=itens, tipos=tipos, perfis=PERFIS_LINK)


# ─────────────────────────────────────────────────────────────────────
#  Admin: novo link
# ─────────────────────────────────────────────────────────────────────
@links_bp.route('/admin/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if not _pode_gerir():
        abort(403)
    tipos = TipoLink.query.order_by(TipoLink.ordem).all()
    if request.method == 'POST':
        ultimo = LinkUtil.query.order_by(LinkUtil.ordem.desc()).first()
        dados = _processar_form_link(None)
        item = LinkUtil(**dados, ordem=(ultimo.ordem + 1 if ultimo else 0),
                        criado_por=current_user.id)
        db.session.add(item)
        db.session.commit()
        flash(f'"{item.nome}" adicionado!', 'success')
        return redirect(url_for('links.admin'))
    return render_template('links/form.html', item=None, tipos=tipos, perfis=PERFIS_LINK)


# ─────────────────────────────────────────────────────────────────────
#  Admin: editar link
# ─────────────────────────────────────────────────────────────────────
@links_bp.route('/admin/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not _pode_gerir():
        abort(403)
    item  = LinkUtil.query.get_or_404(id)
    tipos = TipoLink.query.order_by(TipoLink.ordem).all()
    if request.method == 'POST':
        for k, v in _processar_form_link(item).items():
            setattr(item, k, v)
        db.session.commit()
        flash('Link atualizado!', 'success')
        return redirect(url_for('links.admin'))
    return render_template('links/form.html', item=item, tipos=tipos, perfis=PERFIS_LINK)


# ─────────────────────────────────────────────────────────────────────
#  Admin: excluir link
# ─────────────────────────────────────────────────────────────────────
@links_bp.route('/admin/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    if not _pode_gerir():
        abort(403)
    item = LinkUtil.query.get_or_404(id)
    _apagar_imagem(item.imagem_path)
    db.session.delete(item)
    db.session.commit()
    flash(f'"{item.nome}" removido.', 'info')
    return redirect(url_for('links.admin'))


# ─────────────────────────────────────────────────────────────────────
#  Admin: reordenar links (drag-and-drop)
# ─────────────────────────────────────────────────────────────────────
@links_bp.route('/admin/reordenar', methods=['POST'])
@login_required
def reordenar():
    if not _pode_gerir():
        abort(403)
    ids = request.json.get('ids', [])
    for ordem, item_id in enumerate(ids):
        LinkUtil.query.filter_by(id=item_id).update({'ordem': ordem})
    db.session.commit()
    return jsonify(ok=True)


# ─────────────────────────────────────────────────────────────────────
#  Admin: CRUD de TipoLink
# ─────────────────────────────────────────────────────────────────────
@links_bp.route('/admin/tipos')
@login_required
def admin_tipos():
    if not _pode_gerir():
        abort(403)
    tipos = TipoLink.query.order_by(TipoLink.ordem).all()
    return render_template('links/tipos.html', tipos=tipos)


@links_bp.route('/admin/tipos/novo', methods=['GET', 'POST'])
@login_required
def novo_tipo():
    if not _pode_gerir():
        abort(403)
    if request.method == 'POST':
        ultimo = TipoLink.query.order_by(TipoLink.ordem.desc()).first()
        t = TipoLink(
            nome=request.form['nome'].strip(),
            descricao=request.form.get('descricao', '').strip() or None,
            icone=_normalizar_icone_fontawesome(request.form.get('icone', 'fas fa-folder')) or 'fas fa-folder',
            cor=request.form.get('cor', '#1a6abf').strip() or '#1a6abf',
            ativo=request.form.get('ativo') == 'on',
            ordem=(ultimo.ordem + 1 if ultimo else 0),
        )
        db.session.add(t)
        db.session.commit()
        flash(f'Tipo "{t.nome}" criado!', 'success')
        return redirect(url_for('links.admin_tipos'))
    return render_template('links/form_tipo.html', tipo=None)


@links_bp.route('/admin/tipos/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tipo(id):
    if not _pode_gerir():
        abort(403)
    t = TipoLink.query.get_or_404(id)
    if request.method == 'POST':
        t.nome      = request.form['nome'].strip()
        t.descricao = request.form.get('descricao', '').strip() or None
        t.icone     = _normalizar_icone_fontawesome(request.form.get('icone', 'fas fa-folder')) or 'fas fa-folder'
        t.cor       = request.form.get('cor', '#1a6abf').strip() or '#1a6abf'
        t.ativo     = request.form.get('ativo') == 'on'
        db.session.commit()
        flash('Tipo atualizado!', 'success')
        return redirect(url_for('links.admin_tipos'))
    return render_template('links/form_tipo.html', tipo=t)


@links_bp.route('/admin/tipos/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_tipo(id):
    if not _pode_gerir():
        abort(403)
    t = TipoLink.query.get_or_404(id)
    # Desvincula os links do tipo antes de excluir
    LinkUtil.query.filter_by(tipo_link_id=t.id).update({'tipo_link_id': None})
    db.session.delete(t)
    db.session.commit()
    flash(f'Tipo "{t.nome}" removido.', 'info')
    return redirect(url_for('links.admin_tipos'))


@links_bp.route('/admin/tipos/reordenar', methods=['POST'])
@login_required
def reordenar_tipos():
    if not _pode_gerir():
        abort(403)
    ids = request.json.get('ids', [])
    for ordem, tid in enumerate(ids):
        TipoLink.query.filter_by(id=tid).update({'ordem': ordem})
    db.session.commit()
    return jsonify(ok=True)
