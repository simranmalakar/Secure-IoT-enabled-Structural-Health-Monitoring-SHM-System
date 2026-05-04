/**
 * SHM Dashboard — Alerts Panel
 */

function updateAlerts(alerts) {
    const list = document.getElementById('alerts-list');
    const badge = document.getElementById('alerts-badge');
    if (!list) return;

    if (badge) badge.textContent = alerts.length;

    if (!alerts.length) {
        list.innerHTML = `
            <div class="empty-state">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                <p>No active incidents.</p>
                <p style="font-size: 0.8rem; margin-top: 8px;">Start the sensor simulator to see real-time data and potential alerts.</p>
            </div>
        `;
        return;
    }

    list.innerHTML = alerts.map(alert => {
        const time = new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const severityClass = (alert.severity || 'LOW').toLowerCase();
        
        // Detailed engineering explanations
        let humanMessage = alert.message;
        let explanation = "";
        
        if (alert.alert_type === 'HIGH_VIBRATION') {
            humanMessage = `Mechanical Resonance Alert`;
            explanation = `Vibration level on ${alert.sensor_id} exceeds structural safety limit. Potential fatigue risk.`;
        } else if (alert.alert_type === 'HIGH_STRAIN') {
            humanMessage = `Elastic Deformation Limit`;
            explanation = `Strain gauge on ${alert.sensor_id} reporting critical load. Inspect for structural yielding.`;
        } else if (alert.alert_type === 'SPOOFING_DETECTED') {
            humanMessage = `Data Integrity Violation`;
            explanation = `MAC mismatch detected on ${alert.sensor_id}. Potential sensor spoofing attack blocked.`;
        } else if (alert.alert_type === 'DOS_ATTACK') {
            humanMessage = `Network Availability Hazard`;
            explanation = `Abnormal traffic volume detected. Mitigating potential DoS attack on MQTT broker.`;
        }
        
        const comparison = alert.value && alert.threshold ? 
            `<div class="alert-comparison">Observed: <span style="color:var(--text-primary); font-weight:600;">${alert.value.toFixed(2)}</span> | Threshold: <span style="color:var(--red); font-weight:600;">${alert.threshold.toFixed(2)}</span></div>` : '';
        
        return `
            <div class="alert-item ${severityClass}">
                <span class="alert-dot ${severityClass}"></span>
                <div class="alert-content">
                    <div class="alert-type">${humanMessage}</div>
                    <div class="alert-msg">${explanation || alert.details || alert.message}</div>
                    ${comparison}
                </div>
                <span class="alert-time">${time}</span>
            </div>
        `;
    }).join('');
}
