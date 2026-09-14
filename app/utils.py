from datetime import datetime, timedelta, date, timezone
from io import BytesIO
from urllib.parse import quote
import base64

try:
    from zoneinfo import ZoneInfo
    TZ_BRASILIA = ZoneInfo('America/Sao_Paulo')
except Exception:
    # Windows sem pacote tzdata: Brasília é UTC-3 o ano todo (sem horário de verão desde 2019).
    TZ_BRASILIA = timezone(timedelta(hours=-3))
_ASSINATURA_PNG_PREFIXO = 'data:image/png;base64,'


def recortar_assinatura_png(data_url, padding=12, alpha_min=12):
    """Recorta o PNG ao traço (pixels visíveis) e descarta a área transparente."""
    if not data_url:
        return None
    bruto = str(data_url).strip()
    if not bruto.startswith(_ASSINATURA_PNG_PREFIXO):
        return bruto
    try:
        from PIL import Image
        raw = base64.b64decode(bruto.split(',', 1)[1], validate=False)
        img = Image.open(BytesIO(raw)).convert('RGBA')
    except Exception:
        return bruto
    mascara = img.split()[-1].point(lambda p, lim=alpha_min: 255 if p >= lim else 0)
    bbox = mascara.getbbox()
    if not bbox:
        return None
    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(img.width, right + padding)
    bottom = min(img.height, bottom + padding)
    recorte = img.crop((left, top, right, bottom))
    buf = BytesIO()
    recorte.save(buf, format='PNG', optimize=True)
    return _ASSINATURA_PNG_PREFIXO + base64.b64encode(buf.getvalue()).decode('ascii')


def agora_local():
    """Instante atual em UTC (naive) para gravar no banco.

    Independente do fuso do servidor. Na tela, use ``br_datetime`` /
    ``formatar_brasilia`` — nunca ``strftime`` cru.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def agora_local_callable():
    """Default SQLAlchemy: mesmo instante de ``agora_local``."""
    return agora_local()


def hoje_brasilia():
    """Data de calendário em Brasília (não a do servidor)."""
    return datetime.now(TZ_BRASILIA).date()


def agora_brasilia():
    """Relógio de parede em Brasília (naive). Use em agenda/expediente, não para gravar timestamp."""
    return datetime.now(TZ_BRASILIA).replace(tzinfo=None)


def para_brasilia(value):
    """Converte datetime gravado (UTC naive ou aware) para Brasília naive.

    Objetos ``date`` (nascimento, prazo, vigência) não são instante — devolve iguais.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(TZ_BRASILIA).replace(tzinfo=None)
    return value


def formatar_brasilia(value, fmt='%d/%m/%Y %H:%M'):
    """Texto em horário de Brasília. ``None`` vira '—'."""
    if value is None:
        return '—'
    dt = para_brasilia(value)
    if dt is None:
        return '—'
    return dt.strftime(fmt)


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
        f'Ficha gerada em: {formatar_brasilia(ficha.gerado_em)}',
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
        f'Data: {formatar_brasilia(ficha.gerado_em)}',
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
            return formatar_brasilia(value, '%d/%m/%Y')
        return value.strftime('%d/%m/%Y')

    @app.template_filter('br_datetime')
    def br_datetime(value, fmt='%d/%m/%Y %H:%M'):
        if value is None:
            return '—'
        return formatar_brasilia(value, fmt)

    _MESES = ('janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
              'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro')

    @app.template_filter('br_date_extenso')
    def br_date_extenso(value):
        """Retorna data no formato 'DD de MMMM de AAAA' (ex: 28 de fevereiro de 2025)."""
        if value is None:
            return '—'
        dt = para_brasilia(value) if isinstance(value, datetime) else value
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

    @app.template_filter('br_cnpj')
    def br_cnpj(value):
        """Formata CNPJ para exibição: 00.000.000/0001-00."""
        if not value:
            return '—'
        digits = ''.join(c for c in str(value) if c.isdigit())
        if len(digits) == 14:
            return f'{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}'
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

    @app.template_filter('assinatura_crop')
    def assinatura_crop(value):
        """PNG da assinatura só com o traço, sem a faixa transparente em volta."""
        return recortar_assinatura_png(value) or ''


def prefixed_static_url(path):
    """Prefixa path com APPLICATION_ROOT quando configurado (ex: /sigus para proxy reverso)."""
    try:
        from flask import current_app
        prefix = (current_app.config.get('APPLICATION_ROOT') or '').rstrip('/')
        p = path if path.startswith('/') else f'/{path}'
        return f'{prefix}{p}' if prefix else p
    except RuntimeError:
        return path if path.startswith('/') else f'/{path}'
