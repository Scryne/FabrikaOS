document.addEventListener('DOMContentLoaded', () => {
    const bildirimDropdown = document.getElementById('bildirimDropdown');
    
    // Sadece bildirim ikonu olan sayfalarda çalıştır
    if (!bildirimDropdown) return;
    
    const sayac = document.getElementById('bildirimSayaci');
    const menu = document.querySelector('.dropdown-menu', bildirimDropdown.parentElement);
    let sonBildirimler = [];
    
    // HTML Element oluşturucu
    const renderBildirimler = (data) => {
        let html = `<li>
                        <div class="dropdown-header d-flex justify-content-between align-items-center py-3 border-bottom" style="border-color: rgba(255,255,255,0.1) !important; background-color: var(--bg-card); border-top-left-radius: 12px; border-top-right-radius: 12px;">
                            <span class="fw-bold text-white" style="font-size: 1rem;"><i class="bi bi-bell-fill me-2 text-primary"></i>Bildirimler</span>
                            <a href="#" class="text-muted small text-decoration-none" id="btnHepsiniOku">Hepsini Oku</a>
                        </div>
                    </li>`;
                    
        if (data.length === 0) {
            html += `<li>
                        <div class="p-5 text-center text-muted" style="background-color: var(--bg-card); border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;">
                            <i class="bi bi-check2-all display-4 d-block mb-3 text-success opacity-50"></i>
                            <span class="small fw-bold">Yeni bildirim yok</span>
                        </div>
                     </li>`;
        } else {
            html += `<li><div style="max-height: 350px; overflow-y: auto; overflow-x: hidden; background-color: var(--bg-card);" class="custom-scrollbar">`;
            data.forEach(b => {
                let iconClass = "bi-info-circle text-info";
                let bgCircle = "background: rgba(9, 132, 227, 0.1);"; // info
                
                if (b.seviye === "kritik") { 
                    iconClass = "bi-exclamation-octagon text-danger"; 
                    bgCircle = "background: rgba(214, 48, 49, 0.1);"; 
                } else if (b.seviye === "uyari") { 
                    iconClass = "bi-exclamation-triangle text-warning"; 
                    bgCircle = "background: rgba(253, 203, 110, 0.1);"; 
                } else if (b.seviye === "guvenlik") { 
                    iconClass = "bi-shield-lock text-danger"; 
                    bgCircle = "background: rgba(214, 48, 49, 0.1);"; 
                }
                
                html += `
                    <a class="dropdown-item py-3 border-bottom bildirim-item" href="${b.url || '#'}" data-id="${b.id}" style="border-color: rgba(255,255,255,0.05) !important;">
                        <div class="d-flex align-items-start px-2">
                            <div class="rounded-circle d-flex align-items-center justify-content-center me-3 flex-shrink-0" style="width: 40px; height: 40px; ${bgCircle}">
                                <i class="bi ${iconClass} fs-5"></i>
                            </div>
                            <div class="flex-grow-1 text-wrap">
                                <h6 class="mb-1 text-white fw-bold" style="font-size: 0.9rem;">${b.baslik}</h6>
                                <p class="mb-2 text-muted small lh-sm" style="font-size: 0.8rem;">${b.mesaj}</p>
                                <small class="text-muted" style="font-size: 0.75rem;"><i class="bi bi-clock me-1"></i>${b.tarih}</small>
                            </div>
                        </div>
                    </a>
                `;
            });
            html += `</div></li>`;
            html += `<li>
                        <a class="dropdown-item text-center py-3 text-primary small fw-bold" href="/bildirimler" style="background: rgba(0,0,0,0.2); border-bottom-left-radius: 12px; border-bottom-right-radius: 12px; transition: 0.2s;">
                            Tümünü Gör <i class="bi bi-arrow-right ms-1"></i>
                        </a>
                     </li>`;
        }
        
        menu.innerHTML = html;
        
        // Event Listeners for read
        document.querySelectorAll('.bildirim-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if(item.getAttribute('href') === '#') {
                    e.preventDefault();
                }
                markAsRead(item.dataset.id);
            });
        });
        
        const btnHepsini = document.getElementById('btnHepsiniOku');
        if(btnHepsini) {
            btnHepsini.addEventListener('click', (e) => {
                e.preventDefault();
                markAsRead('all');
            });
        }
    };
    
    // API'den başlangıç yüklemesi
    const fetchBildirimler = async () => {
        try {
            const res = await fetch('/api/bildirimler');
            if (res.ok) {
                const data = await res.json();
                
                // Sayacı güncelle
                if (data.okunmamis_sayisi > 0) {
                    sayac.textContent = data.okunmamis_sayisi;
                    sayac.classList.remove('d-none');
                } else {
                    sayac.classList.add('d-none');
                }
                
                sonBildirimler = data.bildirimler;
                renderBildirimler(sonBildirimler);
            }
        } catch (err) {
            console.error("Bildirimler yüklenemedi:", err);
        }
    };
    
    // Okundu işaretleme API çağrısı
    const markAsRead = async (id) => {
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            const res = await fetch('/api/bildirim/okundu', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({id: id})
            });
            if (res.ok) {
                fetchBildirimler(); // Listeyi yenile
            }
        } catch(err) {}
    };

    // İlk yükleme
    fetchBildirimler();
    
    // Socket.IO Bağlantısı
    if (typeof io !== 'undefined') {
        const socket = io();
        
        socket.on('connect', () => {
            console.log('Bildirim sistemine bağlanıldı.');
            
            // Kullanıcıyı kendi odasına alabilmek için authentication event
            // Ama sunucuda @socketio.on('connect') var ise otomatik halleder.
        });
        
        socket.on('yeni_bildirim', (data) => {
            // Toast / Alert gösterilebilir
            showToast(data.baslik, data.mesaj, data.seviye);
            
            // Listeyi yenile
            fetchBildirimler();
        });
    }
    
    // Toast Gösterici
    function showToast(title, message, type) {
        // Bootstrap toast container yoksa oluştur
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            toastContainer.style.zIndex = '1055';
            document.body.appendChild(toastContainer);
        }
        
        let bgClass = "bg-white text-dark";
        let iconClass = "bi-info-circle text-info";
        
        if (type === "kritik") { bgClass = "bg-danger text-white"; iconClass = "bi-exclamation-octagon text-white"; }
        else if (type === "uyari") { bgClass = "bg-warning text-dark"; iconClass = "bi-exclamation-triangle text-dark"; }
        
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center border-0 ${bgClass} shadow" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header ${type === 'kritik' ? 'text-white border-bottom border-light' : ''}" style="${type === 'kritik' ? 'background: rgba(0,0,0,0.1)' : ''}">
                    <i class="bi ${iconClass} me-2"></i>
                    <strong class="me-auto">${title}</strong>
                    <small>Şimdi</small>
                    <button type="button" class="btn-close ${type === 'kritik' ? 'btn-close-white' : ''}" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastEl = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
        toast.show();
        
        // Toast bittikten sonra DOM'dan sil
        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    }
});
