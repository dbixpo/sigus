/* Busca de tipo de equipamento. O campo só lista depois de 2 letras.
 * <input data-busca-tipo data-url data-alvo="id-do-hidden">
 * A lista é o .js-lista-tipo irmão seguinte do grupo, ou o próximo .js-lista-tipo. */
(function () {
    'use strict';

    document.querySelectorAll('[data-busca-tipo]').forEach(function (input) {
        var hidden = document.getElementById(input.dataset.alvo);
        var lista = input.parentElement.querySelector('.js-lista-tipo');
        var form = input.closest('form');
        if (!hidden || !lista) return;
        var timer = null;
        var seq = 0;
        var escolhido = hidden.value ? input.value : '';

        function fechar() {
            lista.style.display = 'none';
            lista.innerHTML = '';
        }

        function exigirEscolha() {
            if (hidden.value) {
                input.setCustomValidity('');
                return true;
            }
            input.setCustomValidity('Escolha um tipo da lista.');
            return false;
        }

        input.addEventListener('input', function () {
            input.setCustomValidity('');
            if (input.value !== escolhido) {
                if (hidden.value) {
                    hidden.value = '';
                    hidden.dispatchEvent(new Event('change', { bubbles: true }));
                }
                escolhido = '';
            }
            var q = input.value.trim();
            clearTimeout(timer);
            if (q.length < 2) { fechar(); return; }
            timer = setTimeout(function () {
                var meu = ++seq;
                fetch(input.dataset.url + '?q=' + encodeURIComponent(q), { headers: { 'Accept': 'application/json' } })
                    .then(function (resp) { return resp.ok ? resp.json() : null; })
                    .then(function (data) {
                        if (!data || meu !== seq) return;
                        lista.innerHTML = '';
                        var itens = data.resultados || [];
                        if (!itens.length) {
                            var vazio = document.createElement('div');
                            vazio.className = 'list-group-item text-muted small';
                            vazio.textContent = 'Nenhum tipo com esse nome.';
                            lista.appendChild(vazio);
                        } else {
                            itens.forEach(function (tipo) {
                                var botao = document.createElement('button');
                                botao.type = 'button';
                                botao.className = 'list-group-item list-group-item-action py-2';
                                botao.textContent = tipo.nome;
                                if (tipo.classificacao) {
                                    var extra = document.createElement('span');
                                    extra.className = 'text-muted';
                                    extra.textContent = ' — ' + tipo.classificacao;
                                    botao.appendChild(extra);
                                }
                                botao.addEventListener('click', function () {
                                    hidden.value = String(tipo.id);
                                    input.value = tipo.nome;
                                    escolhido = tipo.nome;
                                    input.setCustomValidity('');
                                    fechar();
                                    hidden.dispatchEvent(new Event('change', { bubbles: true }));
                                });
                                lista.appendChild(botao);
                            });
                        }
                        lista.style.display = 'block';
                    })
                    .catch(function () { fechar(); });
            }, 250);
        });

        document.addEventListener('click', function (ev) {
            if (!input.contains(ev.target) && !lista.contains(ev.target)) fechar();
        });

        if (form) {
            form.addEventListener('submit', function (ev) {
                if (!exigirEscolha()) {
                    ev.preventDefault();
                    input.reportValidity();
                }
            });
        }
    });
})();
