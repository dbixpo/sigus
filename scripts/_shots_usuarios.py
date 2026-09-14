# -*- coding: utf-8 -*-
"""Prints temporários das telas de usuário para o manual da Estante.

Usa o SIGUS local em http://localhost:5001/sigus (não use 127.0.0.1:
o Chrome recusa cookie de sessão em endereço IP). Dados visíveis nos
PNG são fictícios — nomes reais da base são trocados via JS antes do print.
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
from app.models.matricula import MatriculaProfissional
from app.models.usuario import Usuario

OUT = ROOT / 'app' / 'static' / 'uploads' / 'manuais_tmp'
BASE = 'http://localhost:5001/sigus'

JS_ANON_NAV = """
const toggles = document.querySelectorAll('.sigus-navbar .dropdown-toggle');
const userBtn = toggles[toggles.length - 1];
if (userBtn) {
  userBtn.querySelectorAll('span').forEach((s) => {
    if (s.textContent.trim().length <= 2) s.textContent = 'A';
    else s.textContent = 'Admin';
  });
}
"""

JS_ANON_LISTA = JS_ANON_NAV + """
document.querySelectorAll('table tbody tr').forEach((tr, i) => {
  const tds = tr.querySelectorAll('td');
  if (!tds.length) return;
  const n = String(i + 1).padStart(2, '0');
  if (tds[0]) tds[0].textContent = i === 0 ? 'PROFISSIONAL EXEMPLO' : ('USUÁRIO DEMONSTRAÇÃO ' + n);
  if (tds[1]) tds[1].textContent = i === 0 ? 'profissional.exemplo@sorocaba.sp.gov.br' : ('usuario' + n + '@sorocaba.sp.gov.br');
  if (tds[2]) tds[2].textContent = '(15) 90000-0000';
  if (tds[4]) tds[4].textContent = i === 0 ? '123456 | Enfermeiro' : '—';
});
"""

JS_FILL_NOVO = """
const setv = (sel, val) => { const el = document.querySelector(sel); if (el) el.value = val; };
setv('#campoCPF', '000.000.000-00');
setv('[name=nome]', 'PROFISSIONAL EXEMPLO');
setv('[name=email]', 'profissional.exemplo');
setv('#inputWhatsapp', '(15) 90000-0000');
const st = document.getElementById('statusImportarCadastro');
if (st) {
  st.textContent = 'Importamos 18 campos. Confira as abas — nada fica travado. Conselho COREN-SP 000000 — depois de criar o usuário, importe na aba Matrículas.';
  st.className = 'small mt-2 mb-0 text-success';
}
setv('#campoCNS', '000000000000000');
setv('[name=nome_mae]', 'MARIA EXEMPLO');
setv('[name=nome_pai]', 'JOSE EXEMPLO');
setv('[name=data_nasc]', '1985-03-15');
const sexoF = document.getElementById('sexoF');
if (sexoF) sexoF.checked = true;
setv('[name=rg]', '00.000.000-0');
setv('[name=rg_uf]', 'SP');
setv('[name=rg_orgao]', 'SSP');
setv('[name=uf_nasc]', 'SP');
setv('[name=municipio_nasc]', 'SOROCABA');
setv('[name=end_logradouro]', 'RUA EXEMPLO');
setv('[name=end_numero]', '100');
setv('[name=end_bairro]', 'CENTRO');
setv('[name=end_municipio]', 'Sorocaba');
setv('[name=end_uf]', 'SP');
setv('[name=end_cep]', '18000-000');
setv('[name=telefone]', '(15) 3222-0000');
"""

JS_ANON_EDIT = JS_ANON_NAV + JS_FILL_NOVO + """
const h1 = document.querySelector('.page-header h1');
if (h1) h1.innerHTML = '<i class="fas fa-user-plus"></i> Editar — PROFISSIONAL EXEMPLO';
document.querySelectorAll('#listaMatriculas tbody tr').forEach((tr, i) => {
  const tds = tr.querySelectorAll('td');
  if (!tds.length) return;
  if (tds[0]) tds[0].textContent = i === 0 ? '123456' : 'Sem Matrícula';
  if (tds[4]) tds[4].textContent = '000000';
  if (tds[5]) tds[5].textContent = 'COREN-SP';
});
"""

JS_CONSULTA_SIS = JS_ANON_NAV + """
const cardNome = document.querySelector('.avatar-wrap') && document.querySelector('.avatar-wrap').closest('.card');
if (cardNome) {
  const fw = cardNome.querySelector('.fw-semibold');
  if (fw) fw.textContent = 'PROFISSIONAL EXEMPLO';
}
const ini = document.getElementById('avatarInicial');
if (ini) ini.textContent = 'P';
const nome = document.querySelector('input[name=nome]');
if (nome) nome.value = 'PROFISSIONAL EXEMPLO';
document.querySelectorAll('input.form-control').forEach((el) => {
  if ((el.getAttribute('type') === 'email') || (el.value && el.value.indexOf('@') >= 0 && el.disabled)) {
    el.value = 'profissional.exemplo@sorocaba.sp.gov.br';
  }
});
document.querySelectorAll('.notif-item-perfil').forEach((el) => {
  el.innerHTML = '<div class="fw-semibold">Notificação de exemplo</div><div class="text-muted small">Aviso ilustrativo para o manual.</div>';
});
const status = document.getElementById('statusSisPerfil');
const painel = document.getElementById('painelSisPerfil');
if (status) {
  status.textContent = 'Consulta concluída. Isso é só visualização — o SIGUS não altera o SIS.';
  status.className = 'small mt-2 mb-0 text-success';
}
if (painel) {
  painel.classList.remove('d-none');
  painel.innerHTML = `
    <div class="card mb-2"><div class="card-header py-2 small fw-semibold">Pessoa no SIS</div>
    <div class="card-body py-2">
      <div class="d-flex justify-content-between gap-3 py-1 border-bottom"><span class="text-muted small">Nome</span><span class="small text-end">PROFISSIONAL EXEMPLO</span></div>
      <div class="d-flex justify-content-between gap-3 py-1 border-bottom"><span class="text-muted small">CPF</span><span class="small text-end">000.000.000-00</span></div>
      <div class="d-flex justify-content-between gap-3 py-1 border-bottom"><span class="text-muted small">Nascimento</span><span class="small text-end">15/03/1985</span></div>
    </div></div>
    <div class="card mb-2"><div class="card-header py-2 small fw-semibold">Profissional / operador</div>
    <div class="card-body py-2">
      <div class="d-flex justify-content-between gap-3 py-1 border-bottom"><span class="text-muted small">E-mail</span><span class="small text-end">profissional.exemplo@sorocaba.sp.gov.br</span></div>
      <div class="d-flex justify-content-between gap-3 py-1 border-bottom"><span class="text-muted small">Conselho</span><span class="small text-end">COREN-SP 000000</span></div>
    </div></div>
    <div class="card mb-2"><div class="card-header py-2 small fw-semibold">CNES</div>
    <div class="card-body py-2">
      <div class="d-flex justify-content-between gap-3 py-1 border-bottom"><span class="text-muted small">CNS</span><span class="small text-end">000000000000000</span></div>
    </div></div>`;
}
"""


def session_cookie(app, user_id: int) -> str:
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user_id)
            sess['_fresh'] = True
        if hasattr(client, 'get_cookie'):
            ck = client.get_cookie('session')
            if ck:
                return ck.value
        raise RuntimeError('Não consegui montar o cookie de sessão para o print.')


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
            raise SystemExit('Nenhum administrador ativo para o print.')
        mat = (
            MatriculaProfissional.query.filter_by(ativo=True)
            .join(Usuario)
            .filter(Usuario.perfil != 'administrador')
            .first()
        )
        edit_id = mat.usuario_id if mat else u.id
        uid = u.id

    cookie = session_cookie(app, uid)
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--window-size=1440,1100')
    opts.add_argument('--hide-scrollbars')
    opts.add_argument('--disable-gpu')
    opts.add_experimental_option('excludeSwitches', ['enable-automation'])
    drv = webdriver.Chrome(options=opts)
    wait = WebDriverWait(drv, 40)

    def shot(stem: str) -> None:
        time.sleep(0.35)
        drv.save_screenshot(str(OUT / f'{stem}.png'))

    def goto(path: str, css: str) -> None:
        drv.get(f'{BASE}{path}')
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
        if drv.find_elements(By.CSS_SELECTOR, '.login-wrapper'):
            raise RuntimeError(f'Sessão não colou em {path} (caiu no login). url={drv.current_url}')

    try:
        # Página estática do mesmo host: o GET em /login gravaria um cookie
        # HttpOnly anônimo e o Chrome não deixa o Selenium sobrescrever.
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

        goto('/usuarios/', '.page-header')
        drv.execute_script("""
            const g = document.querySelector('.sidebar-group[data-group="configuracoes"]');
            if (g) g.classList.add('open', 'has-active');
            const btn = g && g.querySelector('.sidebar-group-toggle');
            if (btn) btn.setAttribute('aria-expanded', 'true');
        """)
        drv.execute_script(JS_ANON_LISTA)
        shot('usr-menu')
        shot('usr-lista')

        goto('/usuarios/novo', '#campoCPF')
        drv.execute_script(JS_ANON_NAV)
        shot('usr-novo-acesso')
        drv.execute_script(JS_FILL_NOVO)
        drv.execute_script(JS_ANON_NAV)
        shot('usr-novo-importado')

        drv.find_element(By.CSS_SELECTOR, '[data-bs-target="#tab-pessoal"]').click()
        time.sleep(0.4)
        shot('usr-novo-pessoal')

        drv.find_element(By.CSS_SELECTOR, '[data-bs-target="#tab-endereco"]').click()
        time.sleep(0.4)
        shot('usr-novo-endereco')

        goto(f'/usuarios/{edit_id}/editar', '#campoCPF')
        drv.execute_script(JS_ANON_EDIT)
        drv.find_element(By.CSS_SELECTOR, '[data-bs-target="#tab-matriculas"]').click()
        time.sleep(0.45)
        shot('usr-matriculas')
        drv.find_element(By.CSS_SELECTOR, '[data-bs-target="#modalNovaMatricula"]').click()
        wait.until(EC.visibility_of_element_located((By.ID, 'modalNovaMatricula')))
        drv.execute_script("""
            const st = document.getElementById('statusConselhoSis');
            if (st) {
              st.textContent = 'Encontramos 1 conselho: COREN-SP 000000. Conferimos os campos — você pode alterar.';
              st.className = 'small mt-2 mb-0 text-success';
            }
            const org = document.getElementById('matOrgao');
            if (org) org.value = 'COREN-SP';
            const n = document.getElementById('matConselho');
            if (n) n.value = '000000';
        """)
        time.sleep(0.45)
        shot('usr-matricula-modal')

        goto('/perfil', '.page-header')
        drv.execute_script(JS_CONSULTA_SIS)
        drv.execute_script("""
            const p = document.getElementById('painelSisPerfil');
            const s = document.getElementById('statusSisPerfil');
            if (p) p.classList.add('d-none');
            if (s) { s.textContent = ''; s.className = 'small mt-2 mb-0'; }
        """)
        drv.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(0.4)
        shot('usr-perfil-sis')
        drv.execute_script(JS_CONSULTA_SIS)
        drv.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(0.4)
        shot('usr-perfil-sis-resultado')

        print('ok', edit_id)
        for p in sorted(OUT.glob('usr-*.png')):
            print(p.name, p.stat().st_size)
    except Exception:
        try:
            (OUT / '_debug_url.txt').write_text(
                f'{drv.current_url}\n{drv.title}\n{drv.page_source[:2500]}',
                encoding='utf-8',
            )
        except Exception:
            pass
        raise
    finally:
        drv.quit()


if __name__ == '__main__':
    main()
