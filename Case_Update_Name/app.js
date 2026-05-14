/**
 * app.js — SF Case Intent Processor: Call Center UI
 * Approval routing: auto-approve / ops-team / compliance-team
 */

// ── Approval levels ───────────────────────────────────────────────────────────
const APPROVAL = {
  AUTO: {
    key:     'AUTO',
    label:   'Auto-Approve',
    labelTh: 'อนุมัติอัตโนมัติ',
    team:    null,
    badge:   'sf-badge--valid',
    icon:    '✅',
    desc:    'This change is processed immediately — no approval required.',
  },
  OPS: {
    key:     'OPS',
    label:   'Operations Team',
    labelTh: 'ทีมปฏิบัติการ',
    team:    'Operations Team',
    badge:   'sf-badge--high',
    icon:    '📋',
    desc:    'Requires Operations Team to verify the supporting document and approve.',
  },
  COMPLIANCE: {
    key:     'COMPLIANCE',
    label:   'Compliance Team',
    labelTh: 'ทีมกำกับดูแล',
    team:    'Compliance Team',
    badge:   'sf-badge--compliance',
    icon:    '🔒',
    desc:    'Requires Compliance Team review — sensitive identity data change.',
  },
};

// ── Intent definitions (with approval routing) ────────────────────────────────
const INTENTS = {
  'change-firstname': {
    label:    'เปลี่ยนแปลงชื่อ',
    labelEn:  'Change First Name',
    code:     'ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ',
    fields:   ['firstName'],
    approval: 'OPS',
    approvalReason: 'Legal name change — Operations Team must verify ID document',
  },
  'change-lastname': {
    label:    'เปลี่ยนแปลงนามสกุล',
    labelEn:  'Change Last Name',
    code:     'ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงนามสกุล',
    fields:   ['lastName'],
    approval: 'OPS',
    approvalReason: 'Legal name change — Operations Team must verify ID document',
  },
  'change-title': {
    label:    'เปลี่ยนแปลงคำนำหน้า',
    labelEn:  'Change Title / Prefix',
    code:     'ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงคำนำหน้า',
    fields:   ['titleCode'],
    approval: 'AUTO',
    approvalReason: 'Low-risk prefix change — no legal impact',
  },
  'change-fullname': {
    label:    'เปลี่ยนแปลงชื่อ-นามสกุล',
    labelEn:  'Change Full Name',
    code:     'ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงชื่อ-นามสกุล',
    fields:   ['thaiFirstName', 'thaiLastName', 'engFirstName', 'engLastName'],
    approval: 'OPS',
    approvalReason: 'Full legal name change — Operations Team must verify ID document and marriage/court certificate',
  },
  'change-id': {
    label:    'เปลี่ยนแปลงเลขบัตรประชาชน',
    labelEn:  'Change National ID',
    code:     'ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงเลขบัตรประชาชน',
    fields:   ['nationalId'],
    approval: 'COMPLIANCE',
    approvalReason: 'Sensitive identity data — Compliance Team review required per regulatory policy',
  },
  'change-dob': {
    label:    'เปลี่ยนแปลงวันเกิด',
    labelEn:  'Change Date of Birth',
    code:     'ขอใช้บริการ:CC - ข้อมูลส่วนตัว : เปลี่ยนแปลงวันเกิด',
    fields:   ['dob'],
    approval: 'AUTO',
    approvalReason: 'Minor date correction — auto-approved with document on file',
  },
  'change-address': {
    label:    'เปลี่ยนแปลงที่อยู่',
    labelEn:  'Change Address',
    code:     'ขอใช้บริการ:CC - ข้อมูลส่วนตัว - ที่อยู่',
    fields:   ['addressNumber', 'moo', 'soi', 'thanon', 'subDistrict', 'district', 'province', 'zipCode'],
    approval: 'AUTO',
    approvalReason: 'Address update — auto-approved with supporting document',
  },
  'change-phone': {
    label:    'เปลี่ยนแปลงหมายเลขโทรศัพท์',
    labelEn:  'Change Phone Number',
    code:     'ขอใช้บริการ:CC - ข้อมูลส่วนตัว - หมายเลขโทรศัพท์ในการติดต่อ',
    fields:   ['contactPhone'],
    approval: 'AUTO',
    approvalReason: 'Phone number update — auto-approved (OTP verification)',
  },
  'change-email': {
    label:    'เปลี่ยนแปลงอีเมล',
    labelEn:  'Change Email',
    code:     'ขอใช้บริการ:CC - ข้อมูลส่วนตัว - อีเมล',
    fields:   ['contactEmail'],
    approval: 'AUTO',
    approvalReason: 'Email update — auto-approved (OTP verification)',
  },
};

// ── Field definitions ─────────────────────────────────────────────────────────
const FIELD_DEFS = {
  // ── Name/Title (PUT /party/cust-profile) ────────────────────────────────────
  titleCode: {
    label:   'คำนำหน้า (Title Code)',
    hint:    'เลือกคำนำหน้าใหม่',
    type:    'select',
    options: ['MR.', 'MRS.', 'MISS', 'นาย', 'นาง', 'นางสาว'],
    dbKey:   'titleCode',
  },
  thaiFirstName: {
    label:  'ชื่อ (Thai First Name)',
    hint:   'กรอกชื่อใหม่ภาษาไทย',
    type:   'text',
    dbKey:  'thaiFirstName',
  },
  thaiLastName: {
    label:  'นามสกุล (Thai Last Name)',
    hint:   'กรอกนามสกุลใหม่ภาษาไทย',
    type:   'text',
    dbKey:  'thaiLastName',
  },
  engFirstName: {
    label:  'ชื่อภาษาอังกฤษ (English First Name)',
    hint:   'e.g. Somchai',
    type:   'text',
    dbKey:  'engFirstName',
  },
  engLastName: {
    label:  'นามสกุลภาษาอังกฤษ (English Last Name)',
    hint:   'e.g. Saetang',
    type:   'text',
    dbKey:  'engLastName',
  },

  // ── Address (POST /party/cust-profile/address) ──────────────────────────────
  addressNumber: {
    label:  'บ้านเลขที่ (Address No.)',
    hint:   'เช่น 66/8',
    type:   'text',
    dbKey:  'addressNumber',
    required: true,
  },
  moo: {
    label:  'หมู่ (Moo)',
    hint:   'เช่น 2 (ไม่บังคับ)',
    type:   'text',
    dbKey:  'moo',
    required: false,
  },
  soi: {
    label:  'ซอย (Soi)',
    hint:   'เช่น อารีย์ 23 (ไม่บังคับ)',
    type:   'text',
    dbKey:  'soi',
    required: false,
  },
  thanon: {
    label:  'ถนน (Road)',
    hint:   'เช่น รัชดาภิเษก (ไม่บังคับ)',
    type:   'text',
    dbKey:  'thanon',
    required: false,
  },
  subDistrict: {
    label:  'แขวง/ตำบล (Sub-District)',
    hint:   'เช่น จตุจักร',
    type:   'text',
    dbKey:  'subDistrict',
    required: true,
  },
  district: {
    label:  'เขต/อำเภอ (District)',
    hint:   'เช่น จตุจักร',
    type:   'text',
    dbKey:  'district',
    required: true,
  },
  province: {
    label:  'จังหวัด (Province)',
    hint:   'เช่น กรุงเทพมหานคร',
    type:   'text',
    dbKey:  'province',
    required: true,
  },
  zipCode: {
    label:  'รหัสไปรษณีย์ (Zip Code)',
    hint:   'เช่น 10150',
    type:   'text',
    dbKey:  'zipCode',
    required: true,
  },

  // ── Contact (POST /party/cust-profile/{cif}/Contacts) ───────────────────────
  contactPhone: {
    label:  'หมายเลขโทรศัพท์ (Phone Number)',
    hint:   'เช่น 0891234567',
    type:   'text',
    dbKey:  'contactPhone',
  },
  contactEmail: {
    label:  'อีเมล (Email)',
    hint:   'เช่น name@company.com',
    type:   'text',
    dbKey:  'contactEmail',
  },
};

// ── State ─────────────────────────────────────────────────────────────────────
let state = {
  currentStep:    1,
  selectedIntent: null,
  newValues:      {},
  currentCid:     null,
  caseCounter:    12345,
  docOverride:    false,
  ocrResult:      null,
};

// Doc upload state (module-level so all handlers can access)
let docFile        = null;
let ocrResult      = null;
let isOcrRunning   = false;
let autoAdvanceTimer = null;

const $ = id => document.getElementById(id);

function now() {
  return new Date().toLocaleTimeString('th-TH', { hour12: false });
}

function addLog(msg, type = 'info') {
  const log = $('processing-log');
  const entry = document.createElement('div');
  entry.className = `sf-log-entry sf-log-entry--${type}`;
  entry.innerHTML = `<span class="sf-log-time">${now()}</span><span class="sf-log-msg">${msg}</span>`;
  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
}

function currentCustomer() { return DB.getCustomer(state.currentCid); }
function currentFieldValue(fk) {
  // If we have a real SF case loaded, show current values from case data
  if (state.currentSfCase) {
    const sfCase = state.currentSfCase;
    const map = {
      // Name/Title — show current customer name from SF case
      titleCode:      sfCase.newTitle || '—',
      thaiFirstName:  sfCase.customerName ? sfCase.customerName.split(/\s+/)[0] : '—',
      thaiLastName:   sfCase.customerName ? sfCase.customerName.split(/\s+/).slice(1).join(' ') : '—',
      engFirstName:   '—',
      engLastName:    '—',
      // Address — no current value from SF case
      addressNumber:  '—',
      moo:            '—',
      soi:            '—',
      thanon:         '—',
      subDistrict:    '—',
      district:       '—',
      province:       '—',
      zipCode:        '—',
      // Contact
      contactPhone:   '—',
      contactEmail:   '—',
    };
    return map[fk] || '—';
  }
  // Fallback to mock DB
  const c = currentCustomer();
  return c ? (c[FIELD_DEFS[fk]?.dbKey] || '') : '';
}

// ── Tab switching ─────────────────────────────────────────────────────────────
document.querySelectorAll('.sf-app-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    if (!tab.dataset || !tab.dataset.tab) return; // Skip links without data-tab (e.g., CEO Dashboard)
    document.querySelectorAll('.sf-app-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.sf-tab-panel').forEach(p => p.classList.add('hidden'));
    tab.classList.add('active');
    const panel = $(`tab-${tab.dataset.tab}`);
    if (panel) panel.classList.remove('hidden');
    if (tab.dataset.tab === 'customer-db')    renderCustomerTable();
    if (tab.dataset.tab === 'audit-log')      renderAuditTable();
    if (tab.dataset.tab === 'approval-queue') renderApprovalQueue();
    if (tab.dataset.tab === 'sf-cases')       renderSfCasesTable();
  });
});

// ── Case selector (from Salesforce data) ──────────────────────────────────────
function populateCustomerSelector() {
  const sel = $('customer-selector');
  sel.innerHTML = '';

  // Load SF cases — prefer localStorage (fresh from Refresh), fallback to global variable
  let sfCases = [];
  const storedCases = localStorage.getItem('sfcc_sf_cases');
  if (storedCases) {
    sfCases = JSON.parse(storedCases);
  } else if (typeof SF_CASES_DATA !== 'undefined' && SF_CASES_DATA.length > 0) {
    sfCases = SF_CASES_DATA;
  }

  if (sfCases.length > 0) {
    // Use real SF cases
    sfCases.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.caseNumber;
      opt.textContent = `#${c.caseNumber} — ${c.customerName || 'Unknown'} (${c.status})`;
      opt.dataset.caseData = JSON.stringify(c);
      sel.appendChild(opt);
    });
  } else {
    // Fallback to mock customers if no SF cases
    Object.values(DB.getAllCustomers()).forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.cid;
      opt.textContent = `${c.cid} — ${c.title} ${c.firstName} ${c.lastName}`;
      sel.appendChild(opt);
    });
  }

  // Set initial selection
  state.currentCid = sel.value;
  loadSelectedCase();
}

function loadSelectedCase() {
  const sel = $('customer-selector');
  const selectedOpt = sel.options[sel.selectedIndex];
  if (!selectedOpt) return;

  const caseDataStr = selectedOpt.dataset.caseData;
  if (caseDataStr) {
    // Real SF case
    const sfCase = JSON.parse(caseDataStr);
    state.currentCid = sfCase.citizenId || sfCase.caseNumber;
    state.currentSfCase = sfCase;
    refreshFromSfCase(sfCase);
  } else {
    // Fallback mock
    state.currentCid = sel.value;
    state.currentSfCase = null;
    refreshCustomerPanel();
  }
}

function refreshFromSfCase(sfCase) {
  // Update Case Details panel
  $('header-case-id').textContent   = `Case #${sfCase.caseNumber}`;
  $('breadcrumb-case').textContent  = `Case #${sfCase.caseNumber}`;
  $('case-id-display').textContent  = sfCase.caseNumber;
  $('case-cid-display').textContent = sfCase.citizenId || '—';
  $('case-created').textContent     = sfCase.status + ' / ' + (sfCase.subStatus || '—');

  // Update Customer Info panel from SF case data
  $('customer-info-panel').innerHTML = [
    ['Case #',       sfCase.caseNumber],
    ['Status',       sfCase.status],
    ['Sub Status',   sfCase.subStatus || '—'],
    ['Customer',     sfCase.customerName || '—'],
    ['Citizen ID',   sfCase.citizenId || '—'],
    ['Intent',       sfCase.intentType || '—'],
    ['New First',    sfCase.newFirstName || '—'],
    ['New Last',     sfCase.newLastName || '—'],
    ['New Title',    sfCase.newTitle || '—'],
    ['Old Name',     sfCase.oldName || '—'],
  ].map(([label, val]) => `
    <div class="sf-detail-item">
      <span class="sf-detail-label">${label}</span>
      <span class="sf-detail-value">${val}</span>
    </div>`).join('');
}

$('customer-selector').addEventListener('change', e => {
  loadSelectedCase();
  resetToStep1(false);
  addLog(`Case changed to: #${e.target.value}`);
});

// Refresh cases from Salesforce API (same as SF Cases tab)
$('btn-refresh-cases').addEventListener('click', async () => {
  const btn    = $('btn-refresh-cases');
  const status = $('cases-refresh-status');

  btn.disabled = true;
  btn.textContent = '⏳';
  status.textContent = 'Querying Salesforce...';
  status.style.color = 'var(--sf-blue)';

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s for SF query
    const resp = await fetch(SF_API_URL, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    localStorage.setItem('sfcc_sf_cases', JSON.stringify(data.cases));
    populateCustomerSelector(); // Reload dropdown with fresh data
    renderSfCasesTable(); // Also update SF Cases tab if visible

    status.textContent = `✓ ${data.count} cases`;
    status.style.color = 'var(--sf-green)';
    addLog(`Refreshed: ${data.count} cases from Salesforce`, 'success');
  } catch (e) {
    if (e.name === 'AbortError') {
      status.textContent = '✗ Timeout';
    } else {
      status.textContent = '✗ Server not running';
    }
    status.style.color = 'var(--sf-red)';
  } finally {
    btn.disabled = false;
    btn.textContent = '🔄 Refresh';
  }
});

function refreshCustomerPanel() {
  const c = currentCustomer();
  if (!c) return;
  $('customer-info-panel').innerHTML = [
    ['CID', c.cid], ['Title', c.title], ['First Name', c.firstName],
    ['Last Name', c.lastName], ['National ID', c.nationalId],
    ['Date of Birth', c.dob], ['Phone', c.phone], ['Email', c.email],
  ].map(([label, val]) => `
    <div class="sf-detail-item">
      <span class="sf-detail-label">${label}</span>
      <span class="sf-detail-value">${val || '—'}</span>
    </div>`).join('');

  const caseId = `000${state.caseCounter}`;
  $('header-case-id').textContent   = `Case #${caseId}`;
  $('breadcrumb-case').textContent  = `Case #${caseId}`;
  $('case-id-display').textContent  = caseId;
  $('case-cid-display').textContent = c.cid;
  $('case-created').textContent     = new Date().toLocaleString('th-TH');
}

// ── Step management ───────────────────────────────────────────────────────────
function setStep(n) {
  ['1','2','doc','3','result'].forEach(id => {
    const el = $(`step-${id}`);
    if (el) el.classList.add('hidden');
  });
  $(`step-${n}`).classList.remove('hidden');
  state.currentStep = n;

  // Step indicator IDs: step-indicator-1, step-indicator-2, step-indicator-doc, step-indicator-3
  const indicators = ['1','2','doc','3'];
  const activeIdx  = indicators.indexOf(String(n)); // 0-based index of active step

  indicators.forEach((key, idx) => {
    const ind = $(`step-indicator-${key}`);
    if (!ind) return;
    ind.classList.remove('active','done');
    if (n === 'result') {
      ind.classList.add('done');
    } else if (idx < activeIdx) {
      ind.classList.add('done');
    } else if (idx === activeIdx) {
      ind.classList.add('active');
    }
  });

  document.querySelectorAll('.sf-step__line').forEach((line, idx) => {
    line.classList.toggle('done', n === 'result' || idx < activeIdx);
  });
}

function resetToStep1(clearIntent = true) {
  if (clearIntent) {
    state.selectedIntent = null;
    state.newValues = {};
    state.docOverride = false;
    state.ocrResult = null;
    docFile = null;
    ocrResult = null;
    document.querySelectorAll('.sf-intent-card').forEach(c => {
      c.classList.remove('selected');
      c.querySelector('input[type="radio"]').checked = false;
    });
    $('btn-step1-next').disabled = true;
  }
  $('btn-submit').disabled = false;
  $('btn-submit').textContent = '✓ Submit';
  setStep(1);
}

// ── Step 1: Intent selection — show approval badge on each card ───────────────
function decorateIntentCards() {
  document.querySelectorAll('.sf-intent-card').forEach(card => {
    const intentKey = card.dataset.intent;
    const intent    = INTENTS[intentKey];
    const level     = APPROVAL[intent.approval];
    // Remove old badge if any
    card.querySelectorAll('.intent-approval-badge').forEach(b => b.remove());
    const badge = document.createElement('div');
    badge.className = `intent-approval-badge approval-${intent.approval.toLowerCase()}`;
    badge.innerHTML = `${level.icon} ${level.label}`;
    card.appendChild(badge);
  });
}

document.querySelectorAll('.sf-intent-card').forEach(card => {
  card.addEventListener('click', () => {
    document.querySelectorAll('.sf-intent-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    card.querySelector('input[type="radio"]').checked = true;
    state.selectedIntent = card.dataset.intent;
    $('btn-step1-next').disabled = false;
    const intent = INTENTS[state.selectedIntent];
    const level  = APPROVAL[intent.approval];
    addLog(`Intent: ${intent.label} — Approval: ${level.label}`);
    // Show routing hint below grid
    $('approval-hint').innerHTML = `
      <span class="approval-hint-icon">${level.icon}</span>
      <span><strong>${level.label}:</strong> ${intent.approvalReason}</span>`;
    $('approval-hint').className = `sf-approval-hint approval-hint--${intent.approval.toLowerCase()}`;
    $('approval-hint').classList.remove('hidden');
  });
});

$('btn-step1-next').addEventListener('click', () => {
  if (!state.selectedIntent) return;
  buildStep2();
  setStep(2);
});

// ── Step 2: Dynamic form ──────────────────────────────────────────────────────
function buildStep2() {
  const intent = INTENTS[state.selectedIntent];
  const level  = APPROVAL[intent.approval];

  $('intent-summary').innerHTML =
    `🎯 <strong>${intent.label}</strong> &nbsp;·&nbsp; ${intent.labelEn}` +
    `&nbsp;·&nbsp; <span class="approval-pill approval-pill--${intent.approval.toLowerCase()}">${level.icon} ${level.label}</span>`;

  const form = $('dynamic-form');
  form.innerHTML = '';
  const useRow = intent.fields.length === 2;
  const useGrid = intent.fields.length > 2; // Address has 8 fields — use grid
  const wrapper = useRow
    ? Object.assign(document.createElement('div'), { className: 'sf-form-row' })
    : useGrid
      ? Object.assign(document.createElement('div'), { className: 'sf-form-grid' })
      : form;

  intent.fields.forEach(fk => {
    const def = FIELD_DEFS[fk];
    const currentVal = currentFieldValue(fk);
    const group = document.createElement('div');
    group.className = 'sf-form-group';

    const currentDiv = document.createElement('div');
    currentDiv.className = 'sf-current-value';
    currentDiv.innerHTML = `Current: <strong>${currentVal || '—'}</strong>`;

    const label = document.createElement('label');
    label.setAttribute('for', `field-${fk}`);
    label.innerHTML = `${def.label} <span class="sf-form-hint">${def.hint}</span>`;

    let input;
    if (def.type === 'select') {
      input = document.createElement('select');
      input.className = 'sf-select';
      def.options.forEach(opt => {
        const o = document.createElement('option');
        o.value = opt; o.textContent = opt;
        if (opt === currentVal) o.selected = true;
        input.appendChild(o);
      });
    } else {
      input = document.createElement('input');
      input.type = def.type;
      input.className = 'sf-input';
      input.placeholder = def.hint;
      if (def.maxlength) input.maxLength = def.maxlength;
    }
    input.id = `field-${fk}`;
    group.appendChild(currentDiv);
    group.appendChild(label);
    group.appendChild(input);
    (useRow || useGrid ? wrapper : form).appendChild(group);
  });
  if (useRow || useGrid) form.appendChild(wrapper);
}

$('btn-step2-back').addEventListener('click', () => setStep(1));

$('btn-step2-next').addEventListener('click', () => {
  state.newValues = {};
  let valid = true;
  INTENTS[state.selectedIntent].fields.forEach(fk => {
    const input = $(`field-${fk}`);
    const val = input ? input.value.trim() : '';
    const def = FIELD_DEFS[fk];
    const isRequired = def && def.required !== false; // Default: required unless explicitly false

    if (!val && isRequired) {
      if (input) input.style.borderColor = 'var(--sf-red)';
      valid = false;
    } else {
      if (input) input.style.borderColor = '';
      if (val) state.newValues[fk] = val; // Only include non-empty values
    }
  });
  if (!valid) { addLog('Required fields are missing', 'warn'); return; }
  buildDocStep();
  setStep('doc');
  addLog('Values entered — proceeding to document verification');
});

// ── Step 3: Confirm — show approval routing prominently ──────────────────────
function buildStep3() {
  const intent = INTENTS[state.selectedIntent];
  const level  = APPROVAL[intent.approval];
  const caseId = `000${state.caseCounter}`;

  // Approval routing banner
  $('approval-routing-banner').innerHTML = `
    <div class="approval-banner approval-banner--${intent.approval.toLowerCase()}">
      <div class="approval-banner__icon">${level.icon}</div>
      <div class="approval-banner__body">
        <div class="approval-banner__title">
          ${intent.approval === 'AUTO' ? 'Auto-Approve — Immediate Update' : `Requires Approval: ${level.team}`}
        </div>
        <div class="approval-banner__reason">${intent.approvalReason}</div>
      </div>
      <div class="approval-banner__badge">
        <span class="sf-badge ${level.badge}">${level.labelTh}</span>
      </div>
    </div>`;

  // Change summary
  const rows = [
    { label: 'Case ID',     value: `#${caseId}` },
    { label: 'CID',         value: state.currentCid },
    { label: 'Intent',      value: `${intent.label} — ${intent.labelEn}` },
  ];
  intent.fields.forEach(fk => {
    rows.push({ label: FIELD_DEFS[fk].label.split(' (')[0],
                oldValue: currentFieldValue(fk), newValue: state.newValues[fk] });
  });

  $('confirm-box').innerHTML = rows.map(r => r.newValue !== undefined
    ? `<div class="sf-confirm-row">
        <span class="sf-confirm-label">${r.label}</span>
        <span class="sf-confirm-value">
          <span class="change-before">${r.oldValue}</span>
          <span class="change-arrow">→</span>
          <span class="change-after">${r.newValue}</span>
        </span>
       </div>`
    : `<div class="sf-confirm-row">
        <span class="sf-confirm-label">${r.label}</span>
        <span class="sf-confirm-value">${r.value}</span>
       </div>`
  ).join('');

  // Update submit button label based on routing
  const btn = $('btn-submit');
  if (intent.approval === 'AUTO') {
    btn.textContent = '✓ Submit & Apply Now';
    btn.className = 'sf-btn sf-btn--success';
  } else {
    btn.textContent = `📤 Submit for ${level.team} Approval`;
    btn.className = 'sf-btn sf-btn--pending';
  }
}

$('btn-step3-back').addEventListener('click', () => setStep('doc'));

// ── Submit ────────────────────────────────────────────────────────────────────
$('btn-submit').addEventListener('click', () => {
  const intent   = INTENTS[state.selectedIntent];
  const level    = APPROVAL[intent.approval];
  const caseId   = `000${state.caseCounter}`;
  const customer = currentCustomer();

  $('btn-submit').disabled = true;
  $('btn-submit').textContent = '⏳ Processing...';

  setTimeout(() => {
    const beforeValues = {};
    intent.fields.forEach(fk => { beforeValues[fk] = currentFieldValue(fk); });

    if (intent.approval === 'AUTO') {
      // Apply immediately
      const fieldUpdates = {};
      intent.fields.forEach(fk => { fieldUpdates[FIELD_DEFS[fk].dbKey] = state.newValues[fk]; });
      DB.updateCustomer(state.currentCid, fieldUpdates);

      intent.fields.forEach(fk => {
        DB.addAuditEntry({
          timestamp: new Date().toISOString(), caseId, cid: state.currentCid,
          customerName: `${customer.title} ${customer.firstName} ${customer.lastName}`,
          intentKey: state.selectedIntent, intentLabel: intent.label,
          intentLabelEn: intent.labelEn, intentCode: intent.code,
          fieldKey: fk, fieldLabel: FIELD_DEFS[fk].label.split(' (')[0],
          beforeValue: beforeValues[fk], afterValue: state.newValues[fk],
          agent: 'Call Center Agent', approvalLevel: 'AUTO', status: 'COMPLETED',
        });
      });

      refreshCustomerPanel();
      addLog(`✓ Auto-approved & applied — CID: ${state.currentCid}`, 'success');
      state.caseCounter++;
      showResult('auto', intent, beforeValues, caseId, null);

    } else {
      // Send to approval queue — do NOT update customer yet
      const approvalId = DB.addApprovalRequest({
        caseId, cid: state.currentCid,
        customerName: `${customer.title} ${customer.firstName} ${customer.lastName}`,
        intentKey: state.selectedIntent, intentLabel: intent.label,
        intentLabelEn: intent.labelEn, intentCode: intent.code,
        approvalLevel: intent.approval, approvalTeam: level.team,
        fields: intent.fields.map(fk => ({
          fieldKey: fk,
          fieldLabel: FIELD_DEFS[fk].label.split(' (')[0],
          beforeValue: beforeValues[fk],
          afterValue: state.newValues[fk],
        })),
        agent: 'Call Center Agent',
        approvalReason: intent.approvalReason,
      });

      // Write audit entry as PENDING
      intent.fields.forEach(fk => {
        DB.addAuditEntry({
          timestamp: new Date().toISOString(), caseId, cid: state.currentCid,
          customerName: `${customer.title} ${customer.firstName} ${customer.lastName}`,
          intentKey: state.selectedIntent, intentLabel: intent.label,
          intentLabelEn: intent.labelEn, intentCode: intent.code,
          fieldKey: fk, fieldLabel: FIELD_DEFS[fk].label.split(' (')[0],
          beforeValue: beforeValues[fk], afterValue: state.newValues[fk],
          agent: 'Call Center Agent', approvalLevel: intent.approval,
          approvalId, status: 'PENDING_APPROVAL',
        });
      });

      addLog(`📤 Sent to ${level.team} for approval — ID: ${approvalId}`, 'warn');
      state.caseCounter++;
      showResult('pending', intent, beforeValues, caseId, approvalId);
    }

    setStep('result');
  }, 900);
});

// ── Result ────────────────────────────────────────────────────────────────────
function showResult(type, intent, beforeValues, caseId, approvalId) {
  const level = APPROVAL[intent.approval];
  const changeRows = intent.fields.map(fk =>
    `<div><strong>${FIELD_DEFS[fk].label.split(' (')[0]}:</strong>
      <span style="color:var(--sf-gray-4)">${beforeValues[fk]}</span>
      → <span style="font-weight:700;color:${type==='auto'?'var(--sf-green)':'var(--sf-orange)'}">${state.newValues[fk]}</span>
    </div>`).join('');

  const panel = $('result-panel');
  if (type === 'auto') {
    panel.innerHTML = `
      <div class="sf-result__icon">✅</div>
      <div class="sf-result__title success">Update Applied Successfully</div>
      <div class="sf-result__desc">Auto-approved. Customer record updated immediately.</div>
      <div class="sf-result__detail">
        <div><strong>Case:</strong> #${caseId} &nbsp;·&nbsp; <strong>CID:</strong> ${state.currentCid}</div>
        <div><strong>Intent:</strong> ${intent.label}</div>
        ${changeRows}
        <div style="margin-top:8px;color:var(--sf-gray-4);font-size:12px">
          ✅ Auto-Approve &nbsp;·&nbsp; ✓ DB updated &nbsp;·&nbsp; ✓ Audit logged
        </div>
      </div>`;
  } else {
    panel.innerHTML = `
      <div class="sf-result__icon">📤</div>
      <div class="sf-result__title pending">Sent for Approval</div>
      <div class="sf-result__desc">
        Request submitted to <strong>${level.team}</strong>. Customer record will be updated after approval.
      </div>
      <div class="sf-result__detail">
        <div><strong>Approval ID:</strong> <span style="font-family:monospace">${approvalId}</span></div>
        <div><strong>Case:</strong> #${caseId} &nbsp;·&nbsp; <strong>CID:</strong> ${state.currentCid}</div>
        <div><strong>Intent:</strong> ${intent.label}</div>
        ${changeRows}
        <div style="margin-top:8px;color:var(--sf-gray-4);font-size:12px">
          ${level.icon} Pending ${level.team} &nbsp;·&nbsp; ✓ Audit logged as PENDING_APPROVAL
        </div>
      </div>`;
  }
}

$('btn-new-case').addEventListener('click', () => {
  resetToStep1(true);
  $('approval-hint').classList.add('hidden');
  addLog('─── New case session started ───');
});

$('btn-view-audit').addEventListener('click', () => switchTab('audit-log'));
$('btn-view-approvals').addEventListener('click', () => switchTab('approval-queue'));

function switchTab(tabKey) {
  document.querySelectorAll('.sf-app-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.sf-tab-panel').forEach(p => p.classList.add('hidden'));
  document.querySelector(`[data-tab="${tabKey}"]`).classList.add('active');
  $(`tab-${tabKey}`).classList.remove('hidden');
  if (tabKey === 'audit-log')      renderAuditTable();
  if (tabKey === 'approval-queue') renderApprovalQueue();
}

$('log-toggle').addEventListener('click', () => {
  const log = $('processing-log');
  const btn = $('log-toggle');
  const hidden = log.style.display === 'none';
  log.style.display = hidden ? '' : 'none';
  btn.textContent = hidden ? '▼' : '▶';
});

// ── Customer DB tab ───────────────────────────────────────────────────────────
function renderCustomerTable() {
  const customers = Object.values(DB.getAllCustomers());
  $('customer-table-body').innerHTML = customers.map(c => `
    <tr class="${c.cid === state.currentCid ? 'sf-table-row--active' : ''}">
      <td><span class="sf-badge sf-badge--new">${c.cid}</span></td>
      <td>${c.title}</td><td>${c.firstName}</td><td>${c.lastName}</td>
      <td class="mono">${c.nationalId}</td><td>${c.dob}</td>
      <td>${c.phone}</td><td>${c.email}</td>
    </tr>`).join('');
  $('customer-count-badge').textContent = `${customers.length} records`;
}

$('btn-reset-db').addEventListener('click', () => {
  if (!confirm('Reset all data to seed values? This clears customers, audit log, and approval queue.')) return;
  DB.reset();
  populateCustomerSelector();
  renderCustomerTable();
  renderAuditTable();
  renderApprovalQueue();
  addLog('Database reset to seed data', 'warn');
});

// ── Audit log tab ─────────────────────────────────────────────────────────────
function statusBadge(status) {
  const map = {
    COMPLETED:        'sf-badge--valid',
    PENDING_APPROVAL: 'sf-badge--pending',
    APPROVED:         'sf-badge--valid',
    REJECTED:         'sf-badge--rejected',
  };
  return `<span class="sf-badge ${map[status] || 'sf-badge--new'}">${status.replace('_',' ')}</span>`;
}

function renderAuditTable() {
  const log = DB.getAuditLog();
  $('audit-count-badge').textContent = `${log.length} record${log.length !== 1 ? 's' : ''}`;
  const empty = $('audit-empty');
  if (log.length === 0) {
    $('audit-table-body').innerHTML = '';
    empty.classList.remove('hidden'); return;
  }
  empty.classList.add('hidden');
  $('audit-table-body').innerHTML = log.map((e, i) => `
    <tr>
      <td style="color:var(--sf-gray-4);font-size:12px">${log.length - i}</td>
      <td style="white-space:nowrap;font-size:12px">${new Date(e.timestamp).toLocaleString('th-TH')}</td>
      <td><span style="font-family:monospace;font-size:12px">#${e.caseId}</span></td>
      <td><span class="sf-badge sf-badge--new">${e.cid}</span></td>
      <td>${e.customerName}</td>
      <td>
        <div style="font-size:12px;font-weight:600">${e.intentLabel}</div>
        <div style="font-size:10px;color:var(--sf-gray-4)">${e.intentLabelEn}</div>
      </td>
      <td>${approvalLevelBadge(e.approvalLevel)}</td>
      <td style="font-weight:600">${e.fieldLabel}</td>
      <td><span class="audit-before">${e.beforeValue}</span></td>
      <td><span class="audit-after">${e.afterValue}</span></td>
      <td style="font-size:12px">${e.agent}</td>
      <td>${statusBadge(e.status)}</td>
    </tr>`).join('');
}

function approvalLevelBadge(level) {
  const map = {
    AUTO:       '<span class="sf-badge sf-badge--valid">Auto</span>',
    OPS:        '<span class="sf-badge sf-badge--high">Ops Team</span>',
    COMPLIANCE: '<span class="sf-badge sf-badge--compliance">Compliance</span>',
  };
  return map[level] || `<span class="sf-badge">${level}</span>`;
}

$('btn-clear-audit').addEventListener('click', () => {
  if (!confirm('Clear all audit log entries?')) return;
  DB.clearAuditLog(); renderAuditTable();
  addLog('Audit log cleared', 'warn');
});

$('btn-export-csv').addEventListener('click', () => {
  const log = DB.getAuditLog();
  if (!log.length) { alert('No records to export.'); return; }
  const headers = ['#','Timestamp','Case ID','CID','Customer','Intent','Approval Level','Field','Before','After','Agent','Status'];
  const rows = log.map((e, i) => [
    log.length - i, new Date(e.timestamp).toLocaleString('th-TH'),
    e.caseId, e.cid, e.customerName, e.intentLabel, e.approvalLevel || '',
    e.fieldLabel, e.beforeValue, e.afterValue, e.agent, e.status,
  ].map(v => `"${String(v).replace(/"/g,'""')}"`).join(','));
  const csv  = [headers.join(','), ...rows].join('\n');
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  Object.assign(document.createElement('a'), {
    href: url, download: `audit_log_${new Date().toISOString().slice(0,10)}.csv`,
  }).click();
  URL.revokeObjectURL(url);
  addLog(`Exported ${log.length} records to CSV`, 'success');
});

// ── Approval queue tab ────────────────────────────────────────────────────────
function renderApprovalQueue() {
  const queue = DB.getApprovalQueue();
  const pending  = queue.filter(r => r.status === 'PENDING');
  const resolved = queue.filter(r => r.status !== 'PENDING');

  $('approval-pending-count').textContent  = `${pending.length} pending`;
  $('approval-resolved-count').textContent = `${resolved.length} resolved`;

  renderQueueSection('approval-pending-body', 'approval-pending-empty', pending, true);
  renderQueueSection('approval-resolved-body', 'approval-resolved-empty', resolved, false);
}

function renderQueueSection(tbodyId, emptyId, items, showActions) {
  const tbody = $(tbodyId);
  const empty = $(emptyId);
  if (!items.length) {
    tbody.innerHTML = '';
    empty.classList.remove('hidden'); return;
  }
  empty.classList.add('hidden');
  tbody.innerHTML = items.map(r => {
    const fieldRows = r.fields.map(f =>
      `<div style="font-size:12px">${f.fieldLabel}: <span class="audit-before">${f.beforeValue}</span> → <span class="audit-after">${f.afterValue}</span></div>`
    ).join('');
    const levelBadge = r.approvalLevel === 'COMPLIANCE'
      ? '<span class="sf-badge sf-badge--compliance">Compliance</span>'
      : '<span class="sf-badge sf-badge--high">Ops Team</span>';
    const actions = showActions ? `
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <button class="sf-btn sf-btn--success" style="height:28px;font-size:12px"
          onclick="approveRequest('${r.id}')">✓ Approve</button>
        <button class="sf-btn" style="height:28px;font-size:12px;background:var(--sf-red);color:#fff;border-color:var(--sf-red)"
          onclick="rejectRequest('${r.id}')">✗ Reject</button>
      </div>` : '';
    const resolvedInfo = !showActions ? `
      <div style="font-size:11px;color:var(--sf-gray-4);margin-top:4px">
        ${r.status === 'APPROVED' ? '✓' : '✗'} ${r.reviewedBy || ''} · ${r.reviewedAt ? new Date(r.reviewedAt).toLocaleString('th-TH') : ''}
        ${r.remarks ? `<br>Remarks: ${r.remarks}` : ''}
      </div>` : '';
    return `<tr>
      <td><span style="font-family:monospace;font-size:11px">${r.id}</span></td>
      <td style="font-size:12px;white-space:nowrap">${new Date(r.submittedAt).toLocaleString('th-TH')}</td>
      <td><span style="font-family:monospace;font-size:12px">#${r.caseId}</span></td>
      <td><span class="sf-badge sf-badge--new">${r.cid}</span></td>
      <td>${r.customerName}</td>
      <td>
        <div style="font-size:12px;font-weight:600">${r.intentLabel}</div>
        <div style="font-size:10px;color:var(--sf-gray-4)">${r.intentLabelEn}</div>
      </td>
      <td>${levelBadge}</td>
      <td>${fieldRows}</td>
      <td style="font-size:12px">${r.agent}</td>
      <td>${statusBadge(r.status)}${resolvedInfo}</td>
      <td>${actions}</td>
    </tr>`;
  }).join('');
}

function approveRequest(id) {
  const reviewer = prompt('Reviewer name:', 'Ops Supervisor');
  if (reviewer === null) return;
  const remarks  = prompt('Remarks (optional):', 'Document verified — approved') || '';

  const queue = DB.getApprovalQueue();
  const req   = queue.find(r => r.id === id);
  if (!req) return;

  // Apply the field updates to customer DB
  const fieldUpdates = {};
  req.fields.forEach(f => { fieldUpdates[FIELD_DEFS[f.fieldKey].dbKey] = f.afterValue; });
  DB.updateCustomer(req.cid, fieldUpdates);

  // Update approval status
  DB.updateApprovalStatus(id, 'APPROVED', reviewer, remarks);

  // Update audit entries for this approval ID
  const auditLog = DB.getAuditLog();
  auditLog.forEach(e => { if (e.approvalId === id) e.status = 'APPROVED'; });
  localStorage.setItem('sfcc_audit_log', JSON.stringify(auditLog));

  addLog(`✓ Approved by ${reviewer} — ID: ${id}, CID: ${req.cid}`, 'success');
  renderApprovalQueue();
  renderAuditTable();
  refreshCustomerPanel();
}

function rejectRequest(id) {
  const reviewer = prompt('Reviewer name:', 'Ops Supervisor');
  if (reviewer === null) return;
  const remarks  = prompt('Rejection reason:', 'Document not valid') || 'Rejected';

  DB.updateApprovalStatus(id, 'REJECTED', reviewer, remarks);

  const auditLog = DB.getAuditLog();
  auditLog.forEach(e => { if (e.approvalId === id) e.status = 'REJECTED'; });
  localStorage.setItem('sfcc_audit_log', JSON.stringify(auditLog));

  addLog(`✗ Rejected by ${reviewer} — ID: ${id}, reason: ${remarks}`, 'error');
  renderApprovalQueue();
  renderAuditTable();
}

$('btn-clear-approvals').addEventListener('click', () => {
  if (!confirm('Clear all resolved approval records?')) return;
  const queue = DB.getApprovalQueue().filter(r => r.status === 'PENDING');
  localStorage.setItem('sfcc_approval_queue', JSON.stringify(queue));
  renderApprovalQueue();
});

// ── Init ──────────────────────────────────────────────────────────────────────
decorateIntentCards();
populateCustomerSelector();
setStep(1);

// ── Document Upload & OCR Step ────────────────────────────────────────────────
function buildDocStep() {
  const req = DOC_REQUIREMENTS[state.selectedIntent];
  docFile   = null;
  ocrResult = null;
  isOcrRunning = false;

  // Cancel any pending auto-advance from a previous run
  if (autoAdvanceTimer) { clearInterval(autoAdvanceTimer); autoAdvanceTimer = null; }
  const toast = document.getElementById('auto-advance-toast');
  if (toast) toast.remove();

  // Reset UI
  $('doc-upload-zone').classList.remove('hidden');
  $('doc-preview').classList.add('hidden');
  $('ocr-progress').classList.add('hidden');
  $('ocr-results').classList.add('hidden');
  $('btn-run-ocr').disabled = true;
  $('btn-run-ocr').classList.remove('hidden');
  $('btn-run-ocr').textContent = '🔍 Re-verify';
  $('btn-doc-next').classList.add('hidden');
  $('btn-skip-ocr').style.display = '';

  // Requirement banner
  $('doc-requirement-banner').innerHTML = `
    <div class="doc-req-banner">
      <div class="doc-req-banner__icon">${req.icon}</div>
      <div class="doc-req-banner__body">
        <div class="doc-req-banner__title">${req.docLabel}</div>
        <div class="doc-req-banner__sub">${req.docLabelEn}</div>
        <div class="doc-req-banner__desc">${req.description}</div>
      </div>
    </div>`;

  $('doc-file-input').accept = req.acceptTypes;

  // Pre-warm Tesseract in background — fire and forget, 30s timeout
  const warmup = OCR.init();
  const timeout = new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 30000));
  Promise.race([warmup, timeout]).catch(() => {
    // Pre-warm failed or timed out — OCR will show error when user tries to verify
    // This is non-blocking: the upload UI still works fine
  });
}

// File browse button — only the button triggers file dialog, NOT the whole zone
$('btn-browse-doc').addEventListener('click', (e) => {
  e.stopPropagation();
  $('doc-file-input').click();
});

// Drag & drop on the zone (but NOT click-to-open — that's the button's job)
const uploadZone = $('doc-upload-zone');
uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) handleDocFile(file);
});
// Remove the zone click handler — it caused double file dialog with the button

$('doc-file-input').addEventListener('change', e => {
  if (e.target.files[0]) handleDocFile(e.target.files[0]);
  // Reset input so same file can be re-selected
  e.target.value = '';
});

function handleDocFile(file) {
  if (!file.type.startsWith('image/')) {
    addLog('Please upload an image file (JPG, PNG, WEBP)', 'warn');
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    addLog('File too large — maximum 10MB', 'warn');
    return;
  }
  docFile = file;

  // Show preview, then auto-trigger OCR
  const reader = new FileReader();
  reader.onload = ev => {
    $('doc-preview-img').src = ev.target.result;
    $('doc-preview-filename').textContent = file.name;
    $('doc-upload-zone').classList.add('hidden');
    $('doc-preview').classList.remove('hidden');
    $('ocr-results').classList.add('hidden');
    $('btn-run-ocr').disabled = false;
    $('btn-doc-next').classList.add('hidden');
    // Auto-start OCR immediately after preview renders
    addLog(`Document loaded: ${file.name} — starting verification...`);
    runOcr();
  };
  reader.readAsDataURL(file);
}

$('btn-remove-doc').addEventListener('click', () => {
  // Cancel any pending auto-advance
  if (autoAdvanceTimer) { clearInterval(autoAdvanceTimer); autoAdvanceTimer = null; }
  const toast = document.getElementById('auto-advance-toast');
  if (toast) toast.remove();

  docFile = null;
  ocrResult = null;
  $('doc-file-input').value = '';
  $('doc-preview').classList.add('hidden');
  $('doc-upload-zone').classList.remove('hidden');
  $('ocr-results').classList.add('hidden');
  $('btn-run-ocr').disabled = true;
  $('btn-doc-next').classList.add('hidden');
});

$('btn-doc-back').addEventListener('click', () => setStep(2));

// Skip verification — agent proceeds without OCR (logged as manual override)
$('btn-skip-ocr').addEventListener('click', () => {
  if (!confirm('Skip document verification? This will be logged as a manual override and may require supervisor approval.')) return;
  state.docOverride = true;
  state.ocrResult = null;
  addLog('⚠️ Document verification skipped by agent — manual override', 'warn');
  buildStep3();
  setStep(3);
});

// ── Run OCR (called automatically on file load, or manually via button) ───────
async function runOcr() {
  if (!docFile || isOcrRunning) return;

  // Check if OCR engine is available before starting
  if (!OCR.isAvailable()) {
    $('ocr-progress').classList.add('hidden');
    $('ocr-results').classList.remove('hidden');
    $('ocr-results').innerHTML = `
      <div style="padding:20px;background:#fef5e7;border-radius:8px;font-size:13px">
        <div style="font-weight:700;color:#a05a00;margin-bottom:6px">⚠️ OCR Engine Not Available</div>
        <div style="color:var(--sf-gray-4)">Tesseract.js could not be loaded from CDN. This requires an internet connection on first use.</div>
        <div style="margin-top:10px;color:var(--sf-gray-5)">You can still proceed using <strong>Skip Verification</strong> — the request will be flagged for manual document review.</div>
      </div>`;
    addLog('OCR unavailable — Tesseract.js not loaded. Use Skip Verification to proceed.', 'warn');
    return;
  }

  isOcrRunning = true;

  $('btn-run-ocr').disabled = true;
  $('btn-run-ocr').textContent = '⏳ Verifying...';
  $('ocr-progress').classList.remove('hidden');
  $('ocr-results').classList.add('hidden');
  $('ocr-progress-bar').style.width = '5%';
  $('ocr-progress-label').textContent = 'Analysing image quality...';

  addLog('Starting document verification — image analysis + OCR...', 'info');

  try {
    ocrResult = await OCR.verifyDocument(state.selectedIntent, docFile, state.newValues);
    renderOcrResults(ocrResult);

    const logType = ocrResult.score >= 80 ? 'success' : ocrResult.score >= 60 ? 'warn' : 'error';
    addLog(
      `Verification complete — Image: ${ocrResult.imageScore ?? '?'}%, OCR: ${ocrResult.ocrScore ?? '?'}%, Combined: ${ocrResult.score}%`,
      logType
    );

    if (ocrResult.score >= 80) {
      addLog('Score ≥ 80% — auto-advancing in 3 seconds...', 'success');
      showAutoAdvanceToast(ocrResult.score, 3);
    }

  } catch (err) {
    addLog(`Verification error: ${err.message}`, 'error');
    $('ocr-progress').classList.add('hidden');
    $('ocr-results').classList.remove('hidden');
    $('ocr-results').innerHTML = `<div style="color:var(--sf-red);padding:16px;font-size:13px">
      ⚠️ Verification failed: ${err.message}<br>
      <small style="color:var(--sf-gray-4)">Check your internet connection (Tesseract.js requires CDN access on first run)</small>
    </div>`;
  } finally {
    isOcrRunning = false;
    $('btn-run-ocr').disabled = false;
    $('btn-run-ocr').textContent = '🔍 Re-verify';
    $('ocr-progress').classList.add('hidden');
  }
}

// Manual re-verify button
$('btn-run-ocr').addEventListener('click', () => runOcr());

// ── Auto-advance countdown toast ──────────────────────────────────────────────
function showAutoAdvanceToast(score, seconds) {
  // Cancel any existing countdown
  if (autoAdvanceTimer) { clearInterval(autoAdvanceTimer); autoAdvanceTimer = null; }

  // Remove existing toast
  const existing = document.getElementById('auto-advance-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'auto-advance-toast';
  toast.className = 'auto-advance-toast';
  toast.innerHTML = `
    <div class="aat-icon">✅</div>
    <div class="aat-body">
      <div class="aat-title">Score ${score}% — Auto-verified</div>
      <div class="aat-sub">Advancing to confirm step in <strong id="aat-countdown">${seconds}</strong>s</div>
      <div class="aat-bar-track"><div class="aat-bar" id="aat-bar" style="width:100%"></div></div>
    </div>
    <button class="aat-cancel" id="aat-cancel">Cancel</button>`;
  document.body.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => toast.classList.add('aat-visible'));

  let remaining = seconds;
  const totalMs = seconds * 1000;
  const startTime = Date.now();

  autoAdvanceTimer = setInterval(() => {
    remaining = seconds - Math.floor((Date.now() - startTime) / 1000);
    const pct = Math.max(0, ((totalMs - (Date.now() - startTime)) / totalMs) * 100);
    const cd = document.getElementById('aat-countdown');
    const bar = document.getElementById('aat-bar');
    if (cd) cd.textContent = Math.max(0, remaining);
    if (bar) bar.style.width = `${pct}%`;

    if (remaining <= 0) {
      clearInterval(autoAdvanceTimer);
      autoAdvanceTimer = null;
      toast.remove();
      // Auto-advance
      state.docOverride = false;
      buildStep3();
      setStep(3);
      addLog('Auto-advanced to confirm step (score ≥ 80%)', 'success');
    }
  }, 100);

  document.getElementById('aat-cancel').addEventListener('click', () => {
    clearInterval(autoAdvanceTimer);
    autoAdvanceTimer = null;
    toast.remove();
    addLog('Auto-advance cancelled by agent', 'warn');
  });
}

function renderOcrResults(result) {
  $('ocr-results').classList.remove('hidden');

  // Score circle
  const circle = $('ocr-score-circle');
  circle.textContent = `${result.score}%`;
  circle.className = `ocr-results__score ${result.score >= 80 ? 'score--high' : result.score >= 60 ? 'score--mid' : 'score--low'}`;

  // Sub-scores
  const subScores = document.getElementById('ocr-sub-scores');
  if (subScores) {
    subScores.innerHTML = `
      <span class="sub-score">🖼 Image: <strong>${result.imageScore ?? '—'}%</strong></span>
      <span class="sub-score">📝 OCR: <strong>${result.ocrScore ?? '—'}%</strong></span>`;
  }

  // Verdict
  const verdict    = $('ocr-verdict');
  const verdictSub = $('ocr-verdict-sub');
  if (result.score >= 80) {
    verdict.textContent = '✅ Document Verified — High Confidence';
    verdict.style.color = 'var(--sf-green)';
    verdictSub.textContent = `Score ${result.score}% ≥ 80% — auto-advancing to confirm step.`;
    $('btn-doc-next').classList.remove('hidden');
    $('btn-doc-next').className = 'sf-btn sf-btn--success';
    $('btn-doc-next').textContent = '✓ Proceed Now';
    $('btn-skip-ocr').style.display = 'none'; // hide skip when verified
  } else if (result.ok) {
    verdict.textContent = '✅ Document Verified';
    verdict.style.color = 'var(--sf-green)';
    verdictSub.textContent = 'Document passes verification — you may proceed.';
    $('btn-doc-next').classList.remove('hidden');
    $('btn-doc-next').className = 'sf-btn sf-btn--success';
    $('btn-doc-next').textContent = '✓ Proceed to Confirm';
    $('btn-skip-ocr').style.display = 'none';
  } else {
    verdict.textContent = '⚠️ Verification Issues Found';
    verdict.style.color = 'var(--sf-orange)';
    verdictSub.textContent = 'Review the checks below. You may still proceed with supervisor override.';
    $('btn-doc-next').classList.remove('hidden');
    $('btn-doc-next').className = 'sf-btn sf-btn--pending';
    $('btn-doc-next').textContent = '⚠️ Proceed with Override';
  }

  // Checks — split into image and OCR sections
  const imageChecks = result.checks.filter(c =>
    ['Image Resolution','Document Aspect Ratio','Image Content','Image Brightness','Document Structure','Document Color Profile'].includes(c.label)
  );
  const ocrChecks = result.checks.filter(c => !imageChecks.includes(c));

  const renderChecks = (checks) => checks.map(c => `
    <div class="ocr-check-item ${c.pass ? 'ocr-check--pass' : 'ocr-check--fail'}">
      <span class="ocr-check-icon">${c.pass ? '✓' : '✗'}</span>
      <div>
        <div class="ocr-check-label">${c.label}${c.critical ? ' <span class="ocr-critical">required</span>' : ''}</div>
        <div class="ocr-check-detail">${c.detail}</div>
      </div>
    </div>`).join('');

  $('ocr-checks').innerHTML = `
    <div class="ocr-checks-section">
      <div class="ocr-checks-section-title">🖼 Image Quality Checks</div>
      ${renderChecks(imageChecks)}
    </div>
    ${ocrChecks.length ? `
    <div class="ocr-checks-section">
      <div class="ocr-checks-section-title">📝 Document Content Checks (OCR)</div>
      ${renderChecks(ocrChecks)}
    </div>` : ''}`;

  // Extracted fields
  const fields = result.extractedFields;
  if (Object.keys(fields).length > 0) {
    $('ocr-extracted').classList.remove('hidden');
    $('ocr-extracted-fields').innerHTML = Object.entries(fields)
      .map(([k, v]) => `<div class="ocr-field-row"><span class="ocr-field-key">${k}</span><span class="ocr-field-val">${v}</span></div>`)
      .join('');
  }

  // Raw text
  $('ocr-raw-text-content').textContent = result.rawText || '(no text extracted)';
  state.ocrResult = { score: result.score, ok: result.ok, extractedFields: result.extractedFields };
}

$('btn-doc-next').addEventListener('click', () => {
  const override = ocrResult && !ocrResult.ok;
  if (override) {
    addLog('⚠️ Agent proceeding with document override — supervisor review required', 'warn');
    state.docOverride = true;
  } else {
    state.docOverride = false;
  }
  buildStep3();
  setStep(3);
});

// ── SF Cases tab (from Salesforce sandbox via sf_cases.json) ──────────────────
const SF_API_URL = 'http://localhost:5000/api/cases';

function renderSfCasesTable() {
  const cases = JSON.parse(localStorage.getItem('sfcc_sf_cases') || '[]');
  const tbody = document.getElementById('sf-cases-table-body');
  const empty = document.getElementById('sf-cases-empty');
  const badge = document.getElementById('sf-cases-count');

  if (badge) badge.textContent = `${cases.length} cases`;

  if (!cases.length) {
    if (tbody) tbody.innerHTML = '';
    if (empty) empty.classList.remove('hidden');
    return;
  }
  if (empty) empty.classList.add('hidden');

  if (tbody) {
    tbody.innerHTML = cases.map(c => `
      <tr>
        <td><span style="font-family:monospace;font-weight:700">#${c.caseNumber}</span></td>
        <td><span class="sf-badge sf-badge--open">${c.status}</span></td>
        <td>${c.subStatus || '—'}</td>
        <td style="font-weight:600">${c.customerName || '—'}</td>
        <td class="mono">${c.citizenId || '—'}</td>
        <td>${c.newFirstName ? '<span class="audit-after">' + c.newFirstName + '</span>' : '—'}</td>
        <td>${c.newLastName ? '<span class="audit-after">' + c.newLastName + '</span>' : '—'}</td>
        <td>${c.newTitle || '—'}</td>
        <td style="color:var(--sf-gray-4)">${c.oldName || '—'}</td>
        <td>${c.documents && c.documents.length ? c.documents.length + ' files' : '0'}</td>
      </tr>`).join('');
  }
}

// Refresh button — live query from local API server
document.getElementById('btn-refresh-sf').addEventListener('click', async () => {
  const btn    = document.getElementById('btn-refresh-sf');
  const status = document.getElementById('sf-refresh-status');

  btn.disabled = true;
  btn.textContent = '⏳ Querying...';
  status.textContent = 'Connecting to Salesforce...';
  status.style.color = 'var(--sf-blue)';

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout (SF query can be slow)

    const resp = await fetch(SF_API_URL, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    localStorage.setItem('sfcc_sf_cases', JSON.stringify(data.cases));
    renderSfCasesTable();

    status.textContent = `✓ ${data.count} cases loaded — ${new Date().toLocaleTimeString('th-TH')}`;
    status.style.color = 'var(--sf-green)';
    addLog(`SF Refresh: ${data.count} cases loaded from Salesforce`, 'success');
  } catch (e) {
    if (e.name === 'AbortError') {
      status.textContent = '✗ Timeout — API server not responding';
    } else if (e.message.includes('Failed to fetch') || e.message.includes('NetworkError')) {
      status.textContent = '✗ API server not running. Start: python api_server.py';
    } else {
      status.textContent = `✗ ${e.message}`;
    }
    status.style.color = 'var(--sf-red)';
    addLog(`SF Refresh failed: ${e.message || e.name}`, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '🔄 Refresh from Salesforce';
  }
});

// Auto-render if SF cases tab is visible on load
setTimeout(() => renderSfCasesTable(), 500);
