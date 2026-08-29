"""Acesso compartilhado: chamados logados ou abertura externa (sem login)."""
from functools import wraps

from flask import g, session, redirect, url_for, request, abort
from flask_login import current_user

from app.models.chamado import Chamado


def is_chamado_externo():
    return bool(
        session.get('externo_nome')
        and session.get('externo_whatsapp')
        and session.get('externo_email')
        and session.get('externo_unidade_id')
    )


def externo_session():
    return {
        'nome': (session.get('externo_nome') or '').strip(),
        'whatsapp': (session.get('externo_whatsapp') or '').strip(),
        'email': (session.get('externo_email') or '').strip(),
        'unidade_id': session.get('externo_unidade_id'),
    }


def chamado_abertura_acesso(f):
    """Permite usuário logado com permissão ou visitante com sessão externa."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if current_user.is_authenticated:
            if not current_user.pode('abrir_chamado'):
                abort(403)
            g.chamado_externo = False
            g.externo = None
        elif is_chamado_externo():
            g.chamado_externo = True
            g.externo = externo_session()
        else:
            nxt = request.full_path if request.query_string else request.path
            return redirect(url_for('chamados_externo.identificacao', next=nxt))
        return f(*args, **kwargs)
    return wrapped


def tpl_ctx_abertura(**kwargs):
    from app.models.unidade import Unidade
    externo = getattr(g, 'chamado_externo', False)
    kwargs.setdefault('chamado_externo', externo)
    kwargs.setdefault('externo', getattr(g, 'externo', None))
    kwargs.setdefault('abrir_chamado_bp', 'chamados_externo' if externo else 'chamados')
    kwargs.setdefault('chamados_api_prefix', '/abrir-chamado/api' if externo else '/chamados/api')
    if externo and kwargs.get('externo'):
        u = Unidade.query.get(kwargs['externo'].get('unidade_id'))
        kwargs.setdefault('externo_unidade_nome', u.nome if u else '—')
    return kwargs


def aplicar_solicitante_chamado(chamado):
    if getattr(g, 'chamado_externo', False) and g.externo:
        chamado.externo_nome = g.externo['nome']
        chamado.externo_whatsapp = g.externo['whatsapp']
        chamado.externo_email = g.externo['email']
        chamado.aberto_por = None
    else:
        chamado.aberto_por = current_user.id
        chamado.externo_nome = None
        chamado.externo_whatsapp = None
        chamado.externo_email = None


def historico_usuario_id():
    if getattr(g, 'chamado_externo', False):
        return None
    return current_user.id if current_user.is_authenticated else None


def historico_acao(acao):
    if getattr(g, 'chamado_externo', False) and g.externo:
        return f'{acao} — solicitante externo: {g.externo["nome"]}'
    return acao


def notificar_abertura(chamado):
    from app.notificar import notificar_chamado_aberto
    uid = None if getattr(g, 'chamado_externo', False) else current_user.id
    notificar_chamado_aberto(chamado, uid)


def redirect_pos_abertura(chamado):
    if getattr(g, 'chamado_externo', False):
        conceder_acompanhamento(chamado)
        return redirect(url_for('chamados_externo.confirmacao', numero=chamado.numero))
    from flask import flash
    flash(f'Chamado {chamado.numero} aberto com sucesso!', 'success')
    return redirect(url_for('chamados.detalhe', id=chamado.id))


def conceder_acompanhamento(chamado):
    """Permite ver o andamento deste chamado na área pública (sessão)."""
    acc = session.get('acompanhar_chamados') or {}
    acc[str(chamado.id)] = chamado.unidade_id
    session['acompanhar_chamados'] = acc
    session.modified = True


def pode_acompanhar(chamado):
    acc = session.get('acompanhar_chamados') or {}
    return acc.get(str(chamado.id)) == chamado.unidade_id


def buscar_chamado_acompanhamento(numero, unidade_id):
    """Valida número + unidade solicitante. Retorna (chamado, erro)."""
    numero = (numero or '').strip().upper()
    if not numero:
        return None, 'Informe o número do chamado.'
    if not unidade_id:
        return None, 'Selecione a unidade.'
    chamado = Chamado.query.filter(Chamado.numero.ilike(numero)).first()
    if not chamado or chamado.unidade_id != unidade_id:
        return None, (
            'Não encontramos este chamado para a unidade informada. '
            'Verifique o número e a unidade.'
        )
    return chamado, None
