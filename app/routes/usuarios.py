from datetime import date
from urllib.parse import quote
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models.usuario import Usuario, PERFIS, CBOS, VINCULOS, TIPOS_VINCULO, ESCOLARIDADES
from app.models.cbo import CBO
from app.models.unidade import Unidade
from app.models.ficha_cnes import FichaCnesVinculo
from app.models.matricula import MatriculaProfissional
from app.utils import _montar_corpo_email, _montar_corpo_email_ficha

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

# Perfis que cada nível pode atribuir ao cadastrar/editar um usuário
_PERFIS_PERMITIDOS = {
    'administrador':    ['administrador', 'gestor_secretaria', 'coordenador', 'administrativo', 'profissional'],
    'gestor_secretaria': ['gestor_secretaria', 'coordenador', 'administrativo', 'profissional'],  # Gestor Central pode editar perfil (exceto admin)
    'coordenador':      ['coordenador', 'administrativo', 'profissional'],
}

def _perfis_disponiveis():
    """Retorna dict {chave: label} dos perfis que o usuário logado pode atribuir."""
    permitidos = _PERFIS_PERMITIDOS.get(current_user.perfil, [])
    return {k: v for k, v in PERFIS.items() if k in permitidos}

def _pode_ver_usuario(usuario):
    """Verifica se o usuário logado tem permissão para ver/editar determinado usuário."""
    if current_user.pode('gerenciar_usuarios'):
        return True
    if usuario.perfil == 'administrador':
        return False  # Só administrador pode ver/editar outro administrador
    return (
        current_user.perfil in ('gestor_secretaria', 'coordenador')
        or current_user.pode('cadastrar_usuario')
    )


# Campos do formulário de cadastro/edição de usuário
# (Dados profissionais — CBO, vínculo, carga horária etc. — ficam no modal de vínculo com unidade)
_CAMPOS_PROF = [
    'cpf', 'cns', 'sexo', 'nome_mae', 'nome_pai',
    'nacionalidade', 'uf_nasc', 'municipio_nasc', 'pais_origem',
    'rg', 'rg_uf', 'rg_orgao', 'escolaridade',
    'end_logradouro', 'end_numero', 'end_complemento',
    'end_bairro', 'end_municipio', 'end_uf', 'end_cep',
    'telefone', 'whatsapp',
    # Registro no conselho de classe e matrícula ficam no cadastro pois são fixos do profissional
    'reg_conselho', 'orgao_emissor', 'matricula',
]

_DATAS = {
    'data_nasc':      'data_nasc',
    'dt_entrada_pais': 'dt_entrada_pais',
    'rg_emissao':     'rg_emissao',
}


def _parse_date(val):
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except (ValueError, TypeError):
        return None


def _normalizar_numero_matricula(numero):
    """Normaliza número da matrícula para comparação sem duplicidade."""
    return ' '.join((numero or '').strip().upper().split())


def _preencher_usuario(u, form):
    for campo in _CAMPOS_PROF:
        val = form.get(campo, '').strip() or None
        setattr(u, campo, val)
    for form_key, attr in _DATAS.items():
        setattr(u, attr, _parse_date(form.get(form_key, '')))
    ch = form.get('carga_horaria', '')
    u.carga_horaria = int(ch) if ch.isdigit() else None
    fe = form.get('frequenta_escola')
    u.frequenta_escola = True if fe == '1' else (False if fe == '0' else None)


@usuarios_bp.route('/')
@login_required
def listar():
    if not current_user.pode('cadastrar_usuario') and not current_user.pode('gerenciar_usuarios'):
        abort(403)

    page = request.args.get('page', 1, type=int)
    per_page = min(max(request.args.get('per_page', 50, type=int), 10), 200)
    q_busca = (request.args.get('q') or '').strip()

    # Administradores não aparecem para quem não pode gerenciá-los (evita lista “óbvia” para apoio).
    # Quem tem gerenciar_usuários (perfil Administrador na matriz padrão) vê todos, inclusive outros admins.
    query = Usuario.query
    if not current_user.pode('gerenciar_usuarios'):
        query = query.filter(Usuario.perfil != 'administrador')

    if q_busca:
        like = f'%{q_busca}%'
        query = query.filter(
            or_(Usuario.nome.ilike(like), Usuario.email.ilike(like))
        )

    query = query.order_by(Usuario.nome)
    paginacao = query.paginate(page=page, per_page=per_page, error_out=False)
    usuarios = paginacao.items

    pode_cadastrar = current_user.pode('cadastrar_usuario')
    return render_template(
        'usuarios/listar.html',
        usuarios=usuarios,
        perfis=PERFIS,
        pode_cadastrar=pode_cadastrar,
        is_admin=current_user.pode('gerenciar_usuarios'),
        paginacao=paginacao,
        q_busca=q_busca,
    )


@usuarios_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if not current_user.pode('cadastrar_usuario'):
        abort(403)

    perfis_disponiveis = _perfis_disponiveis()

    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        # Se não tiver @, adiciona o domínio padrão
        if '@' not in email:
            email = email + '@sorocaba.sp.gov.br'
        if Usuario.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado.', 'danger')
            return redirect(url_for('usuarios.novo'))

        perfil_solicitado = request.form.get('perfil', 'profissional')
        # Garante que não consiga atribuir perfil acima do permitido
        if perfil_solicitado not in perfis_disponiveis:
            perfil_solicitado = list(perfis_disponiveis.keys())[-1]

        u = Usuario(
            nome=request.form['nome'].strip(),
            email=email,
            perfil=perfil_solicitado,
        )
        # Senha inicial = CPF (só dígitos). Fallback: token aleatório se CPF não informado.
        cpf_raw = request.form.get('cpf', '').strip()
        senha_inicial = ''.join(c for c in cpf_raw if c.isdigit()) or __import__('secrets').token_urlsafe(8)
        u.set_senha(senha_inicial)
        _preencher_usuario(u, request.form)
        db.session.add(u)
        db.session.commit()
        flash(f'Usuário {u.nome} criado com sucesso!', 'success')
        return redirect(url_for('usuarios.editar', id=u.id))

    # Busca CBOs ativos do banco de dados
    cbos_ativos = [(c.codigo, c.descricao) for c in CBO.query.filter_by(ativo=True).order_by(CBO.codigo).all()]
    return render_template('usuarios/form.html', usuario=None,
                           perfis=perfis_disponiveis,
                           escolaridades=ESCOLARIDADES,
                           cbos=cbos_ativos,
                           matriculas=[],
                           pode_alterar_perfil=True,
                           is_admin=current_user.pode('gerenciar_usuarios'))


@usuarios_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    if not current_user.pode('cadastrar_usuario') and not current_user.pode('gerenciar_usuarios'):
        abort(403)

    usuario = Usuario.query.get_or_404(id)

    # Verifica se tem acesso a este usuário específico (exceto admin que tem acesso a todos)
    if not _pode_ver_usuario(usuario):
        abort(403)

    perfis_disponiveis = _perfis_disponiveis()
    is_admin = current_user.pode('gerenciar_usuarios')
    # Admin pode mudar qualquer perfil; outros só dentro do seu escopo
    pode_alterar_perfil = is_admin or (usuario.perfil in perfis_disponiveis)

    if request.method == 'POST':
        try:
            usuario.nome = request.form['nome'].strip()

            # Apenas administrador pode alterar o e-mail
            if is_admin:
                novo_email = request.form.get('email', '').strip().lower()
                # Se não tiver @, adiciona o domínio padrão
                if '@' not in novo_email:
                    novo_email = novo_email + '@sorocaba.sp.gov.br'
                # Verifica se o novo e-mail já existe (exceto o próprio usuário)
                if novo_email != usuario.email:
                    if Usuario.query.filter(Usuario.email == novo_email, Usuario.id != usuario.id).first():
                        flash('Este e-mail já está cadastrado para outro usuário.', 'danger')
                        return redirect(url_for('usuarios.editar', id=usuario.id))
                    usuario.email = novo_email

            novo_perfil = request.form.get('perfil', usuario.perfil)
            if pode_alterar_perfil and (is_admin or novo_perfil in perfis_disponiveis):
                usuario.perfil = novo_perfil

            if is_admin:
                usuario.ativo = request.form.get('ativo') == 'on'

            nova_senha = request.form.get('nova_senha', '')
            if nova_senha:
                usuario.set_senha(nova_senha)
            _preencher_usuario(usuario, request.form)
            db.session.commit()
            flash('Usuário atualizado!', 'success')
            return redirect(url_for('usuarios.editar', id=usuario.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar usuário: {str(e)}', 'danger')
            # Em caso de erro, também volta para a tela de edição
            return redirect(url_for('usuarios.editar', id=usuario.id))

    matriculas = (MatriculaProfissional.query
                  .filter_by(usuario_id=usuario.id)
                  .order_by(MatriculaProfissional.ativo.desc(), MatriculaProfissional.numero)
                  .all())
    # Busca CBOs ativos do banco de dados
    cbos_ativos = [(c.codigo, c.descricao) for c in CBO.query.filter_by(ativo=True).order_by(CBO.codigo).all()]
    return render_template('usuarios/form.html', usuario=usuario,
                           perfis=perfis_disponiveis if not is_admin else PERFIS,
                           escolaridades=ESCOLARIDADES,
                           cbos=cbos_ativos,
                           matriculas=matriculas,
                           pode_alterar_perfil=pode_alterar_perfil,
                           is_admin=is_admin)


@usuarios_bp.route('/<int:id>/fichas')
@login_required
def historico_fichas(id):
    if not current_user.pode('cadastrar_usuario') and not current_user.pode('gerenciar_usuarios'):
        abort(403)
    usuario = Usuario.query.get_or_404(id)
    if not _pode_ver_usuario(usuario):
        abort(403)
    fichas  = (FichaCnesVinculo.query
               .filter_by(usuario_id=id)
               .order_by(FichaCnesVinculo.gerado_em.desc())
               .all())
    # Pre-montar links de e-mail para cada ficha
    links_email = {}
    for f in fichas:
        assunto = quote(f'{"Vinculação" if f.tipo == "cadastro" else "Desvinculação"} CNES — {usuario.nome} — {f.unidade.nome}')
        corpo   = quote(_montar_corpo_email_ficha(f))
        dest    = 'cnes@sorocaba.sp.gov.br,suportesis.sorocaba@sorocaba.sp.gov.br'
        links_email[f.id] = f'mailto:{dest}?subject={assunto}&body={corpo}'

    return render_template('usuarios/historico_fichas.html',
                           usuario=usuario, fichas=fichas, links_email=links_email)


@usuarios_bp.route('/<int:id>/ficha-cnes')
@login_required
def ficha_cnes(id):
    if not current_user.pode('cadastrar_usuario') and not current_user.pode('gerenciar_usuarios'):
        abort(403)
    usuario = Usuario.query.get_or_404(id)
    if not _pode_ver_usuario(usuario):
        abort(403)
    unidades = (
        Unidade.query
        .join(Unidade.usuarios)
        .filter(
            db.text('usuario_unidade.usuario_id = :uid AND usuario_unidade.ativo = true'),
        )
        .params(uid=id)
        .all()
    )
    # Pré-monta os links mailto para cada unidade
    links_email = {}
    for u in unidades:
        assunto = quote(f'Vinculação CNES — {usuario.nome} — {u.nome}')
        corpo   = quote(_montar_corpo_email(usuario, u))
        links_email[u.id] = f'mailto:cnes@sorocaba.sp.gov.br?subject={assunto}&body={corpo}'

    return render_template('usuarios/ficha_cnes.html',
                           usuario=usuario,
                           unidades=unidades,
                           links_email=links_email,
                           vinculos=VINCULOS,
                           tipos_vinculo=TIPOS_VINCULO,
                           escolaridades=ESCOLARIDADES)


# ─── API de Matrículas ─────────────────────────────────────────────────────────

@usuarios_bp.route('/<int:id>/matriculas', methods=['POST'])
@login_required
def criar_matricula(id):
    if not current_user.pode('cadastrar_usuario') and not current_user.pode('gerenciar_usuarios'):
        abort(403)
    usuario = Usuario.query.get_or_404(id)
    if not _pode_ver_usuario(usuario):
        abort(403)

    data = request.get_json() or {}
    numero = (data.get('numero') or '').strip()
    tipo_vinculo = data.get('tipo_vinculo') or None
    
    # Matrícula é opcional apenas para "Contrato por Prazo Determinado" (tipo_vinculo = '3')
    if not numero and tipo_vinculo != '3':
        return jsonify(ok=False, erro='Número da matrícula é obrigatório.')
    
    # Se tipo_vinculo for '3' e não tiver número, salva como "Sem Matrícula"
    if tipo_vinculo == '3' and not numero:
        numero = 'Sem Matrícula'

    numero_norm = _normalizar_numero_matricula(numero)
    existente = (MatriculaProfissional.query
                 .filter_by(usuario_id=id)
                 .all())
    if any(_normalizar_numero_matricula(m.numero) == numero_norm for m in existente):
        return jsonify(ok=False, erro='Esta matrícula já está cadastrada para este usuário.')

    m = MatriculaProfissional(
        usuario_id    = id,
        numero        = numero,
        vinculo       = data.get('vinculo') or None,
        tipo_vinculo  = tipo_vinculo,
        cbo           = data.get('cbo') or None,
        reg_conselho  = (data.get('reg_conselho') or '').strip() or None,
        orgao_emissor = (data.get('orgao_emissor') or '').strip() or None,
        ativo         = bool(data.get('ativo', True)),
    )
    db.session.add(m)
    db.session.commit()
    return jsonify(ok=True, id=m.id)


@usuarios_bp.route('/<int:id>/matriculas/json')
@login_required
def listar_matriculas_json(id):
    """Retorna as matrículas ativas de um usuário em JSON (para o modal de vínculo)."""
    usuario = Usuario.query.get_or_404(id)
    matriculas = (MatriculaProfissional.query
                  .filter_by(usuario_id=id, ativo=True)
                  .order_by(MatriculaProfissional.numero)
                  .all())
    return jsonify(matriculas=[{
        'id':           m.id,
        'numero':       m.numero,
        'cbo':          m.cbo or '',
        'cbo_label':    m.cbo_label,
        'vinculo':      m.vinculo or '',
        'tipo_vinculo': m.tipo_vinculo or '',
        'reg_conselho': m.reg_conselho or '',
        'orgao_emissor': m.orgao_emissor or '',
    } for m in matriculas])


@usuarios_bp.route('/<int:uid>/matriculas/<int:mid>', methods=['PUT', 'DELETE'])
@login_required
def atualizar_matricula(uid, mid):
    if not current_user.pode('cadastrar_usuario') and not current_user.pode('gerenciar_usuarios'):
        abort(403)
    usuario = Usuario.query.get_or_404(uid)
    if not _pode_ver_usuario(usuario):
        abort(403)

    m = MatriculaProfissional.query.filter_by(id=mid, usuario_id=uid).first_or_404()

    if request.method == 'DELETE':
        db.session.delete(m)
        db.session.commit()
        return jsonify(ok=True)

    data = request.get_json() or {}

    numero = (data.get('numero') or '').strip()
    tipo_vinculo = data.get('tipo_vinculo') or None
    
    # Matrícula é opcional apenas para "Contrato por Prazo Determinado" (tipo_vinculo = '3')
    if not numero and tipo_vinculo != '3':
        return jsonify(ok=False, erro='Número da matrícula é obrigatório.')
    
    # Se tipo_vinculo for '3' e não tiver número, salva como "Sem Matrícula"
    if tipo_vinculo == '3' and not numero:
        numero = 'Sem Matrícula'

    numero_norm = _normalizar_numero_matricula(numero)
    existente = (MatriculaProfissional.query
                 .filter(MatriculaProfissional.usuario_id == uid, MatriculaProfissional.id != mid)
                 .all())
    if any(_normalizar_numero_matricula(x.numero) == numero_norm for x in existente):
        return jsonify(ok=False, erro='Esta matrícula já está cadastrada para este usuário.')

    m.numero        = numero
    m.vinculo       = data.get('vinculo') or None
    m.tipo_vinculo  = tipo_vinculo
    m.cbo           = data.get('cbo') or None
    m.reg_conselho  = (data.get('reg_conselho') or '').strip() or None
    m.orgao_emissor = (data.get('orgao_emissor') or '').strip() or None
    m.ativo         = bool(data.get('ativo', True))
    db.session.commit()
    return jsonify(ok=True)
