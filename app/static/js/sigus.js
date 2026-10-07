/* SIGUS — JavaScript Principal */

document.addEventListener('DOMContentLoaded', function () {

    // ── Toggle sidebar ──────────────────────────────────────
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const main = document.querySelector('.sigus-main');

    // Cria overlay uma vez
    let overlay = document.getElementById('sidebarOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'sidebarOverlay';
        overlay.className = 'sigus-sidebar-overlay';
        document.body.appendChild(overlay);
    }

    function closeSidebarMobile() {
        if (sidebar) sidebar.classList.remove('mobile-open');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function () {
            if (window.innerWidth < 992) {
                const isOpen = sidebar.classList.toggle('mobile-open');
                overlay.classList.toggle('active', isOpen);
                document.body.style.overflow = isOpen ? 'hidden' : '';
            } else {
                sidebar.classList.toggle('collapsed');
                if (main) main.classList.toggle('expanded');
            }
        });

        // Fechar ao clicar no overlay
        overlay.addEventListener('click', closeSidebarMobile);

        // Fechar ao navegar (links do sidebar)
        sidebar.querySelectorAll('a').forEach(a => {
            a.addEventListener('click', function () {
                if (window.innerWidth < 992) closeSidebarMobile();
            });
        });
    }

    // ── Menu: busca + seções recolhíveis ────────────────────
    (function initSidebarMenu() {
        if (!sidebar) return;
        const STORAGE_KEY = 'sigus-sidebar-groups';
        const groups = Array.from(sidebar.querySelectorAll('.sidebar-group'));
        const searchInput = document.getElementById('sidebarSearch');
        const emptyEl = document.getElementById('sidebarSearchEmpty');
        const topItems = Array.from(sidebar.querySelectorAll('.sidebar-nav > ul > .nav-item'));

        function loadState() {
            try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
            catch (e) { return {}; }
        }
        function saveState() {
            const state = {};
            groups.forEach(g => { state[g.dataset.group] = g.classList.contains('open'); });
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        }
        function setOpen(group, open) {
            group.classList.toggle('open', open);
            const btn = group.querySelector('.sidebar-group-toggle');
            if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
        }
        function normalize(text) {
            return (text || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
        }

        const saved = loadState();
        groups.forEach(group => {
            const hasActive = !!group.querySelector('.nav-link.active');
            group.classList.toggle('has-active', hasActive);
            const remembered = saved[group.dataset.group];
            setOpen(group, hasActive || remembered === true);
            const btn = group.querySelector('.sidebar-group-toggle');
            if (btn) {
                btn.addEventListener('click', function () {
                    if (searchInput && searchInput.value.trim()) return;
                    setOpen(group, !group.classList.contains('open'));
                    saveState();
                });
            }
        });

        if (!searchInput) return;

        function applySearch() {
            const q = normalize(searchInput.value);
            let visible = 0;

            function matchItem(item) {
                const label = item.querySelector('.nav-link span');
                const ok = !q || normalize(label ? label.textContent : '').includes(q);
                item.classList.toggle('d-none', !ok);
                if (ok) visible += 1;
                return ok;
            }

            topItems.forEach(matchItem);
            groups.forEach(group => {
                let any = false;
                group.querySelectorAll(':scope > .sidebar-group-items > .nav-item').forEach(item => {
                    if (matchItem(item)) any = true;
                });
                group.classList.toggle('d-none', !!q && !any);
                group.classList.toggle('filtering', !!q && any);
            });

            if (emptyEl) emptyEl.classList.toggle('d-none', !(q && visible === 0));
        }

        searchInput.addEventListener('input', applySearch);
        searchInput.addEventListener('keydown', function (ev) {
            if (ev.key === 'Escape') {
                searchInput.value = '';
                applySearch();
                searchInput.blur();
            }
        });
    })();

    // ── Auto-fechar alertas após 5s ─────────────────────────
    document.querySelectorAll('.alert:not(.alert-permanent)').forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // ── Carregar salas ao selecionar unidade (chamados) ─────
    const selectUnidade = document.getElementById('unidade_id');
    const selectSala = document.getElementById('sala_id');
    const selectEquip = document.getElementById('equipamento_id');

    const selectPredio = document.getElementById('predio_id');

    if (selectUnidade && selectSala) {
        selectUnidade.addEventListener('change', function () {
            const unidadeId = this.value;
            selectSala.innerHTML = '<option value="">Selecione uma sala...</option>';
            if (selectEquip) selectEquip.innerHTML = '<option value="">Selecione um equipamento...</option>';

            if (!unidadeId) return;
            const baseUrl = window.SIGUS_BASE_URL || '';
            fetch(`${baseUrl}/chamados/api/salas/${unidadeId}`)
                .then(r => r.json())
                .then(data => {
                    // Suporte ao novo formato {predio_id, salas} e ao antigo array
                    const salas = Array.isArray(data) ? data : data.salas;
                    salas.forEach(s => {
                        const opt = document.createElement('option');
                        opt.value = s.id;
                        opt.textContent = s.nome;
                        selectSala.appendChild(opt);
                    });
                    // Preenche predio_id automaticamente se a unidade pertence a um prédio
                    if (selectPredio && !Array.isArray(data) && data.predio_id) {
                        selectPredio.value = data.predio_id;
                        selectPredio.dispatchEvent(new Event('change'));
                    } else if (selectPredio && !Array.isArray(data) && !data.predio_id) {
                        selectPredio.value = '';
                    }
                });
        });
    }

    if (selectSala && selectEquip) {
        selectSala.addEventListener('change', function () {
            const salaId = this.value;
            selectEquip.innerHTML = '<option value="">Selecione um equipamento...</option>';
            if (!salaId) return;
            const baseUrl = window.SIGUS_BASE_URL || '';
            fetch(`${baseUrl}/chamados/api/equipamentos/${salaId}`)
                .then(r => r.json())
                .then(equips => {
                    equips.forEach(e => {
                        const opt = document.createElement('option');
                        opt.value = e.id;
                        opt.textContent = e.nome;
                        selectEquip.appendChild(opt);
                    });
                });
        });
    }

    // ── Carregar modelos ao selecionar marca (equipamentos) ─
    const selectMarca = document.getElementById('marca_id');
    const selectModelo = document.getElementById('modelo_id');

    if (selectMarca && selectModelo) {
        selectMarca.addEventListener('change', function () {
            const marcaId = this.value;
            selectModelo.innerHTML = '<option value="">Selecione o modelo...</option>';
            if (!marcaId) return;
            const baseUrl = window.SIGUS_BASE_URL || '';
            fetch(`${baseUrl}/equipamentos/api/modelos/${marcaId}`)
                .then(r => r.json())
                .then(modelos => {
                    modelos.forEach(m => {
                        const opt = document.createElement('option');
                        opt.value = m.id;
                        opt.textContent = m.nome;
                        selectModelo.appendChild(opt);
                    });
                });
        });
    }

    // ── Carregar campos customizados ao selecionar tipo ─────
    const selectTipo = document.getElementById('tipo_equipamento_id');
    const camposContainer = document.getElementById('campos-customizados');

    if (selectTipo && camposContainer) {
        selectTipo.addEventListener('change', function () {
            const tipoId = this.value;
            camposContainer.innerHTML = '';
            if (!tipoId) return;
            const baseUrl = window.SIGUS_BASE_URL || '';
            fetch(`${baseUrl}/equipamentos/api/campos/${tipoId}`)
                .then(r => r.json())
                .then(campos => {
                    if (campos.length === 0) return;
                    const titulo = document.createElement('div');
                    titulo.className = 'form-section-title mt-3';
                    titulo.textContent = 'Informações Específicas do Tipo';
                    camposContainer.appendChild(titulo);

                    campos.forEach(c => {
                        const div = document.createElement('div');
                        div.className = 'col-md-6 mb-3';
                        const label = document.createElement('label');
                        label.className = 'form-label';
                        label.textContent = c.nome_campo + (c.obrigatorio ? ' *' : '');
                        div.appendChild(label);

                        let input;
                        if (c.tipo_dado === 'selecao' && c.opcoes_selecao) {
                            input = document.createElement('select');
                            input.className = 'form-select';
                            input.name = `campo_${c.id}`;
                            if (!c.obrigatorio) {
                                const opt = document.createElement('option');
                                opt.value = '';
                                opt.textContent = 'Selecione...';
                                input.appendChild(opt);
                            }
                            c.opcoes_selecao.forEach(op => {
                                const opt = document.createElement('option');
                                opt.value = op;
                                opt.textContent = op;
                                input.appendChild(opt);
                            });
                        } else if (c.tipo_dado === 'texto_longo') {
                            input = document.createElement('textarea');
                            input.className = 'form-control';
                            input.name = `campo_${c.id}`;
                            input.rows = 2;
                        } else {
                            input = document.createElement('input');
                            input.className = 'form-control';
                            input.name = `campo_${c.id}`;
                            input.type = c.tipo_dado === 'numero' ? 'number' :
                                         c.tipo_dado === 'data' ? 'date' : 'text';
                        }
                        if (c.obrigatorio) input.required = true;
                        div.appendChild(input);
                        camposContainer.appendChild(div);
                    });
                });
        });
    }

    // ── Confirmar ações destrutivas (modal do SIGUS) ────────
    // Uso: data-confirm="Texto" em <form>, botão ou link.
    // Opcionais: data-confirm-titulo, data-confirm-ok, data-confirm-icone, data-confirm-perigo="0".
    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form.matches || !form.matches('form[data-confirm]')) return;
        if (form._sigusConfirmado) { form._sigusConfirmado = false; return; }
        e.preventDefault();
        const submitter = e.submitter || null;
        sigusConfirmar(opcoesConfirm(form)).then(function (ok) {
            if (!ok) return;
            form._sigusConfirmado = true;
            if (form.requestSubmit) form.requestSubmit(submitter && submitter.form === form ? submitter : undefined);
            else form.submit();
        });
    }, true);

    document.addEventListener('click', function (e) {
        const el = e.target.closest && e.target.closest('[data-confirm]:not(form)');
        if (!el) return;
        if (el._sigusConfirmado) { el._sigusConfirmado = false; return; }
        e.preventDefault();
        e.stopImmediatePropagation();
        sigusConfirmar(opcoesConfirm(el)).then(function (ok) {
            if (!ok) return;
            el._sigusConfirmado = true;
            el.click();
        });
    }, true);

    // ── Máscaras simples ────────────────────────────────────
    const cepInput = document.querySelector('input[name="cep"]');
    if (cepInput) {
        cepInput.addEventListener('input', function () {
            let v = this.value.replace(/\D/g, '').slice(0, 8);
            if (v.length > 5) v = v.slice(0, 5) + '-' + v.slice(5);
            this.value = v;
        });
    }

    const telInput = document.querySelector('input[name="telefone"]');
    if (telInput) {
        telInput.addEventListener('input', function () {
            let v = this.value.replace(/\D/g, '').slice(0, 11);
            if (v.length > 10) v = `(${v.slice(0,2)}) ${v.slice(2,7)}-${v.slice(7)}`;
            else if (v.length > 6) v = `(${v.slice(0,2)}) ${v.slice(2,6)}-${v.slice(6)}`;
            else if (v.length > 2) v = `(${v.slice(0,2)}) ${v.slice(2)}`;
            this.value = v;
        });
    }
});

function opcoesConfirm(el) {
    const d = el.dataset;
    return {
        titulo: d.confirmTitulo || 'Confirmar',
        texto: d.confirm || 'Tem certeza?',
        ok: d.confirmOk || 'Confirmar',
        perigo: d.confirmPerigo !== '0',
        icone: d.confirmIcone || '',
    };
}

/* Modal de confirmação do SIGUS. Retorna Promise<boolean>. */
function sigusConfirmar(opts) {
    opts = opts || {};
    let modalEl = document.getElementById('sigusConfirmModal');
    if (!modalEl) {
        modalEl = document.createElement('div');
        modalEl.className = 'modal fade sigus-confirm';
        modalEl.id = 'sigusConfirmModal';
        modalEl.tabIndex = -1;
        modalEl.setAttribute('aria-hidden', 'true');
        modalEl.innerHTML =
            '<div class="modal-dialog modal-dialog-centered">' +
              '<div class="modal-content">' +
                '<div class="modal-body">' +
                  '<div class="sigus-confirm-icone"><i class="fas fa-trash-alt"></i></div>' +
                  '<h5 class="sigus-confirm-titulo"></h5>' +
                  '<p class="sigus-confirm-texto"></p>' +
                '</div>' +
                '<div class="modal-footer">' +
                  '<button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancelar</button>' +
                  '<button type="button" class="btn sigus-confirm-ok"></button>' +
                '</div>' +
              '</div>' +
            '</div>';
        document.body.appendChild(modalEl);
    }
    const perigo = opts.perigo !== false;
    modalEl.classList.toggle('is-perigo', perigo);
    modalEl.querySelector('.sigus-confirm-icone i').className = 'fas ' + (opts.icone || (perigo ? 'fa-exclamation-triangle' : 'fa-question'));
    modalEl.querySelector('.sigus-confirm-titulo').textContent = opts.titulo || 'Confirmar';
    modalEl.querySelector('.sigus-confirm-texto').textContent = opts.texto || 'Tem certeza?';
    const btnOk = modalEl.querySelector('.sigus-confirm-ok');
    btnOk.textContent = opts.ok || 'Confirmar';
    btnOk.className = 'btn sigus-confirm-ok ' + (perigo ? 'btn-danger' : 'btn-primary');

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    return new Promise(function (resolve) {
        let confirmado = false;
        function aoOk() { confirmado = true; modal.hide(); }
        function aoMostrar() {
            (perigo ? modalEl.querySelector('[data-bs-dismiss="modal"]') : btnOk).focus();
        }
        function aoFechar() {
            btnOk.removeEventListener('click', aoOk);
            modalEl.removeEventListener('shown.bs.modal', aoMostrar);
            resolve(confirmado);
        }
        btnOk.addEventListener('click', aoOk);
        modalEl.addEventListener('shown.bs.modal', aoMostrar);
        modalEl.addEventListener('hidden.bs.modal', aoFechar, { once: true });
        modal.show();
    });
}
window.sigusConfirmar = sigusConfirmar;
