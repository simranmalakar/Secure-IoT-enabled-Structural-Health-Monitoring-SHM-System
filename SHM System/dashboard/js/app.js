/**
 * SHM Dashboard — Main Application Logic
 */

const API_BASE = (window.location.origin && window.location.origin.startsWith('http')) 
    ? window.location.origin 
    : 'http://localhost:8000';
const POLL_INTERVAL = 3000;

let authToken = null;
let pollTimer = null;

// Filter state
const filters = {
    sensor: 'ALL',
    severity: 'ALL',
    time: '24H'
};

// ── API Helper ──
async function api(endpoint, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (authToken) headers['Authorization'] = `Bearer ${authToken}`;

    try {
        const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
        if (res.status === 401) { logout(); throw new Error('Session expired'); }
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        return await res.json();
    } catch (e) {
        if (e.message === 'Failed to fetch') setConnectionStatus(false);
        throw e;
    }
}

// ── Auth ──
function initLogin() {
    const form = document.getElementById('login-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        const errorEl = document.getElementById('login-error');
        const btnText = form.querySelector('.btn-text');
        const btnLoader = form.querySelector('.btn-loader');

        if (errorEl) errorEl.style.display = 'none';
        if (btnText) btnText.style.display = 'none';
        if (btnLoader) btnLoader.style.display = 'inline-block';

        try {
            const data = await api('/login', {
                method: 'POST',
                body: JSON.stringify({ username, password }),
            });
            authToken = data.access_token;
            sessionStorage.setItem('shm_token', authToken);
            sessionStorage.setItem('shm_user', data.username);
            sessionStorage.setItem('shm_role', data.role);
            showDashboard(data.username);
        } catch (err) {
            if (errorEl) {
                errorEl.textContent = err.message || 'Login failed';
                errorEl.style.display = 'block';
            }
        } finally {
            if (btnText) btnText.style.display = 'inline';
            if (btnLoader) btnLoader.style.display = 'none';
        }
    });
}

function showDashboard(username) {
    const loginScreen = document.getElementById('login-screen');
    const dashboard = document.getElementById('dashboard');
    
    if (loginScreen) loginScreen.style.display = 'none';
    if (dashboard) dashboard.style.display = 'block';
    
    document.querySelectorAll('.user-name').forEach(el => el.textContent = username);
    document.querySelectorAll('.user-avatar').forEach(el => el.textContent = username.charAt(0).toUpperCase());
    
    startPolling();
    
    // Sync system status
    if (typeof checkSystemStatus === 'function') checkSystemStatus();
}

function logout() {
    authToken = null;
    sessionStorage.removeItem('shm_token');
    sessionStorage.removeItem('shm_user');
    sessionStorage.removeItem('shm_role');
    stopPolling();
    
    const dashboardEl = document.getElementById('dashboard');
    const loginEl = document.getElementById('login-screen');
    
    if (dashboardEl) dashboardEl.style.display = 'none';
    if (loginEl) {
        loginEl.style.display = 'flex';
    } else {
        window.location.href = 'index.html';
    }
}

// ── Connection Status ──
function setConnectionStatus(online) {
    const dot = document.querySelector('.status-dot');
    const text = document.querySelector('.status-text');
    if (!dot || !text) return;

    if (online) {
        dot.style.background = '#22c55e';
        dot.style.boxShadow = '0 0 8px rgba(34, 197, 94, 0.4)';
        text.textContent = 'Connected';
    } else {
        dot.style.background = '#ef4444';
        dot.style.boxShadow = '0 0 8px rgba(239, 68, 68, 0.4)';
        text.textContent = 'Disconnected';
    }
}

// ── Polling ──
async function pollData() {
    try {
        const [health, sensorRes, alertsRes, logsRes] = await Promise.all([
            api('/health'),
            api('/sensor-data?limit=200'),
            api('/alerts?limit=100'),
            api('/logs?limit=100'),
        ]);

        setConnectionStatus(true);
        
        // Update UI
        if (typeof updateStats === 'function') updateStats(health, sensorRes.readings, alertsRes.alerts, logsRes.logs);
        if (typeof updateCharts === 'function') updateCharts(sensorRes.readings, logsRes.logs);
        if (typeof updateAlerts === 'function') updateAlerts(alertsRes.alerts);
        if (typeof updateSecurityLogs === 'function') updateSecurityLogs(logsRes.logs);
        
    } catch (e) {
        console.error('Poll error:', e.message);
    }
}

function updateStats(health, readings, alerts, logs) {
    animateValue('stat-sensors-value', health.active_sensors || 0);
    
    if (!readings || readings.length === 0) {
        animateValue('stat-risk-value', 0);
        animateValue('stat-alerts-value', 0);
        updateRiskBadge(0);
        updateSystemBanner(0, 0, [], []);
        updateSecurityOverview([]);
        updateWhyStatus(0, [], [], []);
        return;
    }
    
    // 1. Calculate Risk Score Dynamically
    const now = Date.now();
    // Use a very large window or handle UTC offset for reliable detection
    const windowMs = 60 * 60000; // 1 hour window to account for timezone drift
    
    const recentAlerts = alerts.filter(a => {
        const diff = Math.abs(now - new Date(a.timestamp + 'Z').getTime());
        return diff < windowMs;
    });
    const recentLogs = logs.filter(l => {
        const diff = Math.abs(now - new Date(l.timestamp + 'Z').getTime());
        return diff < windowMs;
    });
    
    // Corrected event types to match IDS logic
    const criticalAlerts = recentAlerts.filter(a => a.severity === 'CRITICAL');
    const highAlerts = recentAlerts.filter(a => a.severity === 'HIGH' || a.severity === 'MEDIUM');
    const securityEvents = recentLogs.filter(l => 
        ['SPOOFED_PACKET', 'DOS_ATTACK', 'REPLAY_ATTACK', 'UNAUTHORIZED_ACCESS'].includes(l.event_type)
    );


    // Risk components (Increased weights for immediate impact)
    const alertScore = (criticalAlerts.length * 30) + (highAlerts.length * 10);
    const securityScore = (securityEvents.length * 40);
    const anomalyScore = recentAlerts.length * 5;

    let totalRisk = Math.min(100, alertScore + securityScore + anomalyScore);
    
    // If an attack is ongoing, ensure risk is high
    if (securityEvents.length > 0) totalRisk = Math.max(totalRisk, 85);
    else if (criticalAlerts.length > 0) totalRisk = Math.max(totalRisk, 70);

    animateValue('stat-risk-value', totalRisk);
    updateRiskBadge(totalRisk);

    // 2. Update Active Incidents (Critical Security Events + Critical Alerts)
    const activeIncidentsCount = securityEvents.length + criticalAlerts.length;
    animateValue('stat-alerts-value', activeIncidentsCount);

    // 3. Update System Status & Banner
    updateSystemBanner(activeIncidentsCount, totalRisk, criticalAlerts, securityEvents);

    // 4. Security Overview Update
    updateSecurityOverview(logs);

    // 5. Why Status Panel
    updateWhyStatus(totalRisk, criticalAlerts, recentAlerts.filter(a => a.severity === 'HIGH'), securityEvents);
}

function updateRiskBadge(score) {
    const badge = document.getElementById('risk-level-badge');
    const fill = document.getElementById('risk-progress-fill');
    if (!badge || !fill) return;
    
    badge.className = 'risk-level';
    fill.style.width = `${score}%`;

    if (score >= 75) {
        badge.textContent = 'Critical';
        badge.classList.add('risk-high');
        fill.style.background = 'var(--red)';
    } else if (score >= 40) {
        badge.textContent = 'Elevated';
        badge.classList.add('risk-med');
        fill.style.background = 'var(--amber)';
    } else {
        badge.textContent = 'Low';
        badge.classList.add('risk-low');
        fill.style.background = 'var(--green)';
    }
}

function updateSystemBanner(incidents, score, criticalAlerts, securityEvents) {
    const banner = document.getElementById('system-status-banner');
    const title = document.getElementById('banner-title');
    const desc = document.getElementById('banner-desc');
    if (!banner || !title || !desc) return;

    if (score >= 75 || criticalAlerts.length > 0 || securityEvents.length > 0) {
        banner.className = 'status-banner critical';
        title.textContent = 'System Status: CRITICAL';
        
        let reason = "Active security threats or structural violations detected.";
        if (securityEvents.length > 0) reason = `Ongoing ${securityEvents[0].event_type.replace('_', ' ')} detected!`;
        else if (criticalAlerts.length > 0) reason = `Critical structural anomaly on ${criticalAlerts[0].sensor_id}.`;
        
        desc.textContent = reason + " Immediate intervention required.";
    } else if (score >= 40 || incidents > 0) {
        banner.className = 'status-banner warning';
        title.textContent = 'System Status: WARNING';
        desc.textContent = 'Elevated risk levels. Monitoring anomalous patterns in vibration and strain.';
    } else {
        banner.className = 'status-banner';
        title.textContent = 'System Status: NORMAL';
        desc.textContent = 'All structural parameters are within safe operational limits. No security threats detected.';
    }
}

function updateSecurityOverview(logs) {
    const spoofCount = logs.filter(l => l.event_type === 'SPOOFING_ATTACK').length;
    const dosCount = logs.filter(l => l.event_type === 'DOS_ATTACK').length;
    const totalAttacks = spoofCount + dosCount;
    
    const lastAttackLog = logs.find(l => ['SPOOFING_ATTACK', 'DOS_ATTACK'].includes(l.event_type));
    const lastAttackTime = lastAttackLog ? new Date(lastAttackLog.timestamp).toLocaleTimeString() : 'Never';

    const els = {
        'sec-total-attacks': totalAttacks,
        'sec-spoof-attempts': spoofCount,
        'sec-dos-events': dosCount,
        'sec-last-attack': lastAttackTime
    };

    for (const [id, val] of Object.entries(els)) {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    }
}

function updateWhyStatus(risk, criticals, highs, security) {
    const list = document.getElementById('why-status-list');
    if (!list) return;

    let items = [];

    // 1. Critical & Security Threats (Highest Priority)
    if (security.length > 0) {
        security.forEach(s => {
            items.push({
                title: 'Cyber-Security Threat',
                reason: `${s.event_type.replace(/_/g, ' ')} detected from <span class="reason-detail">${s.source || 'Unknown'}</span>. Signature mismatch triggered IDS alert.`,
                icon: '🛡️',
                color: '#ef4444'
            });
        });
    }

    if (criticals.length > 0) {
        criticals.forEach(a => {
            items.push({
                title: 'Critical Structural Breach',
                reason: `Sensor <span class="reason-detail">${a.sensor_id}</span> reports ${a.alert_type.replace(/_/g, ' ')} at ${a.value.toFixed(2)}. Exceeds safety threshold.`,
                icon: '⚠️',
                color: '#ef4444'
            });
        });
    }

    // 2. High Warnings
    if (highs.length > 0 && items.length < 5) {
        highs.slice(0, 2).forEach(a => {
            items.push({
                title: 'Infrastructure Warning',
                reason: `Anomalous pattern detected on ${a.sensor_id}. Drift analysis shows a deviation of <span class="reason-detail">${a.value.toFixed(2)}</span> from baseline.`,
                icon: '🔸',
                color: '#f97316'
            });
        });
    }

    // 3. Normal State Diagnostics (AI Heartbeat)
    if (items.length === 0) {
        items.push({
            title: 'Encryption Verified',
            reason: 'All incoming IoT packets are cryptographically signed using HMAC-SHA256. No integrity failures.',
            icon: '🔒',
            color: '#10b981'
        });
        items.push({
            title: 'Structural Stability',
            reason: 'Bridge vibration and strain cycles are within the 3-sigma statistical baseline. No drift detected.',
            icon: '🏗️',
            color: '#10b981'
        });
        items.push({
            title: 'IDS Active',
            reason: 'Intrusion Detection System is monitoring for DoS bursts and spoofing patterns. Zero threats detected.',
            icon: '🕵️',
            color: '#10b981'
        });
    }

    list.innerHTML = items.map(item => `
        <div class="why-status-item" style="border-left: 2px solid ${item.color || 'var(--border)'};">
            <div class="why-status-icon" style="background: ${item.color}15; color: ${item.color};">${item.icon}</div>
            <div class="why-status-content">
                <div class="why-status-title" style="color: ${item.color};">${item.title}</div>
                <div class="why-status-reason">${item.reason}</div>
            </div>
        </div>
    `).join('');
}

function animateValue(id, newVal) {
    const el = document.getElementById(id);
    if (!el) return;
    const currentText = el.textContent.replace(/,/g, '');
    const current = parseInt(currentText) || 0;
    if (current === newVal) return;
    
    // Pulse effect on change
    el.style.transition = 'none';
    el.style.color = '#fff';
    el.style.textShadow = '0 0 10px var(--accent)';
    
    el.textContent = newVal.toLocaleString();
    
    setTimeout(() => {
        el.style.transition = 'color 0.5s';
        el.style.color = '';
        el.style.textShadow = '';
    }, 500);
}

// ── RCA & Mitigation ──
function showRCA(type, asset, value, threshold) {
    const modal = document.getElementById('rca-modal');
    if (!modal) return;

    const iconEl = document.getElementById('rca-icon');
    const typeEl = document.getElementById('rca-type');
    const assetEl = document.getElementById('rca-asset');
    const probEl = document.getElementById('rca-prob');
    const analysisEl = document.getElementById('rca-analysis');
    const mitigateBtn = document.getElementById('rca-mitigate-btn');

    typeEl.textContent = type.replace(/_/g, ' ');
    assetEl.textContent = asset || 'System Wide';
    
    let analysis = "";
    let prob = "0%";
    let icon = "🛡️";

    if (type.includes('VIBRATION')) {
        analysis = "Mechanical resonance detected. Vibration amplitude is exceeding safe operating envelope. Recommend visual inspection of structural joints and dampeners.";
        prob = "65%";
        icon = "🏗️";
    } else if (type.includes('SPOOF')) {
        analysis = "Cryptographic integrity failure. The incoming packet signature does not match the registered sensor certificate. Source IP has been flagged for investigation.";
        prob = "85%";
        icon = "🔒";
    } else if (type.includes('DOS')) {
        analysis = "Ingress traffic rate exceeds throttle threshold. MQTT broker is experiencing queue saturation. Mitigation involves enabling adaptive rate-limiting on the gateway.";
        prob = "92%";
        icon = "🌩️";
    } else {
        analysis = "Anomalous pattern detected by ML engine. Deviation from historical baseline exceeds 3-sigma. Monitor for trend progression.";
        prob = "30%";
        icon = "🔍";
    }

    iconEl.textContent = icon;
    probEl.textContent = prob;
    analysisEl.innerHTML = analysis;

    mitigateBtn.onclick = () => mitigateIncident(type, asset);
    modal.style.display = 'flex';
}

function closeRCA() {
    const modal = document.getElementById('rca-modal');
    if (modal) modal.style.display = 'none';
}

async function mitigateIncident(type, asset) {
    const btn = document.getElementById('rca-mitigate-btn');
    btn.textContent = "Deploying...";
    btn.disabled = true;

    // Simulate mitigation delay
    await new Promise(r => setTimeout(r, 1500));

    showFeedback(`Countermeasure deployed for ${type}. Traffic from ${asset || 'source'} throttled.`, 'success');
    
    // In a real system, we'd call an API to block/reset
    // await api('/mitigate', { method: 'POST', body: JSON.stringify({ type, asset }) });

    closeRCA();
    btn.textContent = "Deploy Countermeasure";
    btn.disabled = false;
}

async function downloadLogs(type) {
    try {
        const logs = await api('/logs?limit=1000');
        const data = type === 'security' ? logs.logs : logs;
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `shm_${type}_audit_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showFeedback("Log export successful.", "success");
    } catch (e) {
        showFeedback("Failed to export logs.", "error");
    }
}

function startPolling() {
    pollData();
    pollTimer = setInterval(pollData, POLL_INTERVAL);
}

function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}


// ── Simulation & System Control ──
function showFeedback(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>';
    if (['spoof', 'dos', 'structural'].includes(type)) {
        icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';
    }

    toast.innerHTML = `
        ${icon}
        <div style="flex:1;">
            <div style="font-weight:700; font-size:0.85rem; text-transform:uppercase;">${type} Simulation</div>
            <div style="font-size:0.8rem; opacity:0.9;">${message}</div>
        </div>
    `;

    if (container) {
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(20px)';
            setTimeout(() => toast.remove(), 500);
        }, 4000);
    }
}

function playSirenSound() {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        oscillator.type = 'sawtooth';
        oscillator.frequency.setValueAtTime(440, audioCtx.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.5);
        oscillator.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 1.0);
        oscillator.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 1.5);
        oscillator.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 2.0);
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gainNode.gain.linearRampToValueAtTime(0, audioCtx.currentTime + 2.0);
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 2.0);
        setTimeout(() => audioCtx.close(), 3000);
    } catch (e) { console.error("Audio failed", e); }
}

function triggerEmergencyUI() {
    const bar = document.getElementById('emergency-alert-bar');
    const overlay = document.getElementById('red-alert-overlay');
    if (bar) bar.style.display = 'block';
    if (overlay) overlay.style.display = 'block';
    playSirenSound();
    setTimeout(() => {
        if (bar) bar.style.display = 'none';
        if (overlay) overlay.style.display = 'none';
    }, 5000);
}

async function toggleSystem(action) {
    try {
        const res = await api(`/simulation/${action}`, { method: 'POST' });
        showFeedback(res.message, action === 'start' ? 'success' : 'info');
        updateSystemUI(action === 'start');
    } catch (e) {
        showFeedback(`Failed to ${action} system: ${e.message}`, 'error');
    }
}

function updateSystemUI(active) {
    const startBtn = document.getElementById('btn-start-system');
    const stopBtn = document.getElementById('btn-stop-system');
    const statusText = document.getElementById('system-status-indicator');
    const attackBtns = document.querySelectorAll('.attack-btn');

    if (active) {
        if (startBtn) startBtn.style.display = 'none';
        if (stopBtn) stopBtn.style.display = 'block';
        if (statusText) statusText.innerHTML = 'Status: <span style="color: #10b981; font-weight: 700;">SYSTEM RUNNING</span>';
        attackBtns.forEach(btn => btn.disabled = false);
    } else {
        if (startBtn) startBtn.style.display = 'block';
        if (stopBtn) stopBtn.style.display = 'none';
        if (statusText) statusText.innerHTML = 'Status: <span style="color: #ef4444; font-weight: 700;">SYSTEM OFFLINE</span>';
        attackBtns.forEach(btn => btn.disabled = true);
    }
}

async function checkSystemStatus() {
    try {
        const res = await api('/simulation/status');
        updateSystemUI(res.active);
    } catch (e) {}
}

async function simulateAttack(type) {
    try {
        const res = await api('/simulate/' + type, { method: 'POST' });
        if (res.status === 'error') { showFeedback(res.message, 'error'); return; }
        showFeedback(`${type.toUpperCase()} attack triggered. Monitoring response...`, type);
        triggerEmergencyUI();
    } catch (e) { showFeedback(`Failed: ${e.message}`, 'error'); }
}

// Attach to window for onclick handlers
window.toggleSystem = toggleSystem;
window.simulateAttack = simulateAttack;

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
    initLogin();
    
    // Logout
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) logoutBtn.addEventListener('click', logout);

    // Theme Toggle
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
        });
    }

    // Session Restore
    const savedToken = sessionStorage.getItem('shm_token');
    const savedUser = sessionStorage.getItem('shm_user');
    
    if (savedToken && savedUser) {
        authToken = savedToken;
        if (document.getElementById('dashboard') && document.getElementById('login-screen')) {
            showDashboard(savedUser);
        } else {
            document.querySelectorAll('.user-name').forEach(el => el.textContent = savedUser);
            document.querySelectorAll('.user-avatar').forEach(el => el.textContent = savedUser.charAt(0).toUpperCase());
            startPolling();
        }
        checkSystemStatus();
    }
});
