/* Lê código de barras (ou QR) com a câmera e preenche um campo.
 * Botão: .js-ler-codigo[data-alvo][data-prefixo opcional, ex. PMS-]
 * Chrome e Edge usam a câmera direto. Nos outros, carrega o leitor ZXing. */
(function () {
    'use strict';

    var video = null;
    var modal = null;
    var statusEl = null;
    var stream = null;
    var timer = null;
    var leitor = null;
    var alvo = null;
    var prefixo = '';

    function limpar(texto) {
        var valor = String(texto || '').replace(/[\r\n\t]/g, '').trim();
        if (prefixo) {
            var re = new RegExp('^' + prefixo.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '-?', 'i');
            valor = valor.replace(re, '');
        }
        return valor.trim();
    }

    function parar() {
        if (timer) {
            clearTimeout(timer);
            timer = null;
        }
        if (leitor && leitor.reset) {
            try { leitor.reset(); } catch (e) { /* câmera já fechada */ }
            leitor = null;
        }
        if (stream) {
            stream.getTracks().forEach(function (t) { t.stop(); });
            stream = null;
        }
        if (video) video.srcObject = null;
    }

    function aplicar(texto) {
        var valor = limpar(texto);
        if (!alvo || !valor) return;
        alvo.value = valor;
        alvo.dispatchEvent(new Event('input', { bubbles: true }));
        parar();
        if (modal) bootstrap.Modal.getOrCreateInstance(modal).hide();
        alvo.focus();
    }

    function dizer(msg) {
        if (statusEl) statusEl.textContent = msg;
    }

    function loopNativo(detector) {
        if (!stream) return;
        detector.detect(video).then(function (codes) {
            if (!stream) return;
            if (codes && codes.length && codes[0].rawValue) {
                aplicar(codes[0].rawValue);
                return;
            }
            timer = setTimeout(function () { loopNativo(detector); }, 180);
        }).catch(function () {
            if (stream) timer = setTimeout(function () { loopNativo(detector); }, 300);
        });
    }

    function abrirNativo() {
        var formatos = ['code_128', 'code_39', 'ean_13', 'ean_8', 'itf', 'codabar', 'upc_a', 'upc_e', 'qr_code'];
        var detector = new BarcodeDetector({ formats: formatos });
        return navigator.mediaDevices.getUserMedia({
            video: { facingMode: { ideal: 'environment' } },
            audio: false
        }).then(function (s) {
            stream = s;
            video.srcObject = s;
            return video.play();
        }).then(function () {
            dizer('Aponte a câmera para o código.');
            loopNativo(detector);
        });
    }

    function carregarZxing() {
        if (window.ZXing && window.ZXing.BrowserMultiFormatReader) return Promise.resolve();
        return new Promise(function (resolve, reject) {
            var s = document.createElement('script');
            s.src = 'https://cdn.jsdelivr.net/npm/@zxing/library@0.21.3/umd/index.min.js';
            s.onload = function () { resolve(); };
            s.onerror = function () { reject(new Error('zxing')); };
            document.head.appendChild(s);
        });
    }

    function abrirZxing() {
        dizer('Preparando o leitor…');
        return carregarZxing().then(function () {
            leitor = new ZXing.BrowserMultiFormatReader();
            return leitor.decodeFromVideoDevice(undefined, video, function (resultado) {
                if (resultado) aplicar(resultado.getText());
            });
        });
    }

    function abrir() {
        dizer('Abrindo a câmera…');
        var promessa = window.BarcodeDetector
            ? abrirNativo().catch(function () { return abrirZxing(); })
            : abrirZxing();
        promessa.catch(function () {
            parar();
            dizer('Não consegui abrir a câmera. Digite o código ou use um leitor que escreve no campo.');
        });
    }

    function garantirModal() {
        if (document.getElementById('modalLerCodigo')) {
            modal = document.getElementById('modalLerCodigo');
            video = document.getElementById('videoLerCodigo');
            statusEl = document.getElementById('statusLerCodigo');
            return;
        }
        var html = ''
            + '<div class="modal fade" id="modalLerCodigo" tabindex="-1" aria-hidden="true">'
            + '  <div class="modal-dialog modal-dialog-centered">'
            + '    <div class="modal-content">'
            + '      <div class="modal-header py-2">'
            + '        <h6 class="modal-title"><i class="fas fa-barcode me-2"></i>Ler código de barras</h6>'
            + '        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>'
            + '      </div>'
            + '      <div class="modal-body">'
            + '        <video id="videoLerCodigo" playsinline autoplay muted style="width:100%;border-radius:8px;background:#0D3B5E;min-height:180px"></video>'
            + '        <p id="statusLerCodigo" class="small text-muted mt-2 mb-0">Aponte a câmera para o código.</p>'
            + '      </div>'
            + '    </div>'
            + '  </div>'
            + '</div>';
        document.body.insertAdjacentHTML('beforeend', html);
        modal = document.getElementById('modalLerCodigo');
        video = document.getElementById('videoLerCodigo');
        statusEl = document.getElementById('statusLerCodigo');
        modal.addEventListener('hidden.bs.modal', parar);
    }

    document.addEventListener('click', function (ev) {
        var botao = ev.target.closest('.js-ler-codigo');
        if (!botao) return;
        ev.preventDefault();
        alvo = document.getElementById(botao.dataset.alvo);
        prefixo = botao.dataset.prefixo || '';
        if (!alvo) return;
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            window.alert('Este navegador não abre a câmera. Digite o código ou use um leitor que escreve no campo.');
            alvo.focus();
            return;
        }
        garantirModal();
        bootstrap.Modal.getOrCreateInstance(modal).show();
        abrir();
    });
})();
