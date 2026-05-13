/**
 * FDYS — Gelişmiş Analitik JS (Kategori 4)
 */
const CSRF = document.querySelector('meta[name="csrf-token"]')?.content;

// ═══ KORELASYON ═══
function yukleKorelasyon() {
    const gun = document.getElementById('omGunFiltre')?.value || 30;
    yukleInsightlar();
    yukleOperatorMakine(gun);
    yukleEnerjiUretim(gun);
    yukleHataZaman();
}

function yukleInsightlar() {
    fetch('/analitik/api/korelasyon/insightlar').then(r=>r.json()).then(data => {
        const c = document.getElementById('insightCards');
        if (!c) return;
        const renkler = {success:'#10b981',danger:'#ef4444',warning:'#f59e0b',info:'#06b6d4'};
        c.innerHTML = data.map(d => {
            const renk = renkler[d.seviye] || '#3b82f6';
            let bg;
            if (d.seviye === 'danger') bg = 'rgba(239, 68, 68, 0.12)';
            else if (d.seviye === 'warning') bg = 'rgba(245, 158, 11, 0.12)';
            else if (d.seviye === 'success') bg = 'rgba(16, 185, 129, 0.12)';
            else bg = 'rgba(59, 130, 246, 0.12)';

            return `
            <div class="col-xl col-md-6">
                <div class="card border-0 shadow-sm h-100 p-3" style="border-left: 4px solid ${renk} !important; border-radius: 1rem; transition: transform 0.2s ease;">
                    <div class="d-flex align-items-start gap-3">
                        <div class="d-flex align-items-center justify-content-center flex-shrink-0" style="width: 44px; height: 44px; border-radius: 12px; background: ${bg}; color: ${renk};">
                            <i class="bi ${d.icon} fs-4"></i>
                        </div>
                        <div>
                            <div class="fw-bold mb-1" style="color: var(--text-heading); font-size: 0.95rem; line-height: 1.3;">${d.baslik}</div>
                            <div class="text-muted" style="font-size: 0.8rem; line-height: 1.4;">${d.aciklama}</div>
                        </div>
                    </div>
                </div>
            </div>`;
        }).join('');
    }).catch(() => {});
}

function yukleOperatorMakine(gun) {
    fetch(`/analitik/api/korelasyon/operator-makine?gun=${gun}`).then(r=>r.json()).then(data => {
        const c = document.getElementById('omMatrisContainer');
        if (!c || !data.operatorler?.length) { c.innerHTML = '<div class="p-4 text-center text-muted">Yeterli veri yok.</div>'; return; }
        let html = '<table class="table table-hover align-middle mb-0"><thead><tr><th>Operatör</th>';
        data.makineler.forEach(m => html += `<th class="text-center">${m.kod}</th>`);
        html += '</tr></thead><tbody>';
        data.operatorler.forEach((op, i) => {
            html += `<tr><td class="fw-bold">${op.ad}</td>`;
            data.makineler.forEach((_, j) => {
                const d = data.matris[i][j];
                if (d.oee !== null && d.oee !== undefined) {
                    const renk = d.oee >= 85 ? '#10b981' : d.oee >= 70 ? '#f59e0b' : '#ef4444';
                    const bg = d.oee >= 85 ? 'rgba(16,185,129,0.12)' : d.oee >= 70 ? 'rgba(245,158,11,0.12)' : 'rgba(239,68,68,0.12)';
                    html += `<td class="text-center" style="background:${bg}"><span class="fw-bold" style="color:${renk}">%${d.oee}</span><br><small class="text-muted">${d.uretim} adet</small></td>`;
                } else {
                    html += '<td class="text-center text-muted">—</td>';
                }
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        c.innerHTML = html;
    }).catch(() => {});
}

function yukleEnerjiUretim(gun) {
    fetch(`/analitik/api/korelasyon/enerji-uretim?gun=${gun}`).then(r=>r.json()).then(resp => {
        const data = resp.makineler || [];
        const el = document.getElementById('enerjiUretimChart');
        if (!el) return;
        const parent = el.parentElement;
        
        if (!data.length) {
            parent.innerHTML = '<div class="text-center py-5 text-muted">Yeterli enerji/üretim verisi bulunamadı.</div>';
            return;
        }
        
        if (window._euChart) window._euChart.destroy();
        const renkler = data.map(d => d.verimlilik === 'yuksek' ? '#10b981' : d.verimlilik === 'orta' ? '#f59e0b' : '#ef4444');
        window._euChart = new Chart(el.getContext('2d'), {
            type: 'bar', data: {
                labels: data.map(d => d.makine_kod),
                datasets: [{ label: 'kWh/adet', data: data.map(d => d.birim_enerji), backgroundColor: renkler, borderRadius: 8, borderSkipped: false }]
            }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, grid: { color: 'rgba(148,163,184,0.08)' }, ticks: { color: '#64748B' } }, x: { grid: { display: false }, ticks: { color: '#64748B' } } } }
        });

        // Pearson korelasyon notunu ekle
        let notEl = document.getElementById('pearsonNot');
        if (!notEl) {
            notEl = document.createElement('div');
            notEl.id = 'pearsonNot';
            notEl.className = 'text-center mt-3 small text-muted';
            parent.appendChild(notEl);
        }
        notEl.innerHTML = `<strong>Korelasyon:</strong> ${resp.pearson_yorum}`;

    }).catch(() => {});
}

function yukleHataZaman() {
    fetch('/analitik/api/korelasyon/hata-zaman').then(r=>r.json()).then(data => {
        const c = document.getElementById('hataZamanContainer');
        if (!c) return;
        let html = '<table class="table table-sm mb-2"><thead><tr><th></th>';
        data.vardiyalar.forEach(v => html += `<th class="text-center">${v}</th>`);
        html += '</tr></thead><tbody>';
        const max = Math.max(...data.matris.flat(), 1);
        data.gunler.forEach((g, i) => {
            html += `<tr><td class="fw-bold" style="font-size:0.82rem;">${g}</td>`;
            data.matris[i].forEach(val => {
                const yo = val / max;
                const bg = val === 0 ? 'transparent' : `rgba(239,68,68,${0.1 + yo * 0.6})`;
                html += `<td class="text-center" style="background:${bg};border-radius:6px;"><span class="fw-bold" style="font-size:0.85rem;">${val || '—'}</span></td>`;
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        if (data.insight) html += `<div class="alert alert-warning py-2 mb-0"><i class="bi bi-lightbulb me-2"></i><strong>${data.insight.baslik}</strong> — ${data.insight.aciklama}</div>`;
        c.innerHTML = html;
    }).catch(() => {});
}

// ═══ KARŞILAŞTIRMA ═══
function makineKarsilastir() {
    const m1 = document.getElementById('karsMakine1')?.value;
    const m2 = document.getElementById('karsMakine2')?.value;
    if (!m1 || !m2) { alert('İki makine seçin'); return; }
    const bas = document.getElementById('karsBas')?.value || '';
    const bit = document.getElementById('karsBit')?.value || '';
    fetch(`/analitik/api/karsilastir/makine?m1=${m1}&m2=${m2}&bas=${bas}&bit=${bit}`).then(r=>r.json()).then(data => {
        if (data.error) { document.getElementById('makineKarsSonuc').innerHTML = `<div class="alert alert-danger">${data.error}</div>`; return; }
        const mk1 = data.makine1, mk2 = data.makine2;
        const metrikler = [
            {ad:'OEE', k:'ort_oee', b:'%', yukari:true}, {ad:'Üretim', k:'toplam_uretim', b:' adet', yukari:true},
            {ad:'Hata Oranı', k:'hata_orani', b:'%', yukari:false}, {ad:'Arıza', k:'ariza_sayisi', b:'', yukari:false},
            {ad:'Duruş', k:'durus_dk', b:' dk', yukari:false}, {ad:'Bakım Mal.', k:'bakim_maliyeti', b:' ₺', yukari:false}
        ];
        let html = `<div class="row g-3 mb-4"><div class="col-md-5"><div class="card border-0 shadow-sm ${data.kazanan===1?'border-success':''}"><div class="card-body text-center">
            <h5 class="fw-bold mb-1">${mk1.makine_kod}</h5><p class="text-muted mb-3">${mk1.makine_ad}</p>`;
        metrikler.forEach(m => {
            const iyi = m.yukari ? mk1[m.k] >= mk2[m.k] : mk1[m.k] <= mk2[m.k];
            html += `<div class="d-flex justify-content-between py-1 border-bottom" style="border-color:var(--border-color)!important;"><span class="text-muted">${m.ad}</span><span class="fw-bold ${iyi?'text-success':'text-danger'}">${mk1[m.k]}${m.b}</span></div>`;
        });
        html += `</div></div></div><div class="col-md-2 d-flex align-items-center justify-content-center"><div class="text-center"><div class="rounded-circle d-flex align-items-center justify-content-center mx-auto mb-2" style="width:56px;height:56px;background:var(--bg-card);border:2px solid var(--border-color);"><span class="fw-bold text-muted">VS</span></div><span class="badge bg-primary-subtle text-primary-emphasis">${data.skor[0]} — ${data.skor[1]}</span></div></div>`;
        html += `<div class="col-md-5"><div class="card border-0 shadow-sm ${data.kazanan===2?'border-success':''}"><div class="card-body text-center">
            <h5 class="fw-bold mb-1">${mk2.makine_kod}</h5><p class="text-muted mb-3">${mk2.makine_ad}</p>`;
        metrikler.forEach(m => {
            const iyi = m.yukari ? mk2[m.k] >= mk1[m.k] : mk2[m.k] <= mk1[m.k];
            html += `<div class="d-flex justify-content-between py-1 border-bottom" style="border-color:var(--border-color)!important;"><span class="text-muted">${m.ad}</span><span class="fw-bold ${iyi?'text-success':'text-danger'}">${mk2[m.k]}${m.b}</span></div>`;
        });
        html += '</div></div></div></div>';
        // Trend chart
        if (data.trend_labels?.length) {
            html += '<div class="card border-0 shadow-sm"><div class="card-body" style="height:280px;"><canvas id="karsTrendChart"></canvas></div></div>';
        }
        document.getElementById('makineKarsSonuc').innerHTML = html;
        if (data.trend_labels?.length) {
            setTimeout(() => {
                const ctx = document.getElementById('karsTrendChart');
                if (!ctx) return;
                new Chart(ctx.getContext('2d'), { type:'line', data:{ labels:data.trend_labels, datasets:[
                    {label:mk1.makine_kod, data:data.trend_m1, borderColor:'#3b82f6', tension:0.4, pointRadius:3, borderWidth:2},
                    {label:mk2.makine_kod, data:data.trend_m2, borderColor:'#ef4444', tension:0.4, pointRadius:3, borderWidth:2}
                ]}, options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{color:'#CBD5E1'}}},scales:{y:{grid:{color:'rgba(148,163,184,0.08)'},ticks:{color:'#64748B',callback:v=>v+'%'}},x:{grid:{display:false},ticks:{color:'#64748B'}}}}});
            }, 100);
        }
    }).catch(e => { document.getElementById('makineKarsSonuc').innerHTML = `<div class="alert alert-danger">Hata: ${e}</div>`; });
}

function donemKarsilastir() {
    const p = ['d1Bas','d1Bit','d2Bas','d2Bit'].map(id => document.getElementById(id)?.value);
    if (p.some(v => !v)) { alert('Tüm tarihleri seçin'); return; }
    fetch(`/analitik/api/karsilastir/donem?d1_bas=${p[0]}&d1_bit=${p[1]}&d2_bas=${p[2]}&d2_bit=${p[3]}`).then(r=>r.json()).then(data => {
        if (data.error) { document.getElementById('donemKarsSonuc').innerHTML = `<div class="alert alert-danger">${data.error}</div>`; return; }
        const metrikler = [{ad:'OEE',k:'ort_oee',b:'%',i:'bi-speedometer2'},{ad:'Üretim',k:'toplam_uretim',b:' adet',i:'bi-box'},{ad:'Hata Oranı',k:'hata_orani',b:'%',i:'bi-bug'},{ad:'Arıza',k:'ariza_sayisi',b:'',i:'bi-tools'},{ad:'Enerji Mal.',k:'enerji_maliyeti',b:' ₺',i:'bi-lightning'},{ad:'Kaza',k:'kaza_sayisi',b:'',i:'bi-shield-exclamation'}];
        let html = '<div class="row g-3">';
        metrikler.forEach(m => {
            const d = data.degisimler[m.k] || 0;
            const renk = d > 0 ? (m.k==='ort_oee'||m.k==='toplam_uretim'?'success':'danger') : (m.k==='ort_oee'||m.k==='toplam_uretim'?'danger':'success');
            html += `<div class="col-md-4"><div class="card border-0 shadow-sm"><div class="card-body"><div class="d-flex justify-content-between align-items-center mb-2"><span class="text-muted"><i class="bi ${m.i} me-1"></i>${m.ad}</span><span class="badge bg-${renk}-subtle text-${renk}-emphasis">${d>0?'+':''}${d}%</span></div>
            <div class="d-flex justify-content-between"><div><small class="text-muted d-block">Dönem 1</small><span class="fw-bold fs-5">${data.donem1[m.k]}${m.b}</span></div><div class="text-end"><small class="text-muted d-block">Dönem 2</small><span class="fw-bold fs-5">${data.donem2[m.k]}${m.b}</span></div></div></div></div></div>`;
        });
        html += '</div>';
        document.getElementById('donemKarsSonuc').innerHTML = html;
    }).catch(e => { document.getElementById('donemKarsSonuc').innerHTML = `<div class="alert alert-danger">Hata: ${e}</div>`; });
}

function yukleVardiya() {
    fetch('/analitik/api/karsilastir/vardiya').then(r=>r.json()).then(data => {
        const c = document.getElementById('vardiyaKarsSonuc');
        if (!c || !data.length) { c.innerHTML = '<div class="p-4 text-center text-muted">Veri yok.</div>'; return; }
        const renkler = ['#3b82f6','#f59e0b','#8b5cf6'];
        let html = '<div class="row g-3 mb-4">';
        data.forEach((v, i) => {
            html += `<div class="col-md-4"><div class="card border-0 shadow-sm" style="border-top:3px solid ${renkler[i]}"><div class="card-body text-center">
            <h5 class="fw-bold">${v.ad}</h5>
            <div class="display-6 fw-bold mb-2" style="color:${renkler[i]}">%${v.ort_oee}</div><small class="text-muted">OEE</small>
            <hr style="border-color:var(--border-color);">
            <div class="d-flex justify-content-around text-center">
            <div><div class="fw-bold">${v.toplam_uretim.toLocaleString('tr-TR')}</div><small class="text-muted">Üretim</small></div>
            <div><div class="fw-bold text-danger">%${v.hata_orani}</div><small class="text-muted">Hata</small></div>
            <div><div class="fw-bold text-warning">%${v.durus_yuzde}</div><small class="text-muted">Duruş</small></div>
            </div></div></div></div>`;
        });
        html += '</div>';
        c.innerHTML = html;
    }).catch(() => {});
}

// ═══ KPI ═══
function yukleKpi() {
    const yil = document.getElementById('kpiYilFiltre')?.value || new Date().getFullYear();
    const ay = document.getElementById('kpiAyFiltre')?.value || (new Date().getMonth()+1);
    fetch(`/analitik/api/kpi/ozet?yil=${yil}&ay=${ay}`).then(r=>r.json()).then(data => {
        const c = document.getElementById('kpiSonuclar');
        if (!c) return;
        if (!data.length) { c.innerHTML = '<div class="col-12 text-center text-muted py-5"><i class="bi bi-bullseye fs-1 d-block mb-3 opacity-50"></i><p>Henüz KPI hedefi tanımlanmamış.</p><p class="small">Varsayılan hedefleri yüklemek için yukarıdaki butonu kullanın.</p></div>'; return; }
        const durumRenk = {basarili:'success',uyari:'warning',kritik:'danger',belirsiz:'secondary'};
        const durumIcon = {basarili:'bi-check-circle-fill',uyari:'bi-exclamation-triangle-fill',kritik:'bi-x-circle-fill',belirsiz:'bi-question-circle'};
        const modRenk = {makine:'#3b82f6',kalite:'#10b981',enerji:'#f59e0b',isg:'#ef4444',stok:'#06b6d4',personel:'#8b5cf6'};
        c.innerHTML = data.map(k => {
            const r = durumRenk[k.durum]||'secondary';
            const g = k.gerceklesen !== null ? k.gerceklesen : '—';
            const bar = Math.min(k.tutma_yuzde || 0, 100);
            return `<div class="col-xl-4 col-md-6"><div class="card border-0 shadow-sm h-100" style="border-top:3px solid ${modRenk[k.modul]||'#3b82f6'}"><div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div><span class="badge bg-${r}-subtle text-${r}-emphasis mb-1">${k.modul_adi}</span><h6 class="fw-bold mb-0">${k.kpi_adi}</h6></div>
                    <i class="bi ${durumIcon[k.durum]} text-${r} fs-5"></i></div>
                <div class="d-flex justify-content-between mb-1"><span class="text-muted small">Gerçekleşen</span><span class="fw-bold">${g} ${k.birim}</span></div>
                <div class="d-flex justify-content-between mb-2"><span class="text-muted small">Hedef</span><span class="fw-bold">${k.hedef} ${k.birim}</span></div>
                <div class="progress mb-1" style="height:8px;background:var(--border-color);border-radius:8px;">
                    <div class="progress-bar bg-${r}" style="width:${bar}%;border-radius:8px;"></div></div>
                <div class="d-flex justify-content-between"><small class="text-muted">${k.periyot_adi}</small><small class="fw-bold text-${r}">%${k.tutma_yuzde}</small></div>
                <div class="mt-2 pt-2 border-top d-flex gap-1" style="border-color:var(--border-color)!important;">
                    <form method="POST" action="/analitik/kpi/${k.id}/sil" class="d-inline"><input type="hidden" name="csrf_token" value="${CSRF}"><button type="button" class="btn btn-sm btn-outline-danger" onclick="window.fdysConfirm('Bu KPI hedefini silmek istediğinize emin misiniz?').then(c => { if(c) this.closest('form').submit(); })"><i class="bi bi-trash3"></i></button></form>
                </div></div></div></div>`;
        }).join('');
    }).catch(() => {});
}

// ═══ MALİYET ═══
function yukleTco() {
    const id = document.getElementById('tcoMakineSecim')?.value;
    if (!id) return;
    fetch(`/analitik/api/maliyet/tco/${id}`).then(r=>r.json()).then(data => {
        if (data.error) { document.getElementById('tcoSonuc').innerHTML = `<div class="alert alert-danger">${data.error}</div>`; return; }
        const fmt = v => v.toLocaleString('tr-TR', {minimumFractionDigits:0, maximumFractionDigits:0});
        let html = `<div class="text-center mb-3"><div class="display-6 fw-bold" style="color:var(--text-heading);">${fmt(data.toplam_tco)} ₺</div><small class="text-muted">Toplam Sahip Olma Maliyeti</small></div>`;
        data.dagilim.forEach(d => {
            const yuzde = data.toplam_tco > 0 ? Math.round((d.tutar / data.toplam_tco) * 100) : 0;
            html += `<div class="d-flex justify-content-between align-items-center py-2 border-bottom" style="border-color:var(--border-color)!important;">
                <div class="d-flex align-items-center gap-2"><div style="width:12px;height:12px;border-radius:50%;background:${d.renk};"></div><span>${d.kategori}</span></div>
                <div class="text-end"><span class="fw-bold">${fmt(d.tutar)} ₺</span><small class="text-muted ms-2">%${yuzde}</small></div></div>`;
        });
        html += `<div class="mt-3 text-center"><small class="text-muted">Günlük ortalama: <strong>${fmt(data.gunluk_ort)} ₺</strong></small></div>`;
        document.getElementById('tcoSonuc').innerHTML = html;
    }).catch(() => {});
}

function yukleBirimMaliyet() {
    fetch('/analitik/api/maliyet/birim-maliyet').then(r=>r.json()).then(data => {
        const c = document.getElementById('birimMaliyetSonuc');
        if (!c || !data.length) { c.innerHTML = '<div class="p-4 text-center text-muted">Veri yok.</div>'; return; }
        let html = '<table class="table table-hover align-middle mb-0"><thead><tr><th>#</th><th>Makine</th><th>Toplam Maliyet</th><th>Üretim</th><th>Birim Maliyet</th></tr></thead><tbody>';
        data.forEach((d, i) => {
            const renk = i < data.length / 3 ? 'success' : i < 2 * data.length / 3 ? 'warning' : 'danger';
            html += `<tr><td>${i+1}</td><td class="fw-bold">${d.makine_kod}</td><td>${d.toplam_maliyet.toLocaleString('tr-TR')} ₺</td><td>${d.toplam_uretim.toLocaleString('tr-TR')}</td><td><span class="badge bg-${renk}">${d.birim_maliyet} ₺/adet</span></td></tr>`;
        });
        html += '</tbody></table>';
        c.innerHTML = html;
    }).catch(() => {});
}

function yukleRoi() {
    const id = document.getElementById('roiMakineSecim')?.value;
    if (!id) return;
    fetch(`/analitik/api/maliyet/roi/${id}`).then(r=>r.json()).then(data => {
        if (data.error) { document.getElementById('roiSonuc').innerHTML = `<div class="alert alert-warning">${data.error}</div>`; return; }
        const fmt = v => v?.toLocaleString('tr-TR', {minimumFractionDigits:0, maximumFractionDigits:0}) || '—';
        const roiRenk = data.roi_yuzde >= 100 ? 'success' : data.roi_yuzde >= 0 ? 'warning' : 'danger';
        let html = `<div class="row g-4"><div class="col-md-3 text-center"><div class="display-5 fw-bold text-${roiRenk}">%${data.roi_yuzde}</div><small class="text-muted">ROI</small></div>
        <div class="col-md-3 text-center"><div class="fs-4 fw-bold">${fmt(data.satin_alma)} ₺</div><small class="text-muted">Satın Alma</small></div>
        <div class="col-md-3 text-center"><div class="fs-4 fw-bold text-success">${fmt(data.toplam_gelir)} ₺</div><small class="text-muted">Toplam Gelir</small></div>
        <div class="col-md-3 text-center"><div class="fs-4 fw-bold text-info">${data.amortisman_gun ? data.amortisman_gun+' gün' : '—'}</div><small class="text-muted">Amortisman Süresi</small></div></div>`;
        document.getElementById('roiSonuc').innerHTML = html;
    }).catch(() => {});
}
