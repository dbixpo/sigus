/* Acesso público: baixar QR code (PNG) e copiar endereço.
 * Botões: .js-qr-baixar[data-url][data-titulo][data-arquivo] e .js-copiar-url[data-url].
 * Depende de qrcode.min.js (qrcode-generator, global `qrcode`). */
(function () {
    'use strict';

    function gerarQr(url) {
        var qr = qrcode(0, 'M');
        qr.addData(url);
        qr.make();
        return qr;
    }

    function quebrarTexto(ctx, texto, larguraMax) {
        var partes = [];
        var atual = '';
        for (var i = 0; i < texto.length; i++) {
            var teste = atual + texto[i];
            if (ctx.measureText(teste).width > larguraMax && atual) {
                partes.push(atual);
                atual = texto[i];
            } else {
                atual = teste;
            }
        }
        if (atual) partes.push(atual);
        return partes;
    }

    function desenharCartao(url, titulo) {
        var qr = gerarQr(url);
        var n = qr.getModuleCount();
        var W = 900;
        var qrLado = 640;
        var celula = Math.floor(qrLado / (n + 8));
        var qrPx = celula * (n + 8);
        var canvas = document.createElement('canvas');
        canvas.width = W;
        canvas.height = 1040;
        var ctx = canvas.getContext('2d');

        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, W, canvas.height);

        var terco = W / 3;
        ctx.fillStyle = '#E63030'; ctx.fillRect(0, 0, terco, 14);
        ctx.fillStyle = '#F5C500'; ctx.fillRect(terco, 0, terco, 14);
        ctx.fillStyle = '#1A82B8'; ctx.fillRect(terco * 2, 0, W - terco * 2, 14);

        ctx.textAlign = 'center';
        ctx.fillStyle = '#0D3B5E';
        ctx.font = '700 52px Inter, "Segoe UI", Arial, sans-serif';
        ctx.fillText(titulo || 'Acesso público', W / 2, 110);
        ctx.fillStyle = '#718096';
        ctx.font = '500 26px Inter, "Segoe UI", Arial, sans-serif';
        ctx.fillText('Aponte a câmera do celular para acessar', W / 2, 160);

        var x0 = Math.round((W - qrPx) / 2);
        var y0 = 200;
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(x0, y0, qrPx, qrPx);
        ctx.fillStyle = '#0D3B5E';
        for (var r = 0; r < n; r++) {
            for (var c = 0; c < n; c++) {
                if (qr.isDark(r, c)) {
                    ctx.fillRect(x0 + (c + 4) * celula, y0 + (r + 4) * celula, celula, celula);
                }
            }
        }

        ctx.fillStyle = '#1E3A50';
        ctx.font = '500 24px Inter, "Segoe UI", Arial, sans-serif';
        var linhas = quebrarTexto(ctx, url, W - 120);
        var y = y0 + qrPx + 60;
        linhas.forEach(function (l) { ctx.fillText(l, W / 2, y); y += 34; });

        ctx.fillStyle = '#1A82B8';
        ctx.font = '700 28px Inter, "Segoe UI", Arial, sans-serif';
        ctx.fillText('SIGUS · Saúde Digital', W / 2, canvas.height - 50);
        return canvas;
    }

    function baixarQr(url, titulo, arquivo) {
        if (typeof qrcode === 'undefined') {
            alert('Não foi possível gerar o QR code agora. Recarregue a página e tente de novo.');
            return;
        }
        var fontes = (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve();
        fontes.then(function () {
            var canvas = desenharCartao(url, titulo);
            var a = document.createElement('a');
            a.download = (arquivo || 'qrcode') + '.png';
            a.href = canvas.toDataURL('image/png');
            document.body.appendChild(a);
            a.click();
            a.remove();
        });
    }

    function copiar(url, botao) {
        function ok() {
            if (!botao) return;
            var original = botao.innerHTML;
            botao.innerHTML = '<i class="fas fa-check"></i>' + (botao.dataset.rotuloCopiado ? ' ' + botao.dataset.rotuloCopiado : '');
            botao.classList.add('copiado');
            setTimeout(function () { botao.innerHTML = original; botao.classList.remove('copiado'); }, 1600);
        }
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(url).then(ok, function () { copiarFallback(url); ok(); });
        } else {
            copiarFallback(url);
            ok();
        }
    }

    function copiarFallback(url) {
        var t = document.createElement('textarea');
        t.value = url;
        t.setAttribute('readonly', '');
        t.style.position = 'fixed';
        t.style.opacity = '0';
        document.body.appendChild(t);
        t.select();
        try { document.execCommand('copy'); } catch (e) { /* sem suporte */ }
        t.remove();
    }

    function previaQr(el, url) {
        if (!el || typeof qrcode === 'undefined') return;
        el.innerHTML = gerarQr(url).createSvgTag({ scalable: true, margin: 2 });
        var svg = el.querySelector('svg');
        if (svg) svg.style.cssText = 'width:100%;height:100%;display:block;';
    }

    document.addEventListener('click', function (ev) {
        var qrBtn = ev.target.closest('.js-qr-baixar');
        if (qrBtn) {
            ev.preventDefault();
            baixarQr(qrBtn.dataset.url, qrBtn.dataset.titulo, qrBtn.dataset.arquivo);
            return;
        }
        var cpBtn = ev.target.closest('.js-copiar-url');
        if (cpBtn) {
            ev.preventDefault();
            copiar(cpBtn.dataset.url, cpBtn);
        }
    });

    window.SigusAcessoPublico = { baixarQr: baixarQr, copiar: copiar, previaQr: previaQr };
})();
