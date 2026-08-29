"""Atendimento TARM - Registro de Chamada e Ocorrências."""
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app import db
from app.models.ocorrencia import Ocorrencia, STATUS_AGUARDANDO, STATUS_EM_ATENDIMENTO, STATUS_FINALIZADA, STATUS_ENVIADA_MEDICO, STATUS_REGULADA
from app.models.usuario import Usuario, CBOS
from app.models.tipo_ligacao import TipoLigacao
from app.models.origem_ligacao import OrigemLigacao
from app.models.algoritmo_acolhimento import AlgoritmoAcolhimento
from app.models.pergunta_protocolo import PerguntaProtocolo
from app.models.opcao_resposta import OpcaoResposta
from app.models.unidade_saude import UnidadeSaude
from app.models.tipo_ocorrencia import TipoOcorrencia
from app.models.motivo_ocorrencia import MotivoOcorrencia
from app.models.tipo_unidade_samu import TipoUnidadeSamu
from app.models.classificacao_risco import ClassificacaoRisco
from app.models.unidade_samu import UnidadeSamu
from app.models.intercorrencia import Intercorrencia
from app.models.veiculo import Veiculo
from app.models.equipe import Equipe, EquipeMembro
from app.utils import br_fone

atendimento_bp = Blueprint('atendimento', __name__, url_prefix='/atendimento')


def _digitos_telefone(val):
    """Retorna apenas dígitos do telefone."""
    if not val:
        return ''
    return ''.join(c for c in str(val) if c.isdigit())


def _proximo_numero_ocorrencia():
    """Gera próximo número no formato AAMMDD0000 (ano 2 dígitos, mês, dia, sequência)."""
    hoje = date.today()
    prefixo = hoje.strftime('%y%m%d')  # 250307
    ultima = Ocorrencia.query.filter(Ocorrencia.numero.like(prefixo + '%')).order_by(Ocorrencia.numero.desc()).first()
    seq = 1
    if ultima and len(ultima.numero) >= 10:
        try:
            seq = int(ultima.numero[-4:]) + 1
        except ValueError:
            pass
    return f'{prefixo}{seq:04d}'


def _ocorrencia_editavel(status):
    """Status que permitem edição pelo telefonista (inclui enviada ao médico)."""
    return status in (STATUS_AGUARDANDO, STATUS_EM_ATENDIMENTO, STATUS_ENVIADA_MEDICO)


@atendimento_bp.route('/registro-chamada')
@atendimento_bp.route('/registro-chamada/<int:ocorrencia_id>')
@login_required
def registro_chamada(ocorrencia_id=None):
    """Tela única do TARM: registro + ocorrências em aberto + não reguladas."""
    ocorrencia = None
    bloqueada = False
    editando_por_usuario = None
    pode_assumir = False

    if ocorrencia_id:
        ocorrencia = Ocorrencia.query.get_or_404(ocorrencia_id)
        if _ocorrencia_editavel(ocorrencia.status):
            outro = ocorrencia.editando_por
            if ocorrencia.editando_por_id is None:
                ocorrencia.editando_por_id = current_user.id
                ocorrencia.editando_desde = datetime.utcnow()
                db.session.commit()
            elif ocorrencia.editando_por_id != current_user.id:
                bloqueada = True
                editando_por_usuario = outro.usuario if outro else 'outro atendente'
                pode_assumir = True

    algoritmos = AlgoritmoAcolhimento.query.filter_by(ativo=True).order_by(AlgoritmoAcolhimento.ordem, AlgoritmoAcolhimento.nome).all()
    tipos_ligacao = TipoLigacao.query.filter_by(ativo=True).order_by(TipoLigacao.nome).all()
    origens = OrigemLigacao.query.filter_by(ativo=True).order_by(OrigemLigacao.nome).all()

    ocorrencias_abertas = Ocorrencia.query.filter(
        Ocorrencia.status.in_([STATUS_AGUARDANDO, STATUS_EM_ATENDIMENTO])
    ).order_by(Ocorrencia.atualizado_em.desc()).all()

    ocorrencias_nao_reguladas = Ocorrencia.query.filter_by(status=STATUS_ENVIADA_MEDICO)\
        .order_by(Ocorrencia.enviada_medico_em.desc()).all()

    unidades_saude = UnidadeSaude.query.filter_by(ativo=True).order_by(UnidadeSaude.nome).all()

    return render_template('atendimento/registro_chamada.html',
        ocorrencia=ocorrencia, algoritmos=algoritmos, tipos_ligacao=tipos_ligacao, origens=origens, unidades_saude=unidades_saude,
        ocorrencias_abertas=ocorrencias_abertas, ocorrencias_nao_reguladas=ocorrencias_nao_reguladas,
        bloqueada=bloqueada, editando_por_usuario=editando_por_usuario, pode_assumir=pode_assumir)


@atendimento_bp.route('/api/criar-ocorrencia', methods=['POST'])
@login_required
def api_criar_ocorrencia():
    """Cria ocorrência ao digitar telefone e pressionar Enter/Tab."""
    data = request.get_json() or {}
    telefone = _digitos_telefone(data.get('telefone', ''))
    if len(telefone) < 10:
        return jsonify(erro='Informe um telefone válido (10 ou 11 dígitos)'), 400

    # Verifica última ligação para pré-preencher: origem, unidade (se origem for UBS), endereço
    ultima = Ocorrencia.query.filter_by(telefone=telefone).order_by(Ocorrencia.criado_em.desc()).first()

    numero = _proximo_numero_ocorrencia()
    o = Ocorrencia(
        numero=numero,
        telefone=telefone,
        status=STATUS_EM_ATENDIMENTO,
        atendente_id=current_user.id,
        iniciada_em=datetime.utcnow(),
        nome_solicitante=ultima.nome_solicitante if ultima else None,
        origem_ligacao_id=ultima.origem_ligacao_id if ultima else None,
        unidade_saude_id=ultima.unidade_saude_id if ultima else None,
        end_cidade=ultima.end_cidade if ultima else None,
        end_uf=ultima.end_uf if ultima else None,
        end_logradouro=ultima.end_logradouro if ultima else None,
        end_numero=ultima.end_numero if ultima else None,
        end_complemento=ultima.end_complemento if ultima else None,
        end_bairro=ultima.end_bairro if ultima else None,
        end_cep=ultima.end_cep if ultima else None,
    )
    db.session.add(o)
    db.session.commit()
    return jsonify(ok=True, id=o.id, numero=o.numero, redirect=url_for('atendimento.registro_chamada', ocorrencia_id=o.id))


@atendimento_bp.route('/api/historico-telefone')
@login_required
def api_historico_telefone():
    """Retorna últimas 5 ligações do número."""
    telefone = _digitos_telefone(request.args.get('telefone', ''))
    if len(telefone) < 10:
        return jsonify(itens=[])

    itens = Ocorrencia.query.filter_by(telefone=telefone)\
        .order_by(Ocorrencia.criado_em.desc()).limit(5).all()
    from app.utils import br_datetime_local
    return jsonify(itens=[{
        'data_hora': br_datetime_local(i.iniciada_em) if i.iniciada_em else '',
        'nome_solicitante': i.nome_solicitante or '—',
        'tipo_ligacao': i.tipo_ligacao.nome if i.tipo_ligacao else '',
        'apelido': i.apelido or '',
    } for i in itens])


@atendimento_bp.route('/api/unidade-saude/<int:unidade_id>')
@login_required
def api_unidade_saude(unidade_id):
    """Retorna endereço da unidade de saúde para preenchimento automático."""
    u = UnidadeSaude.query.get_or_404(unidade_id)
    return jsonify(
        cidade=u.cidade or u.municipio or '',
        uf=u.uf or '',
        logradouro=u.logradouro or u.endereco or '',
        numero=u.numero or '',
        complemento=u.complemento or '',
        bairro=u.bairro or '',
        cep=u.cep or '',
    )


@atendimento_bp.route('/api/algoritmo-perguntas/<int:algoritmo_id>')
@login_required
def api_algoritmo_perguntas(algoritmo_id):
    """Retorna perguntas do algoritmo para o formulário dinâmico."""
    algo = AlgoritmoAcolhimento.query.get_or_404(algoritmo_id)
    perguntas = []
    for p in algo.perguntas.order_by(PerguntaProtocolo.ordem).all():
        opcoes = [{'id': o.id, 'texto': o.texto, 'pontuacao': o.pontuacao} for o in p.opcoes.order_by(OpcaoResposta.ordem).all()]
        perguntas.append({
            'id': p.id,
            'enunciado': p.enunciado,
            'tipo': p.tipo,
            'opcoes': opcoes,
        })
    return jsonify(perguntas=perguntas, algoritmo_nome=algo.nome)


@atendimento_bp.route('/api/assumir-ocorrencia/<int:ocorrencia_id>', methods=['POST'])
@login_required
def api_assumir_ocorrencia(ocorrencia_id):
    """Assume a edição da ocorrência (retira do outro atendente)."""
    o = Ocorrencia.query.get_or_404(ocorrencia_id)
    if not _ocorrencia_editavel(o.status):
        return jsonify(erro='Ocorrência não pode ser editada.'), 400
    o.editando_por_id = current_user.id
    o.editando_desde = datetime.utcnow()
    db.session.commit()
    return jsonify(ok=True, redirect=url_for('atendimento.registro_chamada', ocorrencia_id=o.id))


@atendimento_bp.route('/registro-chamada/<int:ocorrencia_id>/salvar', methods=['POST'])
@login_required
def salvar_ocorrencia(ocorrencia_id):
    """Salva/atualiza ocorrência (formulário completo)."""
    o = Ocorrencia.query.get_or_404(ocorrencia_id)
    if not _ocorrencia_editavel(o.status):
        flash('Esta ocorrência já foi finalizada. Apenas visualização.', 'warning')
        return redirect(url_for('atendimento.registro_chamada', ocorrencia_id=o.id))

    if o.editando_por_id is not None and o.editando_por_id != current_user.id:
        flash('Outro atendente assumiu esta ocorrência. Suas alterações não foram salvas. Atualize a página.', 'danger')
        return redirect(url_for('atendimento.registro_chamada', ocorrencia_id=o.id))

    acao = request.form.get('acao')  # aguardando | finalizar | enviar_medico
    if acao == 'aguardando':
        o.status = STATUS_AGUARDANDO
        _preencher_ocorrencia(o)
        o.editando_por_id = None
        o.editando_desde = None
        db.session.commit()
        flash(f'Ocorrência {o.numero} salva como "Em espera" para conclusão posterior.', 'success')
        return redirect(url_for('atendimento.registro_chamada'))
    elif acao == 'finalizar':
        _preencher_ocorrencia(o)  # aplica tipo_ligacao_id do formulário antes de validar
        tipo = o.tipo_ligacao
        if not tipo or not getattr(tipo, 'permite_encerrar_direto', False):
            flash('O tipo de ligação selecionado não permite finalizar o atendimento diretamente.', 'warning')
            return redirect(url_for('atendimento.registro_chamada', ocorrencia_id=o.id))
        o.status = STATUS_FINALIZADA
        o.finalizada_em = datetime.utcnow()
        o.editando_por_id = None
        o.editando_desde = None
        db.session.commit()
        flash(f'Atendimento {o.numero} finalizado.', 'success')
        return redirect(url_for('atendimento.registro_chamada'))
    elif acao == 'enviar_medico':
        o.status = STATUS_ENVIADA_MEDICO
        o.enviada_medico_em = datetime.utcnow()
        o.finalizada_em = o.finalizada_em or datetime.utcnow()
        _preencher_ocorrencia(o)
        o.editando_por_id = None
        o.editando_desde = None
        db.session.commit()
        flash(f'Ocorrência {o.numero} enviada ao médico regulador.', 'success')
        return redirect(url_for('atendimento.registro_chamada'))

    # Apenas salvar (sem ação)
    _preencher_ocorrencia(o)
    db.session.commit()
    flash('Registro salvo.', 'success')
    return redirect(url_for('atendimento.registro_chamada', ocorrencia_id=o.id))


def _preencher_ocorrencia(o):
    """Preenche campos da ocorrência a partir do request.form."""
    o.nome_solicitante = request.form.get('nome_solicitante', '').strip() or None
    o.apelido = request.form.get('apelido', '').strip() or None
    o.motivo_queixa = request.form.get('motivo_queixa', '').strip() or None
    o.algoritmo_id = request.form.get('algoritmo_id') or None
    if o.algoritmo_id:
        try:
            o.algoritmo_id = int(o.algoritmo_id)
        except (ValueError, TypeError):
            o.algoritmo_id = None
    o.tipo_ligacao_id = request.form.get('tipo_ligacao_id') or None
    if o.tipo_ligacao_id:
        try:
            o.tipo_ligacao_id = int(o.tipo_ligacao_id)
        except (ValueError, TypeError):
            o.tipo_ligacao_id = None
    o.origem_ligacao_id = request.form.get('origem_ligacao_id') or None
    if o.origem_ligacao_id:
        try:
            o.origem_ligacao_id = int(o.origem_ligacao_id)
        except (ValueError, TypeError):
            o.origem_ligacao_id = None
    o.end_cidade = request.form.get('end_cidade', '').strip() or None
    o.end_uf = request.form.get('end_uf', '').strip() or None
    o.end_logradouro = request.form.get('end_logradouro', '').strip() or None
    o.end_numero = request.form.get('end_numero', '').strip() or None
    o.end_complemento = request.form.get('end_complemento', '').strip() or None
    o.end_bairro = request.form.get('end_bairro', '').strip() or None
    o.end_cep = request.form.get('end_cep', '').replace('-', '').strip() or None
    o.unidade_saude_id = request.form.get('unidade_saude_id', type=int) or None
    # Respostas do algoritmo (JSON)
    resp = {}
    for k, v in request.form.items():
        if k.startswith('algo_') and v:
            try:
                pid = int(k.replace('algo_', ''))
                resp[str(pid)] = v
            except ValueError:
                pass
    o.respostas_algoritmo = resp
    # Pacientes
    p_list = []
    idx = 0
    while True:
        nome = request.form.get(f'paciente_{idx}_nome', '').strip()
        sexo = request.form.get(f'paciente_{idx}_sexo', '').strip()
        idade = request.form.get(f'paciente_{idx}_idade', '').strip()
        idade_unidade = request.form.get(f'paciente_{idx}_idade_unidade', 'ano').strip() or 'ano'
        if idade_unidade not in ('ano', 'mes', 'dia'):
            idade_unidade = 'ano'
        if not nome and not sexo and not idade:
            idx += 1
            if idx > 50:
                break
            continue
        p_list.append({'nome': nome or None, 'sexo': sexo or None, 'idade': idade or None, 'idade_unidade': idade_unidade})
        idx += 1
        if idx > 50:
            break
    o.pacientes = p_list if p_list else []


def _preencher_endereco_pacientes(o):
    """Preenche endereço e pacientes (para regulação médica)."""
    o.end_cidade = request.form.get('end_cidade', '').strip() or None
    o.end_uf = request.form.get('end_uf', '').strip() or None
    o.end_logradouro = request.form.get('end_logradouro', '').strip() or None
    o.end_numero = request.form.get('end_numero', '').strip() or None
    o.end_complemento = request.form.get('end_complemento', '').strip() or None
    o.end_bairro = request.form.get('end_bairro', '').strip() or None
    o.end_cep = request.form.get('end_cep', '').replace('-', '').strip() or None
    o.unidade_saude_id = request.form.get('unidade_saude_id', type=int) or None
    p_list = []
    idx = 0
    while True:
        nome = request.form.get(f'paciente_{idx}_nome', '').strip()
        sexo = request.form.get(f'paciente_{idx}_sexo', '').strip()
        idade = request.form.get(f'paciente_{idx}_idade', '').strip()
        idade_unidade = request.form.get(f'paciente_{idx}_idade_unidade', 'ano').strip() or 'ano'
        if idade_unidade not in ('ano', 'mes', 'dia'):
            idade_unidade = 'ano'
        if not nome and not sexo and not idade:
            idx += 1
            if idx > 50:
                break
            continue
        p_list.append({'nome': nome or None, 'sexo': sexo or None, 'idade': idade or None, 'idade_unidade': idade_unidade})
        idx += 1
        if idx > 50:
            break
    o.pacientes = p_list if p_list else []


# ══════════════════════════════════════════════════════════
#  REGULAÇÃO MÉDICA (médico regulador)
# ══════════════════════════════════════════════════════════

def _exigir_regulacao_medica():
    """Exige permissão de regulação médica."""
    if not current_user.pode('regulacao_medica'):
        flash('Acesso negado. Apenas médico regulador ou administrador pode acessar Regulação Médica.', 'warning')
        return redirect(url_for('dashboard.index'))
    return None


@atendimento_bp.route('/regulacao-medica')
@login_required
def regulacao_medica():
    """Duas tabelas: Aguardando Regulação e Ocorrências Reguladas."""
    r = _exigir_regulacao_medica()
    if r:
        return r
    aguardando = Ocorrencia.query.filter_by(status=STATUS_ENVIADA_MEDICO)\
        .options(db.joinedload(Ocorrencia.atendente), db.joinedload(Ocorrencia.algoritmo))\
        .order_by(Ocorrencia.enviada_medico_em.asc()).all()
    reguladas = Ocorrencia.query.filter_by(status=STATUS_REGULADA)\
        .options(
            db.joinedload(Ocorrencia.atendente),
            db.joinedload(Ocorrencia.algoritmo),
            db.joinedload(Ocorrencia.unidade_samu),
        )\
        .order_by(Ocorrencia.regulada_em.desc()).all()
    tipos_map = {t.id: t for t in TipoUnidadeSamu.query.all()}
    classes_map = {c.id: c for c in ClassificacaoRisco.query.all()}
    return render_template('atendimento/regulacao_medica_listar.html',
        aguardando=aguardando,
        reguladas=reguladas,
        tipos_map=tipos_map,
        classes_map=classes_map,
    )


@atendimento_bp.route('/regulacao-medica/<numero_ocorrencia>', methods=['GET', 'POST'])
@login_required
def regulacao_medica_atender(numero_ocorrencia):
    """Formulário para o médico regular a ocorrência (numero = AAMMDD0000)."""
    r = _exigir_regulacao_medica()
    if r:
        return r
    ocorrencia = Ocorrencia.query.filter_by(numero=numero_ocorrencia).first_or_404()
    if ocorrencia.status not in (STATUS_ENVIADA_MEDICO, STATUS_REGULADA):
        flash(f'Ocorrência {ocorrencia.numero} não está disponível para regulação.', 'warning')
        return redirect(url_for('atendimento.regulacao_medica'))

    tipos_ocorrencia = TipoOcorrencia.query.filter_by(ativo=True).order_by(TipoOcorrencia.nome).all()
    motivos = MotivoOcorrencia.query.filter_by(ativo=True).order_by(MotivoOcorrencia.nome).all()
    # Apenas tipos que têm viaturas cadastradas nas unidades SAMU
    tipos_unidade = TipoUnidadeSamu.query.join(UnidadeSamu, UnidadeSamu.tipo_unidade_id == TipoUnidadeSamu.id)\
        .filter(UnidadeSamu.tipo_registro == 'viatura', UnidadeSamu.ativo == True, TipoUnidadeSamu.ativo == True)\
        .distinct().order_by(TipoUnidadeSamu.ordem_prioridade, TipoUnidadeSamu.sigla).all()
    classificacoes = ClassificacaoRisco.query.filter_by(ativo=True).order_by(ClassificacaoRisco.ordem).all()
    unidades_saude = UnidadeSaude.query.filter_by(ativo=True).order_by(UnidadeSaude.nome).all()
    origens = OrigemLigacao.query.filter_by(ativo=True).order_by(OrigemLigacao.nome).all()

    if request.method == 'POST':
        _preencher_endereco_pacientes(ocorrencia)
        ocorrencia.tipo_ocorrencia_id = request.form.get('tipo_ocorrencia_id', type=int) or None
        ocorrencia.motivo_ocorrencia_id = request.form.get('motivo_ocorrencia_id', type=int) or None
        ocorrencia.avaliacao_medica_historico = request.form.get('avaliacao_medica_historico', '').strip() or None
        ocorrencia.decisao_protocolo = request.form.get('decisao_protocolo', '').strip() or None
        # decisoes_medicas: JSON array de {tipo_unidade_id, classificacao_risco_id}
        dec = []
        for k, v in request.form.items():
            if k.startswith('decisao_') and v:
                try:
                    parts = k.replace('decisao_', '').split('_')
                    if len(parts) >= 2:
                        tipo_id = int(parts[0])
                        class_id = int(parts[1])
                        dec.append({'tipo_unidade_id': tipo_id, 'classificacao_risco_id': class_id})
                except (ValueError, IndexError):
                    pass
        ocorrencia.decisoes_medicas = dec
        ocorrencia.status = STATUS_REGULADA
        ocorrencia.regulada_por_id = current_user.id
        ocorrencia.regulada_em = datetime.utcnow()
        db.session.commit()
        flash(f'Ocorrência {ocorrencia.numero} regulada com sucesso.', 'success')
        return redirect(url_for('atendimento.regulacao_medica'))

    return render_template('atendimento/regulacao_medica_atender.html',
        ocorrencia=ocorrencia,
        tipos_ocorrencia=tipos_ocorrencia,
        motivos=motivos,
        tipos_unidade=tipos_unidade,
        classificacoes=classificacoes,
        unidades_saude=unidades_saude,
        origens=origens,
    )


# ══════════════════════════════════════════════════════════
#  DESPACHO DE VIATURAS (rádio operador)
# ══════════════════════════════════════════════════════════

def _exigir_despacho_viaturas():
    """Exige permissão de despacho de viaturas."""
    if not current_user.pode('despacho_viaturas'):
        flash('Acesso negado. Apenas rádio operador ou administrador pode acessar Despacho de Viaturas.', 'warning')
        return redirect(url_for('dashboard.index'))
    return None


@atendimento_bp.route('/despacho-viaturas')
@login_required
def despacho_viaturas():
    """Duas tabelas: Aguardando Atendimento e Em Ocorrência."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    tipos_map = {t.id: t for t in TipoUnidadeSamu.query.all()}
    classes_map = {c.id: c for c in ClassificacaoRisco.query.all()}
    # Aguardando: ocorrências reguladas sem viatura, expandir cada decisão em uma linha
    ocorrencias_aguardando = Ocorrencia.query.options(
        db.joinedload(Ocorrencia.origem_ligacao),
    ).filter(
        Ocorrencia.status == STATUS_REGULADA,
        Ocorrencia.unidade_samu_id.is_(None),
        Ocorrencia.decisoes_medicas.isnot(None),
    ).all()
    aguardando_rows = []
    for o in ocorrencias_aguardando:
        decisoes = o.decisoes_medicas or []
        for d in decisoes:
            tipo_id = d.get('tipo_unidade_id')
            class_id = d.get('classificacao_risco_id')
            if tipo_id and class_id:
                t = tipos_map.get(tipo_id)
                c = classes_map.get(class_id)
                if t and c:
                    aguardando_rows.append({
                        'ocorrencia': o,
                        'tipo': t,
                        'classificacao': c,
                    })
    # Ordenar: ordem_prioridade do tipo, depois ordem da classificação
    aguardando_rows.sort(key=lambda r: (
        r['tipo'].ordem_prioridade or 999,
        r['classificacao'].ordem or 999,
    ))
    # Em Ocorrência: ocorrências com viatura vinculada
    em_ocorrencia = Ocorrencia.query.options(
        db.joinedload(Ocorrencia.unidade_samu),
        db.joinedload(Ocorrencia.origem_ligacao),
    ).filter(
        Ocorrencia.status == STATUS_REGULADA,
        Ocorrencia.unidade_samu_id.isnot(None),
    ).order_by(Ocorrencia.regulada_em.desc()).all()
    # Ocorrências únicas para o mapa (aguardando + em ocorrência), com endereço e dados para tooltip
    def _paciente_str(pacientes):
        if not pacientes:
            return ''
        p = pacientes[0]
        nome = (p.get('nome') or '').strip()
        primeiro = (nome.split() or [''])[0]
        if primeiro:
            primeiro = primeiro[0].upper() + primeiro[1:].lower() if len(primeiro) > 1 else primeiro.upper()
        idade = p.get('idade')
        un = (p.get('idade_unidade') or 'ano')
        un_label = 'ANOS' if un == 'ano' else ('MESES' if un == 'mes' else 'DIAS')
        if idade:
            return f'{primeiro} ({idade} {un_label})' if primeiro else f'{idade} {un_label}'
        return primeiro or ''

    mapa_ids = {}
    for row in aguardando_rows:
        o = row['ocorrencia']
        if o.id not in mapa_ids and o.endereco_formatado:
            cidade_uf = ''
            if o.end_cidade:
                cidade_uf = f'{o.end_cidade}/{o.end_uf}' if o.end_uf else o.end_cidade
            elif o.end_uf:
                cidade_uf = o.end_uf
            mapa_ids[o.id] = {
                'numero': o.numero,
                'endereco': o.endereco_formatado,
                'paciente': _paciente_str(o.pacientes),
                'apelido': o.apelido or '',
                'origem': o.origem_ligacao.nome if o.origem_ligacao else '',
                'cidade_uf': cidade_uf,
                'tipo': f'{row["tipo"].sigla}',
                'cor': row['classificacao'].cor or '#6c757d',
            }
    for o in em_ocorrencia:
        if o.id not in mapa_ids and o.endereco_formatado:
            cidade_uf = ''
            if o.end_cidade:
                cidade_uf = f'{o.end_cidade}/{o.end_uf}' if o.end_uf else o.end_cidade
            elif o.end_uf:
                cidade_uf = o.end_uf
            viatura = (o.unidade_samu.apelido or o.unidade_samu.nome) if o.unidade_samu else ''
            mapa_ids[o.id] = {
                'numero': o.numero,
                'endereco': o.endereco_formatado,
                'paciente': _paciente_str(o.pacientes),
                'apelido': o.apelido or '',
                'origem': o.origem_ligacao.nome if o.origem_ligacao else '',
                'cidade_uf': cidade_uf,
                'tipo': f'Viatura: {viatura}' if viatura else '',
                'cor': '#0d6efd',
            }
    mapa_ocorrencias = list(mapa_ids.values())
    # Unidades de saúde para o mapa (com endereço para geocoding)
    unidades_saude = UnidadeSaude.query.options(
        db.joinedload(UnidadeSaude.tipo_unidade),
    ).filter_by(ativo=True).order_by(UnidadeSaude.nome).all()
    mapa_unidades_saude = []
    for u in unidades_saude:
        partes = []
        if u.endereco_completo:
            partes.append(u.endereco_completo)
        if u.cidade or u.municipio:
            partes.append(u.cidade or u.municipio)
        if u.uf:
            partes.append(u.uf)
        endereco_geo = ', '.join(partes) if partes else None
        if endereco_geo:
            mapa_unidades_saude.append({
                'nome': u.nome or '',
                'apelido': u.apelido or '',
                'tipo': u.tipo_unidade.nome if u.tipo_unidade else '',
                'endereco': endereco_geo,
                'cidade_uf': u.cidade_uf or '',
                'link_maps': u.link_google_maps or '',
            })
    intercorrencias_cancelamento = Intercorrencia.query.filter_by(ativo=True, disponivel_cancelamento=True).order_by(Intercorrencia.nome).all()
    ocorrencias_para_redirecionar = [(o.id, o.numero, o.apelido or '') for o in ocorrencias_aguardando]
    return render_template('atendimento/despacho_viaturas.html',
        aguardando_rows=aguardando_rows,
        em_ocorrencia=em_ocorrencia,
        mapa_ocorrencias=mapa_ocorrencias,
        mapa_unidades_saude=mapa_unidades_saude,
        intercorrencias_cancelamento=intercorrencias_cancelamento,
        ocorrencias_para_redirecionar=ocorrencias_para_redirecionar,
    )


@atendimento_bp.route('/despacho-viaturas/<numero_ocorrencia>', methods=['GET', 'POST'])
@login_required
def despacho_viaturas_atender(numero_ocorrencia):
    """Tela para o rádio operador: despachar viatura (aguardando) ou registrar eventos/redirecionar/cancelar (em ocorrência)."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    ocorrencia = Ocorrencia.query.options(
        db.joinedload(Ocorrencia.origem_ligacao),
        db.joinedload(Ocorrencia.tipo_ligacao),
        db.joinedload(Ocorrencia.tipo_ocorrencia),
        db.joinedload(Ocorrencia.motivo_ocorrencia),
    ).filter_by(numero=numero_ocorrencia).first_or_404()
    if ocorrencia.status != STATUS_REGULADA:
        flash(f'Ocorrência {ocorrencia.numero} não está disponível para despacho.', 'warning')
        return redirect(url_for('atendimento.despacho_viaturas'))
    em_ocorrencia = bool(ocorrencia.unidade_samu_id)
    if request.method == 'POST' and not em_ocorrencia:
        unidade_samu_id = request.form.get('unidade_samu_id', type=int)
        if not unidade_samu_id:
            flash('Selecione uma viatura.', 'warning')
            return redirect(url_for('atendimento.despacho_viaturas_atender', numero_ocorrencia=numero_ocorrencia))
        v = UnidadeSamu.query.get(unidade_samu_id)
        if not v or v.tipo_registro != 'viatura' or not v.ativo:
            flash('Viatura inválida.', 'danger')
            return redirect(url_for('atendimento.despacho_viaturas_atender', numero_ocorrencia=numero_ocorrencia))
        eq = Equipe.query.filter_by(unidade_samu_id=unidade_samu_id).first()
        if not eq or not eq.membros:
            flash('A viatura selecionada não possui equipe montada.', 'warning')
            return redirect(url_for('atendimento.despacho_viaturas_atender', numero_ocorrencia=numero_ocorrencia))
        em_uso = Ocorrencia.query.filter(
            Ocorrencia.unidade_samu_id == unidade_samu_id,
            Ocorrencia.equipe_liberada_em.is_(None),
        ).first()
        if em_uso:
            flash('Viatura já em uso em outra ocorrência.', 'warning')
            return redirect(url_for('atendimento.despacho_viaturas_atender', numero_ocorrencia=numero_ocorrencia))
        ocorrencia.unidade_samu_id = unidade_samu_id
        ocorrencia.envio_viatura_em = datetime.utcnow()
        db.session.commit()
        flash(f'Viatura despachada com sucesso para a ocorrência {ocorrencia.numero}.', 'success')
        return redirect(url_for('atendimento.despacho_viaturas_atender', numero_ocorrencia=numero_ocorrencia))
    tipos_map = {t.id: t for t in TipoUnidadeSamu.query.all()}
    classes_map = {c.id: c for c in ClassificacaoRisco.query.all()}
    viaturas_com_equipe = []
    equipe_dados = None
    if not em_ocorrencia:
        ids_em_uso = [r[0] for r in db.session.query(Ocorrencia.unidade_samu_id).filter(
            Ocorrencia.unidade_samu_id.isnot(None),
            Ocorrencia.equipe_liberada_em.is_(None),
        ).distinct().all() if r[0]]
        ids_com_equipe = [r[0] for r in db.session.query(Equipe.unidade_samu_id).join(
            EquipeMembro, EquipeMembro.equipe_id == Equipe.id
        ).distinct().all() if r[0]]
        q = UnidadeSamu.query.filter(
            UnidadeSamu.tipo_registro == 'viatura',
            UnidadeSamu.ativo == True,
        )
        if ids_com_equipe:
            q = q.filter(UnidadeSamu.id.in_(ids_com_equipe))
        else:
            q = q.filter(UnidadeSamu.id == -1)
        if ids_em_uso:
            q = q.filter(UnidadeSamu.id.notin_(ids_em_uso))
        viaturas_com_equipe = q.options(db.joinedload(UnidadeSamu.tipo_unidade)).order_by(UnidadeSamu.apelido, UnidadeSamu.nome).all()
    else:
        eq = Equipe.query.options(
            db.joinedload(Equipe.veiculo),
            db.joinedload(Equipe.membros).joinedload(EquipeMembro.usuario),
        ).filter_by(unidade_samu_id=ocorrencia.unidade_samu_id).first()
        if eq:
            perfil_map = dict(EQUIPE_PERFIS)
            membros = []
            for m in eq.membros:
                perfil_cod = m.perfil or m.cbo
                membros.append({
                    'nome': m.usuario.nome or '—',
                    'perfil_nome': perfil_map.get(perfil_cod, perfil_cod or '—'),
                    'whatsapp': m.usuario.whatsapp or m.usuario.telefone or '',
                })
            equipe_dados = {
                'veiculo_prefixo': eq.veiculo.prefixo if eq.veiculo else '—',
                'membros': membros,
            }
    intercorrencias_cancelamento = Intercorrencia.query.filter_by(ativo=True, disponivel_cancelamento=True).order_by(Intercorrencia.nome).all()
    ocorrencias_aguardando = Ocorrencia.query.filter(
        Ocorrencia.status == STATUS_REGULADA,
        Ocorrencia.unidade_samu_id.is_(None),
    ).order_by(Ocorrencia.regulada_em.asc()).all()
    ocorrencias_para_redirecionar = [(o.id, o.numero, o.apelido or '') for o in ocorrencias_aguardando if o.id != ocorrencia.id]
    # Tabelas (mesmo layout do despacho_viaturas) para manter contexto
    ocorrencias_aguardando_full = Ocorrencia.query.options(
        db.joinedload(Ocorrencia.origem_ligacao),
    ).filter(
        Ocorrencia.status == STATUS_REGULADA,
        Ocorrencia.unidade_samu_id.is_(None),
        Ocorrencia.decisoes_medicas.isnot(None),
    ).all()
    aguardando_rows = []
    for o in ocorrencias_aguardando_full:
        for d in (o.decisoes_medicas or []):
            tipo_id, class_id = d.get('tipo_unidade_id'), d.get('classificacao_risco_id')
            if tipo_id and class_id:
                t, c = tipos_map.get(tipo_id), classes_map.get(class_id)
                if t and c:
                    aguardando_rows.append({'ocorrencia': o, 'tipo': t, 'classificacao': c})
    aguardando_rows.sort(key=lambda r: (r['tipo'].ordem_prioridade or 999, r['classificacao'].ordem or 999))
    em_ocorrencia_list = Ocorrencia.query.options(
        db.joinedload(Ocorrencia.unidade_samu),
        db.joinedload(Ocorrencia.origem_ligacao),
    ).filter(
        Ocorrencia.status == STATUS_REGULADA,
        Ocorrencia.unidade_samu_id.isnot(None),
    ).order_by(Ocorrencia.regulada_em.desc()).all()
    return render_template('atendimento/despacho_viaturas_atender.html',
        ocorrencia=ocorrencia,
        tipos_map=tipos_map,
        classes_map=classes_map,
        viaturas_com_equipe=viaturas_com_equipe,
        em_ocorrencia=em_ocorrencia,
        equipe_dados=equipe_dados,
        intercorrencias_cancelamento=intercorrencias_cancelamento,
        ocorrencias_para_redirecionar=ocorrencias_para_redirecionar,
        aguardando_rows=aguardando_rows,
        em_ocorrencia_list=em_ocorrencia_list,
    )


@atendimento_bp.route('/despacho-viaturas/api/ocorrencia/<int:ocorrencia_id>')
@login_required
def despacho_api_ocorrencia(ocorrencia_id):
    """Retorna timestamps da ocorrência em andamento."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    o = Ocorrencia.query.get(ocorrencia_id)
    if not o or o.status != STATUS_REGULADA or not o.unidade_samu_id:
        return jsonify({}), 404
    def _fmt(dt):
        return dt.strftime('%d/%m/%Y %H:%M') if dt else None
    return jsonify({
        'envio': _fmt(o.envio_viatura_em),
        'saida_base': _fmt(o.saida_base_em),
        'chegada_local': _fmt(o.chegada_local_em),
        'saida_local': _fmt(o.saida_local_em),
        'chegada_destino': _fmt(o.chegada_destino_em),
        'equipe_liberada': _fmt(o.equipe_liberada_em),
        'chegada_base': _fmt(o.chegada_base_em),
        'endereco': o.endereco_formatado,
        'google_maps_url': o.google_maps_url,
    })


@atendimento_bp.route('/despacho-viaturas/api/viaturas-disponiveis')
@login_required
def despacho_api_viaturas_disponiveis():
    """Retorna viaturas disponíveis para a ocorrência (tipo compatível com decisões, não em uso)."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    ocorrencia_id = request.args.get('ocorrencia_id', type=int)
    if not ocorrencia_id:
        return jsonify({'viaturas': []}), 400
    o = Ocorrencia.query.get(ocorrencia_id)
    if not o or o.status != STATUS_REGULADA or o.unidade_samu_id:
        return jsonify({'viaturas': []}), 400
    tipos_ids = {d.get('tipo_unidade_id') for d in (o.decisoes_medicas or []) if d.get('tipo_unidade_id')}
    if not tipos_ids:
        return jsonify({'viaturas': []}), 200
    ids_em_uso = [r[0] for r in db.session.query(Ocorrencia.unidade_samu_id).filter(
        Ocorrencia.unidade_samu_id.isnot(None),
        Ocorrencia.equipe_liberada_em.is_(None),
    ).distinct().all() if r[0]]
    q = UnidadeSamu.query.filter(
        UnidadeSamu.tipo_registro == 'viatura',
        UnidadeSamu.ativo == True,
        UnidadeSamu.tipo_unidade_id.in_(tipos_ids),
    )
    if ids_em_uso:
        q = q.filter(UnidadeSamu.id.notin_(ids_em_uso))
    viaturas = q.options(db.joinedload(UnidadeSamu.tipo_unidade)).order_by(UnidadeSamu.apelido, UnidadeSamu.nome).all()
    return jsonify({'viaturas': [{'id': v.id, 'nome': v.apelido or v.nome, 'tipo': v.tipo_unidade.sigla if v.tipo_unidade else ''} for v in viaturas]})


@atendimento_bp.route('/despacho-viaturas/api/enviar', methods=['POST'])
@login_required
def despacho_api_enviar():
    """Vincula viatura à ocorrência e registra envio."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    ocorrencia_id = request.form.get('ocorrencia_id', type=int)
    unidade_samu_id = request.form.get('unidade_samu_id', type=int)
    if not ocorrencia_id or not unidade_samu_id:
        return jsonify({'ok': False, 'erro': 'Dados inválidos'}), 400
    o = Ocorrencia.query.get(ocorrencia_id)
    v = UnidadeSamu.query.get(unidade_samu_id)
    if not o or not v or o.status != STATUS_REGULADA or o.unidade_samu_id:
        return jsonify({'ok': False, 'erro': 'Ocorrência ou viatura inválida'}), 400
    tipos_ids = {d.get('tipo_unidade_id') for d in (o.decisoes_medicas or []) if d.get('tipo_unidade_id')}
    if v.tipo_unidade_id not in tipos_ids:
        return jsonify({'ok': False, 'erro': 'Tipo de viatura incompatível'}), 400
    em_uso = Ocorrencia.query.filter(Ocorrencia.unidade_samu_id == unidade_samu_id, Ocorrencia.equipe_liberada_em.is_(None)).first()
    if em_uso:
        return jsonify({'ok': False, 'erro': 'Viatura já em uso'}), 400
    o.unidade_samu_id = unidade_samu_id
    o.envio_viatura_em = datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True})


@atendimento_bp.route('/despacho-viaturas/api/registrar-evento', methods=['POST'])
@login_required
def despacho_api_registrar_evento():
    """Registra timestamp: saida_base, chegada_local, saida_local, chegada_destino, equipe_liberada, chegada_base."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    ocorrencia_id = request.form.get('ocorrencia_id', type=int)
    evento = request.form.get('evento', '').strip()
    if not ocorrencia_id or not evento:
        return jsonify({'ok': False, 'erro': 'Dados inválidos'}), 400
    campo = {'saida_base': 'saida_base_em', 'chegada_local': 'chegada_local_em', 'saida_local': 'saida_local_em',
             'chegada_destino': 'chegada_destino_em', 'equipe_liberada': 'equipe_liberada_em', 'chegada_base': 'chegada_base_em'}.get(evento)
    if not campo:
        return jsonify({'ok': False, 'erro': 'Evento inválido'}), 400
    o = Ocorrencia.query.get(ocorrencia_id)
    if not o or o.status != STATUS_REGULADA or not o.unidade_samu_id:
        return jsonify({'ok': False, 'erro': 'Ocorrência inválida'}), 400
    setattr(o, campo, datetime.utcnow())
    db.session.commit()
    return jsonify({'ok': True, 'valor': datetime.utcnow().strftime('%d/%m/%Y %H:%M')})


@atendimento_bp.route('/despacho-viaturas/api/redirecionar', methods=['POST'])
@login_required
def despacho_api_redirecionar():
    """Desvincula viatura da ocorrência atual e vincula à nova."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    ocorrencia_atual_id = request.form.get('ocorrencia_atual_id', type=int)
    nova_ocorrencia_id = request.form.get('nova_ocorrencia_id', type=int)
    if not ocorrencia_atual_id or not nova_ocorrencia_id or ocorrencia_atual_id == nova_ocorrencia_id:
        return jsonify({'ok': False, 'erro': 'Dados inválidos'}), 400
    o_atual = Ocorrencia.query.get(ocorrencia_atual_id)
    o_nova = Ocorrencia.query.get(nova_ocorrencia_id)
    if not o_atual or not o_nova or not o_atual.unidade_samu_id or o_nova.unidade_samu_id:
        return jsonify({'ok': False, 'erro': 'Ocorrências inválidas'}), 400
    viatura_id = o_atual.unidade_samu_id
    o_atual.unidade_samu_id = None
    o_nova.unidade_samu_id = viatura_id
    o_nova.envio_viatura_em = datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True})


@atendimento_bp.route('/despacho-viaturas/api/cancelar', methods=['POST'])
@login_required
def despacho_api_cancelar():
    """Cancela envio: desvincula viatura e registra intercorrência."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    ocorrencia_id = request.form.get('ocorrencia_id', type=int)
    intercorrencia_id = request.form.get('intercorrencia_id', type=int)
    observacao = request.form.get('observacao', '').strip()
    if not ocorrencia_id:
        return jsonify({'ok': False, 'erro': 'Ocorrência obrigatória'}), 400
    o = Ocorrencia.query.get(ocorrencia_id)
    if not o or not o.unidade_samu_id:
        return jsonify({'ok': False, 'erro': 'Ocorrência inválida'}), 400
    o.unidade_samu_id = None
    o.cancelamento_intercorrencia_id = intercorrencia_id if intercorrencia_id else None
    o.cancelamento_observacao = observacao or None
    db.session.commit()
    return jsonify({'ok': True})


# ══════════════════════════════════════════════════════════
#  MONTAR EQUIPES (rádio operador)
# ══════════════════════════════════════════════════════════

@atendimento_bp.route('/despacho-viaturas/api/equipes/viaturas')
@login_required
def despacho_api_equipes_viaturas():
    """Lista viaturas (Unidade SAMU tipo viatura) por apelido."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    viaturas = UnidadeSamu.query.filter(
        UnidadeSamu.tipo_registro == 'viatura',
        UnidadeSamu.ativo == True,
    ).order_by(UnidadeSamu.apelido, UnidadeSamu.nome).all()
    return jsonify({'viaturas': [{'id': v.id, 'apelido': v.apelido or v.nome} for v in viaturas]})


@atendimento_bp.route('/despacho-viaturas/api/equipes/veiculos', methods=['GET', 'POST'])
@login_required
def despacho_api_equipes_veiculos():
    """GET: lista veículos ativos. POST: cria novo veículo (prefixo)."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    if request.method == 'POST':
        prefixo = (request.form.get('prefixo') or (request.json.get('prefixo') if request.is_json else '')).strip()
        if not prefixo:
            return jsonify({'ok': False, 'erro': 'Prefixo obrigatório'}), 400
        existe = Veiculo.query.filter(Veiculo.prefixo.ilike(prefixo), Veiculo.ativo == True).first()
        if existe:
            return jsonify({'ok': True, 'veiculo': {'id': existe.id, 'prefixo': existe.prefixo}})
        v = Veiculo(prefixo=prefixo)
        db.session.add(v)
        db.session.commit()
        return jsonify({'ok': True, 'veiculo': {'id': v.id, 'prefixo': v.prefixo}})
    veiculos = Veiculo.query.filter_by(ativo=True).order_by(Veiculo.prefixo).all()
    return jsonify({'veiculos': [{'id': v.id, 'prefixo': v.prefixo} for v in veiculos]})


# Perfis disponíveis para montar equipe (categorias)
EQUIPE_PERFIS = [
    ('medico_intervencionista', 'Médico Intervencionista'),
    ('enfermeiro', 'Enfermeiro'),
    ('aux_tec_enfermagem', 'Aux./Téc. Enfermagem'),
    ('condutor', 'Condutor'),
]


@atendimento_bp.route('/despacho-viaturas/api/equipes/categorias')
@login_required
def despacho_api_equipes_categorias():
    """Lista categorias (perfis) para montar equipe."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    return jsonify({'categorias': [{'cod': c[0], 'nome': c[1]} for c in EQUIPE_PERFIS]})


def _usuario_tem_perfil(u, perfil_cod):
    """Verifica se o usuário tem o perfil."""
    return perfil_cod in (u.perfis_list or [])


@atendimento_bp.route('/despacho-viaturas/api/equipes/profissionais')
@login_required
def despacho_api_equipes_profissionais():
    """Lista profissionais (usuários) com o perfil informado."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    perfil = request.args.get('perfil', '').strip()
    if not perfil or perfil not in [p[0] for p in EQUIPE_PERFIS]:
        return jsonify({'profissionais': []}), 200
    usuarios = Usuario.query.filter_by(ativo=True).order_by(Usuario.nome).all()
    ok = [u for u in usuarios if _usuario_tem_perfil(u, perfil)]
    return jsonify({'profissionais': [{'id': u.id, 'nome': u.nome} for u in ok]})


@atendimento_bp.route('/despacho-viaturas/api/equipes')
@login_required
def despacho_api_equipes_get():
    """Retorna equipe da viatura (unidade_samu_id)."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    unidade_id = request.args.get('unidade_samu_id', type=int)
    if not unidade_id:
        return jsonify({'equipe': None}), 200
    eq = Equipe.query.options(
        db.joinedload(Equipe.veiculo),
        db.joinedload(Equipe.membros).joinedload(EquipeMembro.usuario),
    ).filter_by(unidade_samu_id=unidade_id).first()
    if not eq:
        return jsonify({'equipe': None}), 200
    perfil_map = dict(EQUIPE_PERFIS)
    membros = []
    for m in eq.membros:
        nome = m.usuario.nome or ''
        primeiro = (nome.split() or [''])[0] if nome else ''
        perfil_cod = m.perfil or m.cbo
        membros.append({
            'usuario_id': m.usuario_id,
            'nome': m.usuario.nome,
            'primeiro_nome': primeiro,
            'perfil': perfil_cod,
            'perfil_nome': perfil_map.get(perfil_cod, perfil_cod or '—'),
            'whatsapp': m.usuario.whatsapp or m.usuario.telefone or '',
        })
    return jsonify({
        'equipe': {
            'unidade_samu_id': eq.unidade_samu_id,
            'veiculo_id': eq.veiculo_id,
            'veiculo_prefixo': eq.veiculo.prefixo if eq.veiculo else None,
            'membros': membros,
        }
    })


@atendimento_bp.route('/despacho-viaturas/api/equipes', methods=['POST'])
@login_required
def despacho_api_equipes_salvar():
    """Salva equipe: unidade_samu_id, veiculo_id, membros [{usuario_id, perfil}]."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    import json
    unidade_id = request.form.get('unidade_samu_id', type=int)
    veiculo_id = request.form.get('veiculo_id', type=int)
    membros_json = request.form.get('membros', '[]')
    if not unidade_id:
        return jsonify({'ok': False, 'erro': 'Unidade obrigatória'}), 400
    try:
        membros = json.loads(membros_json) if isinstance(membros_json, str) else membros_json
    except Exception:
        membros = []
    v = UnidadeSamu.query.get(unidade_id)
    if not v or v.tipo_registro != 'viatura':
        return jsonify({'ok': False, 'erro': 'Viatura inválida'}), 400
    eq = Equipe.query.filter_by(unidade_samu_id=unidade_id).first()
    if not eq:
        eq = Equipe(unidade_samu_id=unidade_id)
        db.session.add(eq)
        db.session.flush()
    eq.veiculo_id = veiculo_id if veiculo_id else None
    for m in list(eq.membros):
        db.session.delete(m)
    db.session.flush()
    for item in membros:
        uid = item.get('usuario_id')
        perfil = (item.get('perfil') or '').strip()
        if uid and perfil:
            db.session.add(EquipeMembro(equipe_id=eq.id, usuario_id=int(uid), perfil=perfil))
    db.session.commit()
    return jsonify({'ok': True})


@atendimento_bp.route('/despacho-viaturas/api/equipes/por-ocorrencia/<int:ocorrencia_id>')
@login_required
def despacho_api_equipes_por_ocorrencia(ocorrencia_id):
    """Retorna equipe da ocorrência (via unidade_samu_id)."""
    r = _exigir_despacho_viaturas()
    if r:
        return r
    o = Ocorrencia.query.get(ocorrencia_id)
    if not o or not o.unidade_samu_id:
        return jsonify({'equipe': None}), 200
    eq = Equipe.query.options(
        db.joinedload(Equipe.veiculo),
        db.joinedload(Equipe.membros).joinedload(EquipeMembro.usuario),
    ).filter_by(unidade_samu_id=o.unidade_samu_id).first()
    if not eq:
        return jsonify({'equipe': None}), 200
    perfil_map = dict(EQUIPE_PERFIS)
    membros = []
    for m in eq.membros:
        nome = m.usuario.nome or ''
        primeiro = (nome.split() or [''])[0] if nome else ''
        perfil_cod = m.perfil or m.cbo
        membros.append({
            'usuario_id': m.usuario_id,
            'nome': m.usuario.nome,
            'primeiro_nome': primeiro,
            'perfil': perfil_cod,
            'perfil_nome': perfil_map.get(perfil_cod, perfil_cod or '—'),
            'whatsapp': m.usuario.whatsapp or m.usuario.telefone or '',
        })
    return jsonify({
        'equipe': {
            'unidade_samu_id': eq.unidade_samu_id,
            'veiculo_id': eq.veiculo_id,
            'veiculo_prefixo': eq.veiculo.prefixo if eq.veiculo else None,
            'membros': membros,
        }
    })


