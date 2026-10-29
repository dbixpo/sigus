# -*- coding: utf-8 -*-
"""Campanhas de cor do calendário da saúde (laços). Repetem todo ano."""
from datetime import date

from app import db

LACO_PADRAO = 'padrao'
LACO_BIGODE = 'bigode'
LACOS = {
    LACO_PADRAO: 'Laço',
    LACO_BIGODE: 'Laço com bigode',
}

MESES = (
    '', 'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
)

# Cores de laço usadas no Brasil e nomeadas no calendário do Ministério da Saúde.
# Prioridade desempata quando dois laços cabem no mesmo dia.
SEMENTE = (
    dict(slug='janeiro-branco', nome='Janeiro Branco', cor='#F5F5F5',
         mes_inicio=1, dia_inicio=1, mes_fim=1, dia_fim=31, prioridade=20,
         resumo='Saúde mental. Cuidar da mente também é cuidado de saúde.'),
    dict(slug='janeiro-roxo', nome='Janeiro Roxo', cor='#6A1B9A',
         mes_inicio=1, dia_inicio=1, mes_fim=1, dia_fim=31, prioridade=10,
         resumo='Hanseníase. O último domingo de janeiro é o dia nacional de combate e prevenção.'),
    dict(slug='fevereiro-roxo', nome='Fevereiro Roxo', cor='#7B1FA2',
         mes_inicio=2, dia_inicio=1, mes_fim=2, dia_fim=29, prioridade=15,
         resumo='Lúpus, fibromialgia e Alzheimer.'),
    dict(slug='fevereiro-laranja', nome='Fevereiro Laranja', cor='#EF6C00',
         mes_inicio=2, dia_inicio=1, mes_fim=2, dia_fim=29, prioridade=10,
         resumo='Leucemia. O 15 de fevereiro é o Dia Internacional de Luta contra o Câncer Infantil.'),
    dict(slug='marco-azul-marinho', nome='Março Azul-Marinho', cor='#0D47A1',
         mes_inicio=3, dia_inicio=1, mes_fim=3, dia_fim=31, prioridade=15,
         resumo='Câncer colorretal. O dia nacional é 27 de março.'),
    dict(slug='marco-lilas', nome='Março Lilás', cor='#CE93D8',
         mes_inicio=3, dia_inicio=1, mes_fim=3, dia_fim=31, prioridade=10,
         resumo='Câncer do colo do útero. O dia mundial é 26 de março.'),
    dict(slug='abril-azul', nome='Abril Azul', cor='#1565C0',
         mes_inicio=4, dia_inicio=1, mes_fim=4, dia_fim=30, prioridade=15,
         resumo='Conscientização sobre o autismo. O dia mundial é 2 de abril.'),
    dict(slug='abril-verde', nome='Abril Verde', cor='#2E7D32',
         mes_inicio=4, dia_inicio=1, mes_fim=4, dia_fim=30, prioridade=12,
         resumo='Segurança do paciente, no mês que o Ministério da Saúde dedica a esse tema.'),
    dict(slug='maio-amarelo', nome='Maio Amarelo', cor='#F9A825',
         mes_inicio=5, dia_inicio=1, mes_fim=5, dia_fim=31, prioridade=12,
         resumo='Atenção e cuidado no trânsito.'),
    dict(slug='junho-vermelho', nome='Junho Vermelho', cor='#C62828',
         mes_inicio=6, dia_inicio=1, mes_fim=6, dia_fim=30, prioridade=15,
         resumo='Doação de sangue. O dia mundial do doador é 14 de junho.'),
    dict(slug='julho-amarelo', nome='Julho Amarelo', cor='#FBC02D',
         mes_inicio=7, dia_inicio=1, mes_fim=7, dia_fim=31, prioridade=15,
         resumo='Hepatites virais. O dia mundial é 28 de julho.'),
    dict(slug='agosto-dourado', nome='Agosto Dourado', cor='#C9A227',
         mes_inicio=8, dia_inicio=1, mes_fim=8, dia_fim=31, prioridade=15,
         resumo='Aleitamento materno.'),
    dict(slug='setembro-amarelo', nome='Setembro Amarelo', cor='#F9A825',
         mes_inicio=9, dia_inicio=1, mes_fim=9, dia_fim=30, prioridade=20,
         resumo='Prevenção do suicídio. O dia mundial é 10 de setembro.'),
    dict(slug='setembro-verde', nome='Setembro Verde', cor='#2E7D32',
         mes_inicio=9, dia_inicio=1, mes_fim=9, dia_fim=30, prioridade=12,
         resumo='Doação de órgãos. O dia nacional é 27 de setembro.'),
    dict(slug='setembro-dourado', nome='Setembro Dourado', cor='#C9A227',
         mes_inicio=9, dia_inicio=1, mes_fim=9, dia_fim=30, prioridade=10,
         resumo='Câncer infantojuvenil, no calendário do Ministério da Saúde.'),
    dict(slug='outubro-rosa', nome='Outubro Rosa', cor='#C2185B',
         mes_inicio=10, dia_inicio=1, mes_fim=10, dia_fim=31, prioridade=20,
         resumo='Câncer de mama. Mês instituído pela Lei nº 13.733/2018. O dia mundial é 19 de outubro.'),
    dict(slug='novembro-azul', nome='Novembro Azul', cor='#1565C0',
         mes_inicio=11, dia_inicio=1, mes_fim=11, dia_fim=30, prioridade=20,
         laco=LACO_BIGODE,
         resumo='Câncer de próstata. O bigode no laço é o jeito brasileiro de lembrar a campanha.'),
    dict(slug='dezembro-vermelho', nome='Dezembro Vermelho', cor='#B71C1C',
         mes_inicio=12, dia_inicio=1, mes_fim=12, dia_fim=31, prioridade=20,
         resumo='Prevenção ao HIV/AIDS e outras ISTs. Instituído pela Lei nº 13.504/2017. O dia mundial é 1º de dezembro.'),
    dict(slug='dezembro-laranja', nome='Dezembro Laranja', cor='#E65100',
         mes_inicio=12, dia_inicio=1, mes_fim=12, dia_fim=31, prioridade=12,
         resumo='Câncer de pele, no calendário do Ministério da Saúde.'),
)


def _rgb(hex_cor):
    h = (hex_cor or '').strip().lstrip('#')
    if len(h) != 6:
        return (26, 130, 184)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _canal(c):
    c = c / 255
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _luminancia(rgb):
    r, g, b = rgb
    return 0.2126 * _canal(r) + 0.7152 * _canal(g) + 0.0722 * _canal(b)


def _contraste(a, b):
    claro, escuro = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (claro + 0.05) / (escuro + 0.05)


def _hex(rgb):
    return '#{:02X}{:02X}{:02X}'.format(*rgb)


def cor_texto(hex_cor):
    """Branco ou o azul petróleo, o que ler melhor em cima da cor."""
    rgb = _rgb(hex_cor)
    branco = (255, 255, 255)
    escuro = (13, 59, 94)
    if _contraste(rgb, branco) >= _contraste(rgb, escuro):
        return '#FFFFFF'
    return '#0D3B5E'


def cor_botao(hex_cor):
    """Escurece a cor até o branco do texto passar de 4.5:1."""
    rgb = list(_rgb(hex_cor))
    branco = (255, 255, 255)
    for _ in range(24):
        if _contraste(tuple(rgb), branco) >= 4.5:
            break
        rgb = [max(0, int(c * 0.86)) for c in rgb]
    return _hex(rgb)


def cor_hover(hex_botao):
    rgb = [max(0, int(c * 0.82)) for c in _rgb(hex_botao)]
    return _hex(rgb)


def normalizar_cor(valor):
    texto = (valor or '').strip()
    if not texto.startswith('#'):
        texto = '#' + texto
    if len(texto) == 4:
        texto = '#' + ''.join(c * 2 for c in texto[1:])
    if len(texto) != 7:
        return None
    try:
        int(texto[1:], 16)
    except ValueError:
        return None
    return texto.upper()


class CampanhaSaude(db.Model):
    __tablename__ = 'campanhas_saude'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(40), unique=True)
    nome = db.Column(db.String(120), nullable=False)
    resumo = db.Column(db.String(400))
    cor = db.Column(db.String(7), nullable=False, default='#1A82B8')
    mes_inicio = db.Column(db.SmallInteger, nullable=False)
    dia_inicio = db.Column(db.SmallInteger, nullable=False)
    mes_fim = db.Column(db.SmallInteger, nullable=False)
    dia_fim = db.Column(db.SmallInteger, nullable=False)
    prioridade = db.Column(db.SmallInteger, nullable=False, default=10)
    laco = db.Column(db.String(20), nullable=False, default=LACO_PADRAO)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    @property
    def cor_texto(self):
        return cor_texto(self.cor)

    @property
    def cor_botao(self):
        return cor_botao(self.cor)

    @property
    def cor_hover(self):
        return cor_hover(self.cor_botao)

    @property
    def periodo(self):
        ini = f'{self.dia_inicio:02d}/{self.mes_inicio:02d}'
        fim = f'{self.dia_fim:02d}/{self.mes_fim:02d}'
        return f'{ini} a {fim}'

    @property
    def laco_label(self):
        return LACOS.get(self.laco, self.laco)

    def vigente_em(self, dia):
        if not self.ativo or not dia:
            return False
        atual = (dia.month, dia.day)
        inicio = (self.mes_inicio, self.dia_inicio)
        fim = (self.mes_fim, self.dia_fim)
        if inicio <= fim:
            return inicio <= atual <= fim
        return atual >= inicio or atual <= fim


def campanhas_na_data(dia=None):
    """(principal, todas) ativas na data. A principal pinta o sistema."""
    dia = dia or date.today()
    try:
        linhas = CampanhaSaude.query.filter_by(ativo=True).all()
    except Exception:
        db.session.rollback()
        return None, []
    ativas = [c for c in linhas if c.vigente_em(dia)]
    ativas.sort(key=lambda c: (-c.prioridade, c.nome))
    return (ativas[0] if ativas else None), ativas


def _nome_tipo_livre(nome, ignorar_id=None):
    from app.models.noticias import TipoAcao

    base = (nome or 'Campanha').strip()[:200] or 'Campanha'
    candidato = base
    for n in range(2, 30):
        q = TipoAcao.query.filter_by(nome=candidato)
        if ignorar_id:
            q = q.filter(TipoAcao.id != ignorar_id)
        if not q.first():
            return candidato
        sufixo = f' ({n})'
        candidato = base[:200 - len(sufixo)] + sufixo
    return candidato


def sincronizar_tipo_da_campanha(campanha):
    """O tema do mural acompanha o nome, o texto e o status da campanha."""
    from app.models.noticias import TipoAcao

    tipo = TipoAcao.query.filter_by(campanha_id=campanha.id).first()
    if tipo is None:
        tipo = TipoAcao.query.filter(
            TipoAcao.nome == (campanha.nome or '').strip(),
            TipoAcao.campanha_id.is_(None),
        ).first()
    if tipo is None:
        tipo = TipoAcao(
            nome=_nome_tipo_livre(campanha.nome),
            ordem=200 + int(campanha.mes_inicio or 0),
        )
        db.session.add(tipo)
        db.session.flush()
    tipo.campanha_id = campanha.id
    tipo.nome = _nome_tipo_livre(campanha.nome, ignorar_id=tipo.id)
    tipo.descricao = campanha.resumo
    tipo.ativo = bool(campanha.ativo)


def sincronizar_tipos_campanha():
    for campanha in CampanhaSaude.query.order_by(CampanhaSaude.id).all():
        sincronizar_tipo_da_campanha(campanha)
    db.session.commit()


def garantir_campanhas():
    """Inclui as campanhas oficiais que ainda não existem. Não mexe nas editadas."""
    for item in SEMENTE:
        if CampanhaSaude.query.filter_by(slug=item['slug']).first():
            continue
        db.session.add(CampanhaSaude(
            slug=item['slug'],
            nome=item['nome'],
            resumo=item['resumo'],
            cor=item['cor'],
            mes_inicio=item['mes_inicio'],
            dia_inicio=item['dia_inicio'],
            mes_fim=item['mes_fim'],
            dia_fim=item['dia_fim'],
            prioridade=item['prioridade'],
            laco=item.get('laco', LACO_PADRAO),
            ativo=True,
        ))
    db.session.commit()
    try:
        sincronizar_tipos_campanha()
    except Exception:
        db.session.rollback()
