/**
 * SHM Dashboard — Charts Panel
 */

let charts = {};

function updateCharts(readings, logs) {
    if (!readings || readings.length === 0) {
        // Clear all existing charts if no readings
        Object.keys(charts).forEach(id => {
            charts[id].data.labels = [];
            charts[id].data.datasets[0].data = [];
            charts[id].update();
        });
        return;
    }

    // Apply moving average for smoother visualization
    const windowSize = 5;
    
    // Vibration, Tilt, Strain Charts (Light smoothing)
    updateChart('vibration-chart', readings, 'vibration', '#6366f1', windowSize, 2.5);
    updateChart('tilt-chart', readings, 'tilt', '#06b6d4', windowSize, 4.0);
    updateChart('strain-chart', readings, 'strain', '#f59e0b', windowSize, 200);

    // Anomaly Score Chart (Heavy smoothing for trend line)
    updateChart('anomaly-chart', readings, 'anomaly_score', '#ef4444', 10, 70);

    // Timeline Chart (Keeping raw bars for events)
    updateTimelineChart(readings, logs);
}

function updateTimelineChart(readings, logs) {
    const ctx = document.getElementById('timeline-chart');
    if (!ctx) return;

    // Simple visualization of recent activity
    const labels = readings.slice(0, 15).map(r => new Date(r.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})).reverse();
    const anomalies = readings.slice(0, 15).map(r => r.anomaly_score).reverse();

    if (charts['timeline-chart']) {
        charts['timeline-chart'].data.labels = labels;
        charts['timeline-chart'].data.datasets[0].data = anomalies;
        charts['timeline-chart'].update('none');
    } else {
        charts['timeline-chart'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Anomaly Score',
                    data: anomalies,
                    backgroundColor: 'rgba(239, 68, 68, 0.5)',
                    borderColor: '#ef4444',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { display: true, grid: { display: false }, ticks: { color: '#64748b', font: { size: 10 } } },
                    y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } }
                }
            }
        });
    }
}

function movingAverage(data, window) {
    let result = [];
    for (let i = 0; i < data.length; i++) {
        let start = Math.max(0, i - window + 1);
        let subset = data.slice(start, i + 1);
        let sum = subset.reduce((a, b) => a + b, 0);
        result.push(sum / subset.length);
    }
    return result;
}

function updateChart(id, readings, key, color, smoothWindow = 0, threshold = null) {
    const ctx = document.getElementById(id);
    if (!ctx) return;

    let labels = readings.map(d => new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })).reverse();
    let values = readings.map(d => d[key]).reverse();
    let anomalies = readings.map(d => d.anomaly_score).reverse();

    if (smoothWindow > 1) {
        values = movingAverage(values, smoothWindow);
    }

    // Dynamic point colors based on anomaly score
    const pointColors = anomalies.map(score => score > 70 ? '#ef4444' : color);
    const pointRadii = anomalies.map(score => score > 70 ? 4 : 0);
    const pointHoverRadii = anomalies.map(score => score > 70 ? 6 : 4);

    // Detect if any recent reading has a massive anomaly (attack simulation)
    const isAttackActive = anomalies.slice(-5).some(score => score > 80);

    if (charts[id]) {
        charts[id].options.threshold = threshold;
        charts[id].options.isAttackActive = isAttackActive;
        charts[id].data.labels = labels;
        charts[id].data.datasets[0].data = values;
        charts[id].data.datasets[0].pointBackgroundColor = pointColors;
        charts[id].data.datasets[0].pointBorderColor = pointColors;
        charts[id].data.datasets[0].pointRadius = pointRadii;
        charts[id].update('none');
    } else {
        charts[id] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: key.replace('_', ' ').toUpperCase(),
                    data: values,
                    borderColor: color,
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: pointRadii,
                    pointBackgroundColor: pointColors,
                    pointBorderColor: pointColors,
                    fill: true,
                    backgroundColor: color + '15'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                threshold: threshold,
                isAttackActive: isAttackActive,
                plugins: { 
                    legend: { display: false },
                    tooltip: { enabled: true }
                },
                scales: {
                    x: { display: false },
                    y: { 
                        beginAtZero: true,
                        grid: { color: 'rgba(255,255,255,0.05)' }, 
                        ticks: { color: '#64748b', font: { size: 10 } } 
                    }
                },
                animation: { 
                    duration: 800,
                    easing: 'easeOutQuart'
                }
            },
            plugins: [{
                id: 'attackDetection',
                afterDraw: chart => {
                    const { ctx, chartArea: { top, right } } = chart;
                    const thresh = chart.options.threshold;
                    const isAttack = chart.options.isAttackActive;

                    // Draw Threshold Line
                    if (thresh) {
                        const y = chart.scales.y.getPixelForValue(thresh);
                        ctx.save();
                        ctx.beginPath();
                        ctx.lineWidth = 1;
                        ctx.setLineDash([5, 5]);
                        ctx.strokeStyle = 'rgba(239, 68, 68, 0.4)';
                        ctx.moveTo(chart.chartArea.left, y);
                        ctx.lineTo(chart.chartArea.right, y);
                        ctx.stroke();
                        ctx.restore();
                    }

                    // Draw Attack Warning Label
                    if (isAttack) {
                        ctx.save();
                        ctx.font = 'bold 10px Inter';
                        ctx.fillStyle = '#ef4444';
                        ctx.textAlign = 'right';
                        ctx.fillText('⚠️ ATTACK DETECTED', right - 10, top + 20);
                        
                        // Add a subtle red border glow to the chart area
                        ctx.strokeStyle = 'rgba(239, 68, 68, 0.3)';
                        ctx.lineWidth = 2;
                        ctx.strokeRect(chart.chartArea.left, chart.chartArea.top, chart.chartArea.width, chart.chartArea.height);
                        ctx.restore();
                    }
                }
            }]
        });
    }
}


