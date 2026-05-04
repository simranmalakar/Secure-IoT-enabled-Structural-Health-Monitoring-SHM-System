/**
 * SHM Dashboard — Security Logs Panel
 */

function updateSecurityLogs(logs) {
    const list = document.getElementById('security-list');
    const badge = document.getElementById('security-badge');
    if (!list) return;

    if (badge) badge.textContent = logs.length;

    if (!logs.length) {
        list.innerHTML = '<div class="empty-state">No security events</div>';
        return;
    }

    list.innerHTML = logs.map(log => {
        const severityColor = getSeverityColor(log.severity);
        const time = new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        
        return `
            <div class="security-item" style="border-left: 3px solid ${severityColor}" onclick="showRCA('${log.event_type}', '${log.source}', 0, 0)">
                <div class="sec-content">
                    <div class="sec-type" style="color: ${severityColor}">${log.event_type.replace(/_/g, ' ')} <span style="opacity:0.5;font-weight:400;color: #a1a1aa;">— ${log.source || 'System'}</span></div>
                    <div class="sec-details">${log.details}</div>
                </div>
                <span class="sec-time">${time}</span>
            </div>
        `;
    }).join('');
}

function getSeverityColor(severity) {
    switch ((severity || '').toUpperCase()) {
        case 'CRITICAL': return '#ef4444';
        case 'HIGH': return '#f97316';
        case 'MEDIUM': return '#eab308';
        case 'LOW': return '#3b82f6';
        default: return '#9ca3af';
    }
}
