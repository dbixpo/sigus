(function () {
    var semPat = document.getElementById('sem_patrimonio');
    var semSer = document.getElementById('sem_serie');
    var pat = document.getElementById('numero_patrimonio');
    var ser = document.getElementById('numero_serie');
    var bloco = document.getElementById('blocoFotoEquipamento');
    if (!semPat || !semSer || !pat || !ser || !bloco) return;

    var atual = document.getElementById('fotoAtualEquipamento');
    var aviso = document.getElementById('avisoFoto');
    var recorte = document.getElementById('recorteFoto');
    var palco = document.getElementById('palcoFoto');
    var imgEl = document.getElementById('imgRecorte');
    var zoomEl = document.getElementById('zoomFoto');
    var hidden = document.getElementById('fotoIdentificacao');
    var camera = document.getElementById('inputFotoCamera');
    var arquivo = document.getElementById('inputFotoArquivo');
    var form = semPat.closest('form');

    var fonte = null;
    var zoom = 1;
    var ox = 0;
    var oy = 0;
    var ponteiros = {};
    var distanciaAnterior = 0;

    function botoesDo(input) {
        var grupo = input.closest('.input-group');
        return grupo ? grupo.querySelectorAll('button') : [];
    }

    function travar(check, input) {
        var botoes = botoesDo(input);
        if (check.checked) {
            if (!input.disabled) input.dataset.anterior = input.value;
            input.value = '';
            input.disabled = true;
            botoes.forEach(function (b) { b.disabled = true; });
        } else {
            input.disabled = false;
            if (input.dataset.anterior) input.value = input.dataset.anterior;
            botoes.forEach(function (b) { b.disabled = false; });
        }
    }

    function ambos() {
        return semPat.checked && semSer.checked;
    }

    function atualizarBloco() {
        var mostra = ambos();
        bloco.hidden = !mostra;
        if (!mostra) aviso.hidden = true;
    }

    function ligar(check, input) {
        if (check.checked) {
            input.value = '';
            input.disabled = true;
            botoesDo(input).forEach(function (b) { b.disabled = true; });
        }
        check.addEventListener('change', function () {
            travar(check, input);
            atualizarBloco();
        });
    }

    function medida() {
        return palco.clientWidth || 320;
    }

    function cobertura() {
        var lado = medida();
        return Math.max(lado / fonte.width, lado / fonte.height);
    }

    function limitar() {
        var lado = medida();
        var escala = cobertura() * zoom;
        var dw = fonte.width * escala;
        var dh = fonte.height * escala;
        if (ox > 0) ox = 0;
        if (oy > 0) oy = 0;
        if (ox < lado - dw) ox = lado - dw;
        if (oy < lado - dh) oy = lado - dh;
    }

    function desenhar() {
        var escala = cobertura() * zoom;
        imgEl.style.width = (fonte.width * escala) + 'px';
        imgEl.style.height = (fonte.height * escala) + 'px';
        imgEl.style.transform = 'translate(' + ox + 'px,' + oy + 'px)';
    }

    function reduzir(imagem) {
        var maximo = 2000;
        var w = imagem.naturalWidth || imagem.width;
        var h = imagem.naturalHeight || imagem.height;
        if (Math.max(w, h) <= maximo) {
            return { width: w, height: h, draw: imagem };
        }
        var s = maximo / Math.max(w, h);
        var c = document.createElement('canvas');
        c.width = Math.round(w * s);
        c.height = Math.round(h * s);
        c.getContext('2d').drawImage(imagem, 0, 0, c.width, c.height);
        return { width: c.width, height: c.height, draw: c };
    }

    function montar(imagem) {
        var reduzida = reduzir(imagem);
        fonte = reduzida;
        imgEl.src = imagem.src || '';
        if (!imgEl.src && reduzida.draw.toDataURL) imgEl.src = reduzida.draw.toDataURL('image/jpeg', 0.9);
        zoom = 1;
        zoomEl.value = '1';
        var lado = medida();
        var escala = cobertura();
        ox = (lado - fonte.width * escala) / 2;
        oy = (lado - fonte.height * escala) / 2;
        limitar();
        desenhar();
        recorte.hidden = false;
        aviso.hidden = true;
        if (atual) {
            atual.classList.add('d-none');
            atual.classList.remove('d-flex');
        }
    }

    function abrir(file) {
        if (!file) return;
        var leitor = new FileReader();
        leitor.onload = function () {
            var imagem = new Image();
            imagem.onload = function () { montar(imagem); };
            imagem.onerror = function () {
                aviso.textContent = 'Não consegui abrir essa foto. Tente de novo pela câmera.';
                aviso.hidden = false;
            };
            imagem.src = leitor.result;
        };
        leitor.readAsDataURL(file);
    }

    function exportar() {
        if (!fonte) return '';
        var lado = medida();
        var escala = cobertura() * zoom;
        var canvas = document.createElement('canvas');
        canvas.width = 500;
        canvas.height = 500;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(
            fonte.draw,
            -ox / escala, -oy / escala, lado / escala, lado / escala,
            0, 0, 500, 500
        );
        return canvas.toDataURL('image/jpeg', 0.85);
    }

    function centro(novoZoom) {
        var lado = medida();
        var escalaAntes = cobertura() * zoom;
        var cx = (lado / 2 - ox) / escalaAntes;
        var cy = (lado / 2 - oy) / escalaAntes;
        zoom = novoZoom;
        var escala = cobertura() * zoom;
        ox = lado / 2 - cx * escala;
        oy = lado / 2 - cy * escala;
        limitar();
        desenhar();
    }

    document.getElementById('btnTirarFoto').addEventListener('click', function () {
        camera.value = '';
        camera.click();
    });
    document.getElementById('btnEscolherFoto').addEventListener('click', function () {
        arquivo.value = '';
        arquivo.click();
    });
    camera.addEventListener('change', function () { abrir(camera.files && camera.files[0]); });
    arquivo.addEventListener('change', function () { abrir(arquivo.files && arquivo.files[0]); });

    zoomEl.addEventListener('input', function () {
        if (!fonte) return;
        centro(parseFloat(zoomEl.value) || 1);
    });

    palco.addEventListener('pointerdown', function (ev) {
        palco.setPointerCapture(ev.pointerId);
        ponteiros[ev.pointerId] = { x: ev.clientX, y: ev.clientY };
        distanciaAnterior = 0;
    });
    palco.addEventListener('pointermove', function (ev) {
        if (!ponteiros[ev.pointerId] || !fonte) return;
        var anterior = ponteiros[ev.pointerId];
        ponteiros[ev.pointerId] = { x: ev.clientX, y: ev.clientY };
        var ids = Object.keys(ponteiros);
        if (ids.length >= 2) {
            var a = ponteiros[ids[0]];
            var b = ponteiros[ids[1]];
            var dist = Math.hypot(a.x - b.x, a.y - b.y);
            if (distanciaAnterior) {
                var novo = Math.min(3, Math.max(1, zoom * (dist / distanciaAnterior)));
                zoomEl.value = String(novo);
                centro(novo);
            }
            distanciaAnterior = dist;
            return;
        }
        ox += ev.clientX - anterior.x;
        oy += ev.clientY - anterior.y;
        limitar();
        desenhar();
    });
    function soltar(ev) {
        delete ponteiros[ev.pointerId];
        distanciaAnterior = 0;
    }
    palco.addEventListener('pointerup', soltar);
    palco.addEventListener('pointercancel', soltar);

    if (form) {
        form.addEventListener('submit', function (ev) {
            if (!ambos()) {
                hidden.value = '';
                return;
            }
            var data = exportar();
            if (data) {
                hidden.value = data;
                aviso.hidden = true;
                return;
            }
            if (atual && !atual.classList.contains('d-none')) return;
            ev.preventDefault();
            ev.stopImmediatePropagation();
            aviso.hidden = false;
            bloco.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, true);
    }

    ligar(semPat, pat);
    ligar(semSer, ser);
    atualizarBloco();
})();
