"""Funções auxiliares para gerar notificações de chamados."""
from app import db
from app.models.notificacao import Notificacao
from app.models.unidade import UsuarioUnidade
from app.models.usuario import Usuario


def _add(usuario_id, tipo, titulo, texto, chamado_id):
    db.session.add(Notificacao(
        usuario_id=usuario_id,
        tipo=tipo,
        titulo=titulo,
        texto=texto,
        chamado_id=chamado_id,
    ))


def _gestores_da_unidade(unidade_id, excluir_id=None):
    """IDs de coordenadores e administrativos ativos na unidade."""
    q = (UsuarioUnidade.query
         .filter_by(unidade_id=unidade_id, ativo=True)
         .join(Usuario, Usuario.id == UsuarioUnidade.usuario_id)
         .filter(Usuario.perfil.in_(['coordenador', 'administrativo',
                                     'administrador', 'gestor_secretaria'])))
    ids = [uu.usuario_id for uu in q.all()]
    if excluir_id and excluir_id in ids:
        ids.remove(excluir_id)
    return ids


def _membros_setor(setor_id, excluir_id=None):
    """IDs dos usuários vinculados ao setor de manutenção do chamado."""
    if not setor_id:
        return []
    from app.models.chamado import UsuarioSetor
    ids = [us.usuario_id for us in
           UsuarioSetor.query.filter_by(setor_id=setor_id).all()]
    if excluir_id and excluir_id in ids:
        ids.remove(excluir_id)
    return ids


def notificar_chamado_aberto(chamado, aberto_por_id):
    """Notifica coordenadores/admin da unidade e membros do setor de manutenção."""
    destinos = set()

    # Gestores da unidade (coordenador, administrativo, gestor, admin)
    for uid in _gestores_da_unidade(chamado.unidade_id, excluir_id=aberto_por_id):
        destinos.add(uid)

    # Membros do setor de manutenção designado
    for uid in _membros_setor(chamado.setor_id, excluir_id=aberto_por_id):
        destinos.add(uid)

    for uid in destinos:
        _add(uid, 'chamado_aberto',
             f'Novo chamado: {chamado.numero}',
             chamado.titulo,
             chamado.id)


def notificar_andamento(chamado, andamento, autor_id):
    """Notifica quem abriu o chamado e o responsável sobre novo andamento."""
    tipo = andamento.tipo_andamento
    if tipo == 'alerta':
        tipo_notif = 'alerta_chamado'
        titulo = f'Alerta no chamado {chamado.numero}'
    elif tipo == 'pedido_info':
        tipo_notif = 'pedido_info'
        titulo = f'Pedido de informação: {chamado.numero}'
    else:
        tipo_notif = 'novo_andamento'
        titulo = f'Novo andamento: {chamado.numero}'

    destinos = set()

    # Sempre notifica quem abriu e o responsável
    if chamado.aberto_por and chamado.aberto_por != autor_id:
        destinos.add(chamado.aberto_por)

    # Para alertas e pedidos de info, notifica também gestores da unidade
    if tipo in ('alerta', 'pedido_info'):
        for uid in _gestores_da_unidade(chamado.unidade_id, excluir_id=autor_id):
            destinos.add(uid)

    for uid in destinos:
        _add(uid, tipo_notif, titulo, andamento.acao, chamado.id)


def notificar_status_alterado(chamado, status_anterior, autor_id):
    """Notifica quem abriu o chamado quando o status muda para concluído/cancelado."""
    from app.models.status_chamado import StatusChamado
    status_obj = StatusChamado.query.filter_by(slug=chamado.status).first()
    if not (status_obj and status_obj.encerra_chamado):
        return

    tipo_notif = 'chamado_concluido' if chamado.status == 'concluido' else 'chamado_cancelado'
    titulo = f'Chamado {chamado.numero} {"concluído" if chamado.status == "concluido" else "cancelado"}'

    destinos = set()
    # Notifica quem abriu
    if chamado.aberto_por and chamado.aberto_por != autor_id:
        destinos.add(chamado.aberto_por)
    # E os gestores da unidade
    for uid in _gestores_da_unidade(chamado.unidade_id, excluir_id=autor_id):
        destinos.add(uid)

    for uid in destinos:
        _add(uid, tipo_notif, titulo, chamado.titulo, chamado.id)
