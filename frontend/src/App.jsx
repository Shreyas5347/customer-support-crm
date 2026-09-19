import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "./api";
import "./index.css";

// ── Formatters & Utilities ──────────────────────────────────────────────────
function fmt(dateStr) {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function useToast() {
  const [toasts, setToasts] = useState([]);
  const add = useCallback((msg, type = "success") => {
    const id = Date.now();
    setToasts((t) => [...t, { id, msg, type }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000);
  }, []);
  return { toasts, add };
}

// ── SLA Calculation Helper ──────────────────────────────────────────────────
const SLA_HOURS = { HIGH: 4, MEDIUM: 24, LOW: 48 };

function getSLAInfo(ticket) {
  if (!ticket) return { status: "ON_TIME", label: "On Time", hoursLeft: 24 };

  if (ticket.status === "CLOSED") {
    return { status: "RESOLVED", label: "✅ SLA Met", hoursLeft: 0, text: "Resolved on time" };
  }

  const createdTime = new Date(ticket.created_at).getTime();
  const slaHours = SLA_HOURS[ticket.priority] || 24;
  const dueTime = ticket.sla_due_at
    ? new Date(ticket.sla_due_at).getTime()
    : createdTime + slaHours * 3600000;

  const now = Date.now();
  const diffMs = dueTime - now;
  const diffHours = diffMs / 3600000;

  if (diffMs < 0) {
    const overdueMins = Math.abs(Math.floor(diffMs / 60000));
    const h = Math.floor(overdueMins / 60);
    const m = overdueMins % 60;
    const timeText = h > 0 ? `${h}h ${m}m ago` : `${m}m ago`;
    return {
      status: "BREACHED",
      label: `🚨 BREACHED (${timeText})`,
      hoursLeft: diffHours,
      dueTime,
      text: `Breached ${timeText}`,
    };
  } else if (diffHours <= 2) {
    const minsLeft = Math.floor(diffMs / 60000);
    const h = Math.floor(minsLeft / 60);
    const m = minsLeft % 60;
    const timeText = h > 0 ? `${h}h ${m}m` : `${m}m`;
    return {
      status: "DUE_SOON",
      label: `⏳ DUE SOON (${timeText})`,
      hoursLeft: diffHours,
      dueTime,
      text: `Due in ${timeText}`,
    };
  } else {
    const hours = Math.round(diffHours);
    return {
      status: "ON_TIME",
      label: `🟢 Due in ${hours}h`,
      hoursLeft: diffHours,
      dueTime,
      text: `Due in ~${hours} hours`,
    };
  }
}

// ── Badges ──────────────────────────────────────────────────────────────────
const PRIORITY_ICON = { HIGH: "🔴", MEDIUM: "🟡", LOW: "🟢" };
const CATEGORY_ICON = {
  PAYMENT: "💳", DELIVERY: "📦", ORDER: "🛒",
  ACCOUNT: "👤", TECHNICAL: "🔧", OTHER: "💬"
};
const STATUS_ICON = { OPEN: "🔓", IN_PROGRESS: "⚙️", CLOSED: "✅" };

function PriorityBadge({ p }) {
  const slaTarget = SLA_HOURS[p] ? `${SLA_HOURS[p]}h SLA` : "";
  return (
    <span className={`badge badge-${p?.toLowerCase()}`}>
      {PRIORITY_ICON[p]} {p} ({slaTarget})
    </span>
  );
}

function CategoryBadge({ c }) {
  return <span className="badge badge-category">{CATEGORY_ICON[c] || "💬"} {c}</span>;
}

function StatusBadge({ s }) {
  return <span className={`badge badge-${s?.toLowerCase()}`}>{STATUS_ICON[s]} {s?.replace("_", " ")}</span>;
}

function SLABadge({ ticket }) {
  const sla = getSLAInfo(ticket);
  const className = `badge badge-sla-${sla.status.toLowerCase().replace("_", "")}`;
  return <span className={className}>{sla.label}</span>;
}

// ═════════════════════════════════════════════════════════════════════════════
// 1. DASHBOARD PAGE — Tickets List + SLA Management + Live Search
// ═════════════════════════════════════════════════════════════════════════════
function DashboardPage({ onSelectTicket, onNavigateCreate, toast }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterSLA, setFilterSLA] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [sortBy, setSortBy] = useState("sla"); // "sla" | "newest" | "oldest"
  const debounceRef = useRef(null);

  const loadTickets = useCallback(async (params) => {
    setLoading(true);
    try {
      const data = await api.listTickets(params);
      setTickets(data);
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  // Live search as you type (350ms debounce)
  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      loadTickets({
        search,
        status: filterStatus,
        priority: filterPriority,
        limit: 100,
      });
    }, 350);
    return () => clearTimeout(debounceRef.current);
  }, [search, filterStatus, filterPriority, loadTickets]);

  // SLA Calculation & Client-side SLA filtering & sorting
  const processedTickets = tickets.map((t) => ({
    ...t,
    slaInfo: getSLAInfo(t),
  }));

  const filteredTickets = processedTickets.filter((t) => {
    if (filterSLA === "BREACHED") return t.slaInfo.status === "BREACHED";
    if (filterSLA === "DUE_SOON") return t.slaInfo.status === "DUE_SOON";
    if (filterSLA === "ON_TIME") return t.slaInfo.status === "ON_TIME";
    return true;
  });

  // Prioritization sorting (Breached first -> Due soon -> Open -> Newest)
  const sortedTickets = [...filteredTickets].sort((a, b) => {
    if (sortBy === "sla") {
      // Breached tickets first
      if (a.slaInfo.status === "BREACHED" && b.slaInfo.status !== "BREACHED") return -1;
      if (b.slaInfo.status === "BREACHED" && a.slaInfo.status !== "BREACHED") return 1;
      // Then Due Soon
      if (a.slaInfo.status === "DUE_SOON" && b.slaInfo.status !== "DUE_SOON") return -1;
      if (b.slaInfo.status === "DUE_SOON" && a.slaInfo.status !== "DUE_SOON") return 1;
      // Then by hours left (ascending)
      return a.slaInfo.hoursLeft - b.slaInfo.hoursLeft;
    } else if (sortBy === "newest") {
      return new Date(b.created_at) - new Date(a.created_at);
    } else {
      return new Date(a.created_at) - new Date(b.created_at);
    }
  });

  const stats = {
    total: processedTickets.length,
    open: processedTickets.filter((t) => t.status === "OPEN").length,
    inProgress: processedTickets.filter((t) => t.status === "IN_PROGRESS").length,
    breached: processedTickets.filter((t) => t.slaInfo.status === "BREACHED").length,
    dueSoon: processedTickets.filter((t) => t.slaInfo.status === "DUE_SOON").length,
    closed: processedTickets.filter((t) => t.status === "CLOSED").length,
  };

  const clearFilters = () => {
    setSearch("");
    setFilterStatus("");
    setFilterSLA("");
    setFilterPriority("");
    setSortBy("sla");
  };

  return (
    <div className="portal-main">
      {/* Metrics Banner */}
      <div className="stats-bar">
        <div className="stat-card">
          <div className="stat-number total">{stats.total}</div>
          <div className="stat-label">Total Tickets</div>
        </div>
        <div className="stat-card">
          <div className="stat-number open">{stats.open}</div>
          <div className="stat-label">Open</div>
        </div>
        <div className="stat-card">
          <div className="stat-number inprogress">{stats.inProgress}</div>
          <div className="stat-label">In Progress</div>
        </div>
        <div className="stat-card" style={{ borderColor: stats.breached > 0 ? "var(--high)" : "var(--border)" }}>
          <div className="stat-number breached">{stats.breached}</div>
          <div className="stat-label">🚨 SLA Breached</div>
        </div>
        <div className="stat-card">
          <div className="stat-number duesoon">{stats.dueSoon}</div>
          <div className="stat-label">⏳ SLA Due Soon</div>
        </div>
        <div className="stat-card">
          <div className="stat-number closed">{stats.closed}</div>
          <div className="stat-label">Resolved</div>
        </div>
      </div>

      {/* Controls: Live Search + Filters + SLA Sorting + Create Action */}
      <div className="filters-bar">
        <div className="search-wrap" style={{ flex: 2 }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            id="ticket-search-input"
            className="search-input"
            type="text"
            placeholder="Search by name, email, ticket ID, or subject (works as you type)…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {/* SLA Priority Filter */}
        <select
          id="sla-filter-select"
          className="filter-select"
          value={filterSLA}
          onChange={(e) => setFilterSLA(e.target.value)}
        >
          <option value="">All SLA Statuses</option>
          <option value="BREACHED">🚨 SLA Breached</option>
          <option value="DUE_SOON">⏳ SLA Due Soon</option>
          <option value="ON_TIME">🟢 SLA On Time</option>
        </select>

        {/* Status Filter */}
        <select
          id="status-filter-select"
          className="filter-select"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="">All Ticket Statuses</option>
          <option value="OPEN">🔓 Open</option>
          <option value="IN_PROGRESS">⚙️ In Progress</option>
          <option value="CLOSED">✅ Closed</option>
        </select>

        {/* Priority Filter */}
        <select
          id="priority-filter-select"
          className="filter-select"
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value)}
        >
          <option value="">All Priorities</option>
          <option value="HIGH">🔴 High (4h SLA)</option>
          <option value="MEDIUM">🟡 Medium (24h SLA)</option>
          <option value="LOW">🟢 Low (48h SLA)</option>
        </select>

        {/* Sort By */}
        <select
          id="sort-select"
          className="filter-select"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          style={{ fontWeight: 600, color: "var(--accent)" }}
        >
          <option value="sla">⚡ Sort: SLA Urgency (Breached First)</option>
          <option value="newest">📅 Sort: Newest First</option>
          <option value="oldest">📅 Sort: Oldest First</option>
        </select>

        {(search || filterStatus || filterSLA || filterPriority || sortBy !== "sla") && (
          <button className="btn btn-ghost" onClick={clearFilters}>✕ Reset</button>
        )}

        <button className="btn btn-primary" onClick={onNavigateCreate} style={{ marginLeft: "auto" }}>
          ➕ New Ticket
        </button>
      </div>

      {/* Ticket List Grid */}
      {loading ? (
        <div className="spinner-wrap"><div className="spinner" /></div>
      ) : sortedTickets.length === 0 ? (
        <div className="empty-state">
          <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>🔍</div>
          <h3>No matching tickets found</h3>
          <p>Try adjusting your search criteria or SLA filters.</p>
          <button className="btn btn-primary" onClick={onNavigateCreate} style={{ marginTop: 16 }}>
            Submit a New Ticket
          </button>
        </div>
      ) : (
        <div className="tickets-grid">
          {sortedTickets.map((t) => (
            <div
              key={t.ticket_id}
              className={`ticket-card sla-${t.slaInfo.status.toLowerCase()}`}
              onClick={() => onSelectTicket(t.ticket_id)}
            >
              <div className="ticket-card-header">
                <span className="ticket-card-id">{t.ticket_id}</span>
                <SLABadge ticket={t} />
              </div>

              <h3 className="ticket-card-subject">{t.subject}</h3>

              <div className="ticket-card-customer">
                👤 <strong>{t.customer_name}</strong>
              </div>

              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 4 }}>
                <StatusBadge s={t.status} />
                <PriorityBadge p={t.priority} />
                <CategoryBadge c={t.category} />
              </div>

              <div className="ticket-card-footer">
                <span className="ticket-card-date">Created: {fmt(t.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// 2. CREATE TICKET PAGE — Form with AI Triage & SLA Calculation
// ═════════════════════════════════════════════════════════════════════════════
function CreateTicketPage({ onCreated, toast }) {
  const [form, setForm] = useState({ customer_name: "", customer_email: "", subject: "", description: "" });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const validate = () => {
    const e = {};
    if (!form.customer_name.trim() || form.customer_name.trim().length < 2)
      e.customer_name = "Customer name must be at least 2 characters.";
    if (!form.customer_email.trim() || !/\S+@\S+\.\S+/.test(form.customer_email))
      e.customer_email = "Please enter a valid email address.";
    if (!form.subject.trim() || form.subject.trim().length < 3)
      e.subject = "Subject must be at least 3 characters.";
    if (!form.description.trim() || form.description.trim().length < 10)
      e.description = "Description must be at least 10 characters.";
    return e;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setSubmitting(true);
    try {
      const res = await api.createTicket(form);
      toast("✅ Ticket created! AI priority and SLA target applied.", "success");
      onCreated(res.ticket_id);
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="portal-main" style={{ maxWidth: 740, margin: "20px auto" }}>
      <div className="customer-card">
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 20, paddingBottom: 16, borderBottom: "1px solid var(--border)" }}>
          <div style={{ fontSize: "1.8rem", width: 48, height: 48, borderRadius: 10, background: "var(--accent-light)", display: "flex", alignItems: "center", justify: "center" }}>
            📝
          </div>
          <div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700 }}>Submit New Support Ticket</h2>
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
              AI automatically triages urgency and sets the target SLA turnaround deadline.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="form-grid">
          <div className="form-row">
            <div className="form-field">
              <label className="form-label" htmlFor="create-name">Customer Name <span className="req">*</span></label>
              <input
                id="create-name"
                className="form-input"
                placeholder="e.g. Rahul Sharma"
                value={form.customer_name}
                onChange={(e) => set("customer_name", e.target.value)}
              />
              {errors.customer_name && <span className="field-error">{errors.customer_name}</span>}
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="create-email">Customer Email <span className="req">*</span></label>
              <input
                id="create-email"
                className="form-input"
                type="email"
                placeholder="e.g. rahul@example.com"
                value={form.customer_email}
                onChange={(e) => set("customer_email", e.target.value)}
              />
              {errors.customer_email && <span className="field-error">{errors.customer_email}</span>}
            </div>
          </div>

          <div className="form-field">
            <label className="form-label" htmlFor="create-subject">Issue Title / Subject <span className="req">*</span></label>
            <input
              id="create-subject"
              className="form-input"
              placeholder="e.g. Unable to process checkout payment"
              value={form.subject}
              onChange={(e) => set("subject", e.target.value)}
            />
            {errors.subject && <span className="field-error">{errors.subject}</span>}
          </div>

          <div className="form-field">
            <label className="form-label" htmlFor="create-desc">Detailed Description <span className="req">*</span></label>
            <textarea
              id="create-desc"
              className="form-textarea"
              rows={5}
              placeholder="Describe the issue in detail..."
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
            />
            {errors.description && <span className="field-error">{errors.description}</span>}
          </div>

          <div style={{ background: "var(--surface2)", padding: "12px 16px", borderRadius: 10, border: "1px solid var(--border)", fontSize: "0.85rem", color: "var(--text-muted)" }}>
            ⚡ <strong>Automated SLA Rules:</strong> High Priority = 4 Hours | Medium = 24 Hours | Low = 48 Hours
          </div>

          <button className="btn btn-primary btn-lg w-full" type="submit" disabled={submitting}>
            {submitting ? "⏳ Triaging AI Priority & SLA Target..." : "🚀 Submit Ticket"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// 3. TICKET DETAIL PAGE — View, Update Status & Notes, SLA Audit
// ═════════════════════════════════════════════════════════════════════════════
function TicketDetailPage({ ticketId, onBack, toast }) {
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updateForm, setUpdateForm] = useState({ status: "", notes: "" });
  const [updating, setUpdating] = useState(false);

  const fetchDetail = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getTicket(ticketId);
      setTicket(data);
      setUpdateForm({ status: data.status, notes: "" });
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setLoading(false);
    }
  }, [ticketId, toast]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  const handleUpdate = async () => {
    setUpdating(true);
    try {
      const updated = await api.updateTicket(ticketId, updateForm);
      setTicket(updated);
      setUpdateForm((f) => ({ ...f, notes: "" }));
      toast("✅ Ticket status & internal note saved!", "success");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setUpdating(false);
    }
  };

  const slaInfo = ticket ? getSLAInfo(ticket) : null;

  return (
    <div className="portal-main" style={{ maxWidth: 880, margin: "10px auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
        <button className="btn btn-ghost" onClick={onBack}>
          ← Back to Dashboard
        </button>
        {ticket && <span className="ticket-card-id" style={{ fontSize: "1rem" }}>{ticket.ticket_id}</span>}
      </div>

      {loading ? (
        <div className="spinner-wrap"><div className="spinner" /></div>
      ) : !ticket ? (
        <div className="empty-state">
          <h3>Ticket Not Found</h3>
          <button className="btn btn-primary" onClick={onBack}>Return to Dashboard</button>
        </div>
      ) : (
        <div className="customer-card">
          {/* Header Badges */}
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 }}>
            <SLABadge ticket={ticket} />
            <StatusBadge s={ticket.status} />
            <PriorityBadge p={ticket.priority} />
            <CategoryBadge c={ticket.category} />
          </div>

          <h1 style={{ fontSize: "1.4rem", fontWeight: 700, marginBottom: 16 }}>
            {ticket.subject}
          </h1>

          {/* SLA Tracking Info Card */}
          <div className="detail-section" style={{ background: slaInfo?.status === "BREACHED" ? "#fef2f2" : "var(--surface2)" }}>
            <div className="detail-section-title">⏱️ SLA Target & Resolution Performance</div>
            <div className="detail-grid">
              <div className="detail-row">
                <span className="detail-key">Target SLA Turnaround</span>
                <span className="detail-val">{SLA_HOURS[ticket.priority] || 24} Hours</span>
              </div>
              <div className="detail-row">
                <span className="detail-key">Current SLA Status</span>
                <span className="detail-val" style={{ color: slaInfo?.status === "BREACHED" ? "var(--high)" : "var(--text)" }}>
                  {slaInfo?.text}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-key">SLA Target Deadline</span>
                <span className="detail-val">{fmt(ticket.sla_due_at)}</span>
              </div>
              <div className="detail-row">
                <span className="detail-key">Ticket Created At</span>
                <span className="detail-val">{fmt(ticket.created_at)}</span>
              </div>
            </div>
          </div>

          {/* Ticket Info */}
          <div className="detail-section">
            <div className="detail-section-title">👤 Customer Information</div>
            <div className="detail-grid">
              <div className="detail-row">
                <span className="detail-key">Customer Name</span>
                <span className="detail-val">{ticket.customer_name}</span>
              </div>
              <div className="detail-row">
                <span className="detail-key">Email Address</span>
                <span className="detail-val">{ticket.customer_email}</span>
              </div>
              <div className="detail-row detail-full">
                <span className="detail-key">Issue Description</span>
                <span className="detail-val" style={{ whiteSpace: "pre-wrap", marginTop: 4 }}>{ticket.description}</span>
              </div>
            </div>
          </div>

          {/* AI Summary */}
          {ticket.ai_summary && (
            <div className="detail-section">
              <div className="detail-section-title">🤖 AI Triage Analysis</div>
              <div className="ai-box">
                <p>{ticket.ai_summary}</p>
              </div>
            </div>
          )}

          {/* Internal Notes History */}
          <div className="detail-section">
            <div className="detail-section-title">📋 Internal Agent Notes ({ticket.notes?.length || 0})</div>
            <div className="notes-list">
              {ticket.notes?.length ? (
                ticket.notes.map((n) => (
                  <div key={n.id} className="note-item">
                    <div className="note-text">{n.note_text}</div>
                    <div className="note-date">{fmt(n.created_at)}</div>
                  </div>
                ))
              ) : (
                <p className="no-notes">No internal notes added yet.</p>
              )}
            </div>
          </div>

          {/* Update Action Box */}
          <div className="detail-section" style={{ background: "var(--surface)", border: "2px solid var(--accent)" }}>
            <div className="detail-section-title" style={{ color: "var(--accent)" }}>✏️ Update Ticket Status & Add Note</div>
            <div className="form-grid">
              <div className="form-field">
                <label className="form-label" htmlFor="update-status-select">Change Ticket Status</label>
                <select
                  id="update-status-select"
                  className="form-select"
                  value={updateForm.status}
                  onChange={(e) => setUpdateForm((f) => ({ ...f, status: e.target.value }))}
                >
                  <option value="OPEN">🔓 Open</option>
                  <option value="IN_PROGRESS">⚙️ In Progress</option>
                  <option value="CLOSED">✅ Closed (Resolves SLA Target)</option>
                </select>
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="update-note-text">Add Internal Note (optional)</label>
                <textarea
                  id="update-note-text"
                  className="form-textarea"
                  rows={3}
                  placeholder="e.g. Contacted customer, issue resolved by restoring access..."
                  value={updateForm.notes}
                  onChange={(e) => setUpdateForm((f) => ({ ...f, notes: e.target.value }))}
                />
              </div>

              <button className="btn btn-primary" onClick={handleUpdate} disabled={updating}>
                {updating ? "⏳ Saving Updates…" : "💾 Save Ticket Update"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// MAIN APPLICATION ROOT
// ═════════════════════════════════════════════════════════════════════════════
export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard"); // "dashboard" | "create" | "detail"
  const [selectedTicketId, setSelectedTicketId] = useState(null);
  const { toasts, add: toast } = useToast();

  const handleSelectTicket = (id) => {
    setSelectedTicketId(id);
    setActiveTab("detail");
  };

  return (
    <div className="app-root">
      {/* Top Header */}
      <header className="portal-header">
        <div className="portal-brand" style={{ cursor: "pointer" }} onClick={() => setActiveTab("dashboard")}>
          <div className="portal-logo">💬</div>
          <div>
            <h1>Customer Support CRM</h1>
            <p className="portal-tagline">Where Support Gets Smarter</p>
          </div>
        </div>

        <nav style={{ display: "flex", gap: 10 }}>
          <button
            className={`btn ${activeTab === "dashboard" ? "btn-primary" : "btn-ghost"}`}
            onClick={() => setActiveTab("dashboard")}
          >
            📋 Tickets Dashboard
          </button>

          <button
            className={`btn ${activeTab === "create" ? "btn-primary" : "btn-ghost"}`}
            onClick={() => setActiveTab("create")}
          >
            ➕ New Ticket
          </button>
        </nav>
      </header>

      {/* View Container */}
      <main style={{ flex: 1 }}>
        {activeTab === "dashboard" && (
          <DashboardPage
            onSelectTicket={handleSelectTicket}
            onNavigateCreate={() => setActiveTab("create")}
            toast={toast}
          />
        )}

        {activeTab === "create" && (
          <CreateTicketPage
            onCreated={(id) => handleSelectTicket(id)}
            toast={toast}
          />
        )}

        {activeTab === "detail" && selectedTicketId && (
          <TicketDetailPage
            ticketId={selectedTicketId}
            onBack={() => setActiveTab("dashboard")}
            toast={toast}
          />
        )}
      </main>

      {/* Toast Notifications */}
      <div className="toast-wrap">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.type}`}>{t.msg}</div>
        ))}
      </div>
    </div>
  );
}
