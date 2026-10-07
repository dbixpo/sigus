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

    var FONTE = 'Inter, "Segoe UI", Arial, sans-serif';

    function quebrarCaracteres(ctx, texto, larguraMax) {
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

    /* Junta pedaços (palavras ou trechos de URL) em linhas; pedaço maior que a linha cai por caractere. */
    function quebrarPedacos(ctx, pedacos, larguraMax, separador) {
        var linhas = [];
        var atual = '';
        pedacos.forEach(function (p) {
            var teste = atual ? atual + separador + p : p;
            if (ctx.measureText(teste).width <= larguraMax) {
                atual = teste;
                return;
            }
            if (atual) linhas.push(atual);
            if (ctx.measureText(p).width > larguraMax) {
                var cortes = quebrarCaracteres(ctx, p, larguraMax);
                atual = cortes.pop();
                linhas = linhas.concat(cortes);
            } else {
                atual = p;
            }
        });
        if (atual) linhas.push(atual);
        return linhas;
    }

    function linhasTitulo(ctx, titulo, larguraMax) {
        var palavras = titulo.split(/\s+/).filter(Boolean);
        var trechos = titulo.split(/\s+·\s+/);
        for (var tam = 52; tam >= 34; tam -= 2) {
            ctx.font = '700 ' + tam + 'px ' + FONTE;
            if (trechos.length > 1 && ctx.measureText(titulo).width > larguraMax
                    && trechos.every(function (t) { return ctx.measureText(t).width <= larguraMax; })) {
                return { linhas: trechos, tam: tam };
            }
            var linhas = quebrarPedacos(ctx, palavras, larguraMax, ' ');
            if (linhas.length <= 2 || tam === 34) return { linhas: linhas, tam: tam };
        }
    }

    function linhasUrl(ctx, url, larguraMax) {
        ctx.font = '500 24px ' + FONTE;
        var pedacos = url.replace(/\//g, '/\u0000').split('\u0000').filter(Boolean);
        return quebrarPedacos(ctx, pedacos, larguraMax, '');
    }

    function desenharCartao(url, titulo) {
        var qr = gerarQr(url);
        var n = qr.getModuleCount();
        var W = 900;
        var margem = 70;
        var qrLado = 640;
        var celula = Math.floor(qrLado / (n + 8));
        var qrPx = celula * (n + 8);

        var medida = document.createElement('canvas').getContext('2d');
        var tit = linhasTitulo(medida, titulo || 'Acesso público', W - margem * 2);
        var alturaTitulo = Math.round(tit.tam * 1.2);
        var urls = linhasUrl(medida, url, W - margem * 2);

        var yTitulo = 60 + tit.tam;
        var ySub = yTitulo + (tit.linhas.length - 1) * alturaTitulo + 50;
        var yQr = ySub + 34;
        var yUrl = yQr + qrPx + 56;
        var yRodape = yUrl + (urls.length - 1) * 34 + 80;

        var canvas = document.createElement('canvas');
        canvas.width = W;
        canvas.height = yRodape + 50;
        var ctx = canvas.getContext('2d');

        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, W, canvas.height);

        var terco = W / 3;
        ctx.fillStyle = '#E63030'; ctx.fillRect(0, 0, terco, 14);
        ctx.fillStyle = '#F5C500'; ctx.fillRect(terco, 0, terco, 14);
        ctx.fillStyle = '#1A82B8'; ctx.fillRect(terco * 2, 0, W - terco * 2, 14);

        ctx.textAlign = 'center';
        ctx.fillStyle = '#0D3B5E';
        ctx.font = '700 ' + tit.tam + 'px ' + FONTE;
        tit.linhas.forEach(function (l, i) { ctx.fillText(l, W / 2, yTitulo + i * alturaTitulo); });
        ctx.fillStyle = '#718096';
        ctx.font = '500 26px ' + FONTE;
        ctx.fillText('Aponte a câmera do celular para acessar', W / 2, ySub);

        var x0 = Math.round((W - qrPx) / 2);
        ctx.fillStyle = '#0D3B5E';
        for (var r = 0; r < n; r++) {
            for (var c = 0; c < n; c++) {
                if (qr.isDark(r, c)) {
                    ctx.fillRect(x0 + (c + 4) * celula, yQr + (r + 4) * celula, celula, celula);
                }
            }
        }

        ctx.fillStyle = '#1E3A50';
        ctx.font = '500 24px ' + FONTE;
        urls.forEach(function (l, i) { ctx.fillText(l, W / 2, yUrl + i * 34); });

        ctx.fillStyle = '#1A82B8';
        ctx.font = '700 28px ' + FONTE;
        ctx.fillText('SIGUS · Saúde Digital', W / 2, yRodape);
        return canvas;
    }

    function urlAbsoluta(url) {
        try { return new URL(url, document.baseURI).href; } catch (e) { return url; }
    }

    function nomeArquivo(titulo) {
        var base = (titulo || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60);
        return base ? 'qrcode-' + base : 'qrcode';
    }

    function baixarQr(url, titulo, arquivo) {
        if (typeof qrcode === 'undefined') {
            alert('Não foi possível gerar o QR code agora. Recarregue a página e tente de novo.');
            return;
        }
        url = urlAbsoluta(url);
        var fontes = (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve();
        fontes.then(function () {
            var canvas = desenharCartao(url, titulo);
            var a = document.createElement('a');
            a.download = (arquivo || nomeArquivo(titulo)) + '.png';
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
