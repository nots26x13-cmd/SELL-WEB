/**
 * Shared API client for every page.
 * Set API_BASE_URL to wherever the FastAPI backend is deployed.
 */
const API_BASE_URL = window.ARAFAT_API_BASE_URL || "https://api.arafatcodex.shop";

/** Reads the logged-in Telegram user if this is running inside Telegram;
 *  otherwise checks for a logged-in email/password web session
 *  (see login.html / signup.html); otherwise falls back to a local demo id
 *  so pages still work in a normal browser during development. */
let _sessionUserChecked = false;
let _sessionUser = null;

async function getCurrentUserId() {
  try {
    const tg = window.Telegram && window.Telegram.WebApp;
    const tgUser = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
    if (tgUser && tgUser.id) return `tg-${tgUser.id}`;
  } catch (e) { /* not running inside Telegram */ }

  if (!_sessionUserChecked) {
    _sessionUserChecked = true;
    try {
      _sessionUser = await apiFetch("/api/auth/me");
    } catch (e) {
      _sessionUser = null;
    }
  }
  if (_sessionUser && _sessionUser.id) return _sessionUser.id;

  return localStorage.getItem("ac_demo_user_id") || "demo-user";
}

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const isJson = res.headers.get("content-type")?.includes("application/json");
  const body = isJson ? await res.json() : await res.text();
  if (!res.ok) {
    const message = (isJson && body.detail) || res.statusText;
    throw new Error(message);
  }
  return body;
}

const Api = {
  signup: (name, email, password) =>
    apiFetch("/api/auth/signup", { method: "POST", body: JSON.stringify({ name, email, password }) }),
  login: (email, password) =>
    apiFetch("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logout: () => apiFetch("/api/auth/logout", { method: "POST" }),
  me: () => apiFetch("/api/auth/me"),

  listProducts: () => apiFetch("/api/products"),
  getProduct: (id) => apiFetch(`/api/products/${id}`),
  getPublicSettings: () => apiFetch("/api/settings/public"),
  checkNickname: (uid) => apiFetch(`/api/nickname?uid=${encodeURIComponent(uid)}`),

  getBalance: (userId) => apiFetch(`/api/wallet/balance/${userId}`),
  createDepositIntent: (userId, amountUsdt) =>
    apiFetch(`/api/wallet/deposit/intent/${userId}`, {
      method: "POST",
      body: JSON.stringify({ amount_usdt: amountUsdt }),
    }),
  verifyBinanceDeposit: (userId, txId, expectedAmountUsdt) =>
    apiFetch(`/api/wallet/deposit/binance/verify/${userId}`, {
      method: "POST",
      body: JSON.stringify({ tx_id: txId, expected_amount_usdt: expectedAmountUsdt }),
    }),

  createOrder: (userId, productId, packageId, playerUid) =>
    apiFetch(`/api/orders/${userId}`, {
      method: "POST",
      body: JSON.stringify({ product_id: productId, package_id: packageId, player_uid: playerUid }),
    }),
  listMyOrders: (userId) => apiFetch(`/api/orders/user/${userId}`),
};

function bdt(amount) {
  return `৳${Number(amount).toLocaleString("en-BD")}`;
}

function qs(name) {
  return new URLSearchParams(window.location.search).get(name);
}
