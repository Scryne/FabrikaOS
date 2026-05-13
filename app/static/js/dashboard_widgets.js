/**
 * FDYS — Gelişmiş Dashboard Widget'ları
 * Faz 5 — OEE Gauge, Canlı Üretim Sayacı, Widget Yönetimi
 */

const DashboardWidgets = {

    refreshInterval: null,

    init() {
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
        this._startAutoRefresh();
        this._initDragDrop();
    },

    /* ── OEE Gauge ── */
    createOEEGauge(canvasId, oeeValue) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const renk = oeeValue >= 85 ? '#00b894' : oeeValue >= 70 ? '#fdcb6e' : '#d63031';
        const kalan = 100 - Math.min(oeeValue, 100);

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [oeeValue, kalan],
                    backgroundColor: [renk, 'rgba(255,255,255,0.06)'],
                    borderWidth: 0,
                    circumference: 180,
                    rotation: 270
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '78%',
                layout: {
                    padding: {
                        bottom: 25
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            },
            plugins: [{
                id: 'gaugeText',
                afterDraw(chart) {
                    const { ctx, chartArea } = chart;
                    const centerX = (chartArea.left + chartArea.right) / 2;
                    const centerY = chartArea.bottom - 10;
                    ctx.save();
                    ctx.textAlign = 'center';
                    ctx.fillStyle = renk;
                    ctx.font = "bold 28px 'Outfit', sans-serif";
                    ctx.fillText(`%${oeeValue}`, centerX, centerY - 10);
                    ctx.fillStyle = '#888';
                    ctx.font = "12px 'Inter', sans-serif";
                    ctx.fillText('Anlık OEE', centerX, centerY + 12);
                    ctx.restore();
                }
            }]
        });
    },

    /* ── Canlı Üretim Sayacı ── */
    animateCounter(elementId, targetValue, duration = 1500) {
        const el = document.getElementById(elementId);
        if (!el) return;

        const start = parseInt(el.textContent.replace(/[^0-9]/g, '')) || 0;
        const diff = targetValue - start;
        const startTime = performance.now();

        function step(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
            const current = Math.round(start + diff * eased);
            el.textContent = current.toLocaleString('tr-TR');
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    },

    /* ── Auto Refresh ── */
    _startAutoRefresh() {
        this.refreshInterval = setInterval(() => this._fetchRealtimeData(), 30000);
    },

    async _fetchRealtimeData() {
        try {
            const resp = await fetch('/api/dashboard/realtime');
            if (!resp.ok) return;
            const data = await resp.json();

            if (data.bugun_uretim !== undefined) {
                this.animateCounter('canliUretimSayaci', data.bugun_uretim);
            }
            if (data.ort_oee !== undefined) {
                const gaugeEl = document.getElementById('oeeGaugeValue');
                if (gaugeEl) gaugeEl.textContent = `%${data.ort_oee}`;
            }
            if (data.acik_ariza !== undefined) {
                const el = document.getElementById('canliAcikAriza');
                if (el) el.textContent = data.acik_ariza;
            }
        } catch (err) {
            // Sessizce devam et
        }
    },

    /* ── Widget Drag & Drop ── */
    _initDragDrop() {
        const widgets = document.querySelectorAll('.dashboard-widget');
        if (widgets.length === 0) return;

        widgets.forEach(w => {
            w.setAttribute('draggable', 'true');
            w.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', w.id);
                w.classList.add('dragging');
            });
            w.addEventListener('dragend', () => w.classList.remove('dragging'));
            w.addEventListener('dragover', (e) => { e.preventDefault(); w.classList.add('drag-target'); });
            w.addEventListener('dragleave', () => w.classList.remove('drag-target'));
            w.addEventListener('drop', (e) => {
                e.preventDefault();
                w.classList.remove('drag-target');
                const sourceId = e.dataTransfer.getData('text/plain');
                const sourceEl = document.getElementById(sourceId);
                if (sourceEl && sourceEl !== w) {
                    const parent = w.parentNode;
                    const sourceNext = sourceEl.nextElementSibling;
                    parent.insertBefore(sourceEl, w);
                    if (sourceNext) parent.insertBefore(w, sourceNext);
                    else parent.appendChild(w);
                    this._saveLayout();
                }
            });
        });
    },

    async _saveLayout() {
        const widgets = document.querySelectorAll('.dashboard-widget');
        const layout = Array.from(widgets).map((w, i) => ({ id: w.id, order: i, visible: !w.classList.contains('d-none') }));
        try {
            await fetch('/api/dashboard/layout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
                body: JSON.stringify({ layout })
            });
        } catch (err) { /* sessiz */ }
    },

    toggleWidget(widgetId) {
        const el = document.getElementById(widgetId);
        if (el) {
            el.classList.toggle('d-none');
            this._saveLayout();
        }
    },

    destroy() {
        if (this.refreshInterval) clearInterval(this.refreshInterval);
    }
};
