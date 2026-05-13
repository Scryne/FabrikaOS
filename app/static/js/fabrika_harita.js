/**
 * FDYS — Fabrika Haritası Engine v4.0
 * Professional flat design, clean machine nodes
 */
(function () {
    'use strict';

    let machines = [];
    let editMode = false;
    let snapshot = null;
    let refreshTimer = null;
    let popupMachine = null;
    let popupHideTimer = null;
    let isOverPopup = false;

    // Drag state
    let dragTarget = null;
    let dragOffset = { x: 0, y: 0 };

    const NODE_W = 158, NODE_H = 88;

    const STATUS = {
        aktif:   { color: '#10b981', label: 'Çalışıyor', abbr: 'ON'  },
        arizali: { color: '#ef4444', label: 'Arızalı',   abbr: 'ERR' },
        bakimda: { color: '#f59e0b', label: 'Bakımda',   abbr: 'MNT' },
        kapali:  { color: '#525252', label: 'Kapalı',    abbr: 'OFF' },
    };

    const svg = document.getElementById('fabrikaHarita');
    const layer = document.getElementById('machineLayer');
    const viewport = document.getElementById('haritaViewport');
    const popup = document.getElementById('makinePopup');
    const loadingEl = document.getElementById('haritaLoading');

    // ── INIT ──
    document.addEventListener('DOMContentLoaded', () => {
        setupPopupEvents();
        loadData();
        refreshTimer = setInterval(loadData, 30000);
    });

    function loadData() {
        if (editMode) return;
        fetch(API_URL)
            .then(r => r.json())
            .then(data => { 
                machines = data; 
                render(); 
                hideLoading();
                
                // Minimal auto-refresh indicator
                const indicator = document.querySelector('.badge i.bi-broadcast');
                if (indicator) {
                    indicator.style.color = '#10b981';
                    setTimeout(() => { indicator.style.color = ''; }, 1000);
                }
            })
            .catch(e => { console.error(e); hideLoading(); });
    }

    function hideLoading() {
        if (loadingEl) loadingEl.style.display = 'none';
    }

    // ── RENDER ──
    function render() {
        layer.innerHTML = '';
        machines.forEach(m => {
            if (m.konum_x == null || m.konum_y == null) return;
            layer.appendChild(buildNode(m));
        });
    }

    function buildNode(m) {
        const s = STATUS[m.durum] || STATUS.kapali;
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('data-id', m.id);
        g.setAttribute('class', 'machine-node' + (editMode ? ' is-editing' : ''));
        g.setAttribute('transform', `translate(${m.konum_x},${m.konum_y})`);

        const w = NODE_W, h = NODE_H;

        // ── Card body ──
        const body = mkRect(0, 0, w, h, 8, '#1a1a1a', 'rgba(255,255,255,0.06)', 1);
        g.appendChild(body);

        // ── Top accent line (3px, status color) ──
        const accent = mkRect(0, 0, w, 3, '8 8 0 0', s.color, 'none', 0);
        accent.setAttribute('opacity', '0.7');
        g.appendChild(accent);

        // ── Fault pulse border ──
        if (m.durum === 'arizali') {
            const pulse = mkRect(0, 0, w, h, 8, 'none', s.color, 1);
            pulse.setAttribute('opacity', '0.3');
            const animOpacity = mkAnim('opacity', '0.3', '0.08', '1.8s');
            pulse.appendChild(animOpacity);
            g.appendChild(pulse);
        }

        // ── Content ──
        const cg = document.createElementNS('http://www.w3.org/2000/svg', 'g');

        // Machine code (bold)
        cg.appendChild(mkText(14, 24, m.kod, 11.5, '#e5e5e5', 700, 'Outfit', 'start'));

        // Status pill (top-right)
        const pillW = 32;
        const pillX = w - pillW - 10;
        const pill = mkRect(pillX, 10, pillW, 16, 4, s.color, 'none', 0);
        pill.setAttribute('opacity', '0.12');
        cg.appendChild(pill);
        cg.appendChild(mkText(pillX + pillW / 2, 21, s.abbr, 8, s.color, 700, 'Outfit', 'middle'));

        // Machine name (muted)
        const nm = m.ad.length > 18 ? m.ad.substring(0, 18) + '…' : m.ad;
        cg.appendChild(mkText(14, 40, nm, 9.5, '#737373', 400, 'Inter', 'start'));

        // ── OEE Section ──
        if (m.oee != null) {
            const barY = h - 18;
            const barX = 14;
            const barW = w - 28;
            const barH = 4;

            // Label
            cg.appendChild(mkText(barX, barY - 6, 'OEE', 8, '#525252', 600, 'Outfit', 'start'));

            // Value
            cg.appendChild(mkText(w - 14, barY - 6, m.oee + '%', 9.5, '#e5e5e5', 700, 'Outfit', 'end'));

            // Track
            cg.appendChild(mkRect(barX, barY, barW, barH, 2, '#262626', 'none', 0));

            // Fill
            const fw = Math.max(2, Math.min(barW, (m.oee / 100) * barW));
            const oc = m.oee >= 85 ? '#10b981' : m.oee >= 60 ? '#f59e0b' : '#ef4444';
            cg.appendChild(mkRect(barX, barY, fw, barH, 2, oc, 'none', 0));
        }

        g.appendChild(cg);

        // ── Hover highlight (invisible rect for better hit area) ──
        const hitArea = mkRect(0, 0, w, h, 8, 'transparent', 'none', 0);
        hitArea.style.cursor = 'pointer';
        g.appendChild(hitArea);

        // Edit handle
        if (editMode) {
            g.appendChild(mkText(w / 2, h - 2, '⋮⋮', 10, '#4a4a4a', 400, 'Inter', 'middle'));
            g.addEventListener('mousedown', startDrag);
            g.addEventListener('touchstart', startDrag, { passive: false });
        } else {
            g.addEventListener('mouseenter', () => showPopup(m));
            g.addEventListener('mouseleave', () => scheduleHide());
        }

        return g;
    }

    // ── HELPERS ──
    function mkRect(x, y, w, h, r, fill, stroke, sw) {
        const el = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        el.setAttribute('x', x); el.setAttribute('y', y);
        el.setAttribute('width', w); el.setAttribute('height', h);
        el.setAttribute('rx', r); el.setAttribute('fill', fill);
        if (stroke !== 'none') { el.setAttribute('stroke', stroke); el.setAttribute('stroke-width', sw); }
        return el;
    }

    function mkText(x, y, text, size, fill, weight, family, anchor) {
        const el = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        el.setAttribute('x', x); el.setAttribute('y', y);
        el.setAttribute('fill', fill); el.setAttribute('font-size', size);
        el.setAttribute('font-weight', weight);
        el.setAttribute('font-family', family + ', sans-serif');
        if (anchor) el.setAttribute('text-anchor', anchor);
        el.textContent = text;
        return el;
    }

    function mkAnim(attr, from, to, dur) {
        const el = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
        el.setAttribute('attributeName', attr);
        el.setAttribute('from', from); el.setAttribute('to', to);
        el.setAttribute('dur', dur); el.setAttribute('repeatCount', 'indefinite');
        return el;
    }

    function screenToSVG(cx, cy) {
        const pt = svg.createSVGPoint();
        pt.x = cx; pt.y = cy;
        return pt.matrixTransform(svg.getScreenCTM().inverse());
    }

    // ── POPUP — anchored to machine node ──
    function showPopup(m) {
        if (editMode) return;
        clearTimeout(popupHideTimer);
        popupMachine = m;

        const s = STATUS[m.durum] || STATUS.kapali;
        document.getElementById('popupStatusDot').style.background = s.color;
        document.getElementById('popupStatusDot').style.boxShadow = 'none';
        document.getElementById('popupTitle').textContent = m.ad;
        document.getElementById('popupSubtitle').textContent = m.kod + ' • ' + s.label;

        const oe = document.getElementById('popupOEE');
        oe.textContent = m.oee != null ? '%' + m.oee : '—';
        oe.style.color = m.oee != null ? (m.oee >= 85 ? '#10b981' : m.oee >= 60 ? '#f59e0b' : '#ef4444') : '#737373';

        document.getElementById('popupUretim').textContent = m.bugun_uretim > 0 ? m.bugun_uretim.toLocaleString('tr-TR') + ' adet' : '—';
        document.getElementById('popupOperator').textContent = m.operator || '—';
        document.getElementById('popupBakim').textContent = m.son_bakim_tarihi || '—';

        const ar = document.getElementById('popupArizaRow');
        if (m.son_ariza) {
            ar.style.display = 'flex';
            document.getElementById('popupAriza').textContent = m.son_ariza.tur + ' (' + m.son_ariza.durum + ')';
        } else {
            ar.style.display = 'none';
        }

        // Sparkline render
        const tc = document.getElementById('popupTrendContainer');
        const sl = document.getElementById('popupSparkline');
        if (m.oee_trend && m.oee_trend.length > 1) {
            tc.style.display = 'block';
            drawSparkline(sl, m.oee_trend, m.oee >= 85 ? '#10b981' : m.oee >= 60 ? '#f59e0b' : '#ef4444');
        } else {
            tc.style.display = 'none';
            sl.innerHTML = '';
        }

        document.getElementById('popupDetailLink').href = DETAIL_BASE + '/' + m.id;

        // Position: anchor to the machine node using SVG → screen coordinates
        const node = layer.querySelector('[data-id="' + m.id + '"]');
        if (!node) return;

        const ctm = svg.getScreenCTM();
        const sx = ctm.a * (m.konum_x + NODE_W) + ctm.e;
        const sy = ctm.d * m.konum_y + ctm.f;

        const pw = 300;
        let px = sx + 12;
        let py = sy;

        // If popup goes off right, flip to left
        if (px + pw > window.innerWidth - 16) {
            px = ctm.a * m.konum_x + ctm.e - pw - 12;
        }
        // If popup goes off bottom
        popup.style.display = 'block';
        popup.classList.add('is-visible');
        const ph = popup.offsetHeight || 280;
        if (py + ph > window.innerHeight - 16) {
            py = window.innerHeight - ph - 16;
        }
        if (py < 10) py = 10;

        popup.style.left = px + 'px';
        popup.style.top = py + 'px';
    }

    function scheduleHide() {
        clearTimeout(popupHideTimer);
        popupHideTimer = setTimeout(() => {
            if (!isOverPopup) {
                popup.classList.remove('is-visible');
                setTimeout(() => {
                    if (!popup.classList.contains('is-visible')) popup.style.display = 'none';
                }, 200);
                popupMachine = null;
            }
        }, 300);
    }

    function setupPopupEvents() {
        popup.addEventListener('mouseenter', () => { isOverPopup = true; clearTimeout(popupHideTimer); });
        popup.addEventListener('mouseleave', () => { isOverPopup = false; scheduleHide(); });
    }

    function drawSparkline(svg, data, color) {
        svg.innerHTML = '';
        const min = Math.min(...data) * 0.95;
        const max = Math.max(...data) * 1.05 || 100;
        const range = max - min || 1;
        
        const w = 100;
        const h = 30;
        const step = w / (data.length - 1);
        
        const points = data.map((val, i) => {
            const x = i * step;
            const y = h - ((val - min) / range) * h;
            return `${x},${y}`;
        });
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        path.setAttribute('points', points.join(' '));
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', color);
        path.setAttribute('stroke-width', '2');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        
        // Add animated draw effect
        const len = 150;
        path.style.strokeDasharray = len;
        path.style.strokeDashoffset = len;
        path.style.animation = 'drawSpark 0.8s ease-out forwards';
        
        if (!document.getElementById('sparkAnim')) {
            const style = document.createElement('style');
            style.id = 'sparkAnim';
            style.innerHTML = `@keyframes drawSpark { to { stroke-dashoffset: 0; } }`;
            document.head.appendChild(style);
        }
        
        svg.appendChild(path);
    }

    // ── EDIT MODE ──
    window.toggleEditMode = function () {
        editMode = !editMode;
        const btnEdit = document.getElementById('btnEditMode');
        const btnSave = document.getElementById('btnSaveLayout');
        const btnCancel = document.getElementById('btnCancelEdit');
        const banner = document.getElementById('editBanner');
        const panel = document.getElementById('unplacedPanel');

        if (editMode) {
            snapshot = JSON.parse(JSON.stringify(machines.map(m => ({ id: m.id, x: m.konum_x, y: m.konum_y }))));
            btnEdit.classList.add('d-none');
            btnSave.classList.remove('d-none');
            btnCancel.classList.remove('d-none');
            banner.classList.remove('d-none');
            panel.classList.remove('d-none');
            clearInterval(refreshTimer);
            renderUnplaced();
        } else {
            btnEdit.classList.remove('d-none');
            btnSave.classList.add('d-none');
            btnCancel.classList.add('d-none');
            banner.classList.add('d-none');
            panel.classList.add('d-none');
            refreshTimer = setInterval(loadData, 30000);
            snapshot = null;
        }
        render();
    };

    window.cancelEditMode = function () {
        if (snapshot) {
            snapshot.forEach(s => {
                const m = machines.find(x => x.id === s.id);
                if (m) { m.konum_x = s.x; m.konum_y = s.y; }
            });
        }
        editMode = false;
        document.getElementById('btnEditMode').classList.remove('d-none');
        document.getElementById('btnSaveLayout').classList.add('d-none');
        document.getElementById('btnCancelEdit').classList.add('d-none');
        document.getElementById('editBanner').classList.add('d-none');
        document.getElementById('unplacedPanel').classList.add('d-none');
        refreshTimer = setInterval(loadData, 30000);
        snapshot = null;
        render();
        toast('Değişiklikler iptal edildi.', 'info');
    };

    function renderUnplaced() {
        const list = document.getElementById('unplacedList');
        const hint = document.getElementById('unplacedHint');
        list.innerHTML = '';
        const unplaced = machines.filter(m => m.konum_x == null || m.konum_y == null);
        if (unplaced.length === 0) { hint.textContent = 'Tüm makineler haritaya yerleştirildi.'; return; }
        hint.textContent = 'Tıklayarak makineleri haritaya ekleyin.';
        unplaced.forEach(m => {
            const s = STATUS[m.durum] || STATUS.kapali;
            const el = document.createElement('div');
            el.className = 'unplaced-chip';
            el.innerHTML = '<span class="chip-dot" style="background:' + s.color + '"></span>' + m.kod + ' — ' + m.ad;
            el.addEventListener('click', () => {
                m.konum_x = 200 + Math.random() * 400;
                m.konum_y = 100 + Math.random() * 200;
                m.konum_w = NODE_W; m.konum_h = NODE_H;
                render(); renderUnplaced();
            });
            list.appendChild(el);
        });
    }

    // ── DRAG & DROP ──
    function startDrag(e) {
        if (!editMode) return;
        e.stopPropagation();
        if (e.touches) e.preventDefault();

        const node = e.currentTarget;
        const id = parseInt(node.getAttribute('data-id'));
        dragTarget = machines.find(m => m.id === id);
        if (!dragTarget) return;

        node.classList.add('is-dragging');
        const cx = e.touches ? e.touches[0].clientX : e.clientX;
        const cy = e.touches ? e.touches[0].clientY : e.clientY;
        const pt = screenToSVG(cx, cy);
        dragOffset.x = pt.x - dragTarget.konum_x;
        dragOffset.y = pt.y - dragTarget.konum_y;

        document.addEventListener('mousemove', doDrag);
        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchmove', doDrag, { passive: false });
        document.addEventListener('touchend', endDrag);
    }

    function doDrag(e) {
        if (!dragTarget) return;
        if (e.touches) e.preventDefault();
        const cx = e.touches ? e.touches[0].clientX : e.clientX;
        const cy = e.touches ? e.touches[0].clientY : e.clientY;
        const pt = screenToSVG(cx, cy);
        dragTarget.konum_x = Math.round(pt.x - dragOffset.x);
        dragTarget.konum_y = Math.round(pt.y - dragOffset.y);
        const node = layer.querySelector('[data-id="' + dragTarget.id + '"]');
        if (node) node.setAttribute('transform', 'translate(' + dragTarget.konum_x + ',' + dragTarget.konum_y + ')');
    }

    function endDrag() {
        if (dragTarget) {
            const node = layer.querySelector('[data-id="' + dragTarget.id + '"]');
            if (node) node.classList.remove('is-dragging');
        }
        dragTarget = null;
        document.removeEventListener('mousemove', doDrag);
        document.removeEventListener('mouseup', endDrag);
        document.removeEventListener('touchmove', doDrag);
        document.removeEventListener('touchend', endDrag);
    }

    // ── SAVE ──
    window.saveAllPositions = function () {
        const payload = {
            makineler: machines
                .filter(m => m.konum_x != null && m.konum_y != null)
                .map(m => ({ makine_id: m.id, konum_x: m.konum_x, konum_y: m.konum_y, konum_w: NODE_W, konum_h: NODE_H }))
        };
        fetch(UPDATE_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
            body: JSON.stringify(payload),
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                toast('Yerleşim kaydedildi!', 'success');
                editMode = true;
                toggleEditMode();
                loadData();
            } else {
                toast('Hata: ' + (data.error || ''), 'danger');
            }
        })
        .catch(() => toast('Bağlantı hatası!', 'danger'));
    };

    function toast(msg, type) {
        const c = document.getElementById('toast-container');
        if (!c) return;
        const icons = { success: 'check-circle', danger: 'exclamation-triangle', info: 'info-circle' };
        const el = document.createElement('div');
        el.className = 'alert alert-' + type + ' shadow-lg mb-2';
        el.style.cssText = 'min-width:280px;animation:fadeUp 0.3s ease;font-size:0.88rem;';
        el.innerHTML = '<i class="bi bi-' + (icons[type] || 'info-circle') + ' me-2"></i>' + msg;
        c.appendChild(el);
        setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 3000);
    }
})();
