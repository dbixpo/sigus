# -*- coding: utf-8 -*-
from datetime import timezone, timedelta
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.notificacao import Notificacao

notificacoes_bp = Blueprint('notificacoes', __name__, url_prefix='/notificacoes')

_TZ = timedelta(hours=-3)  # BRT


def _fmt(notif):
    """Serializa uma notificação para JSON."""
    dt = (notif.criado_em + _TZ).strftime('%d/%m/%Y %H:%M') if notif.criado_em else ''
    return {
        'id':        notif.id,
        'tipo':      notif.tipo,
        'titulo':    notif.titulo,
        'texto':     notif.texto or '',
        'url':       notif.url,
        'icone':     notif.icone,
        'cor':       notif.cor,
        'lida':      notif.lida,
        'criado_em': dt,
    }


@notificacoes_bp.route('/recentes')
@login_required
def recentes():
    """Retorna as 30 notificações mais recentes não lidas do usuário."""
    notifs = (Notificacao.query
              .filter_by(usuario_id=current_user.id, lida=False)
              .order_by(Notificacao.criado_em.desc())
              .limit(15).all())
    return jsonify(notificacoes=[_fmt(n) for n in notifs])


@notificacoes_bp.route('/contagem')
@login_required
def contagem():
    """Retorna a contagem de notificações não lidas."""
    n = Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).count()
    return jsonify(nao_lidas=n)


@notificacoes_bp.route('/marcar-lida/<int:id>', methods=['POST'])
@login_required
def marcar_lida(id):
    notif = Notificacao.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    notif.lida = True
    db.session.commit()
    return jsonify(ok=True)


@notificacoes_bp.route('/marcar-todas-lidas', methods=['POST'])
@login_required
def marcar_todas_lidas():
    (Notificacao.query
     .filter_by(usuario_id=current_user.id, lida=False)
     .update({'lida': True}))
    db.session.commit()
    return jsonify(ok=True)
