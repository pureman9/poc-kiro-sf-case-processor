/**
 * dashboard.js — CEO Executive Dashboard
 * Reads from localStorage (same DB as the call center app)
 * Auto-refreshes every 30 seconds
 */

// ── Intent metadata ───────────────────────────────────────────────────────────
const INTENT_META = {
  'change-firstname': { label: 'เปลี่ยนแปลงชื่อ',              labelEn: 'Change First Name',   routing: 'OPS',        color: '#f59e0b' },
  'change-lastname':  { label: 'เปลี่ยนแปลงนามสกุล',           labelEn: 'Change Last Name',    routing: 'OPS',        color: '#ef4444' },
  'change-title':     { label: 'เปลี่ยนแปลงคำนำหน้า',          labelEn: 'Change Title',        routing: 'AUTO',       color: '#10b981' },
  'change-fullname':  { label: 'เปลี่ยนแปลงชื่อ-นามสกุล',     labelEn: 'Change Full Name',    routing: 'OPS',        color: '#f97316' },
  'change-id':        { label: 'เปลี่ยนแปลงเลขบัตรประชาชน',   labelEn: 'Change National ID',  routing: 'COMPLIANCE', color: '#8b5cf6' },
  'change-dob':       { label: 'เปลี่ยนแปลงวันเกิด',           labelEn: 'Change Date of Birth',routing: 'AUTO',       color: '#06b6d4' },
};

const ROUTING_COLORS = {
  AUTO:       '#10b981',
  OPS:        '#f59e0b',
  COMPLIANCE: '#8b5cf6',
};

const STATUS_COLORS = {
  COMPLETED:        '#10b981',
  PENDING_APPROVAL: '#f59e0b',
  APPROVED:         '#3b82f6',
  REJECTED:         '#ef4444',
};

// ── Chart instances ───────────────────────────────────────────────────────────
let chartIntent   = null;
let chartApproval = null;
let chartRouting  = null;
let chartDaily    = null;

// ── Refresh state ─────────────────────────────────────────────────────────────
let refreshTimer     = null;
let countdownTimer   = null;
let refreshInterval  = 30; // seconds
let countdown        = refreshInterval;
let prevKpiValues    = {};

// ── Helpers ───────────────────────────────────────────────────────────────────
function today() {
  return new Date().toISOString().slice(0, 10);
}

function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
}

function formatDateTime(iso) {
  return new Date(iso).toLocaleString('th-TH', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });
}

function pct(num, den) {
  if (!den) return '—';
  return Math.round((num / den) * 100) + '%';
}

function animateValue(el, newVal) {
  const old = prevKpiValues[el.id];
  if (old !== undefined && old !== newVal) {
    el.classList.add('updated');
    setTimeout(() => el.classList.remove('updated'), 1000);
  }
  prevKpiValues[el.id] = newVal;
  el.textContent = newVal;
}

// ── Data loading ──────────────────────────────────────────────────────────────
function loadData() {
  const auditLog    = JSON.parse(localStorage.getItem('sfcc_audit_log')    || '[]');
  const approvalQ   = JSON.parse(localStorage.getItem('sfcc_approval_queue') || '[]');
  const customers   = JSON.parse(localStorage.getItem('sfcc_customers')    || '{}');
  return { auditLog, approvalQ, customers };
}

// ── Main render ───────────────────────────────────────────────────────────────
function render() {
  const { auditLog, approvalQ } = loadData();
  const todayStr = today();

  // Filter today's entries
  const todayLog = auditLog.filter(e => e.timestamp && e.timestamp.startsWith(todayStr));

  // Unique cases today (by caseId)
  const uniqueCasesToday = new Set(todayLog.map(e => e.caseId)).size;

  // Status counts (all time for approval queue, today for audit)
  const completed       = todayLog.filter(e => e.status === 'COMPLETED').length;
  const pendingApproval = approvalQ.filter(r => r.status === 'PENDING').length;
  const approved        = auditLog.filter(e => e.status === 'APPROVED').length;
  const rejected        = auditLog.filter(e => e.status === 'REJECTED').length;
  const resolved        = approved + rejected;
  const approvalRate    = resolved > 0 ? Math.round((approved / resolved) * 100) : null;

  // ── KPIs ──────────────────────────────────────────────────────────────────
  animateValue(document.getElementById('kpi-total'),     uniqueCasesToday);
  animateValue(document.getElementById('kpi-completed'), completed);
  animateValue(document.getElementById('kpi-pending'),   pendingApproval);
  animateValue(document.getElementById('kpi-rejected'),  rejected);
  document.getElementById('kpi-approval-rate').textContent = approvalRate !== null ? approvalRate + '%' : '—';

  // Rate bar + numeric breakdown
  const rateFill = document.getElementById('kpi-rate-fill');
  const rateNums = document.getElementById('kpi-rate-nums');
  if (rateFill) {
    rateFill.style.width = (approvalRate ?? 0) + '%';
    rateFill.style.background = approvalRate === null ? '#555'
      : approvalRate >= 80 ? '#10b981'
      : approvalRate >= 50 ? '#f59e0b'
      : '#ef4444';
  }
  if (rateNums) {
    rateNums.textContent = resolved > 0
      ? `${approved} approved · ${rejected} rejected · ${resolved} resolved`
      : 'No resolved cases yet';
  }

  document.getElementById('kpi-completed-pct').textContent  = uniqueCasesToday ? pct(completed, uniqueCasesToday) + ' of today\'s cases' : 'No cases today';
  document.getElementById('kpi-pending-sub').textContent    = `${approvalQ.filter(r=>r.status==='PENDING' && r.approvalLevel==='OPS').length} Ops · ${approvalQ.filter(r=>r.status==='PENDING' && r.approvalLevel==='COMPLIANCE').length} Compliance`;
  document.getElementById('kpi-rejected-pct').textContent   = resolved ? pct(rejected, resolved) + ' of resolved' : 'No resolved yet';

  // ── Intent breakdown chart ─────────────────────────────────────────────────
  const intentCounts = {};
  Object.keys(INTENT_META).forEach(k => { intentCounts[k] = 0; });
  todayLog.forEach(e => {
    if (e.intentKey && intentCounts[e.intentKey] !== undefined) {
      intentCounts[e.intentKey]++;
    }
  });

  const intentLabels = Object.keys(INTENT_META).map(k => INTENT_META[k].labelEn);
  const intentData   = Object.keys(INTENT_META).map(k => intentCounts[k]);
  const intentColors = Object.keys(INTENT_META).map(k => INTENT_META[k].color);

  document.getElementById('intent-total-badge').textContent = `${todayLog.length} entries today`;

  if (!chartIntent) {
    chartIntent = new Chart(document.getElementById('chart-intent'), {
      type: 'bar',
      data: {
        labels: intentLabels,
        datasets: [{
          label: 'Cases Today',
          data: intentData,
          backgroundColor: intentColors.map(c => c + '99'),
          borderColor: intentColors,
          borderWidth: 2,
          borderRadius: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: '#8b8fa8', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#8b8fa8', stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true },
        },
      },
    });
  } else {
    chartIntent.data.datasets[0].data = intentData;
    chartIntent.update('none');
  }

  // ── Approval breakdown donut ───────────────────────────────────────────────
  const approvalData = [
    auditLog.filter(e => e.status === 'COMPLETED').length,
    auditLog.filter(e => e.status === 'PENDING_APPROVAL').length,
    approved,
    rejected,
  ];
  const approvalLabels = ['Completed', 'Pending', 'Approved', 'Rejected'];
  const approvalColors = [STATUS_COLORS.COMPLETED, STATUS_COLORS.PENDING_APPROVAL, STATUS_COLORS.APPROVED, STATUS_COLORS.REJECTED];

  if (!chartApproval) {
    chartApproval = new Chart(document.getElementById('chart-approval'), {
      type: 'doughnut',
      data: {
        labels: approvalLabels,
        datasets: [{ data: approvalData, backgroundColor: approvalColors, borderWidth: 0, hoverOffset: 6 }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '68%',
        plugins: { legend: { display: false } },
      },
    });
  } else {
    chartApproval.data.datasets[0].data = approvalData;
    chartApproval.update('none');
  }

  document.getElementById('donut-legend').innerHTML = approvalLabels.map((l, i) => `
    <div class="donut-legend-item">
      <div class="donut-legend-dot" style="background:${approvalColors[i]}"></div>
      <span>${l}: <strong style="color:#fff">${approvalData[i]}</strong></span>
    </div>`).join('');

  // ── Routing level donut ────────────────────────────────────────────────────
  const routingCounts = { AUTO: 0, OPS: 0, COMPLIANCE: 0 };
  auditLog.forEach(e => {
    if (e.approvalLevel && routingCounts[e.approvalLevel] !== undefined) routingCounts[e.approvalLevel]++;
  });
  const routingData   = Object.values(routingCounts);
  const routingLabels = ['Auto-Approve', 'Operations', 'Compliance'];
  const routingColors = Object.values(ROUTING_COLORS);

  if (!chartRouting) {
    chartRouting = new Chart(document.getElementById('chart-routing'), {
      type: 'doughnut',
      data: {
        labels: routingLabels,
        datasets: [{ data: routingData, backgroundColor: routingColors, borderWidth: 0, hoverOffset: 6 }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '68%',
        plugins: { legend: { display: false } },
      },
    });
  } else {
    chartRouting.data.datasets[0].data = routingData;
    chartRouting.update('none');
  }

  document.getElementById('routing-legend').innerHTML = routingLabels.map((l, i) => `
    <div class="donut-legend-item">
      <div class="donut-legend-dot" style="background:${routingColors[i]}"></div>
      <span>${l}: <strong style="color:#fff">${routingData[i]}</strong></span>
    </div>`).join('');

  // ── Daily trend (last 7 days) ──────────────────────────────────────────────
  const dailyLabels = [];
  const dailyCompleted = [];
  const dailyPending   = [];

  for (let i = 6; i >= 0; i--) {
    const d = daysAgo(i);
    const dayLog = auditLog.filter(e => e.timestamp && e.timestamp.startsWith(d));
    const label = i === 0 ? 'Today' : new Date(d + 'T00:00:00').toLocaleDateString('en', { weekday: 'short', month: 'short', day: 'numeric' });
    dailyLabels.push(label);
    dailyCompleted.push(dayLog.filter(e => e.status === 'COMPLETED' || e.status === 'APPROVED').length);
    dailyPending.push(dayLog.filter(e => e.status === 'PENDING_APPROVAL').length);
  }

  if (!chartDaily) {
    chartDaily = new Chart(document.getElementById('chart-daily'), {
      type: 'line',
      data: {
        labels: dailyLabels,
        datasets: [
          {
            label: 'Completed / Approved',
            data: dailyCompleted,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16,185,129,0.1)',
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#10b981',
            pointRadius: 4,
          },
          {
            label: 'Pending Approval',
            data: dailyPending,
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245,158,11,0.08)',
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#f59e0b',
            pointRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: '#8b8fa8', font: { size: 12 }, boxWidth: 12, padding: 16 },
          },
        },
        scales: {
          x: { ticks: { color: '#8b8fa8', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
          y: { ticks: { color: '#8b8fa8', stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.04)' }, beginAtZero: true },
        },
      },
    });
  } else {
    chartDaily.data.labels = dailyLabels;
    chartDaily.data.datasets[0].data = dailyCompleted;
    chartDaily.data.datasets[1].data = dailyPending;
    chartDaily.update('none');
  }

  // ── Activity feed ──────────────────────────────────────────────────────────
  const recent = [...auditLog].slice(0, 20);
  document.getElementById('activity-count').textContent = auditLog.length;
  document.getElementById('activity-feed').innerHTML = recent.length === 0
    ? '<div style="padding:20px;text-align:center;color:var(--text-muted)">No activity yet</div>'
    : recent.map(e => {
        const dotClass = {
          COMPLETED:        'activity-dot--completed',
          PENDING_APPROVAL: 'activity-dot--pending',
          APPROVED:         'activity-dot--approved',
          REJECTED:         'activity-dot--rejected',
        }[e.status] || 'activity-dot--pending';

        const statusLabel = e.status.replace('_', ' ');
        const intentMeta  = INTENT_META[e.intentKey] || { labelEn: e.intentLabelEn || e.intentKey };

        return `<div class="activity-item">
          <div class="activity-dot ${dotClass}"></div>
          <div class="activity-body">
            <div class="activity-title">${e.customerName || e.cid} — ${intentMeta.labelEn}</div>
            <div class="activity-meta">Case #${e.caseId} · ${e.fieldLabel}: <span style="color:#f87171">${e.beforeValue}</span> → <span style="color:#4ade80">${e.afterValue}</span></div>
          </div>
          <div class="activity-time">${formatTime(e.timestamp)}<br><span style="font-size:10px">${statusLabel}</span></div>
        </div>`;
      }).join('');

  // ── Intent performance table ───────────────────────────────────────────────
  const tbody = document.getElementById('intent-table-body');
  tbody.innerHTML = Object.entries(INTENT_META).map(([key, meta]) => {
    const entries    = auditLog.filter(e => e.intentKey === key);
    const total      = entries.length;
    const comp       = entries.filter(e => e.status === 'COMPLETED').length;
    const pend       = entries.filter(e => e.status === 'PENDING_APPROVAL').length;
    const appr       = entries.filter(e => e.status === 'APPROVED').length;
    const rej        = entries.filter(e => e.status === 'REJECTED').length;
    const resolved   = appr + rej;
    const rate       = resolved > 0 ? Math.round((appr / resolved) * 100) : null;
    const rateColor  = rate === null ? '#8b8fa8' : rate >= 80 ? '#10b981' : rate >= 50 ? '#f59e0b' : '#ef4444';

    // Trend: last 7 days count
    const trend = Array.from({length: 7}, (_, i) => {
      const d = daysAgo(6 - i);
      return entries.filter(e => e.timestamp && e.timestamp.startsWith(d)).length;
    });
    const maxTrend = Math.max(...trend, 1);
    const trendBars = trend.map(v => {
      const h = Math.max(2, Math.round((v / maxTrend) * 20));
      return `<span style="height:${h}px;background:${meta.color}88"></span>`;
    }).join('');

    const routingBadge = {
      AUTO:       '<span class="badge badge--auto">Auto</span>',
      OPS:        '<span class="badge badge--ops">Ops</span>',
      COMPLIANCE: '<span class="badge badge--compliance">Compliance</span>',
    }[meta.routing] || meta.routing;

    return `<tr>
      <td style="font-weight:600">${meta.label}</td>
      <td style="color:var(--text-muted)">${meta.labelEn}</td>
      <td>${routingBadge}</td>
      <td style="font-weight:700;color:#fff">${total}</td>
      <td style="color:#10b981">${comp}</td>
      <td style="color:#f59e0b">${pend}</td>
      <td style="color:#3b82f6">${appr}</td>
      <td style="color:#ef4444">${rej}</td>
      <td>
        <div class="rate-bar">
          <div class="rate-bar__track">
            <div class="rate-bar__fill" style="width:${rate ?? 0}%;background:${rateColor}"></div>
          </div>
          <div class="rate-bar__label" style="color:${rateColor}">${rate !== null ? rate + '%' : '—'}</div>
        </div>
      </td>
      <td><div class="trend-bar">${trendBars}</div></td>
    </tr>`;
  }).join('');

  // ── Timestamp ─────────────────────────────────────────────────────────────
  const now = new Date();
  document.getElementById('last-updated').textContent = now.toLocaleTimeString('th-TH', { hour12: false });
  document.getElementById('dash-date').textContent    = now.toLocaleDateString('en', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
}

// ── Auto-refresh ──────────────────────────────────────────────────────────────
function startRefresh() {
  countdown = refreshInterval;

  refreshTimer = setInterval(() => {
    render();
    countdown = refreshInterval;
  }, refreshInterval * 1000);

  countdownTimer = setInterval(() => {
    countdown--;
    const el = document.getElementById('footer-refresh-countdown');
    if (el) el.textContent = `Next refresh in ${countdown}s`;
    if (countdown <= 0) countdown = refreshInterval;
  }, 1000);
}

// ── Live dot pulse on storage change ─────────────────────────────────────────
window.addEventListener('storage', (e) => {
  if (e.key && e.key.startsWith('sfcc_')) {
    // Data changed in another tab — refresh immediately
    render();
    countdown = refreshInterval;
    // Flash live dot
    const dot = document.getElementById('live-dot');
    const lbl = document.getElementById('live-label');
    if (dot) { dot.style.background = '#60a5fa'; setTimeout(() => { dot.style.background = ''; }, 800); }
    if (lbl) { lbl.textContent = 'UPDATED'; setTimeout(() => { lbl.textContent = 'LIVE'; }, 1500); }
  }
});

// ── Init ──────────────────────────────────────────────────────────────────────
render();
startRefresh();
