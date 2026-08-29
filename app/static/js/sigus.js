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

    // ── Confirmar ações destrutivas ─────────────────────────
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

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
