/**
 * FDYS — Dosya Yönetimi JavaScript
 * Faz 5 — Drag-and-drop dosya yükleme, önizleme, silme
 */

const DosyaYonetimi = {

    /**
     * Dosya yükleme bileşenini başlatır.
     * @param {string} containerId - Bileşenin container div ID'si
     * @param {string} kaynakTablo - Kaynak tablo adı (makine, ariza_kaydi vb.)
     * @param {number} kaynakId - Kaynak kaydın ID'si
     */
    init(containerId, kaynakTablo, kaynakId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        this.container = container;
        this.kaynakTablo = kaynakTablo;
        this.kaynakId = kaynakId;
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

        this._renderUI();
        this._bindEvents();
        this.dosyalariYukle();
    },

    _renderUI() {
        this.container.innerHTML = `
            <div class="dosya-eki-widget">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6 class="fw-bold mb-0"><i class="bi bi-paperclip me-2"></i>Dosya Ekleri</h6>
                    <span class="badge bg-secondary" id="dosyaSayisi">0</span>
                </div>
                <div class="dosya-drop-zone" id="dropZone">
                    <i class="bi bi-cloud-arrow-up display-6 text-muted mb-2 d-block"></i>
                    <p class="text-muted mb-1 small">Dosyaları sürükleyip bırakın veya</p>
                    <label class="btn btn-sm btn-outline-primary">
                        <i class="bi bi-folder2-open me-1"></i>Dosya Seç
                        <input type="file" id="dosyaInput" multiple hidden
                               accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.doc,.docx,.xls,.xlsx,.csv">
                    </label>
                    <div class="progress mt-2 d-none" id="uploadProgress" style="height:4px;">
                        <div class="progress-bar bg-primary" style="width:0%"></div>
                    </div>
                </div>
                <div id="dosyaListesi" class="mt-3"></div>
            </div>`;
    },

    _bindEvents() {
        const dropZone = this.container.querySelector('#dropZone');
        const fileInput = this.container.querySelector('#dosyaInput');

        // Drag & Drop
        ['dragenter', 'dragover'].forEach(evt => {
            dropZone.addEventListener(evt, (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
        });
        ['dragleave', 'drop'].forEach(evt => {
            dropZone.addEventListener(evt, (e) => { e.preventDefault(); dropZone.classList.remove('drag-over'); });
        });
        dropZone.addEventListener('drop', (e) => { this._dosyaYukle(e.dataTransfer.files); });

        // File input
        fileInput.addEventListener('change', (e) => { this._dosyaYukle(e.target.files); e.target.value = ''; });
    },

    async _dosyaYukle(files) {
        if (!files || files.length === 0) return;

        const progress = this.container.querySelector('#uploadProgress');
        progress.classList.remove('d-none');
        progress.querySelector('.progress-bar').style.width = '30%';

        const formData = new FormData();
        formData.append('kaynak_tablo', this.kaynakTablo);
        formData.append('kaynak_id', this.kaynakId);
        for (let f of files) formData.append('dosyalar', f);

        try {
            const resp = await fetch('/dosya/yukle', {
                method: 'POST',
                headers: { 'X-CSRFToken': this.csrfToken },
                body: formData
            });
            progress.querySelector('.progress-bar').style.width = '100%';
            const data = await resp.json();

            if (data.success) {
                if (typeof showToast === 'function') showToast(`${data.yuklenen_sayisi} dosya yüklendi.`, 'success');
                this.dosyalariYukle();
            }
            if (data.hatalar && data.hatalar.length > 0) {
                data.hatalar.forEach(h => { if (typeof showToast === 'function') showToast(h, 'warning'); });
            }
        } catch (err) {
            if (typeof showToast === 'function') showToast('Dosya yükleme hatası.', 'danger');
        } finally {
            setTimeout(() => { progress.classList.add('d-none'); progress.querySelector('.progress-bar').style.width = '0%'; }, 500);
        }
    },

    async dosyalariYukle() {
        try {
            const resp = await fetch(`/dosya/listele/${this.kaynakTablo}/${this.kaynakId}`);
            const data = await resp.json();
            this._renderDosyaListesi(data.dosyalar);
            const badge = this.container.querySelector('#dosyaSayisi');
            if (badge) badge.textContent = data.toplam;
        } catch (err) {
            console.error('Dosya listeleme hatası:', err);
        }
    },

    _renderDosyaListesi(dosyalar) {
        const listDiv = this.container.querySelector('#dosyaListesi');
        if (!dosyalar || dosyalar.length === 0) {
            listDiv.innerHTML = '<p class="text-muted small text-center py-2"><i class="bi bi-inbox me-1"></i>Henüz dosya eklenmemiş.</p>';
            return;
        }

        // Resimler (galeri) ve diğer dosyalar ayrı
        const resimler = dosyalar.filter(d => d.resim_mi);
        const belgeler = dosyalar.filter(d => !d.resim_mi);

        let html = '';

        if (resimler.length > 0) {
            html += '<div class="row g-2 mb-3">';
            for (const r of resimler) {
                html += `
                <div class="col-4 col-md-3">
                    <div class="dosya-thumbnail" onclick="DosyaYonetimi._onizle('${r.onizleme_url}', '${r.orijinal_adi}')">
                        <img src="${r.onizleme_url}" alt="${r.orijinal_adi}" class="img-fluid rounded">
                        <div class="dosya-thumbnail-overlay">
                            <small class="text-truncate d-block">${r.orijinal_adi}</small>
                            <div class="dosya-actions mt-1">
                                <a href="${r.indirme_url}" class="btn btn-sm btn-outline-light py-0 px-1" title="İndir" onclick="event.stopPropagation()"><i class="bi bi-download"></i></a>
                                <button class="btn btn-sm btn-outline-danger py-0 px-1" title="Sil" onclick="event.stopPropagation(); DosyaYonetimi._sil(${r.id})"><i class="bi bi-trash"></i></button>
                            </div>
                        </div>
                    </div>
                </div>`;
            }
            html += '</div>';
        }

        if (belgeler.length > 0) {
            html += '<div class="list-group list-group-flush">';
            for (const b of belgeler) {
                html += `
                <div class="list-group-item d-flex justify-content-between align-items-center px-0 py-2 border-0" style="background:transparent;">
                    <div class="d-flex align-items-center text-truncate">
                        <i class="${b.ikon} me-2 text-muted fs-5"></i>
                        <div class="text-truncate">
                            <span class="small fw-medium" style="color:var(--text-heading);">${b.orijinal_adi}</span>
                            <br><small class="text-muted">${b.boyut} · ${b.yukleyen} · ${b.tarih}</small>
                        </div>
                    </div>
                    <div class="d-flex gap-1 flex-shrink-0 ms-2">
                        <a href="${b.indirme_url}" class="btn btn-sm btn-outline-secondary py-0 px-1" title="İndir"><i class="bi bi-download"></i></a>
                        <button class="btn btn-sm btn-outline-danger py-0 px-1" title="Sil" onclick="DosyaYonetimi._sil(${b.id})"><i class="bi bi-trash"></i></button>
                    </div>
                </div>`;
            }
            html += '</div>';
        }

        listDiv.innerHTML = html;
    },

    _onizle(url, ad) {
        // Lightbox modal
        let modal = document.getElementById('dosyaOnizleModal');
        if (!modal) {
            document.body.insertAdjacentHTML('beforeend', `
                <div class="modal fade" id="dosyaOnizleModal" tabindex="-1">
                    <div class="modal-dialog modal-lg modal-dialog-centered">
                        <div class="modal-content bg-dark border-0">
                            <div class="modal-header border-0 pb-0">
                                <h6 class="modal-title text-white" id="dosyaOnizleBaslik"></h6>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body text-center p-2">
                                <img id="dosyaOnizleImg" class="img-fluid rounded" style="max-height:70vh;">
                            </div>
                        </div>
                    </div>
                </div>`);
            modal = document.getElementById('dosyaOnizleModal');
        }
        document.getElementById('dosyaOnizleImg').src = url;
        document.getElementById('dosyaOnizleBaslik').textContent = ad;
        new bootstrap.Modal(modal).show();
    },

    async _sil(id) {
        if (!(await window.fdysConfirm('Bu dosyayı silmek istediğinize emin misiniz?'))) return;
        try {
            const resp = await fetch(`/dosya/sil/${id}`, {
                method: 'POST',
                headers: { 'X-CSRFToken': this.csrfToken, 'Content-Type': 'application/json' }
            });
            const data = await resp.json();
            if (data.success) {
                if (typeof showToast === 'function') showToast('Dosya silindi.', 'success');
                this.dosyalariYukle();
            } else {
                if (typeof showToast === 'function') showToast(data.error || 'Silme hatası.', 'danger');
            }
        } catch (err) {
            if (typeof showToast === 'function') showToast('Dosya silme hatası.', 'danger');
        }
    }
};
