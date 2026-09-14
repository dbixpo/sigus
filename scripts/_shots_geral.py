# -*- coding: utf-8 -*-
"""Prints das telas gerais do SIGUS para o manual da Estante.

Usa http://localhost:5001/sigus (não 127.0.0.1). Anonimiza nomes de
pessoas e dados de NSP. Patrimônio tem capítulo próprio.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

from app import create_app
from app.models.chamado import Chamado
from app.models.nsp import NspOcorrencia
from app.models.unidade import Unidade
from app.models.usuario import Usuario

OUT = ROOT / 'app' / 'static' / 'uploads' / 'manuais_tmp'
BASE = 'http://localhost:5001/sigus'

JS_NAV = """
const toggles = document.querySelectorAll('.sigus-navbar .dropdown-toggle');
const userBtn = toggles[toggles.length - 1];
if (userBtn) {
  userBtn.querySelectorAll('span').forEach((s) => {
    if (s.textContent.trim().length <= 2) s.textContent = 'A';
    else s.textContent = 'Admin';
  });
}
"""

JS_ANON_TABLE_LAST = """
document.querySelectorAll('table tbody tr').forEach((tr, i) => {
  const tds = tr.querySelectorAll('td');
  if (!tds.length) return;
  const lastTxt = tds[tds.length - 1] && tds[tds.length - 1].textContent;
  tds.forEach((td) => {
    const t = (td.textContent || '').trim();
    if (/@/.test(t)) td.textContent = 'usuario.exemplo@sorocaba.sp.gov.br';
  });
});
"""

JS_NSP_LISTA = JS_NAV + """
document.querySelectorAll('table tbody tr').forEach((tr, i) => {
  const tds = tr.querySelectorAll('td');
  if (tds.length < 7) return;
  const proto = tds[0].querySelector('.text-primary, .fw-semibold') || tds[0];
  const num = String(i + 1).padStart(5, '0');
  const badge = tds[0].querySelector('.badge');
  proto.childNodes.forEach((n) => {
    if (n.nodeType === 3) n.textContent = 'SP-2026-' + num + ' ';
  });
  if (!proto.querySelector('.fw-semibold') && proto === tds[0]) {
    tds[0].childNodes[0] && (tds[0].childNodes[0].textContent = 'SP-2026-' + num + ' ');
  }
  tds[6].textContent = 'Profissional exemplo';
});
"""

JS_NSP_DETALHE = JS_NAV + """
document.querySelectorAll('.card-body .col-md-6, .card-body .col-12').forEach((el) => {
  const lab = el.querySelector('.text-muted');
  if (!lab) return;
  const t = lab.textContent || '';
  if (t.includes('Notificante')) {
    const s = el.querySelector('strong');
    if (s) s.textContent = 'PROFISSIONAL EXEMPLO';
  }
  if (t.includes('Pessoa afetada')) {
    el.innerHTML = '<span class="text-muted d-block">Pessoa afetada</span>CIDADÃO EXEMPLO · Paciente';
  }
  if (t.includes('Prontuário')) {
    el.innerHTML = '<span class="text-muted d-block">Prontuário</span>000000';
  }
  if (t.trim() === 'CNS') {
    el.innerHTML = '<span class="text-muted d-block">CNS</span>000000000000000';
  }
  if (t.trim() === 'CPF') {
    el.innerHTML = '<span class="text-muted d-block">CPF</span>000.000.000-00';
  }
  if (t.includes('Descrição')) {
    const d = el.querySelector('div.mt-1');
    if (d) d.textContent = 'Descrição ilustrativa para o manual, sem dado de cidadão.';
  }
  if (t.includes('Ação imediata')) {
    const d = el.querySelector('div.mt-1');
    if (d) d.textContent = 'Conduta imediata de exemplo — proteger a pessoa e comunicar a chefia.';
  }
});
"""

JS_NSP_FORM = JS_NAV + """
const nome = document.querySelector('[name=notificante_nome]');
if (nome) nome.value = 'PROFISSIONAL EXEMPLO';
const sel = document.getElementById('tipo_pessoa_id');
if (sel) {
  const opt = [...sel.options].find((o) =>
    (o.dataset.slug || '').toLowerCase().includes('paciente') ||
    (o.textContent || '').toLowerCase().includes('paciente')
  );
  if (opt) {
    sel.value = opt.value;
    sel.dispatchEvent(new Event('change', { bubbles: true }));
  }
}
const bloco = document.getElementById('blocoSis');
if (bloco) bloco.classList.remove('d-none');
const busca = document.getElementById('blocoSisBusca');
if (busca) busca.classList.remove('d-none');
const cpf = document.getElementById('sisTipoCpf');
if (cpf) cpf.checked = true;
"""


def session_cookie(app, user_id: int) -> str:
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        ck = client.get_cookie('session')
        if not ck:
            raise RuntimeError('Sem cookie de sessão.')
        return ck.value


def main() -> None:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    OUT.mkdir(parents=True, exist_ok=True)
    app = create_app('development')
    with app.app_context():
        u = Usuario.query.filter_by(ativo=True, perfil='administrador').first()
        if not u:
            raise SystemExit('Sem administrador ativo.')
        uid = u.id
        unid = (
            Unidade.query.filter_by(status='ativa')
            .order_by(Unidade.id)
            .first()
        )
        unid_id = unid.id if unid else None
        ch = Chamado.query.order_by(Chamado.id.desc()).first()
        ch_id = ch.id if ch else None
        nsp = NspOcorrencia.query.order_by(NspOcorrencia.id.desc()).first()
        nsp_id = nsp.id if nsp else None

    cookie = session_cookie(app, uid)
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--window-size=1440,1100')
    opts.add_argument('--hide-scrollbars')
    opts.add_argument('--disable-gpu')
    opts.add_experimental_option('excludeSwitches', ['enable-automation'])
    opts.add_experimental_option('prefs', {
        'credentials_enable_service': False,
        'profile.password_manager_enabled': False,
        'autofill.profile_enabled': False,
    })
    drv = webdriver.Chrome(options=opts)
    wait = WebDriverWait(drv, 25)

    def shot(stem: str) -> None:
        time.sleep(0.4)
        drv.save_screenshot(str(OUT / f'{stem}.png'))
        print(' ', stem)

    def goto(path: str, css: str, js: str = JS_NAV) -> bool:
        drv.get(f'{BASE}{path}')
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
        except Exception:
            print('  timeout', path, drv.current_url)
            return False
        if drv.find_elements(By.CSS_SELECTOR, '.login-wrapper'):
            print('  login', path)
            return False
        if js:
            drv.execute_script(js)
        return True

    try:
        drv.get(f'{BASE}/login')
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name=email]')))
        drv.execute_script("""
            const em = document.querySelector('input[name=email]');
            const se = document.getElementById('senhaInput') || document.querySelector('input[type=password]');
            if (em) em.value = '';
            if (se) se.value = '';
        """)
        time.sleep(0.3)
        shot('login')

        drv.execute_cdp_cmd('Network.enable', {})
        drv.get(f'{BASE}/static/css/sigus.css')
        drv.execute_cdp_cmd('Network.clearBrowserCookies', {})
        drv.execute_cdp_cmd('Network.setCookie', {
            'name': 'session',
            'value': cookie,
            'url': 'http://localhost:5001/',
            'path': '/',
            'httpOnly': True,
            'secure': False,
            'sameSite': 'Lax',
        })

        if goto('/dashboard', '.page-header'):
            shot('dash')
            drv.execute_script("""
                const btn = document.querySelector('.sigus-navbar .fa-hospital');
                if (btn) {
                  const b = btn.closest('button');
                  if (b) b.click();
                }
            """)
            time.sleep(0.5)
            shot('dash-unidade')

        if unid_id and goto(f'/configuracoes/unidades/{unid_id}', '.page-header'):
            shot('un-ficha')
            tab = drv.find_elements(By.CSS_SELECTOR, '[data-bs-target="#tab-info"]')
            if tab:
                tab[0].click()
                time.sleep(0.4)
                shot('un-ficha-info')
            tab = drv.find_elements(By.CSS_SELECTOR, '[data-bs-target="#tab-chamados"]')
            if tab:
                tab[0].click()
                time.sleep(0.4)
                shot('un-ficha-chamados')

        if goto('/chamados/escolha-tipo', '.escolha-card'):
            shot('ch-escolha')
        if goto('/chamados/novo/predial', '.page-header'):
            shot('ch-predial')
        if goto('/chamados/', '.page-header'):
            shot('ch-lista')
        if goto('/chamados/gestao', '.page-header'):
            shot('ch-gestao')

        if goto('/seguranca-paciente/', '.page-header', JS_NSP_LISTA):
            shot('nsp-lista')
        if goto('/seguranca-paciente/nova', '.page-header'):
            drv.execute_script(JS_NSP_FORM)
            time.sleep(0.4)
            shot('nsp-nova')
            drv.execute_script('document.getElementById("blocoSis")?.scrollIntoView({block:"center"});')
            time.sleep(0.35)
            shot('nsp-nova-sis')
        if nsp_id and goto(f'/seguranca-paciente/{nsp_id}', '.page-header', JS_NSP_DETALHE):
            shot('nsp-detalhe')

        if goto('/planejamentos/', '.page-header'):
            shot('plan')
        if goto('/agenda/', '.page-header'):
            time.sleep(0.8)
            shot('agenda')

        if goto('/transferencias/', '.page-header'):
            shot('tr-lista')
        if goto('/rh/faltas-abonadas', '.page-header'):
            shot('faltas')
            btn = drv.find_elements(By.CSS_SELECTOR, '[data-bs-target="#modalNovaAbonada"]')
            if btn and btn[0].is_enabled():
                btn[0].click()
                time.sleep(0.5)
                shot('faltas-modal')

        drv.get(f'{BASE}/solicitar-vinculo-profissional')
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
            shot('vinculo')
        except Exception:
            print('  timeout vinculo')

        if goto('/relatorios/', '.page-header'):
            shot('relatorios')
        if goto('/contratos/', '.page-header'):
            shot('contratos')
        if goto('/configuracoes/', '.page-header'):
            shot('cfg')
        if goto('/configuracoes/perfis', '.page-header'):
            shot('cfg-perfis')
        if goto('/configuracoes/seguranca-paciente', '.page-header'):
            shot('cfg-nsp')

        print('ok')
        for p in sorted(OUT.glob('*.png')):
            if p.name.startswith('usr-'):
                continue
            print(p.name, p.stat().st_size)
    finally:
        drv.quit()


if __name__ == '__main__':
    main()
