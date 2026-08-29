from datetime import datetime, timedelta

_TZ_OFFSET = timedelta(hours=-3)  # UTC-3 (horário de Brasília)
from urllib.parse import quote


def _montar_corpo_email(usuario, unidade):
    """Monta o corpo do e-mail de solicitação de vínculo CNES."""
    linhas = [
        f'Prezados,',
        f'',
        f'Solicito o cadastro/vinculação do profissional abaixo no CNES da unidade:',
        f'',
        f'UNIDADE: {unidade.nome}',
    ]
    if unidade.numero_cnes:
        linhas.append(f'CNES: {unidade.numero_cnes}')
    linhas += [
        f'',
        f'DADOS DO PROFISSIONAL:',
        f'Nome: {usuario.nome}',
    ]
    if usuario.cpf:
        linhas.append(f'CPF: {usuario.cpf}')
    if usuario.cns:
        linhas.append(f'CNS: {usuario.cns}')
    if usuario.data_nasc:
        linhas.append(f'Data de Nascimento: {usuario.data_nasc.strftime("%d/%m/%Y")}')
    if usuario.sexo:
        linhas.append(f'Sexo: {"Masculino" if usuario.sexo == "M" else "Feminino"}')
    if usuario.reg_conselho:
        linhas.append(f'Registro no Conselho: {usuario.reg_conselho} / {usuario.orgao_emissor or ""}')
    if usuario.cbo:
        linhas.append(f'CBO: {usuario.cbo_label}')
    if usuario.vinculo:
        linhas.append(f'Vínculo: {usuario.vinculo} – {usuario.vinculo_label}')
    if usuario.tipo_vinculo:
        linhas.append(f'Tipo: {usuario.tipo_vinculo} – {usuario.tipo_vinculo_label}')
    if usuario.carga_horaria:
        linhas.append(f'Carga Horária Semanal: {usuario.carga_horaria}h')
    if usuario.dt_entrada_unidade:
        linhas.append(f'Data de Entrada na Unidade: {usuario.dt_entrada_unidade.strftime("%d/%m/%Y")}')
    if usuario.matricula:
        linhas.append(f'Matrícula: {usuario.matricula}')
    linhas += [
        f'',
        f'Atenciosamente,',
    ]
    return '\n'.join(linhas)


def _montar_corpo_email_ficha(ficha):
    """Monta o corpo do e-mail a partir de uma FichaCnesVinculo já gravada."""
    usuario = ficha.usuario
    unidade = ficha.unidade
    tipo_str = 'CADASTRO' if ficha.tipo == 'cadastro' else 'DESCADASTRO'
    linhas = [
        f'Prezados,',
        f'',
        f'Solicito o {tipo_str.lower()} do profissional abaixo no CNES:',
        f'',
        f'UNIDADE: {unidade.nome}',
    ]
    if unidade.numero_cnes:
        linhas.append(f'CNES DA UNIDADE: {unidade.numero_cnes}')
    linhas += [
        f'',
        f'PROFISSIONAL:',
        f'Nome: {usuario.nome}',
    ]
    if usuario.cpf:
        linhas.append(f'CPF: {usuario.cpf}')
    if ficha.cns_profissional or usuario.cns:
        linhas.append(f'CNS: {ficha.cns_profissional or usuario.cns}')
    if usuario.data_nasc:
        linhas.append(f'Data de Nascimento: {usuario.data_nasc.strftime("%d/%m/%Y")}')
    if usuario.sexo:
        linhas.append(f'Sexo: {"Masculino" if usuario.sexo == "M" else "Feminino"}')
    if usuario.reg_conselho:
        linhas.append(f'Registro Conselho: {usuario.reg_conselho} / {usuario.orgao_emissor or ""}')

    if ficha.tipo == 'cadastro':
        linhas.append(f'')
        linhas.append(f'DADOS DE VÍNCULO:')
        if ficha.cbo:
            linhas.append(f'CBO: {ficha.cbo_label}')
        if ficha.vinculo:
            linhas.append(f'Vínculo: {ficha.vinculo} – {ficha.vinculo_label}')
        if ficha.tipo_vinculo:
            linhas.append(f'Tipo: {ficha.tipo_vinculo} – {ficha.tipo_vinculo_label}')
        if ficha.carga_horaria:
            linhas.append(f'Carga Horária Semanal: {ficha.carga_horaria}h')
        if ficha.dt_entrada_unidade:
            linhas.append(f'Data de Entrada na Unidade: {ficha.dt_entrada_unidade.strftime("%d/%m/%Y")}')
        if ficha.especialidade_residencia:
            linhas.append(f'Especialidade/Residência: {ficha.especialidade_residencia}')
    else:
        if ficha.observacoes:
            linhas.append(f'')
            linhas.append(f'Motivo: {ficha.observacoes}')

    linhas += [
        f'',
        f'Ficha gerada em: {ficha.gerado_em.strftime("%d/%m/%Y %H:%M")}',
        f'Solicitado por: {ficha.gerador.nome if ficha.gerador else "Sistema"}',
        f'',
        f'Atenciosamente,',
    ]
    return '\n'.join(linhas)


def _montar_corpo_email_rede(ficha):
    """Monta o corpo do e-mail de solicitação de acesso à REDE para um profissional.

    A 'Rede' refere-se ao sistema de acesso/rede municipal de saúde (login de rede,
    e-mail corporativo, sistemas internos, etc.).
    O destinatário e o conteúdo exato serão ajustados quando o fluxo for definido.
    """
    usuario = ficha.usuario
    unidade = ficha.unidade
    linhas = [
        f'Prezados,',
        f'',
        f'Solicito a {"liberação de acesso" if ficha.tipo == "cadastro" else "remoção de acesso"} à Rede para o profissional abaixo:',
        f'',
        f'UNIDADE: {unidade.nome}',
    ]
    if unidade.numero_cnes:
        linhas.append(f'CNES DA UNIDADE: {unidade.numero_cnes}')
    linhas += [
        f'',
        f'PROFISSIONAL:',
        f'Nome: {usuario.nome}',
    ]
    if usuario.cpf:
        linhas.append(f'CPF: {usuario.cpf}')
    if ficha.cns_profissional or usuario.cns:
        linhas.append(f'CNS: {ficha.cns_profissional or usuario.cns}')
    if usuario.email:
        linhas.append(f'E-mail: {usuario.email}')
    if usuario.whatsapp:
        linhas.append(f'WhatsApp: {usuario.whatsapp}')
    if usuario.matricula:
        linhas.append(f'Matrícula: {usuario.matricula}')
    if usuario.reg_conselho:
        linhas.append(f'Registro Conselho: {usuario.reg_conselho} / {usuario.orgao_emissor or ""}')
    if ficha.tipo == 'cadastro':
        if ficha.cbo:
            linhas.append(f'CBO: {ficha.cbo_label}')
        if ficha.vinculo:
            linhas.append(f'Vínculo: {ficha.vinculo} – {ficha.vinculo_label}')
        if ficha.carga_horaria:
            linhas.append(f'Carga Horária Semanal: {ficha.carga_horaria}h')
        if ficha.dt_entrada_unidade:
            linhas.append(f'Data de Entrada na Unidade: {ficha.dt_entrada_unidade.strftime("%d/%m/%Y")}')
    else:
        if ficha.observacoes:
            linhas.append(f'Motivo: {ficha.observacoes}')
    linhas += [
        f'',
        f'Solicitado por: {ficha.gerador.nome if ficha.gerador else "Sistema"}',
        f'Data: {ficha.gerado_em.strftime("%d/%m/%Y %H:%M")}',
        f'',
        f'Atenciosamente,',
    ]
    return '\n'.join(linhas)


def registrar_filtros(app):
    @app.template_filter('br_date')
    def br_date(value):
        if value is None:
            return '—'
        if isinstance(value, datetime):
            return (value + _TZ_OFFSET).strftime('%d/%m/%Y')
        return value.strftime('%d/%m/%Y')

    @app.template_filter('br_datetime')
    def br_datetime(value):
        if value is None:
            return '—'
        return (value + _TZ_OFFSET).strftime('%d/%m/%Y %H:%M')

    _MESES = ('janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
              'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro')

    @app.template_filter('br_date_extenso')
    def br_date_extenso(value):
        """Retorna data no formato 'DD de MMMM de AAAA' (ex: 28 de fevereiro de 2025)."""
        if value is None:
            return '—'
        dt = value + _TZ_OFFSET if isinstance(value, datetime) else value
        return f'{dt.day:02d} de {_MESES[dt.month - 1]} de {dt.year}'

    @app.template_filter('br_fone')
    def br_fone(value):
        """Formata número de telefone/WhatsApp para exibição: (15) 99999-9999."""
        if not value:
            return '—'
        digits = ''.join(c for c in str(value) if c.isdigit())
        if len(digits) == 11:   # celular com DDD: 11 dígitos
            return f'({digits[:2]}) {digits[2:7]}-{digits[7:]}'
        if len(digits) == 10:   # fixo com DDD: 10 dígitos
            return f'({digits[:2]}) {digits[2:6]}-{digits[6:]}'
        return value  # retorna original se não bater o padrão

    @app.template_filter('br_currency')
    def br_currency(value):
        if value is None:
            return '—'
        return f'R$ {float(value):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    @app.template_filter('google_qr_url')
    def google_qr_url(link, size=110):
        """Gera a URL da API Google Charts para um QR code simples."""
        if not link:
            return ''
        encoded = quote(str(link), safe='')
        return (f'https://chart.googleapis.com/chart'
                f'?chs={size}x{size}&cht=qr&choe=UTF-8&chld=L|1&chl={encoded}')

    @app.template_filter('pluralize')
    def pluralize(count, singular, plural=None):
        if plural is None:
            plural = singular + 's'
        return singular if count == 1 else plural


def prefixed_static_url(path):
    """Prefixa path com APPLICATION_ROOT quando configurado (ex: /sigus para proxy reverso)."""
    try:
        from flask import current_app
        prefix = (current_app.config.get('APPLICATION_ROOT') or '').rstrip('/')
        p = path if path.startswith('/') else f'/{path}'
        return f'{prefix}{p}' if prefix else p
    except RuntimeError:
        return path if path.startswith('/') else f'/{path}'
