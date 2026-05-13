/**
 * FDYS — Dashboard Grafikleri & Yardımcılar
 * Ana gösterge paneli için etkileşimli KPI kartları ve dinamik veri güncellemeleri.
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // ── KPI Kartları Hover Efektleri ──
    const kpiCards = document.querySelectorAll('.kpi-mini-card');
    kpiCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px) scale(1.02)';
            this.style.transition = 'transform 0.25s ease, box-shadow 0.25s ease';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });

    // ── Tarih Göstergesi ──
    const dateEl = document.querySelector('.welcome-section p');
    if (dateEl && !dateEl.textContent.trim()) {
        const now = new Date();
        const opts = { day: 'numeric', month: 'long', year: 'numeric' };
        dateEl.textContent = now.toLocaleDateString('tr-TR', opts);
    }

    // ── Sayıları Animasyonlu Göster ──
    const animateValue = (el, start, end, duration) => {
        const range = end - start;
        const startTime = performance.now();
        const step = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
            el.textContent = Math.round(start + range * eased).toLocaleString('tr-TR');
            if (progress < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
    };

    // KPI rakamlarını animasyonla göster
    const kpiValues = document.querySelectorAll('.kpi-mini-card h3');
    kpiValues.forEach(el => {
        const text = el.textContent.trim();
        const numericValue = parseFloat(text.replace(/[^0-9.,\-]/g, '').replace(',', '.'));
        if (!isNaN(numericValue) && numericValue > 0 && numericValue < 100000) {
            const prefix = text.startsWith('%') ? '%' : '';
            const suffix = text.endsWith('%') ? '%' : '';
            el.textContent = prefix + '0' + suffix;
            setTimeout(() => {
                animateValue(el, 0, numericValue, 800);
                setTimeout(() => {
                    el.textContent = text; // Restore original with formatting
                }, 850);
            }, 200);
        }
    });

    console.log('FDYS Dashboard modülü yüklendi.');
});
