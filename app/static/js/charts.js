/**
 * FDYS — Chart.js Profesyonel Kurumsal Tema & Yardımcılar
 * Tüm grafiklerde tutarlı, enterprise-grade görünüm sağlar.
 */

const FDYS_CHARTS = (() => {
    'use strict';

    // ── Renk Paleti ──
    const COLORS = {
        // Temel renkler
        primary:       '#5B8DEF',
        primaryLight:  'rgba(91, 141, 239, 0.15)',
        primaryGlow:   'rgba(91, 141, 239, 0.35)',
        accent:        '#A78BFA',
        accentLight:   'rgba(167, 139, 250, 0.15)',
        
        // Durum renkleri
        success:       '#34D399',
        successLight:  'rgba(52, 211, 153, 0.15)',
        warning:       '#FBBF24',
        warningLight:  'rgba(251, 191, 36, 0.15)',
        danger:        '#F87171',
        dangerLight:   'rgba(248, 113, 113, 0.15)',
        dangerGlow:    'rgba(248, 113, 113, 0.35)',
        info:          '#38BDF8',
        infoLight:     'rgba(56, 189, 248, 0.15)',
        
        // Nötr renkler (dark theme)
        text:          '#CBD5E1',
        textMuted:     '#64748B',
        gridLine:      'rgba(148, 163, 184, 0.08)',
        cardBg:        '#1E293B',
        tooltipBg:     'rgba(15, 23, 42, 0.95)',
        
        // Grafik serisi renkleri
        series: [
            '#5B8DEF', '#F87171', '#34D399', '#FBBF24',
            '#A78BFA', '#38BDF8', '#FB923C', '#E879F9'
        ],
        seriesLight: [
            'rgba(91, 141, 239, 0.75)',
            'rgba(248, 113, 113, 0.75)',
            'rgba(52, 211, 153, 0.75)',
            'rgba(251, 191, 36, 0.75)',
            'rgba(167, 139, 250, 0.75)',
            'rgba(56, 189, 248, 0.75)',
            'rgba(251, 146, 60, 0.75)',
            'rgba(232, 121, 249, 0.75)'
        ]
    };

    // ── Ortak Font Ayarları ──
    const FONT = {
        family: "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
        size: 11,
        titleSize: 13,
        weight: '500'
    };

    // ── Türkçe Ay İsimleri ──
    const TR_AYLAR = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'];

    /**
     * YYYY-MM formatındaki etiketi okunabilir Türkçe aya çevirir.
     * Örn: "2026-05" → "May 2026"
     */
    function formatMonthLabel(label) {
        if (typeof label !== 'string') return label;
        const parts = label.split('-');
        if (parts.length === 2 && parts[1].length === 2) {
            const monthIdx = parseInt(parts[1], 10) - 1;
            if (monthIdx >= 0 && monthIdx < 12) {
                return TR_AYLAR[monthIdx] + ' ' + parts[0];
            }
        }
        return label;
    }

    /**
     * snake_case veya alt çizgili etiketi başlık formatına çevirir.
     * Örn: "boyut_hatasi" → "Boyut Hatası"
     */
    function formatSnakeCaseLabel(label) {
        if (typeof label !== 'string') return label;
        return label
            .replace(/_/g, ' ')
            .replace(/\b\w/g, c => c.toUpperCase());
    }

    // ── Tooltip Formatı ──
    const tooltipConfig = (unit = '') => ({
        enabled: true,
        backgroundColor: COLORS.tooltipBg,
        titleColor: '#F1F5F9',
        bodyColor: '#CBD5E1',
        borderColor: 'rgba(148, 163, 184, 0.15)',
        borderWidth: 1,
        cornerRadius: 10,
        padding: { top: 10, bottom: 10, left: 14, right: 14 },
        titleFont: { family: FONT.family, size: 12, weight: '600' },
        bodyFont: { family: FONT.family, size: 11, weight: '400' },
        boxPadding: 6,
        usePointStyle: true,
        displayColors: true,
        caretSize: 6,
        caretPadding: 8,
        callbacks: {
            label: function(ctx) {
                let label = ctx.dataset.label || '';
                let value = ctx.parsed.y !== undefined ? ctx.parsed.y : ctx.parsed;
                if (typeof value === 'number') {
                    value = value.toLocaleString('tr-TR');
                }
                return label ? `  ${label}: ${value}${unit}` : `  ${value}${unit}`;
            }
        }
    });

    // ── Axis Ortak Yapılandırma ──
    const axisDefaults = {
        x: {
            grid: {
                display: false,
                drawBorder: false
            },
            ticks: {
                color: COLORS.textMuted,
                font: { family: FONT.family, size: FONT.size, weight: '400' },
                padding: 8
            },
            border: {
                display: false
            }
        },
        y: {
            grid: {
                color: COLORS.gridLine,
                drawBorder: false,
                lineWidth: 1
            },
            ticks: {
                color: COLORS.textMuted,
                font: { family: FONT.family, size: FONT.size, weight: '400' },
                padding: 10,
                callback: function(value) {
                    if (Math.abs(value) >= 1000) {
                        return value.toLocaleString('tr-TR');
                    }
                    return value;
                }
            },
            border: {
                display: false
            }
        }
    };

    // ── Legend Ortak Yapılandırma ──
    const legendConfig = (position = 'bottom') => ({
        position: position,
        labels: {
            color: COLORS.text,
            font: { family: FONT.family, size: 11, weight: '500' },
            padding: 20,
            usePointStyle: true,
            pointStyleWidth: 10,
            boxHeight: 8
        }
    });

    // ── Gradient Oluşturucu ──
    function createGradient(ctx, colorTop, colorBottom, height = 300) {
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, colorTop);
        gradient.addColorStop(1, colorBottom);
        return gradient;
    }

    // ══════════════════════════════════════════
    //  PUBLIC API — Grafik Oluşturucular
    // ══════════════════════════════════════════

    /**
     * Profesyonel Çizgi Grafik (Area) — Tek veri seti
     */
    function createLineChart(canvasId, config) {
        const el = document.getElementById(canvasId);
        if (!el) return null;
        const ctx = el.getContext('2d');

        const gradient = createGradient(
            ctx,
            config.gradientTop || COLORS.primaryLight,
            'rgba(0,0,0,0)',
            el.parentElement.offsetHeight || 300
        );

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: config.labels,
                datasets: [{
                    label: config.label || '',
                    data: config.values,
                    borderColor: config.lineColor || COLORS.primary,
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2.5,
                    pointRadius: config.pointRadius !== undefined ? config.pointRadius : 4,
                    pointHoverRadius: 7,
                    pointBackgroundColor: config.lineColor || COLORS.primary,
                    pointBorderColor: COLORS.cardBg,
                    pointBorderWidth: 2,
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: config.lineColor || COLORS.primary,
                    pointHoverBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: { ...axisDefaults.x },
                    y: {
                        ...axisDefaults.y,
                        beginAtZero: config.beginAtZero !== false,
                        max: config.maxY || undefined,
                        title: config.yTitle ? {
                            display: true,
                            text: config.yTitle,
                            color: COLORS.textMuted,
                            font: { family: FONT.family, size: 11, weight: '500' }
                        } : undefined
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: tooltipConfig(config.unit || '')
                },
                animation: {
                    duration: 800,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    /**
     * Profesyonel Çoklu Çizgi Grafik — Birden fazla veri seti
     * config.datasets: [{ label, data, color, dashed, fill }]
     */
    function createMultiLineChart(canvasId, config) {
        const el = document.getElementById(canvasId);
        if (!el) return null;
        const ctx = el.getContext('2d');

        const datasets = config.datasets.map((ds, i) => {
            const color = ds.color || COLORS.series[i % COLORS.series.length];
            const dataset = {
                label: ds.label,
                data: ds.data,
                borderColor: color,
                pointBackgroundColor: color,
                pointBorderColor: COLORS.cardBg,
                pointBorderWidth: 2,
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: color,
                tension: 0.4,
                borderWidth: ds.primary ? 2.5 : 2,
                pointRadius: ds.primary ? 4 : 2,
                pointHoverRadius: ds.primary ? 7 : 5,
                fill: false,
                order: i
            };
            if (ds.dashed) {
                dataset.borderDash = [6, 4];
            }
            if (ds.fill && ds.primary) {
                const gradient = createGradient(ctx, ds.gradientTop || COLORS.primaryLight, 'rgba(0,0,0,0)', el.parentElement.offsetHeight || 300);
                dataset.backgroundColor = gradient;
                dataset.fill = true;
            }
            return dataset;
        });

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: config.labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: {
                    x: { ...axisDefaults.x },
                    y: {
                        ...axisDefaults.y,
                        beginAtZero: config.beginAtZero !== false,
                        max: config.maxY || undefined,
                        title: config.yTitle ? {
                            display: true,
                            text: config.yTitle,
                            color: COLORS.textMuted,
                            font: { family: FONT.family, size: 11, weight: '500' }
                        } : undefined,
                        ticks: {
                            ...axisDefaults.y.ticks,
                            callback: config.tickSuffix ? (v => v + config.tickSuffix) : axisDefaults.y.ticks.callback
                        }
                    }
                },
                plugins: {
                    legend: legendConfig('bottom'),
                    tooltip: tooltipConfig(config.unit || '')
                },
                animation: { duration: 900, easing: 'easeOutQuart' }
            }
        });
    }

    /**
     * Profesyonel Pareto Grafiği (Bar + Line combo)
     */
    function createParetoChart(canvasId, config) {
        const el = document.getElementById(canvasId);
        if (!el) return null;
        const ctx = el.getContext('2d');

        // Kümülatif yüzde hesapla
        const values = config.values;
        const toplam = values.reduce((a, b) => a + b, 0);
        let kumulatif = 0;
        const kumulatifYuzde = values.map(v => {
            kumulatif += v;
            return toplam > 0 ? Math.round((kumulatif / toplam) * 100) : 0;
        });

        // Bar renkleri: İlk çubuk en yoğun, sonrakiler açılır
        const barColors = values.map((_, i) => {
            const opacity = Math.max(0.4, 1 - (i * 0.15));
            return `rgba(91, 141, 239, ${opacity})`;
        });

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: config.labels,
                datasets: [
                    {
                        label: config.barLabel || 'Hata Adedi',
                        data: values,
                        backgroundColor: barColors,
                        borderRadius: 8,
                        borderSkipped: false,
                        barPercentage: 0.7,
                        categoryPercentage: 0.7,
                        yAxisID: 'y',
                        order: 2
                    },
                    {
                        label: 'Kümülatif %',
                        data: kumulatifYuzde,
                        type: 'line',
                        borderColor: COLORS.danger,
                        backgroundColor: 'transparent',
                        pointBackgroundColor: COLORS.danger,
                        pointBorderColor: COLORS.cardBg,
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: COLORS.danger,
                        tension: 0.35,
                        borderWidth: 2.5,
                        yAxisID: 'y1',
                        order: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: { ...axisDefaults.x },
                    y: {
                        ...axisDefaults.y,
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: config.yTitle || 'Hata Adedi',
                            color: COLORS.textMuted,
                            font: { family: FONT.family, size: 11, weight: '500' }
                        },
                        ticks: {
                            ...axisDefaults.y.ticks,
                            stepSize: config.stepSize || undefined
                        }
                    },
                    y1: {
                        position: 'right',
                        beginAtZero: true,
                        max: 100,
                        grid: { display: false, drawBorder: false },
                        border: { display: false },
                        title: {
                            display: true,
                            text: 'Kümülatif %',
                            color: COLORS.textMuted,
                            font: { family: FONT.family, size: 11, weight: '500' }
                        },
                        ticks: {
                            color: COLORS.textMuted,
                            font: { family: FONT.family, size: FONT.size, weight: '400' },
                            padding: 10,
                            callback: v => v + '%'
                        }
                    }
                },
                plugins: {
                    legend: legendConfig('bottom'),
                    tooltip: {
                        ...tooltipConfig(),
                        callbacks: {
                            label: function(ctx) {
                                if (ctx.dataset.yAxisID === 'y1') {
                                    return `  ${ctx.dataset.label}: ${ctx.parsed.y}%`;
                                }
                                return `  ${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString('tr-TR')} adet`;
                            }
                        }
                    }
                },
                animation: {
                    duration: 900,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    /**
     * Profesyonel Çubuk Grafik (Bar Chart)
     */
    function createBarChart(canvasId, config) {
        const el = document.getElementById(canvasId);
        if (!el) return null;
        const ctx = el.getContext('2d');

        const datasets = config.datasets.map((ds, i) => ({
            label: ds.label,
            data: ds.data,
            backgroundColor: ds.color || COLORS.series[i % COLORS.series.length],
            borderRadius: 6,
            borderSkipped: false,
            barPercentage: config.stacked ? 0.55 : 0.7,
            categoryPercentage: config.stacked ? 0.7 : 0.8,
            hoverBackgroundColor: ds.hoverColor || ds.color || COLORS.series[i % COLORS.series.length]
        }));

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: config.labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: {
                        ...axisDefaults.x,
                        stacked: config.stacked || false
                    },
                    y: {
                        ...axisDefaults.y,
                        stacked: config.stacked || false,
                        beginAtZero: true,
                        title: config.yTitle ? {
                            display: true,
                            text: config.yTitle,
                            color: COLORS.textMuted,
                            font: { family: FONT.family, size: 11, weight: '500' }
                        } : undefined,
                        ticks: {
                            ...axisDefaults.y.ticks,
                            stepSize: config.stepSize || undefined
                        }
                    }
                },
                plugins: {
                    legend: config.showLegend !== false ? legendConfig('bottom') : { display: false },
                    tooltip: tooltipConfig(config.unit || '')
                },
                animation: {
                    duration: 800,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    /**
     * Gruplu Çubuk Grafik — Farklı birimlere sahip verileri yan yana gösterir.
     * Her dataset kendi Y eksenini kullanabilir.
     * config.datasets: [{ label, data, color, unit, yAxisID }]
     */
    function createGroupedBarChart(canvasId, config) {
        const el = document.getElementById(canvasId);
        if (!el) return null;
        const ctx = el.getContext('2d');

        const datasets = config.datasets.map((ds, i) => ({
            label: ds.label,
            data: ds.data,
            backgroundColor: ds.color || COLORS.series[i % COLORS.series.length],
            borderRadius: 6,
            borderSkipped: false,
            barPercentage: 0.75,
            categoryPercentage: 0.8,
            yAxisID: ds.yAxisID || 'y'
        }));

        // Y eksenleri oluştur
        const scales = {
            x: { ...axisDefaults.x }
        };

        // Birincil Y ekseni (sol)
        scales.y = {
            ...axisDefaults.y,
            beginAtZero: true,
            position: 'left',
            title: config.yTitle ? {
                display: true,
                text: config.yTitle,
                color: COLORS.textMuted,
                font: { family: FONT.family, size: 11, weight: '500' }
            } : undefined
        };

        // İkincil Y ekseni (sağ) — varsa
        if (config.y1Title) {
            scales.y1 = {
                ...axisDefaults.y,
                beginAtZero: true,
                position: 'right',
                grid: { display: false, drawBorder: false },
                border: { display: false },
                title: {
                    display: true,
                    text: config.y1Title,
                    color: COLORS.textMuted,
                    font: { family: FONT.family, size: 11, weight: '500' }
                }
            };
        }

        return new Chart(ctx, {
            type: 'bar',
            data: { labels: config.labels, datasets: datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: scales,
                plugins: {
                    legend: legendConfig('bottom'),
                    tooltip: {
                        ...tooltipConfig(),
                        callbacks: {
                            label: function(ctx) {
                                const ds = config.datasets[ctx.datasetIndex];
                                const unit = ds.unit || '';
                                const val = ctx.parsed.y.toLocaleString('tr-TR');
                                return `  ${ctx.dataset.label}: ${val} ${unit}`;
                            }
                        }
                    }
                },
                animation: { duration: 800, easing: 'easeOutQuart' }
            }
        });
    }

    /**
     * Profesyonel Doughnut Grafik
     */
    function createDoughnutChart(canvasId, config) {
        const el = document.getElementById(canvasId);
        if (!el) return null;
        const ctx = el.getContext('2d');

        const colors = config.colors || COLORS.series.slice(0, config.values.length);

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: config.labels,
                datasets: [{
                    data: config.values,
                    backgroundColor: colors,
                    borderWidth: 3,
                    borderColor: COLORS.cardBg,
                    hoverBorderColor: '#2d3348',
                    hoverBorderWidth: 3,
                    hoverOffset: 8,
                    spacing: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '68%',
                layout: {
                    padding: 10
                },
                plugins: {
                    legend: {
                        ...legendConfig('bottom'),
                        labels: {
                            ...legendConfig('bottom').labels,
                            generateLabels: function(chart) {
                                const data = chart.data;
                                if (data.labels.length && data.datasets.length) {
                                    const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                    return data.labels.map((label, i) => {
                                        const value = data.datasets[0].data[i];
                                        const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                        return {
                                            text: `${label} (${percentage}%)`,
                                            fillStyle: data.datasets[0].backgroundColor[i],
                                            strokeStyle: 'transparent',
                                            lineWidth: 0,
                                            pointStyle: 'circle',
                                            hidden: false,
                                            index: i,
                                            fontColor: COLORS.text
                                        };
                                    });
                                }
                                return [];
                            }
                        }
                    },
                    tooltip: {
                        ...tooltipConfig(),
                        callbacks: {
                            label: function(ctx) {
                                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total > 0 ? Math.round((ctx.parsed / total) * 100) : 0;
                                const value = ctx.parsed.toLocaleString('tr-TR');
                                const unit = config.unit || '';
                                return `  ${ctx.label}: ${value}${unit} (${pct}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            },
            plugins: [{
                // Ortasına toplam yazan center plugin
                id: 'centerText',
                afterDraw: function(chart) {
                    if (!config.centerText) return;
                    const { ctx, chartArea: { width, height, top } } = chart;
                    ctx.save();
                    
                    const total = chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                    const centerX = width / 2 + chart.chartArea.left;
                    const centerY = height / 2 + top;
                    
                    // Üst yazı (Toplam label)
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = COLORS.textMuted;
                    ctx.font = `500 11px ${FONT.family}`;
                    ctx.fillText(config.centerText, centerX, centerY - 10);
                    
                    // Alt yazı (Toplam değer)
                    ctx.fillStyle = '#F1F5F9';
                    ctx.font = `700 18px 'Outfit', ${FONT.family}`;
                    const formattedTotal = config.centerFormat 
                        ? config.centerFormat(total) 
                        : total.toLocaleString('tr-TR');
                    ctx.fillText(formattedTotal, centerX, centerY + 12);
                    
                    ctx.restore();
                }
            }]
        });
    }

    // ── Return Public API ──
    return {
        COLORS,
        FONT,
        TR_AYLAR,
        formatMonthLabel,
        formatSnakeCaseLabel,
        createLineChart,
        createMultiLineChart,
        createParetoChart,
        createBarChart,
        createGroupedBarChart,
        createDoughnutChart,
        createGradient,
        tooltipConfig,
        legendConfig
    };
})();

// Global Chart.js defaults — dark theme override
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#64748B';
    Chart.defaults.borderColor = 'rgba(148, 163, 184, 0.08)';
    Chart.defaults.font.family = "'Inter', 'Segoe UI', system-ui, sans-serif";
    Chart.defaults.font.size = 11;
    Chart.defaults.plugins.legend.labels.color = '#CBD5E1';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.animation.duration = 800;
    Chart.defaults.animation.easing = 'easeOutQuart';
}

console.log('FDYS Chart.js profesyonel tema yüklendi.');
