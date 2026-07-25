// MindSense Visual Dashboard Chart.js Renderers — Production Quality

document.addEventListener('DOMContentLoaded', () => {

    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#94a3b8' : '#475569';
    const gridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';
    const borderColor = isDark ? '#0f172a' : '#ffffff';

    // ── 1. Emotion Frequency Doughnut Chart ────────────────────────────────
    const doughnutCtx = document.getElementById('emotionDoughnutChart');
    if (doughnutCtx && typeof statsData !== 'undefined' && statsData.emotionCounts) {
        const rawCounts = statsData.emotionCounts;
        // Filter out emotions with 0 count for a cleaner chart
        const labels = Object.keys(rawCounts).filter(k => rawCounts[k] > 0);
        const dataValues = labels.map(k => rawCounts[k]);

        const PALETTE = [
            '#10b981', '#6366f1', '#f59e0b', '#ec4899',
            '#ef4444', '#8b5cf6', '#a855f7', '#3b82f6',
            '#64748b', '#f97316', '#14b8a6'
        ];

        if (dataValues.length === 0) {
            // Show placeholder when no data yet
            labels.push('No Sessions Yet');
            dataValues.push(1);
        }

        new Chart(doughnutCtx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: dataValues,
                    backgroundColor: PALETTE.slice(0, labels.length),
                    borderWidth: 3,
                    borderColor: borderColor,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '68%',
                animation: { animateRotate: true, duration: 1000 },
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: textColor,
                            font: { family: 'Inter', size: 11 },
                            boxWidth: 12,
                            padding: 12,
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.label}: ${ctx.raw} session${ctx.raw !== 1 ? 's' : ''}`
                        }
                    }
                }
            }
        });
    }

    // ── 2. Weekly Wellness & Stress Trend — Line Chart ──────────────────────
    const lineCtx = document.getElementById('weeklyTrendLineChart');
    if (lineCtx && typeof statsData !== 'undefined') {
        const labels = statsData.trendLabels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const wellnessData = statsData.trendWellness || [30, 35, 40, 45, 50, 55, statsData.overall || 60];
        const stressData = statsData.trendStress || [60, 55, 50, 45, 40, 35, statsData.stress || 30];

        new Chart(lineCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Wellness Score',
                        data: wellnessData,
                        borderColor: '#14b8a6',
                        backgroundColor: 'rgba(20, 184, 166, 0.08)',
                        borderWidth: 2.5,
                        pointBackgroundColor: '#14b8a6',
                        pointRadius: 4,
                        pointHoverRadius: 7,
                        tension: 0.45,
                        fill: true
                    },
                    {
                        label: 'Stress Index',
                        data: stressData,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.08)',
                        borderWidth: 2.5,
                        pointBackgroundColor: '#f59e0b',
                        pointRadius: 4,
                        pointHoverRadius: 7,
                        tension: 0.45,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                animation: { duration: 800, easing: 'easeInOutQuart' },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: textColor, font: { family: 'Inter', size: 11 } }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        grid: { color: gridColor },
                        ticks: {
                            color: textColor,
                            font: { family: 'Inter', size: 11 },
                            callback: (val) => val + '%'
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: textColor,
                            font: { family: 'Inter', size: 11 },
                            boxWidth: 12,
                            padding: 16
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.dataset.label}: ${ctx.raw}/100`
                        }
                    }
                }
            }
        });
    }

    // ── 3. Animate Stats Cards on Load ─────────────────────────────────────
    animateStatNumbers();
});

function animateStatNumbers() {
    document.querySelectorAll('[data-count-to]').forEach(el => {
        const target = parseInt(el.getAttribute('data-count-to'), 10);
        if (isNaN(target)) return;
        let current = 0;
        const step = Math.ceil(target / 40);
        const interval = setInterval(() => {
            current = Math.min(current + step, target);
            el.textContent = current;
            if (current >= target) clearInterval(interval);
        }, 25);
    });
}
