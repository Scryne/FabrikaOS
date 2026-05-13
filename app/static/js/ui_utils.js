/**
 * FDYS — ui_utils.js
 * Faz 3 — UX/UI Profesyonelleştirme Paketi
 * 
 * İçerik:
 *  1. Bootstrap Form Validasyonu
 *  2. CSRF Token Interceptor
 *  3. Session Timeout Uyarısı
 *  4. Modern Toast Bildirimleri
 *  5. Silme Onay Modalı (Bootstrap Modal)
 *  6. Form Submit Loading Spinner
 *  7. Sidebar Toggle (Mobile Hamburger)
 *  8. Dark/Light Tema Geçişi
 *  9. Keyboard Shortcuts
 * 10. Client-Side Tablo Sıralama
 * 11. Real-time Form Validation
 * 12. Flash Mesajları → Toast Dönüştürme
 */

document.addEventListener('DOMContentLoaded', function () {

    // ═══════════════════════════════════════════
    // 0. Sadece Dark Tema Zorlaması
    // ═══════════════════════════════════════════
    forceDarkTheme();

    // ═══════════════════════════════════════════
    // 1. Bootstrap Form Validasyonu (Client-side)
    // ═══════════════════════════════════════════
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // ═══════════════════════════════════════════
    // 2. Otomatik CSRF Token Ekleyici
    // ═══════════════════════════════════════════
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (csrfToken) {
        const originalFetch = window.fetch;
        window.fetch = async function() {
            let [resource, config] = arguments;
            if (config === undefined) {
                config = {};
            }
            if (config.method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(config.method.toUpperCase())) {
                config.headers = config.headers || {};
                config.headers['X-CSRFToken'] = csrfToken.getAttribute('content');
            }
            return originalFetch(resource, config);
        };
    }

    // ═══════════════════════════════════════════
    // 3. Session Timeout Uyarısı
    // ═══════════════════════════════════════════
    if (document.getElementById('sidebar')) {
        const SESSION_TIMEOUT_MS = 60 * 60 * 1000;
        const WARNING_BEFORE_MS = 5 * 60 * 1000;
        let sessionTimer;

        function startSessionTimer() {
            clearTimeout(sessionTimer);
            sessionTimer = setTimeout(() => {
                const modal = new bootstrap.Modal(document.getElementById('sessionTimeoutModal'));
                modal.show();
            }, SESSION_TIMEOUT_MS - WARNING_BEFORE_MS);
        }

        startSessionTimer();

        window.renewSession = function() {
            fetch('/auth/profil')
                .then(response => {
                    if(response.ok) {
                        const modal = bootstrap.Modal.getInstance(document.getElementById('sessionTimeoutModal'));
                        if (modal) modal.hide();
                        startSessionTimer();
                        showToast('Başarılı', 'Oturum süreniz uzatıldı.', 'success');
                    }
                });
        };
    }

    // ═══════════════════════════════════════════
    // 5. Silme Onay Modalı — Global Sistem
    // ═══════════════════════════════════════════
    initDeleteConfirmation();

    // ═══════════════════════════════════════════
    // 6. Form Submit Loading Spinner
    // ═══════════════════════════════════════════
    initFormLoadingSpinners();

    // ═══════════════════════════════════════════
    // 7. Sidebar Toggle (Mobile Hamburger)
    // ═══════════════════════════════════════════
    initSidebarToggle();


    // ═══════════════════════════════════════════
    // 10. Client-Side Tablo Sıralama
    // ═══════════════════════════════════════════
    initTableSort();

    // ═══════════════════════════════════════════
    // 11. Real-time Form Validation
    // ═══════════════════════════════════════════
    initRealtimeValidation();

    // ═══════════════════════════════════════════
    // 12. Flash Mesajları → Toast Dönüştürme
    // ═══════════════════════════════════════════
    convertFlashToToast();
});


// ═══════════════════════════════════════════════
// 4. Modern Toast Bildirim Fonksiyonu (Global)
// ═══════════════════════════════════════════════
function showToast(title, message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const icons = {
        success: 'bi-check-circle-fill',
        danger: 'bi-exclamation-octagon-fill',
        warning: 'bi-exclamation-triangle-fill',
        info: 'bi-info-circle-fill'
    };
    const icon = icons[type] || icons.info;

    const toastEl = document.createElement('div');
    toastEl.className = `fdys-toast fdys-toast-${type}`;
    toastEl.innerHTML = `
        <div class="fdys-toast-icon"><i class="bi ${icon}"></i></div>
        <div class="fdys-toast-body">
            <div class="fdys-toast-title">${title}</div>
            <div class="fdys-toast-message">${message}</div>
        </div>
        <button class="fdys-toast-close" onclick="this.parentElement.remove()">
            <i class="bi bi-x"></i>
        </button>
        <div class="fdys-toast-progress"></div>
    `;

    toastContainer.appendChild(toastEl);

    // Auto dismiss after 5s
    setTimeout(() => {
        toastEl.style.animation = 'fdysToastOut 0.3s ease forwards';
        setTimeout(() => toastEl.remove(), 300);
    }, 5000);
}


// ═══════════════════════════════════════════════
// 5. Global Profesyonel Onay Modalı (Promise Tabanlı)
// ═══════════════════════════════════════════════
window.fdysConfirm = function(message, title = 'Onay Bekleniyor', icon = 'bi-exclamation-octagon') {
    return new Promise((resolve) => {
        let modalEl = document.getElementById('fdysConfirmModal');
        if (!modalEl) {
            const html = `
            <div class="modal fade" id="fdysConfirmModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content" style="border: 1px solid var(--border-color); border-radius: 1rem; overflow: hidden;">
                        <div class="modal-body p-5 text-center">
                            <div class="mb-4 d-inline-flex justify-content-center align-items-center" style="width: 80px; height: 80px; border-radius: 50%; background: rgba(239, 68, 68, 0.1); border: 2px solid rgba(239, 68, 68, 0.2);">
                                <i id="fdysConfirmIcon" class="bi bi-exclamation-octagon text-danger" style="font-size: 2.5rem;"></i>
                            </div>
                            <h4 id="fdysConfirmTitle" class="fw-bold mb-3" style="font-family: 'Outfit', sans-serif; letter-spacing: -0.5px; color: var(--text-heading);">Onay Bekleniyor</h4>
                            <p id="fdysConfirmMessage" class="fs-6 mb-5 px-3" style="line-height: 1.6; color: var(--text-secondary);"></p>
                            <div class="d-flex justify-content-center gap-3">
                                <button type="button" class="btn btn-secondary px-4 py-2" data-bs-dismiss="modal" style="border-radius: 0.75rem;">Vazgeç</button>
                                <button type="button" id="fdysConfirmBtn" class="btn btn-danger px-4 py-2 fw-bold" style="border-radius: 0.75rem;">Evet, Onaylıyorum</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
            document.body.insertAdjacentHTML('beforeend', html);
            modalEl = document.getElementById('fdysConfirmModal');
        }

        document.getElementById('fdysConfirmIcon').className = `bi ${icon} text-danger`;
        document.getElementById('fdysConfirmTitle').textContent = title;
        document.getElementById('fdysConfirmMessage').textContent = message;

        const modal = new bootstrap.Modal(modalEl);
        
        const confirmBtn = document.getElementById('fdysConfirmBtn');
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

        let resolved = false;

        newConfirmBtn.addEventListener('click', () => {
            resolved = true;
            modal.hide();
            resolve(true);
        });
        
        const onHidden = () => {
            if (!resolved) resolve(false);
            modalEl.removeEventListener('hidden.bs.modal', onHidden);
        };
        modalEl.addEventListener('hidden.bs.modal', onHidden);

        modal.show();
    });
};

function initDeleteConfirmation() {
    document.querySelectorAll('form[onsubmit*="confirm"]').forEach(form => {
        const confirmText = form.getAttribute('onsubmit');
        let message = 'Bu kaydı silmek istediğinize emin misiniz?';
        const match = confirmText.match(/confirm\(['"](.+?)['"]\)/);
        if (match) message = match[1];

        form.removeAttribute('onsubmit');
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const confirmed = await window.fdysConfirm(message);
            if (confirmed) form.submit();
        });
    });
}


// ═══════════════════════════════════════════════
// 6. Form Submit Loading Spinner
// ═══════════════════════════════════════════════
function initFormLoadingSpinners() {
    document.querySelectorAll('form').forEach(form => {
        // Skip forms that are AJAX or have special handling
        if (form.dataset.noSpinner) return;

        form.addEventListener('submit', function(e) {
            // Only if form is valid
            if (form.checkValidity && !form.checkValidity()) return;

            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (!submitBtn || submitBtn.classList.contains('btn-loading')) return;

            // Don't add spinner for very small forms (like inline filter)
            if (submitBtn.closest('.btn-group')) return;

            const originalHtml = submitBtn.innerHTML;
            submitBtn.classList.add('btn-loading');
            submitBtn.innerHTML = `<span class="fdys-spinner"></span><span class="btn-text">${submitBtn.textContent.trim()}</span>`;
            submitBtn.disabled = true;

            // Safety: re-enable after 10s in case of error
            setTimeout(() => {
                submitBtn.classList.remove('btn-loading');
                submitBtn.innerHTML = originalHtml;
                submitBtn.disabled = false;
            }, 10000);
        });
    });
}


// ═══════════════════════════════════════════════
// 7. Sidebar Toggle (Mobile Hamburger)
// ═══════════════════════════════════════════════
function initSidebarToggle() {
    const hamburger = document.getElementById('hamburgerBtn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    if (!hamburger || !sidebar) return;

    function openSidebar() {
        sidebar.classList.add('show');
        if (overlay) overlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('show');
        if (overlay) overlay.classList.remove('show');
        document.body.style.overflow = '';
    }

    hamburger.addEventListener('click', function(e) {
        e.stopPropagation();
        if (sidebar.classList.contains('show')) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    // Close on ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('show')) {
            closeSidebar();
        }
    });

    // Close sidebar on link click (mobile)
    sidebar.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 992) closeSidebar();
        });
    });
}



// ═══════════════════════════════════════════════
// 10. Client-Side Tablo Sıralama
// ═══════════════════════════════════════════════
function initTableSort() {
    document.querySelectorAll('.table th[data-sort]').forEach(th => {
        th.addEventListener('click', function() {
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            const colIdx = Array.from(th.parentNode.children).indexOf(th);
            const sortType = th.dataset.sort || 'string'; // 'string', 'number', 'date'

            // Toggle direction
            const isAsc = th.classList.contains('sort-asc');
            table.querySelectorAll('th[data-sort]').forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });
            th.classList.add(isAsc ? 'sort-desc' : 'sort-asc');

            const dir = isAsc ? -1 : 1;
            const rows = Array.from(tbody.querySelectorAll('tr'));

            rows.sort((a, b) => {
                let aVal = a.children[colIdx]?.textContent.trim() || '';
                let bVal = b.children[colIdx]?.textContent.trim() || '';

                if (sortType === 'number') {
                    aVal = parseFloat(aVal.replace(/[^0-9.-]/g, '')) || 0;
                    bVal = parseFloat(bVal.replace(/[^0-9.-]/g, '')) || 0;
                    return (aVal - bVal) * dir;
                }
                if (sortType === 'date') {
                    // DD.MM.YYYY format
                    const parseDate = s => {
                        const p = s.split('.');
                        return p.length === 3 ? new Date(p[2], p[1]-1, p[0]) : new Date(0);
                    };
                    return (parseDate(aVal) - parseDate(bVal)) * dir;
                }
                return aVal.localeCompare(bVal, 'tr') * dir;
            });

            rows.forEach(r => tbody.appendChild(r));
        });
    });
}


// ═══════════════════════════════════════════════
// 11. Real-time Form Validation
// ═══════════════════════════════════════════════
function initRealtimeValidation() {
    // Email validation
    document.querySelectorAll('input[type="email"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (input.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value)) {
                input.classList.add('is-invalid');
                input.classList.remove('is-valid');
            } else if (input.value) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            }
        });
    });

    // Required fields
    document.querySelectorAll('input[required], select[required], textarea[required]').forEach(input => {
        input.addEventListener('blur', function() {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                input.classList.remove('is-valid');
            } else {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            }
        });
        input.addEventListener('input', function() {
            if (input.classList.contains('is-invalid') && input.value.trim()) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            }
        });
    });

    // Password strength meter
    document.querySelectorAll('input[type="password"]').forEach(input => {
        if (input.id && (input.id.includes('yeni') || input.id.includes('new'))) {
            const meter = document.createElement('div');
            meter.className = 'fdys-password-meter';
            meter.innerHTML = '<div class="fdys-password-meter-fill"></div>';
            input.parentNode.insertBefore(meter, input.nextSibling);

            const strengthLabel = document.createElement('small');
            strengthLabel.className = 'mt-1 d-block';
            strengthLabel.style.fontSize = '0.72rem';
            meter.parentNode.insertBefore(strengthLabel, meter.nextSibling);

            input.addEventListener('input', function() {
                const val = input.value;
                let score = 0;
                if (val.length >= 8) score++;
                if (val.length >= 12) score++;
                if (/[A-Z]/.test(val)) score++;
                if (/[a-z]/.test(val)) score++;
                if (/[0-9]/.test(val)) score++;
                if (/[^A-Za-z0-9]/.test(val)) score++;

                const fill = meter.querySelector('.fdys-password-meter-fill');
                const pct = Math.min(100, (score / 6) * 100);
                fill.style.width = pct + '%';

                if (score <= 2) {
                    fill.style.background = '#ef4444';
                    strengthLabel.textContent = 'Zayıf şifre';
                    strengthLabel.style.color = '#ef4444';
                } else if (score <= 4) {
                    fill.style.background = '#f59e0b';
                    strengthLabel.textContent = 'Orta güçlükte şifre';
                    strengthLabel.style.color = '#f59e0b';
                } else {
                    fill.style.background = '#10b981';
                    strengthLabel.textContent = 'Güçlü şifre';
                    strengthLabel.style.color = '#10b981';
                }

                if (!val) {
                    fill.style.width = '0';
                    strengthLabel.textContent = '';
                }
            });
        }
    });
}


// ═══════════════════════════════════════════════
// 12. Flash Mesajları → Toast Dönüştürme
// ═══════════════════════════════════════════════
function convertFlashToToast() {
    document.querySelectorAll('.alert[role="alert"]').forEach(alert => {
        // Skip non-flash alerts (like the critical stock warning in stok page)
        if (!alert.querySelector('.btn-close')) return;
        // Skip session timeout modal alerts
        if (alert.closest('.modal')) return;

        let type = 'info';
        if (alert.classList.contains('alert-success')) type = 'success';
        else if (alert.classList.contains('alert-danger')) type = 'danger';
        else if (alert.classList.contains('alert-warning')) type = 'warning';

        const typeLabels = {
            success: 'Başarılı',
            danger: 'Hata',
            warning: 'Uyarı',
            info: 'Bilgi'
        };

        const msg = alert.textContent.trim().replace('×', '').trim();
        showToast(typeLabels[type], msg, type);
        alert.remove();
    });
}


// ═══════════════════════════════════════════════
// 13. Sadece Dark Tema Zorlaması
// ═══════════════════════════════════════════════
function forceDarkTheme() {
    const html = document.documentElement;
    html.setAttribute('data-bs-theme', 'dark');
    localStorage.removeItem('fdys-theme');
}
