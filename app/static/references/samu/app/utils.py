"""Utilitários e filtros Jinja2."""
from datetime import datetime, timezone, timedelta

# Brasília = UTC-3 (offset fixo, evita dependência zoneinfo/tzdata no Windows)
OFFSET_BRASIL = timedelta(hours=-3)


def to_local(dt):
    """Converte datetime UTC (ou naive) para horário de Brasília (UTC-3)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (dt + OFFSET_BRASIL).replace(tzinfo=None)


def br_datetime(dt):
    """Formata datetime para exibição brasileira (sem conversão de fuso)."""
    if dt is None:
        return '—'
    return dt.strftime('%d/%m/%Y %H:%M')


def br_datetime_local(dt):
    """Converte UTC para horário de Brasília (UTC-3) e formata para exibição."""
    local = to_local(dt)
    if local is None:
        return '—'
    return local.strftime('%d/%m/%Y %H:%M')


def br_date(d):
    """Formata date para exibição brasileira."""
    if d is None:
        return '—'
    return d.strftime('%d/%m/%Y')


def br_fone(value):
    """Formata número de telefone/WhatsApp: (15) 99999-9999."""
    if not value:
        return '—'
    digits = ''.join(c for c in str(value) if c.isdigit())
    if len(digits) == 11:
        return f'({digits[:2]}) {digits[2:7]}-{digits[7:]}'
    if len(digits) == 10:
        return f'({digits[:2]}) {digits[2:6]}-{digits[6:]}'
    return value


def hoje_brasil_utc_range():
    """Retorna (inicio, fim) em UTC para o dia de hoje no horário de Brasília."""
    from datetime import date
    hoje = date.today()
    # 00:00 BRT = 03:00 UTC; 23:59 BRT = 02:59 UTC do dia seguinte
    inicio = datetime(hoje.year, hoje.month, hoje.day, 3, 0, 0)
    fim = inicio + timedelta(days=1)
    return inicio, fim


def endereco_relatorio(o):
    """Monta endereço para relatório: Unidade, Logradouro, Nº, Complemento, Bairro, Cidade/UF."""
    if not o:
        return '—'
    partes = []
    if getattr(o, 'unidade_saude', None) and o.unidade_saude:
        partes.append(o.unidade_saude.nome or '')
    if getattr(o, 'end_logradouro', None) and o.end_logradouro:
        partes.append(o.end_logradouro)
    if getattr(o, 'end_numero', None) and o.end_numero:
        partes.append(o.end_numero)
    if getattr(o, 'end_complemento', None) and o.end_complemento:
        partes.append(o.end_complemento)
    if getattr(o, 'end_bairro', None) and o.end_bairro:
        partes.append(o.end_bairro)
    c = getattr(o, 'end_cidade', None) or ''
    u = getattr(o, 'end_uf', None) or ''
    if c or u:
        partes.append((c + '/' + u) if (c and u) else (c or u))
    return ', '.join(p for p in partes if p) if partes else '—'


def links_nova_aba(html):
    """Adiciona target='_blank' e rel='noopener noreferrer' em links de um HTML."""
    if not html:
        return ''
    import re
    return re.sub(r'<a\s+([^>]*?)href=', r'<a \1target="_blank" rel="noopener noreferrer" href=', html, flags=re.IGNORECASE | re.DOTALL)


def formatar_links_wa(html):
    """Garante que links wa.me exibam o telefone com formatação br_fone: (XX) XXXXX-XXXX."""
    if not html:
        return ''
    import re

    def _replacer(m):
        return f'<a{m.group(1)}>{br_fone(m.group(2))}</a>'

    # Suporta href com " ou ', e URL com query string (ex: ?text=)
    return re.sub(
        r'<a([^>]*href=["\'][^"\']*wa\.me/55(\d{10,11})[^"\']*["\'][^>]*)>(.*?)</a>',
        _replacer,
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )


def colapsar_espacos_html(html):
    """Remove espaços extras do HTML Quill: parágrafos vazios e converte <p> em <br> para exibição compacta."""
    if not html or not isinstance(html, str):
        return html or ''
    import re
    # Remove parágrafos/divs vazios (com ou sem <br>)
    vazio = r'<(?:p|div)(?:\s[^>]*)?>\s*(?:<br\s*/?>\s*)?</(?:p|div)>\s*'
    s = re.sub(vazio, '', html, flags=re.IGNORECASE | re.DOTALL)
    # Converte </p><p...> em <br> — evita espaço entre blocos
    s = re.sub(r'</p>\s*<p([^>]*)>', r'<br>', s, flags=re.IGNORECASE)
    # Remove wrapper <p> inicial e final
    s = re.sub(r'^<p[^>]*>', '', s, flags=re.IGNORECASE)
    s = re.sub(r'</p>\s*$', '', s, flags=re.IGNORECASE)
    return s


def icon_class(value):
    """Normaliza classe de ícone para exibição (suporta BI e Font Awesome). Retrocompat: bi-truck -> bi bi-truck. FA6: fa-truck-medical -> fa-solid fa-truck-medical."""
    if not value or not isinstance(value, str):
        return ''
    v = value.strip()
    if v.startswith('bi-') and not v.startswith('bi '):
        return 'bi ' + v
    # Font Awesome 6 exige fa-solid/fa-regular/fa-brands. Se vier só fa-nome, adiciona fa-solid
    if v.startswith('fa-') and not any(v.startswith(p) for p in ('fa-solid', 'fas ', 'fa-regular', 'far ', 'fa-brands', 'fab ', 'fa-light', 'fal ', 'fa-duotone', 'fad ')):
        return 'fa-solid ' + v
    return v


def wa_link(value):
    """Retorna URL wa.me/55XXXXXXXXXXX para link WhatsApp."""
    if not value:
        return None
    digits = ''.join(c for c in str(value) if c.isdigit())
    if len(digits) in (10, 11):
        return f'https://wa.me/55{digits}'
    return None


def registrar_filtros(app):
    app.jinja_env.filters['br_datetime'] = br_datetime
    app.jinja_env.filters['br_datetime_local'] = br_datetime_local
    app.jinja_env.filters['br_date'] = br_date
    app.jinja_env.filters['br_fone'] = br_fone
    app.jinja_env.filters['endereco_relatorio'] = endereco_relatorio
    app.jinja_env.filters['wa_link'] = wa_link
    app.jinja_env.filters['links_nova_aba'] = links_nova_aba
    app.jinja_env.filters['formatar_links_wa'] = formatar_links_wa
    app.jinja_env.filters['colapsar_espacos_html'] = colapsar_espacos_html
    app.jinja_env.filters['icon_class'] = icon_class
    app.jinja_env.globals['getattr'] = getattr
