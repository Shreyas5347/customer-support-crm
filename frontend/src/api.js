const defaultDevUrl = "http://localhost:8000";
const defaultProdUrl = "https://customer-support-crm-h9tx.onrender.com";

const rawUrl =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  (import.meta.env.MODE === "production" ? defaultProdUrl : defaultDevUrl);

const BASE_URL = rawUrl.replace(/\/$/, "");

async function request(path, options = {}) {
  const { headers, ...restOptions } = options;
  const res = await fetch(`${BASE_URL}${path}`, {
    ...restOptions,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = data?.error?.message || data?.detail || "Something went wrong.";
    throw new Error(msg);
  }
  return data;
}

function buildQuery(params) {
  const q = new URLSearchParams();
  for (const [key, val] of Object.entries(params)) {
    if (val !== null && val !== undefined && val !== "") {
      q.set(key, val);
    }
  }
  const str = q.toString();
  return str ? `?${str}` : "";
}

export const api = {
  // Customer endpoints
  createTicket: (body) =>
    request("/api/tickets", { method: "POST", body: JSON.stringify(body) }),
  trackTicket: (ticket_id, email) =>
    request(`/api/tickets/track${buildQuery({ ticket_id, email })}`),

  // Agent endpoints (requires token)
  login: (body) =>
    request("/api/auth/login", { method: "POST", body: JSON.stringify(body) }),
  listTickets: (params = {}, token) =>
    request(`/api/tickets${buildQuery(params)}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    }),
  getTicket: (ticketId, token) =>
    request(`/api/tickets/${ticketId}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    }),
  updateTicket: (ticketId, body, token) =>
    request(`/api/tickets/${ticketId}`, {
      method: "PUT",
      body: JSON.stringify(body),
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    }),
};
