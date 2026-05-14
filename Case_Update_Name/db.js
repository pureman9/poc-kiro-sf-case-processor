/**
 * db.js — In-browser database using localStorage
 * Tables: customers, audit_log
 */

const DB_KEYS = {
  customers:   'sfcc_customers',
  auditLog:    'sfcc_audit_log',
  approvalQueue: 'sfcc_approval_queue',
  seeded:      'sfcc_seeded',
};

// ── Seed data ─────────────────────────────────────────────────────────────────
const SEED_CUSTOMERS = [
  { cid: 'C001234', title: 'นาย',    firstName: 'สมชาย',   lastName: 'ใจดี',      nationalId: '1100100012345', dob: '1985-03-15', phone: '081-234-5678', email: 'somchai@email.com' },
  { cid: 'C002345', title: 'นาง',    firstName: 'สมหญิง',  lastName: 'รักดี',     nationalId: '1100200023456', dob: '1990-07-22', phone: '082-345-6789', email: 'somying@email.com' },
  { cid: 'C003456', title: 'นางสาว', firstName: 'มาลี',    lastName: 'สุขใจ',     nationalId: '1100300034567', dob: '1995-11-08', phone: '083-456-7890', email: 'malee@email.com'   },
  { cid: 'C004567', title: 'นาย',    firstName: 'วิชัย',   lastName: 'เจริญ',     nationalId: '1100400045678', dob: '1978-01-30', phone: '084-567-8901', email: 'wichai@email.com'  },
  { cid: 'C005678', title: 'นาง',    firstName: 'สุดา',    lastName: 'มีสุข',     nationalId: '1100500056789', dob: '1982-09-14', phone: '085-678-9012', email: 'suda@email.com'    },
  { cid: 'C006789', title: 'นาย',    firstName: 'ประสิทธิ์', lastName: 'ดีงาม',   nationalId: '1100600067890', dob: '1970-05-25', phone: '086-789-0123', email: 'prasit@email.com'  },
  { cid: 'C007890', title: 'นางสาว', firstName: 'กนกวรรณ', lastName: 'แสงทอง',   nationalId: '1100700078901', dob: '1998-12-03', phone: '087-890-1234', email: 'kanok@email.com'   },
  { cid: 'C008901', title: 'นาย',    firstName: 'อนุชา',   lastName: 'พรมมา',     nationalId: '1100800089012', dob: '1988-06-18', phone: '088-901-2345', email: 'anucha@email.com'  },
];

// ── Core DB operations ────────────────────────────────────────────────────────
const DB = {

  /** Seed initial data if not already done */
  seed() {
    if (localStorage.getItem(DB_KEYS.seeded)) return;
    const customers = {};
    SEED_CUSTOMERS.forEach(c => { customers[c.cid] = { ...c }; });
    localStorage.setItem(DB_KEYS.customers, JSON.stringify(customers));
    localStorage.setItem(DB_KEYS.auditLog,  JSON.stringify([]));
    localStorage.setItem(DB_KEYS.seeded, '1');
  },

  /** Reset to seed data (for demo purposes) */
  reset() {
    localStorage.removeItem(DB_KEYS.seeded);
    localStorage.removeItem(DB_KEYS.customers);
    localStorage.removeItem(DB_KEYS.auditLog);
    localStorage.removeItem(DB_KEYS.approvalQueue);
    this.seed();
  },

  // ── Customers ──────────────────────────────────────────────────────────────

  getAllCustomers() {
    return JSON.parse(localStorage.getItem(DB_KEYS.customers) || '{}');
  },

  getCustomer(cid) {
    const all = this.getAllCustomers();
    return all[cid] || null;
  },

  updateCustomer(cid, fieldUpdates) {
    const all = this.getAllCustomers();
    if (!all[cid]) return { ok: false, reason: 'CID_NOT_FOUND' };
    all[cid] = { ...all[cid], ...fieldUpdates };
    localStorage.setItem(DB_KEYS.customers, JSON.stringify(all));
    return { ok: true };
  },

  // ── Audit log ──────────────────────────────────────────────────────────────

  getAuditLog() {
    return JSON.parse(localStorage.getItem(DB_KEYS.auditLog) || '[]');
  },

  addAuditEntry(entry) {
    const log = this.getAuditLog();
    log.unshift({ id: Date.now(), ...entry }); // newest first
    localStorage.setItem(DB_KEYS.auditLog, JSON.stringify(log));
  },

  clearAuditLog() {
    localStorage.setItem(DB_KEYS.auditLog, JSON.stringify([]));
  },

  // ── Approval queue ─────────────────────────────────────────────────────────

  getApprovalQueue() {
    return JSON.parse(localStorage.getItem(DB_KEYS.approvalQueue) || '[]');
  },

  addApprovalRequest(req) {
    const queue = this.getApprovalQueue();
    queue.unshift({ id: `APR-${Date.now()}`, submittedAt: new Date().toISOString(), status: 'PENDING', ...req });
    localStorage.setItem(DB_KEYS.approvalQueue, JSON.stringify(queue));
    return queue[0].id;
  },

  updateApprovalStatus(id, status, reviewedBy, remarks) {
    const queue = this.getApprovalQueue();
    const item  = queue.find(r => r.id === id);
    if (!item) return false;
    item.status     = status;   // APPROVED | REJECTED
    item.reviewedBy = reviewedBy;
    item.reviewedAt = new Date().toISOString();
    item.remarks    = remarks || '';
    localStorage.setItem(DB_KEYS.approvalQueue, JSON.stringify(queue));
    return true;
  },

  clearApprovalQueue() {
    localStorage.setItem(DB_KEYS.approvalQueue, JSON.stringify([]));
  },
};

// Auto-seed on load
DB.seed();
